"""HRM Loop - The Orchestration Layer

Wires together Intent, Planner, Executor, Evaluator.

The flow:
1. User input arrives
2. Executor reports current situation to Planner
3. Planner reads intent + situation, creates plan
4. Executor executes plan, reports state
5. Evaluator compares outcome to intent
6. If revision needed, Planner revises (loop back to 3)
7. Response returned to user

Key principle: State flows UP, meaning flows DOWN.
"""
from dataclasses import asdict
from typing import Optional

from the_assist.hrm.intent import IntentStore
from the_assist.hrm.planner import Planner, Plan, Situation
from the_assist.hrm.executor import Executor, ExecutionResult
from the_assist.hrm.evaluator import Evaluator, Evaluation


class HRMLoop:
    """
    The HRM orchestration loop.

    This is NOT a layer - it's the wiring between layers.
    Each layer maintains its own memory type.
    """

    def __init__(self):
        # Initialize all layers
        self.intent = IntentStore()      # L1 - tiny, stable, high authority
        self.planner = Planner()         # L2 - semi-stable, rewritable
        self.executor = Executor()       # L3 - ephemeral, disposable
        self.evaluator = Evaluator()     # L4 - delta-based, time-bounded

        self._last_plan: Optional[Plan] = None
        self._last_evaluation: Optional[Evaluation] = None

    def process(self, user_input: str) -> str:
        """
        Process user input through the HRM loop.

        Returns response to user.
        """
        # Step 1: Get current situation from Executor (state report UP)
        situation = self.executor.get_situation()
        situation.user_input = user_input

        # Step 2: Planner creates plan (meaning flows DOWN)
        # Include last evaluation if revision was needed
        evaluation_feedback = None
        if self._last_evaluation and self._last_evaluation.revision_needed:
            evaluation_feedback = {
                "revision_needed": True,
                "issue": self._last_evaluation.issue,
                "recommendation": self._last_evaluation.recommendation,
                "outcome_summary": self._last_evaluation.outcome_summary
            }

        plan = self.planner.plan(situation, evaluation_feedback)
        self._last_plan = plan

        # Step 3: Executor executes plan (state report UP)
        result = self.executor.execute(plan, user_input, self.planner)

        # Step 4: Evaluator compares to intent (state flows UP)
        evaluation = self.evaluator.evaluate(result, asdict(plan))
        self._last_evaluation = evaluation

        # Step 5: Check if revision needed
        if self.evaluator.should_revise_plan(evaluation):
            # Revision loop - but limit to prevent infinite loops
            revision_context = self.evaluator.get_revision_context(evaluation, result)
            revision_context["last_user_input"] = user_input
            revision_context["conversation_length"] = len(self.executor.get_history()) // 2

            # Revise plan for NEXT exchange, not this one
            # (We don't re-execute - revision is cheap, re-execution is expensive)
            self.planner.revise(plan, revision_context)

        # Step 6: Check if intent escalation needed
        if self.evaluator.should_escalate_to_intent(evaluation):
            # For now, just log this - intent modification requires user action
            # In future, could prompt user to clarify intent
            pass

        return result.response

    def get_opening(self) -> str:
        """
        Generate opening message.

        Uses intent to inform the opening, but Executor generates it.
        """
        intent = self.intent.get_intent()

        # Create initial situation
        situation = Situation(
            user_input="",
            conversation_length=0,
            recent_topics=[],
            user_sentiment="engaged"
        )

        # Plan for opening
        plan = self.planner.plan(situation)
        self._last_plan = plan

        # Generate opening through a simple prompt
        opening_prompt = f"""Based on intent (stance: {intent.stance}, success: {intent.current_success}),
generate a brief opening that:
1. Shows you're ready to engage as a {intent.stance}
2. Reflects the north stars: {intent.north_stars}
3. Is concise and inviting

One or two sentences maximum."""

        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            messages=[{"role": "user", "content": opening_prompt}]
        )

        return response.content[0].text

    def end_session(self):
        """
        End session. Clear ephemeral memory.

        Stable memories (intent, evaluations) persist.
        Plans persist for continuity.
        Conversation history (ephemeral) is cleared.
        """
        self.executor.clear_history()

    # ========================================
    # INSPECTION METHODS
    # ========================================

    def get_current_plan(self) -> Optional[Plan]:
        """Get current plan."""
        return self._last_plan

    def get_last_evaluation(self) -> Optional[Evaluation]:
        """Get last evaluation."""
        return self._last_evaluation

    def get_intent_summary(self) -> dict:
        """Get intent summary."""
        intent = self.intent.get_intent()
        return {
            "north_stars": intent.north_stars,
            "success": intent.current_success,
            "stance": intent.stance,
            "non_goals": intent.non_goals
        }

    def get_evaluation_patterns(self) -> dict:
        """Get evaluation patterns."""
        return self.evaluator.get_patterns()

    # ========================================
    # MODIFICATION METHODS (user actions)
    # ========================================

    def set_stance(self, stance: str):
        """Set current stance. User action."""
        self.intent.set_stance(stance)

    def add_non_goal(self, non_goal: str):
        """Add a non-goal. User action."""
        self.intent.add_non_goal(non_goal)

    def set_success(self, success: str):
        """Set success criteria. User action."""
        self.intent.set_success(success)

    def clear_blocked_topic(self, topic: str):
        """Clear a blocked topic. User action."""
        self.planner.clear_blocked_topic(topic)
