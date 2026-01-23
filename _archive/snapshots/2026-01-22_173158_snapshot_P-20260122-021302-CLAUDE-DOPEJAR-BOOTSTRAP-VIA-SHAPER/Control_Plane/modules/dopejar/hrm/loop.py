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

from dopejar.hrm.intent import IntentStore
from dopejar.hrm.planner import Planner, Plan, Situation
from dopejar.hrm.executor import Executor, ExecutionResult
from dopejar.hrm.evaluator import Evaluator, Evaluation
from dopejar.hrm.altitude import AltitudeGovernor, AltitudePolicy
from dopejar.hrm.history import SessionHistory


class HRMLoop:
    """
    The HRM orchestration loop.

    This is NOT a layer - it's the wiring between layers.
    Each layer maintains its own memory type.
    """

    def __init__(self, altitude_policy: Optional[AltitudePolicy] = None):
        # Initialize all layers
        self.intent = IntentStore()      # L1 - tiny, stable, high authority (PERSISTS)
        self.planner = Planner()         # L2 - semi-stable, rewritable
        self.executor = Executor()       # L3 - ephemeral, disposable
        self.evaluator = Evaluator()     # L4 - delta-based, time-bounded

        # Altitude governance (reusable across agents)
        self.altitude = AltitudeGovernor(altitude_policy)

        # Session history (persists across sessions, loaded on-demand)
        self.history = SessionHistory()

        self._last_plan: Optional[Plan] = None
        self._last_evaluation: Optional[Evaluation] = None

        # New session = clean slate (except intent and history which persist)
        self._reset_session_state()
        self.history.start_session()

    def process(self, user_input: str) -> str:
        """
        Process user input through the HRM loop.

        Returns response to user.
        """
        # Step 0: Check for continuity question (load history on-demand)
        history_context = None
        if SessionHistory.is_continuity_question(user_input):
            history_context = self.history.build_context_for_continuity()

        # Step 1: Get current situation from Executor (state report UP)
        situation = self.executor.get_situation()
        situation.user_input = user_input

        # Step 2: Detect altitude of user input
        detected_altitude = self.altitude.detect_level(user_input)

        # Step 3: Validate altitude transition (with L2 fast lane logic)
        altitude_validation = self.altitude.validate_transition(detected_altitude, user_input)

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

        # Handle altitude validation results
        if not altitude_validation.allowed:
            # BLOCKED: Inject altitude constraint, track friction
            evaluation_feedback = evaluation_feedback or {}
            evaluation_feedback["altitude_blocked"] = True
            evaluation_feedback["altitude_reason"] = altitude_validation.reason
            evaluation_feedback["altitude_required"] = altitude_validation.suggested_level
            self.altitude.record_friction(detected_altitude, altitude_validation.suggested_level, True)

        elif altitude_validation.use_micro_anchor:
            # L2 ATOMIC FAST LANE: Allow but inject micro-anchor
            evaluation_feedback = evaluation_feedback or {}
            evaluation_feedback["micro_anchor"] = altitude_validation.micro_anchor_text
            evaluation_feedback["request_type"] = altitude_validation.request_type

        elif altitude_validation.execute_first:
            # URGENCY: Execute first, offer alignment after
            evaluation_feedback = evaluation_feedback or {}
            evaluation_feedback["execute_first"] = True
            evaluation_feedback["micro_anchor"] = altitude_validation.micro_anchor_text

        elif altitude_validation.requires_verification:
            # HIGH-STAKES: Slow down, verify
            evaluation_feedback = evaluation_feedback or {}
            evaluation_feedback["high_stakes"] = True
            evaluation_feedback["requires_verification"] = True

        # Inject history context if this is a continuity question
        if history_context:
            evaluation_feedback = evaluation_feedback or {}
            evaluation_feedback["history_context"] = history_context

        plan = self.planner.plan(situation, evaluation_feedback)
        self._last_plan = plan

        # Step 5: Executor executes plan (state report UP)
        result = self.executor.execute(plan, user_input, self.planner, history_context)

        # Step 6: Update altitude context and record exchange
        self.altitude.record_exchange()
        self.history.record_exchange(result.topics_discussed or [])
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

    def end_session(self, summary: str = None):
        """
        End session. Save summary, clear ephemeral memory.

        Intent persists (user preferences).
        Session history persists (for continuity).
        Everything else is cleared for next session.
        """
        # Generate summary if not provided
        if not summary:
            summary = self._generate_session_summary()

        # Save to history
        self.history.end_session(summary)

        # Clear ephemeral
        self.executor.clear_history()
        self.altitude.reset()

    def _generate_session_summary(self) -> str:
        """Generate a brief summary of what was discussed."""
        topics = self.history._current_topics
        exchanges = self.history._exchange_count

        if not topics and exchanges == 0:
            return "Brief session, no substantial discussion."

        if not topics:
            return f"Session with {exchanges} exchanges."

        # Quick summary from topics
        topic_str = ", ".join(topics[:5])
        return f"Discussed: {topic_str}"

    def _reset_session_state(self):
        """
        Reset session state for a fresh start.

        Called automatically on init. Clears:
        - Plans (L2) - fresh planning each session
        - Evaluations (L4) - no stale patterns
        - Executor history (L3) - ephemeral anyway
        - Altitude context

        Preserves:
        - Intent (L1) - user's stable preferences
        """
        self.planner.reset()
        self.evaluator.reset()
        self.executor.clear_history()
        self.altitude.reset()
        self._last_plan = None
        self._last_evaluation = None

    def reset(self):
        """
        Manual reset. Clears all session state except intent.
        """
        self._reset_session_state()

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

    def get_friction_status(self) -> dict:
        """Get friction tracking status."""
        return {
            "score": self.altitude.get_friction_score(),
            "is_high": self.altitude.is_friction_high(),
            "events": self.altitude.context.friction_events[-5:]
        }

    def get_session_history(self, n: int = 5) -> list:
        """Get recent session history."""
        return self.history.get_recent_sessions(n)

    def get_last_session(self):
        """Get last session record."""
        return self.history.get_last_session()

    def get_session(self, index: int):
        """Get session by index."""
        return self.history.get_session(index)

    def search_sessions(self, keyword: str) -> list:
        """Search sessions by keyword."""
        return self.history.search_sessions(keyword)

    def format_session_history(self, n: int = 5) -> str:
        """Format recent sessions for display."""
        sessions = self.history.get_recent_sessions(n)
        return self.history.format_sessions_brief(sessions)

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
