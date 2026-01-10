"""HRM Loop - The Orchestration Layer

Wires together Intent, Planner, Executor, Evaluator.

The flow:
1. User input arrives
2. Executor reports current situation to Planner
3. Altitude Governor validates proposed level
4. Planner reads intent + situation, creates plan
5. Executor executes plan, reports state
6. Evaluator compares outcome to intent
7. If revision needed, Planner revises (loop back to 3)
8. Response returned to user

Key principle: State flows UP, meaning flows DOWN.
"""
from dataclasses import asdict
from typing import Optional

from the_assist.hrm.intent import IntentStore
from the_assist.hrm.planner import Planner, Plan, Situation
from the_assist.hrm.executor import Executor, ExecutionResult
from the_assist.hrm.evaluator import Evaluator, Evaluation
from the_assist.hrm.altitude import AltitudeGovernor, AltitudePolicy


class HRMLoop:
    """
    The HRM orchestration loop.

    This is NOT a layer - it's the wiring between layers.
    Each layer maintains its own memory type.
    """

    def __init__(self, altitude_policy: Optional[AltitudePolicy] = None):
        # Initialize all layers
        self.intent = IntentStore()      # L1 - tiny, stable, high authority
        self.planner = Planner()         # L2 - semi-stable, rewritable
        self.executor = Executor()       # L3 - ephemeral, disposable
        self.evaluator = Evaluator()     # L4 - delta-based, time-bounded

        # Altitude governance (reusable across agents)
        self.altitude = AltitudeGovernor(altitude_policy)

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

        # Step 2: Detect altitude of user input
        detected_altitude = self.altitude.detect_level(user_input)

        # Step 3: Validate altitude transition
        altitude_validation = self.altitude.validate_transition(detected_altitude)

        # Step 4: Planner creates plan (meaning flows DOWN)
        # Include altitude context and any evaluation feedback
        evaluation_feedback = None
        if self._last_evaluation and self._last_evaluation.revision_needed:
            evaluation_feedback = {
                "revision_needed": True,
                "issue": self._last_evaluation.issue,
                "recommendation": self._last_evaluation.recommendation,
                "outcome_summary": self._last_evaluation.outcome_summary
            }

        # Add altitude context to situation
        if not altitude_validation.allowed:
            # Inject altitude constraint
            evaluation_feedback = evaluation_feedback or {}
            evaluation_feedback["altitude_blocked"] = True
            evaluation_feedback["altitude_reason"] = altitude_validation.reason
            evaluation_feedback["altitude_required"] = altitude_validation.suggested_level

        plan = self.planner.plan(situation, evaluation_feedback)
        self._last_plan = plan

        # Step 5: Executor executes plan (state report UP)
        result = self.executor.execute(plan, user_input, self.planner)

        # Step 6: Update altitude context based on what happened
        self.altitude.record_exchange()
        if detected_altitude in ["L4", "L3"]:
            # Mark higher levels as established when discussed
            self.altitude.mark_established(detected_altitude)
        if plan.altitude != self.altitude.context.current_level:
            self.altitude.record_transition(plan.altitude)

        # Step 7: Evaluator compares to intent (state flows UP)
        evaluation = self.evaluator.evaluate(result, asdict(plan))
        self._last_evaluation = evaluation

        # Step 8: Check if revision needed
        if self.evaluator.should_revise_plan(evaluation):
            revision_context = self.evaluator.get_revision_context(evaluation, result)
            revision_context["last_user_input"] = user_input
            revision_context["conversation_length"] = len(self.executor.get_history()) // 2
            self.planner.revise(plan, revision_context)

        # Step 9: Check if intent escalation needed
        if self.evaluator.should_escalate_to_intent(evaluation):
            pass  # Intent modification requires user action

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
        Altitude context is reset.
        """
        self.executor.clear_history()
        self.altitude.reset()

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

    def get_altitude_status(self) -> dict:
        """Get current altitude governance status."""
        ctx = self.altitude.get_context()
        return {
            "current_level": ctx.current_level,
            "l4_connected": ctx.l4_connected,
            "l3_established": ctx.l3_established,
            "exchanges_at_level": ctx.time_at_current,
            "history": ctx.level_history[-5:]  # Last 5 transitions
        }

    def get_altitude_rules(self) -> list[str]:
        """Get altitude enforcement rules."""
        return self.altitude.get_enforcement_rules()

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
