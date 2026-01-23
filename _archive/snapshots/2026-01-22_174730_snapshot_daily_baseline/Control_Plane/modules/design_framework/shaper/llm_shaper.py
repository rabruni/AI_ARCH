"""LLM-Powered Shaper CLI.

Uses Claude API as a proposal engine for natural language artifact shaping.
Token-efficient design: minimal context, haiku model, compact prompts.

Flow: User Input → LLM → JSON Proposal → Python Validation → State Update
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Add repo root for imports
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from Control_Plane.modules.slots.llm_anthropic import AnthropicProvider
from Control_Plane.modules.slots.interfaces import Message

from .models import ShaperModel, SpecModel
from .state_machine import ShaperStateMachine
from .renderers import render_work_item, render_spec
from .output_safety import write_output, get_default_filename


# Compact system prompt for token efficiency - STRICT NO INFERENCE
SYSTEM_PROMPT = """You are Shaper. Extract ONLY explicit user statements into JSON. NO prose.

STRICT RULES:
- Extract ONLY what user explicitly states. NEVER infer, expand, or add content.
- L3 meta: ID, Title, Status, ALTITUDE (extract exact values if stated)
- L3 fields: objective, scope, plan, acceptance (extract VERBATIM, no rewording)
- "show me what you have" → {"action":"REVEAL"}
- "freeze it" → {"action":"FREEZE"}

OUTPUT (one JSON object):
{"altitude":"L3"|"L4"|null,"action":"ASK"|"PROPOSE"|"REVEAL"|"FREEZE","content":{"fields":{"field":"value"}}}

CRITICAL: For "plan" field, ONLY include steps user explicitly listed. NEVER add steps.
If user says "steps: 1. X 2. Y" → plan: ["X", "Y"] (verbatim)
If no explicit steps given → action: "ASK", question: "What are the implementation steps?"

For meta fields, extract EXACT values: "ID is ABC" → ID: "ABC"
"""


class LLMShaper:
    """LLM-powered artifact shaper using Claude as proposal engine."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        model: str = "claude-3-haiku-20240307",  # Token-efficient
        max_history: int = 2,  # Keep only last N turns
    ):
        self.output_dir = output_dir or Path(".")
        self.max_history = max_history

        # LLM provider
        self.llm = AnthropicProvider(model=model)
        if not self.llm.is_available():
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        # State
        self.machine = ShaperStateMachine()
        self.model: Optional[ShaperModel | SpecModel] = None
        self.altitude: Optional[str] = None
        self.history: list[dict] = []  # Minimal conversation history
        self.total_tokens = 0

    def _build_context(self) -> str:
        """Build minimal context for LLM (token-efficient)."""
        lines = []

        if self.altitude:
            lines.append(f"ALTITUDE: {self.altitude} (locked)")

        if self.model:
            missing = self.model.missing_sections()
            if missing:
                lines.append(f"MISSING: {', '.join(missing)}")
            else:
                lines.append("STATUS: All fields complete")

        return "\n".join(lines) if lines else "NEW SESSION"

    def _call_llm(self, user_input: str) -> dict:
        """Call LLM and parse JSON response."""
        # Build messages with minimal history
        messages = [Message(role="system", content=SYSTEM_PROMPT)]

        # Add context as a system-like user message
        context = self._build_context()
        if context != "NEW SESSION":
            messages.append(Message(role="user", content=f"[CONTEXT]\n{context}"))
            messages.append(Message(role="assistant", content='{"action":"PROPOSE","content":{}}'))

        # Add recent history (token-efficient: only last N turns)
        for turn in self.history[-self.max_history:]:
            messages.append(Message(role="user", content=turn["user"]))
            messages.append(Message(role="assistant", content=turn["assistant"]))

        # Add current input
        messages.append(Message(role="user", content=user_input))

        # Call LLM with low max_tokens for efficiency
        response = self.llm.chat(messages, max_tokens=512, temperature=0)
        self.total_tokens += response.tokens_used

        # Parse JSON
        try:
            # Handle potential markdown code blocks
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except json.JSONDecodeError:
            return {"action": "ERROR", "content": {"error": f"Invalid JSON: {response.content[:100]}"}}

    def _apply_proposal(self, proposal: dict) -> str:
        """Apply LLM proposal to state machine. Returns response for user."""
        action = proposal.get("action", "ERROR")
        content = proposal.get("content", {})
        proposed_altitude = proposal.get("altitude")

        # Handle altitude detection
        if proposed_altitude in ("L3", "L4") and self.altitude is None:
            self.altitude = proposed_altitude
            self.machine.start_shaping(proposed_altitude)
            if proposed_altitude == "L3":
                self.model = ShaperModel()
            else:
                self.model = SpecModel()
            # Set ALTITUDE meta field
            self.model.meta["ALTITUDE"] = proposed_altitude

        # Process fields first (regardless of action)
        changes = []
        fields = content.get("fields", {})
        if fields and self.model is not None:
            for field, value in fields.items():
                if not value:
                    continue

                # Normalize field name
                field_lower = field.lower()

                # Map to META_FIELDS exact case: ID, Title, Status, ALTITUDE
                meta_key_map = {"id": "ID", "title": "Title", "status": "Status", "altitude": "ALTITUDE"}

                # Meta fields
                if field_lower in meta_key_map:
                    meta_key = meta_key_map[field_lower]
                    if not self.model.meta.get(meta_key):  # Only set if not already set
                        self.model.meta[meta_key] = str(value)
                        changes.append(meta_key)
                # Content fields
                elif hasattr(self.model, field_lower):
                    attr = getattr(self.model, field_lower)
                    if isinstance(attr, list):
                        # Prevent duplicates
                        if isinstance(value, list):
                            for v in value:
                                if str(v) not in attr:
                                    attr.append(str(v))
                                    changes.append(field_lower)
                        else:
                            if str(value) not in attr:
                                attr.append(str(value))
                                changes.append(field_lower)

            if changes:
                self.machine.on_edit()

        # Handle actions
        if action == "ASK":
            question = content.get("question", "Could you clarify?")
            if changes:
                return f"Captured: {', '.join(set(changes))}. {question}"
            return question

        elif action == "PROPOSE":
            if self.model is None:
                return "Please specify if this is a work item (L3) or spec (L4)."

            # Fields already processed above
            missing = self.model.missing_sections()
            if missing:
                return f"Captured: {', '.join(set(changes)) if changes else 'nothing new'}. Still need: {', '.join(missing)}"
            return "All fields captured. Say 'show me what you have' to review."

        elif action == "REVEAL":
            if self.model is None:
                return "Nothing to show yet. Start by describing your task or spec."

            self.model.revealed_once = True
            self.machine.reveal()

            # Render current state
            if self.altitude == "L3":
                rendered = render_work_item(self.model)
            else:
                rendered = render_spec(self.model)

            missing = self.model.missing_sections()
            status = f"\n\nMissing: {', '.join(missing)}" if missing else "\n\nReady to freeze!"
            return f"--- Current Draft ---\n{rendered}{status}"

        elif action == "FREEZE":
            if self.model is None:
                return "Nothing to freeze."
            if not self.model.revealed_once:
                return "Please review first: 'show me what you have'"

            missing = self.model.missing_sections()
            if missing:
                return f"Cannot freeze. Missing: {', '.join(missing)}"

            # L4 phase confirmation check
            if isinstance(self.model, SpecModel) and not self.model.phases_confirmed:
                return "L4 phases need confirmation. Say 'confirm phases' first."

            # Freeze and write
            self.machine.freeze(self.model)

            if self.altitude == "L3":
                content = render_work_item(self.model)
            else:
                content = render_spec(self.model)

            filename = get_default_filename(self.altitude)
            output_path = write_output(self.output_dir / filename, content)

            # Reset for next session
            tokens_used = self.total_tokens
            self._reset()

            return f"Frozen to: {output_path}\n(Used {tokens_used} tokens)"

        elif action == "ERROR":
            return f"Error: {content.get('error', 'Unknown error')}"

        return "I didn't understand that. Try again?"

    def _reset(self):
        """Reset state for new session."""
        self.machine = ShaperStateMachine()
        self.model = None
        self.altitude = None
        self.history = []
        self.total_tokens = 0

    def process(self, user_input: str) -> str:
        """Process user input and return response."""
        # Special commands (bypass LLM for efficiency)
        lower = user_input.strip().lower()
        if lower == "confirm phases" and isinstance(self.model, SpecModel):
            self.model.confirm_phases()
            return "Phases confirmed."
        if lower == "reset":
            self._reset()
            return "Session reset."
        if lower == "tokens":
            return f"Tokens used this session: {self.total_tokens}"

        # Call LLM
        proposal = self._call_llm(user_input)

        # Store in history (compact format)
        self.history.append({
            "user": user_input[:200],  # Truncate for token efficiency
            "assistant": json.dumps(proposal)[:200],
        })

        # Apply and return response
        return self._apply_proposal(proposal)

    def run(self) -> int:
        """Run interactive loop."""
        print("═" * 50)
        print("  SHAPER v2 (LLM-Powered)")
        print("═" * 50)
        print("Describe your task or spec in natural language.")
        print("Commands: 'show me what you have', 'freeze it', 'reset', 'tokens'")
        print("═" * 50)
        print()

        while True:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit", "q"):
                    break

                response = self.process(user_input)
                print(f"\n{response}\n")

            except KeyboardInterrupt:
                print("\n")
                break
            except EOFError:
                break

        return 0


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM-Powered Shaper CLI")
    parser.add_argument("--output-dir", type=Path, default=Path("."),
                        help="Output directory for artifacts")
    parser.add_argument("--model", default="claude-3-haiku-20240307",
                        help="Claude model to use")
    args = parser.parse_args()

    try:
        shaper = LLMShaper(output_dir=args.output_dir, model=args.model)
        return shaper.run()
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
