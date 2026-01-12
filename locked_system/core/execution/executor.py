"""Executor - Response Generation.

Generates responses within:
- Commitment bounds (from slow loop)
- Altitude constraints (from HRM)
- Stance behavioral constraints
"""
from dataclasses import dataclass
from typing import Optional, Callable, Any
from datetime import datetime

from locked_system.core.governance.stance import Stance
from locked_system.core.execution.hrm import HRMAssessment, Altitude
from locked_system.memory.slow import CommitmentLease
from locked_system.memory.fast import FastMemory, InteractionSignals


@dataclass
class ExecutionContext:
    """Context for response execution."""
    user_input: str
    stance: Stance
    hrm_assessment: HRMAssessment
    commitment: Optional[CommitmentLease]
    conversation_history: list[dict]


@dataclass
class ExecutionResult:
    """Result of response execution."""
    response: str
    altitude_used: Altitude
    stance_used: Stance
    execution_notes: list[str]
    timestamp: datetime


class Executor:
    """
    Response executor.

    Operates within constraints set by slow loop.
    Uses HRM assessment for depth calibration.
    """

    # Altitude-based response templates
    ALTITUDE_GUIDANCE = {
        Altitude.L1_ACKNOWLEDGE: {
            "max_length": 50,
            "style": "brief, confirming",
            "structure": "single sentence"
        },
        Altitude.L2_FASTLANE: {
            "max_length": 150,
            "style": "direct, efficient",
            "structure": "1-2 paragraphs"
        },
        Altitude.L3_CONSIDERED: {
            "max_length": 300,
            "style": "thoughtful, balanced",
            "structure": "structured response"
        },
        Altitude.L4_EXPLORATORY: {
            "max_length": 500,
            "style": "exploratory, nuanced",
            "structure": "multi-part exploration"
        },
        Altitude.L5_SYNTHESIS: {
            "max_length": 800,
            "style": "integrative, comprehensive",
            "structure": "synthesis with multiple perspectives"
        },
    }

    # Stance-based behavioral modifiers
    STANCE_BEHAVIORS = {
        Stance.SENSEMAKING: {
            "emphasis": "understanding, clarifying",
            "actions": ["ask clarifying questions", "reframe", "explore context"],
            "avoid": ["premature solutions", "rushing to action"]
        },
        Stance.DISCOVERY: {
            "emphasis": "generating options, brainstorming",
            "actions": ["propose alternatives", "diverge", "prototype ideas"],
            "avoid": ["narrowing too soon", "evaluating ideas"]
        },
        Stance.EXECUTION: {
            "emphasis": "delivering on commitment",
            "actions": ["implement", "progress", "complete tasks"],
            "avoid": ["scope creep", "re-questioning the frame"]
        },
        Stance.EVALUATION: {
            "emphasis": "assessing outcomes",
            "actions": ["measure progress", "compare to goals", "identify gaps"],
            "avoid": ["new execution", "changing goals mid-assessment"]
        },
    }

    def __init__(
        self,
        fast_memory: FastMemory,
        llm_callable: Optional[Callable[[str], str]] = None
    ):
        self.memory = fast_memory
        self._llm = llm_callable or self._default_llm
        self._last_result: Optional[ExecutionResult] = None

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute response generation.

        Returns ExecutionResult with generated response.
        """
        notes = []

        # Get guidance for altitude
        altitude_guide = self.ALTITUDE_GUIDANCE[context.hrm_assessment.recommended_altitude]
        notes.append(f"Altitude: {context.hrm_assessment.recommended_altitude.value}")

        # Get stance behaviors
        stance_behavior = self.STANCE_BEHAVIORS[context.stance]
        notes.append(f"Stance: {context.stance.value}")

        # Build prompt with constraints
        system_prompt = self._build_system_prompt(
            context, altitude_guide, stance_behavior
        )

        # Generate response
        response = self._generate_response(system_prompt, context)

        # Apply constraints
        response = self._apply_constraints(response, context, altitude_guide)

        # Update fast memory with interaction signals
        self._record_interaction(context, response)

        result = ExecutionResult(
            response=response,
            altitude_used=context.hrm_assessment.recommended_altitude,
            stance_used=context.stance,
            execution_notes=notes,
            timestamp=datetime.now()
        )

        self._last_result = result
        return result

    def _build_system_prompt(
        self,
        context: ExecutionContext,
        altitude_guide: dict,
        stance_behavior: dict
    ) -> str:
        """Build system prompt with behavioral constraints.

        Note: If a custom system prompt is provided via Config, it will be
        prepended to these constraints automatically by the LLM callable.
        """
        parts = []

        # Constraints header
        parts.append("## Behavioral Constraints")

        # Altitude guidance
        parts.append(f"\nResponse style: {altitude_guide['style']}")
        parts.append(f"Structure: {altitude_guide['structure']}")
        parts.append(f"Target length: up to {altitude_guide['max_length']} words")

        # Stance behaviors
        parts.append(f"\nCurrent mode emphasis: {stance_behavior['emphasis']}")
        parts.append(f"Recommended actions: {', '.join(stance_behavior['actions'])}")
        parts.append(f"Avoid: {', '.join(stance_behavior['avoid'])}")

        # Commitment constraints
        if context.commitment:
            parts.append(f"\nActive commitment: {context.commitment.frame}")
            if context.commitment.success_criteria:
                parts.append(f"Success criteria: {', '.join(context.commitment.success_criteria)}")
            if context.commitment.non_goals:
                parts.append(f"Non-goals (avoid): {', '.join(context.commitment.non_goals)}")

        # HRM constraints
        if context.hrm_assessment.constraints:
            parts.append(f"\nAdditional constraints: {', '.join(context.hrm_assessment.constraints)}")

        return "\n".join(parts)

    def _generate_response(
        self,
        system_prompt: str,
        context: ExecutionContext
    ) -> str:
        """Generate response using LLM with proper multi-turn conversation."""
        # Build messages from conversation history + current input
        messages = []
        if context.conversation_history:
            # Include recent conversation (last 20 messages = 10 turns)
            messages = list(context.conversation_history[-20:])

        # Add current user input
        messages.append({"role": "user", "content": context.user_input})

        # Call LLM with new signature: (system, messages, prompt)
        return self._llm(system=system_prompt, messages=messages)

    def _apply_constraints(
        self,
        response: str,
        context: ExecutionContext,
        altitude_guide: dict
    ) -> str:
        """Apply post-generation constraints."""
        # Truncate if too long
        max_words = altitude_guide["max_length"]
        words = response.split()
        if len(words) > max_words:
            response = " ".join(words[:max_words]) + "..."

        return response

    def _record_interaction(self, context: ExecutionContext, response: str):
        """Record interaction signals to fast memory."""
        signals = InteractionSignals(
            user_input_length=len(context.user_input.split()),
            response_length=len(response.split()),
            altitude_used=context.hrm_assessment.recommended_altitude.value,
            stance_used=context.stance.value,
            had_commitment=context.commitment is not None
        )
        self.memory.record_interaction(signals)

    def _default_llm(self, system: str = None, messages: list = None, prompt: str = None) -> str:
        """Default LLM implementation (placeholder)."""
        # In production, this would call the actual LLM
        return "[No LLM configured - set llm_callable in LockedLoop]"

    def set_llm(self, llm_callable: Callable):
        """Set the LLM callable."""
        self._llm = llm_callable

    def get_last_result(self) -> Optional[ExecutionResult]:
        """Get most recent execution result."""
        return self._last_result
