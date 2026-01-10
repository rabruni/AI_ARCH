"""The Assist - Core Orchestrator

The main brain. Handles conversation, context, and AI interaction.
"""
import os
from datetime import datetime
import anthropic
from typing import Optional

from the_assist.config.settings import MODEL, MAX_TOKENS, PROMPTS_DIR, MEMORY_DIR
from the_assist.core.memory import Memory  # v1 - kept for conversation saving
from the_assist.core.memory_v2 import CompressedMemory, PATTERN_CODES
from the_assist.core.proactive import ProactiveEngine
from the_assist.core.ai_reflection import AIReflection


class Orchestrator:
    """The cognitive core of The Assist."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.memory = CompressedMemory()  # v2 compressed
        self.memory_v1 = Memory()  # v1 kept for conversation saving
        self.proactive = ProactiveEngine()  # Intuition-first interaction
        self.system_prompt = self._load_system_prompt()
        self.conversation_history = []
        self._last_user_input = None  # For reaction tracking

    def _load_system_prompt(self) -> str:
        """Load the system prompt."""
        path = os.path.join(PROMPTS_DIR, 'system.md')
        with open(path, 'r') as f:
            return f.read()

    def _get_ai_behavioral_guidance(self) -> str:
        """
        Get behavioral guidance from AI reflection - the feedback loop.
        Recent failures, improvements, and patterns inform current behavior.
        """
        try:
            reflector = AIReflection()
            summary = reflector.get_ai_performance_summary()

            guidance_parts = []

            # Recent failures to avoid
            failures = summary.get("recent_failures", [])
            if failures:
                guidance_parts.append("AVOID:" + "|".join(f[:40] for f in failures[-2:]))

            # Improvement actions to implement
            improvements = summary.get("improvement_actions", [])
            if improvements:
                guidance_parts.append("IMPROVE:" + "|".join(i[:40] for i in improvements[-2:]))

            # Recent strengths to continue
            strengths = summary.get("recent_strengths", [])
            if strengths:
                guidance_parts.append("CONTINUE:" + "|".join(s[:40] for s in strengths[-2:]))

            # Trend direction
            trend = summary.get("trend_direction", "unknown")
            if trend in ["declining", "improving"]:
                guidance_parts.append(f"TREND:{trend}")

            # Low-scoring dimensions to focus on
            scores = summary.get("avg_quality_scores", {})
            low_scores = [dim for dim, score in scores.items() if score and score < 0.6]
            if low_scores:
                guidance_parts.append("FOCUS:" + "|".join(low_scores[:3]))

            return "\n".join(guidance_parts) if guidance_parts else ""

        except Exception:
            return ""  # Graceful degradation

    def _build_full_context(self) -> str:
        """Build full system context including memory (v2 compressed)."""
        memory_context = self.memory.build_context()
        ai_guidance = self._get_ai_behavioral_guidance()
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")

        context = f"""{self.system_prompt}

---

# Context

DATE:{date_str}|TIME:{time_str}

{memory_context}
"""
        # Add AI behavioral guidance if available (the feedback loop)
        if ai_guidance:
            context += f"""
# Self-Calibration (from recent session analysis)
{ai_guidance}
"""
        return context

    def get_opening(self) -> str:
        """Get intuition-based opening instead of generic prompt."""
        return self.proactive.generate_opening()

    def chat(self, user_message: str) -> str:
        """Process a user message and return response."""
        # Track for reaction analysis
        if self._last_user_input is None and len(self.conversation_history) == 0:
            # This is first response after opening - analyze reaction
            reaction = self.proactive.analyze_response_for_reaction(user_message)
            self.proactive.record_reaction(reaction)

        self._last_user_input = user_message

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Build context
        system_context = self._build_full_context()

        # Call Claude
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_context,
            messages=self.conversation_history
        )

        # Extract response
        assistant_message = response.content[0].text

        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def process_for_memory(self, user_input: str, ai_response: str):
        """
        Extract memory items in compressed v2 format.
        AI extracts structured data, not prose.
        """
        pattern_codes_str = ", ".join(PATTERN_CODES.keys())

        extraction_prompt = f"""Extract memory items from this exchange in COMPRESSED format.

User: {user_input}
Assistant: {ai_response}

Return JSON with these fields (only include if relevant):
{{
    "active": ["topic:status:detail"],     // New active threads, format topic:status:detail
    "commits": ["what:when:context"],      // New commitments, format what:when:context
    "people": [{{"name":"x","rel":"work_colleague|family|friend","tags":["tag1"]}}],
    "patterns": ["code"],                  // From: {pattern_codes_str}
    "clear_commits": ["topic"]             // Commits that are now done (topic prefix to remove)
}}

Be aggressive about compression. Use codes not prose. Return ONLY valid JSON, or {{}} if nothing."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": extraction_prompt}]
        )

        try:
            import json
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
            extracted = json.loads(text.strip())

            # Update compressed memory
            for item in extracted.get('active', []):
                self.memory.add_active(item)

            for item in extracted.get('commits', []):
                self.memory.add_commit(item)

            for topic in extracted.get('clear_commits', []):
                self.memory.clear_commit(topic)

            for person in extracted.get('people', []):
                if isinstance(person, dict) and 'name' in person:
                    self.memory.add_person(
                        person['name'],
                        person.get('rel', 'unknown'),
                        person.get('tags', [])
                    )

            for code in extracted.get('patterns', []):
                self.memory.add_pattern(code)

        except (json.JSONDecodeError, KeyError):
            pass  # Silently fail - memory extraction is nice-to-have

    def end_session(self, summary: Optional[str] = None):
        """End the current session and save conversation."""
        if self.conversation_history:
            # If no summary provided, ask AI to generate one
            if not summary and len(self.conversation_history) > 2:
                summary_prompt = "Summarize this conversation in one sentence for future reference."
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=100,
                    messages=self.conversation_history + [{"role": "user", "content": summary_prompt}]
                )
                summary = response.content[0].text

            # Use v1 memory for conversation archival
            self.memory_v1.save_conversation(self.conversation_history, summary)
            self.conversation_history = []
