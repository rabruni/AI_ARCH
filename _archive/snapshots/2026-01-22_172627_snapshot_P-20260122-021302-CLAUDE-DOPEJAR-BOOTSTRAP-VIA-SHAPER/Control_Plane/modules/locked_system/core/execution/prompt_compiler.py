"""Prompt Compiler - Enforces prompt precedence.

Assembles prompts with strict precedence:
1. Agent context (style, domain, questions) - SANDBOXED
2. Executor constraints (altitude, stance behaviors)
3. Core laws (ABSOLUTE, cannot be overridden)

Last position = highest precedence.
"""
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class AgentContext:
    """What an agent can provide (sandboxed, not authority)."""
    name: str
    style_profile: dict              # Tone, verbosity, etc.
    domain_focus: list[str]          # Topics this agent specializes in
    bootstrap_content: str           # Agent's onboarding script
    proposed_questions: list[str]    # Questions agent wants to ask


class PromptCompiler:
    """
    Assembles prompts with strict precedence.

    Order (last wins for conflicts):
    1. Agent context (style, domain, questions) - SANDBOXED
    2. Executor constraints (altitude, stance behaviors)
    3. Core laws (ABSOLUTE, cannot be overridden)

    Key invariant: Core laws ALWAYS appear last.
    """

    def __init__(self, core_laws_path: Optional[Path] = None):
        """Initialize with path to core laws (system prompt)."""
        self._core_laws_path = core_laws_path
        self._core_laws: Optional[str] = None

        if core_laws_path and core_laws_path.exists():
            self._core_laws = core_laws_path.read_text()

    def set_core_laws(self, laws: str):
        """Set core laws directly."""
        self._core_laws = laws

    def load_core_laws(self, path: Path):
        """Load core laws from file."""
        if path.exists():
            self._core_laws = path.read_text()
            self._core_laws_path = path

    def compile(
        self,
        agent_context: Optional[AgentContext] = None,
        executor_constraints: Optional[dict] = None,
    ) -> str:
        """
        Compile final prompt with precedence enforcement.

        Returns assembled prompt string.
        """
        parts = []

        # 1. Agent context goes first (can be overridden)
        if agent_context:
            parts.append(self._sandbox_agent_context(agent_context))

        # 2. Executor constraints next
        if executor_constraints:
            parts.append(self._format_constraints(executor_constraints))

        # 3. Laws ALWAYS LAST (highest precedence)
        if self._core_laws:
            parts.append(f"\n\n## CORE LAWS (NON-NEGOTIABLE)\n{self._core_laws}")

        return "\n\n".join(filter(None, parts))

    def _sandbox_agent_context(self, context: AgentContext) -> str:
        """
        Format agent context with sandboxing.

        Agent content is clearly bounded and cannot override core behavior.
        """
        parts = []

        parts.append(f"## Agent: {context.name}")
        parts.append("(Agent context - advisory only, does not override core behavior)")

        if context.style_profile:
            style_str = ", ".join(f"{k}: {v}" for k, v in context.style_profile.items())
            parts.append(f"\nStyle preferences: {style_str}")

        if context.domain_focus:
            parts.append(f"Domain focus: {', '.join(context.domain_focus)}")

        if context.bootstrap_content:
            # Truncate and sandbox bootstrap content
            bootstrap = context.bootstrap_content[:500]
            if len(context.bootstrap_content) > 500:
                bootstrap += "... [truncated]"
            parts.append(f"\nAgent context:\n{bootstrap}")

        if context.proposed_questions:
            questions = "\n".join(f"- {q}" for q in context.proposed_questions[:3])
            parts.append(f"\nProposed questions (agent may want to explore):\n{questions}")

        return "\n".join(parts)

    def _format_constraints(self, constraints: dict) -> str:
        """Format executor constraints."""
        parts = ["## Behavioral Constraints"]

        if "style" in constraints:
            parts.append(f"\nResponse style: {constraints['style']}")

        if "structure" in constraints:
            parts.append(f"Structure: {constraints['structure']}")

        if "max_length" in constraints:
            parts.append(f"Target length: up to {constraints['max_length']} words")

        if "emphasis" in constraints:
            parts.append(f"\nMode emphasis: {constraints['emphasis']}")

        if "actions" in constraints:
            parts.append(f"Recommended actions: {', '.join(constraints['actions'])}")

        if "avoid" in constraints:
            parts.append(f"Avoid: {', '.join(constraints['avoid'])}")

        if "commitment_frame" in constraints:
            parts.append(f"\nActive commitment: {constraints['commitment_frame']}")

        if "success_criteria" in constraints:
            parts.append(f"Success criteria: {', '.join(constraints['success_criteria'])}")

        if "non_goals" in constraints:
            parts.append(f"Non-goals (avoid): {', '.join(constraints['non_goals'])}")

        return "\n".join(parts)

    def validate_no_override(self, content: str) -> list[str]:
        """
        Check content for attempts to override core laws.

        Returns list of detected override attempts.
        """
        violations = []

        override_patterns = [
            "ignore previous",
            "disregard above",
            "override",
            "forget the rules",
            "you are now",
            "new instructions",
            "system prompt",
        ]

        content_lower = content.lower()
        for pattern in override_patterns:
            if pattern in content_lower:
                violations.append(f"Detected potential override attempt: '{pattern}'")

        return violations

    def get_precedence_info(self) -> dict:
        """Get info about current precedence configuration."""
        return {
            "has_core_laws": self._core_laws is not None,
            "core_laws_path": str(self._core_laws_path) if self._core_laws_path else None,
            "precedence_order": [
                "1. Agent context (lowest)",
                "2. Executor constraints",
                "3. Core laws (highest - non-negotiable)"
            ]
        }
