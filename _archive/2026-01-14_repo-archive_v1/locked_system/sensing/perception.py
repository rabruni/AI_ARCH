"""Perception Sensor - User State Detection.

Sensor (not agent) that produces structured perception reports.
No authority, no decisions - only observations.

Detects:
- Emotional state
- Urgency level
- Intent signals
- Context cues
"""
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime

from locked_system.proposals.buffer import PerceptionReport


@dataclass
class PerceptionContext:
    """Context for perception analysis."""
    user_input: str
    conversation_history: list[dict]
    time_since_last_input: Optional[float] = None  # seconds
    session_duration: Optional[float] = None  # seconds


class PerceptionSensor:
    """
    User state perception sensor.

    Produces structured PerceptionReport.
    Does not make decisions or take actions.
    """

    # Emotional state indicators
    EMOTIONAL_INDICATORS = {
        "anxious": ["worried", "nervous", "stressed", "anxious", "overwhelmed", "panicking"],
        "frustrated": ["frustrated", "annoyed", "stuck", "can't", "not working", "again"],
        "confused": ["confused", "don't understand", "unclear", "what do you mean", "lost"],
        "calm": ["okay", "fine", "alright", "good", "sure"],
        "excited": ["excited", "can't wait", "amazing", "awesome", "love"],
        "sad": ["sad", "down", "depressed", "unhappy", "disappointed"],
    }

    # Urgency indicators
    URGENCY_INDICATORS = {
        "high": ["urgent", "asap", "immediately", "right now", "emergency", "critical", "deadline"],
        "medium": ["soon", "when you can", "today", "this week"],
        "low": ["whenever", "no rush", "eventually", "at some point"],
    }

    # Intent patterns
    INTENT_PATTERNS = {
        "seeking_information": ["what", "how", "why", "explain", "tell me", "?"],
        "requesting_action": ["do", "make", "create", "help me", "can you"],
        "expressing_state": ["i feel", "i am", "i'm", "i think"],
        "planning": ["plan", "strategy", "goal", "want to", "trying to"],
        "venting": ["just need to", "can't believe", "so tired of"],
    }

    def __init__(self):
        self._last_report: Optional[PerceptionReport] = None
        self._report_history: list[PerceptionReport] = []

    def sense(self, context: PerceptionContext) -> PerceptionReport:
        """
        Sense user state from context.

        Returns PerceptionReport with observations.
        """
        # Detect emotional state
        emotional_state = self._detect_emotional_state(context.user_input)

        # Detect urgency
        urgency = self._detect_urgency(context.user_input)

        # Infer intent
        intent = self._infer_intent(context.user_input)

        # Detect context cues
        context_cues = self._detect_context_cues(context)

        # Assess confidence
        confidence = self._assess_confidence(context)

        report = PerceptionReport(
            emotional_state=emotional_state,
            urgency=urgency,
            inferred_intent=intent,
            context_cues=context_cues,
            confidence=confidence,
            timestamp=datetime.now()
        )

        self._last_report = report
        self._report_history.append(report)

        return report

    def _detect_emotional_state(self, user_input: str) -> str:
        """Detect emotional state from input."""
        lower = user_input.lower()

        # Score each emotional state
        scores = {}
        for state, indicators in self.EMOTIONAL_INDICATORS.items():
            score = sum(1 for ind in indicators if ind in lower)
            if score > 0:
                scores[state] = score

        if not scores:
            return "neutral"

        # Return highest scoring state
        return max(scores, key=scores.get)

    def _detect_urgency(self, user_input: str) -> Literal["high", "medium", "low"]:
        """Detect urgency level."""
        lower = user_input.lower()

        for level, indicators in self.URGENCY_INDICATORS.items():
            if any(ind in lower for ind in indicators):
                return level

        return "medium"  # Default

    def _infer_intent(self, user_input: str) -> str:
        """Infer primary intent."""
        lower = user_input.lower()

        # Score each intent
        scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if p in lower)
            if score > 0:
                scores[intent] = score

        if not scores:
            return "general_communication"

        return max(scores, key=scores.get)

    def _detect_context_cues(self, context: PerceptionContext) -> list[str]:
        """Detect contextual cues."""
        cues = []

        # Check input length
        words = len(context.user_input.split())
        if words > 100:
            cues.append("verbose_input")
        elif words < 5:
            cues.append("terse_input")

        # Check for repeated themes in history
        if context.conversation_history:
            recent_inputs = [
                msg.get("content", "")
                for msg in context.conversation_history[-5:]
                if msg.get("role") == "user"
            ]

            # Check for escalation
            if recent_inputs:
                if any("again" in inp.lower() for inp in recent_inputs):
                    cues.append("repetition_detected")
                if any("still" in inp.lower() for inp in recent_inputs):
                    cues.append("persistence_detected")

        # Check timing
        if context.time_since_last_input:
            if context.time_since_last_input < 5:  # Very quick response
                cues.append("rapid_response")
            elif context.time_since_last_input > 300:  # Long pause
                cues.append("delayed_response")

        # Check session duration
        if context.session_duration:
            if context.session_duration > 1800:  # 30 minutes
                cues.append("extended_session")

        return cues

    def _assess_confidence(self, context: PerceptionContext) -> float:
        """Assess confidence in perception."""
        confidence = 0.5  # Base confidence

        # More input = more confidence
        words = len(context.user_input.split())
        if words > 20:
            confidence += 0.2
        elif words < 5:
            confidence -= 0.2

        # History provides more context
        if context.conversation_history and len(context.conversation_history) > 3:
            confidence += 0.1

        return max(0.1, min(0.95, confidence))

    def get_last_report(self) -> Optional[PerceptionReport]:
        """Get most recent perception report."""
        return self._last_report

    def get_emotional_trend(self, n: int = 5) -> list[str]:
        """Get recent emotional state trend."""
        return [r.emotional_state for r in self._report_history[-n:]]

    def detect_state_shift(self) -> Optional[str]:
        """Detect if there's been a significant state shift."""
        if len(self._report_history) < 2:
            return None

        current = self._report_history[-1]
        previous = self._report_history[-2]

        # Check for emotional shift
        if current.emotional_state != previous.emotional_state:
            if current.emotional_state in ["anxious", "frustrated", "sad"]:
                return f"shift_to_negative:{current.emotional_state}"
            elif previous.emotional_state in ["anxious", "frustrated", "sad"]:
                return f"shift_to_positive:{current.emotional_state}"

        # Check for urgency shift
        urgency_order = {"low": 0, "medium": 1, "high": 2}
        if urgency_order.get(current.urgency, 1) > urgency_order.get(previous.urgency, 1):
            return "urgency_increased"

        return None
