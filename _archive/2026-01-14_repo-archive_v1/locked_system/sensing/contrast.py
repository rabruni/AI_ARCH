"""Contrast Detector - Gap Detection.

Detects gaps between:
- Inferred user need (from perception)
- Observed assistant behavior (from execution)

Produces ContrastReport for slow loop consideration.
"""
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime

from locked_system.proposals.buffer import PerceptionReport, ContrastReport
from locked_system.fast_loop.executor import ExecutionResult
from locked_system.slow_loop.stance import Stance
from locked_system.memory.slow import CommitmentLease


@dataclass
class ContrastContext:
    """Context for contrast detection."""
    perception: PerceptionReport
    execution: ExecutionResult
    commitment: Optional[CommitmentLease]
    user_input: str


class ContrastDetector:
    """
    Gap detector between user need and assistant behavior.

    Produces ContrastReport when gaps detected.
    Non-authoritative - only reports observations.
    """

    # Gap severity thresholds
    SEVERITY_THRESHOLDS = {
        "critical": 0.7,  # Major misalignment
        "high": 0.5,
        "medium": 0.3,
        "low": 0.1,
    }

    # Stance-intent alignment matrix
    STANCE_INTENT_ALIGNMENT = {
        Stance.SENSEMAKING: {
            "seeking_information": 0.9,
            "expressing_state": 0.8,
            "venting": 0.7,
            "planning": 0.6,
            "requesting_action": 0.3,
        },
        Stance.DISCOVERY: {
            "planning": 0.9,
            "seeking_information": 0.7,
            "requesting_action": 0.6,
            "expressing_state": 0.5,
            "venting": 0.3,
        },
        Stance.EXECUTION: {
            "requesting_action": 0.9,
            "planning": 0.6,
            "seeking_information": 0.4,
            "expressing_state": 0.3,
            "venting": 0.2,
        },
        Stance.EVALUATION: {
            "seeking_information": 0.8,
            "planning": 0.7,
            "requesting_action": 0.5,
            "expressing_state": 0.6,
            "venting": 0.4,
        },
    }

    def __init__(self):
        self._report_history: list[ContrastReport] = []

    def detect(self, context: ContrastContext) -> Optional[ContrastReport]:
        """
        Detect contrast between user need and behavior.

        Returns ContrastReport if gap detected, None otherwise.
        """
        gaps = []

        # Check stance-intent alignment
        stance_gap = self._check_stance_alignment(context)
        if stance_gap:
            gaps.append(stance_gap)

        # Check emotional response appropriateness
        emotional_gap = self._check_emotional_response(context)
        if emotional_gap:
            gaps.append(emotional_gap)

        # Check urgency handling
        urgency_gap = self._check_urgency_handling(context)
        if urgency_gap:
            gaps.append(urgency_gap)

        # Check commitment alignment
        commitment_gap = self._check_commitment_alignment(context)
        if commitment_gap:
            gaps.append(commitment_gap)

        # If no gaps, return None
        if not gaps:
            return None

        # Combine gaps into report
        report = self._create_report(context, gaps)
        self._report_history.append(report)

        return report

    def _check_stance_alignment(
        self,
        context: ContrastContext
    ) -> Optional[dict]:
        """Check if stance aligns with inferred intent."""
        stance = context.execution.stance_used
        intent = context.perception.inferred_intent

        alignment_score = self.STANCE_INTENT_ALIGNMENT.get(stance, {}).get(
            intent, 0.5
        )

        if alignment_score < 0.4:
            return {
                "type": "stance_misalignment",
                "severity": 1 - alignment_score,
                "description": f"Stance {stance.value} may not align with intent {intent}",
            }

        return None

    def _check_emotional_response(
        self,
        context: ContrastContext
    ) -> Optional[dict]:
        """Check emotional response appropriateness."""
        emotional_state = context.perception.emotional_state

        # Critical emotional states need careful handling
        critical_states = ["anxious", "frustrated", "sad"]

        if emotional_state in critical_states:
            # Check if response acknowledges emotional state
            response_lower = context.execution.response.lower()

            acknowledgment_signals = [
                "understand", "hear you", "that sounds",
                "i can see", "makes sense", "difficult"
            ]

            if not any(sig in response_lower for sig in acknowledgment_signals):
                return {
                    "type": "emotional_gap",
                    "severity": 0.6,
                    "description": f"User in {emotional_state} state but response lacks acknowledgment",
                }

        return None

    def _check_urgency_handling(
        self,
        context: ContrastContext
    ) -> Optional[dict]:
        """Check urgency handling."""
        urgency = context.perception.urgency
        altitude = context.execution.altitude_used.value

        # High urgency should not get L4/L5 (too slow)
        if urgency == "high" and altitude in ["L4", "L5"]:
            return {
                "type": "urgency_mismatch",
                "severity": 0.5,
                "description": f"High urgency request got {altitude} response (may be too slow)",
            }

        # Low urgency with L1 might be too terse
        if urgency == "low" and altitude == "L1":
            return {
                "type": "depth_mismatch",
                "severity": 0.3,
                "description": "Low urgency request got minimal response",
            }

        return None

    def _check_commitment_alignment(
        self,
        context: ContrastContext
    ) -> Optional[dict]:
        """Check alignment with active commitment."""
        if not context.commitment:
            return None

        # Check if response relates to commitment frame
        frame_lower = context.commitment.frame.lower()
        response_lower = context.execution.response.lower()

        # Very simplified relevance check
        frame_words = set(frame_lower.split())
        response_words = set(response_lower.split())

        # Remove common words
        common = {"the", "a", "an", "is", "are", "to", "and", "of", "for"}
        frame_words -= common
        response_words -= common

        overlap = len(frame_words & response_words)

        if overlap == 0 and len(frame_words) > 2:
            return {
                "type": "commitment_drift",
                "severity": 0.4,
                "description": f"Response may not relate to commitment: {context.commitment.frame[:50]}",
            }

        return None

    def _create_report(
        self,
        context: ContrastContext,
        gaps: list[dict]
    ) -> ContrastReport:
        """Create contrast report from detected gaps."""
        # Determine overall severity
        max_severity = max(g["severity"] for g in gaps)

        if max_severity >= self.SEVERITY_THRESHOLDS["critical"]:
            severity_label = "critical"
        elif max_severity >= self.SEVERITY_THRESHOLDS["high"]:
            severity_label = "high"
        elif max_severity >= self.SEVERITY_THRESHOLDS["medium"]:
            severity_label = "medium"
        else:
            severity_label = "low"

        # Build descriptions
        gap_descriptions = [g["description"] for g in gaps]

        return ContrastReport(
            inferred_user_need=f"{context.perception.inferred_intent} with {context.perception.emotional_state} state",
            observed_behavior=f"{context.execution.stance_used.value} stance, {context.execution.altitude_used.value} response",
            gap_severity=severity_label,
            gap_details=gap_descriptions,
            timestamp=datetime.now()
        )

    def get_gap_trend(self, n: int = 5) -> list[str]:
        """Get recent gap severity trend."""
        return [r.gap_severity for r in self._report_history[-n:]]

    def has_persistent_gap(self, severity: str = "medium", count: int = 3) -> bool:
        """Check if there's a persistent gap of given severity."""
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        target_level = severity_order.get(severity, 1)

        recent = self._report_history[-count:]
        if len(recent) < count:
            return False

        return all(
            severity_order.get(r.gap_severity, 0) >= target_level
            for r in recent
        )
