"""HRM - Horizon/Risk/Moment Depth Controller.

Fast loop depth control that operates within commitment bounds.
Adjusts response depth based on:
- Horizon: Time-based importance
- Risk: Potential for harm/misalignment
- Moment: Immediate user state
"""
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

from locked_system.memory.slow import CommitmentLease
from locked_system.memory.fast import ProgressState
from locked_system.proposals.buffer import PerceptionReport


class Altitude(Enum):
    """Response depth levels."""
    L1_ACKNOWLEDGE = "L1"      # Quick acknowledgment
    L2_FASTLANE = "L2"         # Direct, efficient response
    L3_CONSIDERED = "L3"       # Thoughtful, balanced
    L4_EXPLORATORY = "L4"      # Deep exploration
    L5_SYNTHESIS = "L5"        # Integration and synthesis


@dataclass
class HRMAssessment:
    """HRM depth assessment."""
    recommended_altitude: Altitude
    horizon_score: float        # 0-1, higher = longer-term importance
    risk_score: float           # 0-1, higher = more risk
    moment_score: float         # 0-1, higher = more immediate need
    rationale: str
    constraints: list[str]      # From commitment


class HRM:
    """
    Horizon/Risk/Moment depth controller.

    Operates within commitment bounds set by slow loop.
    Only controls response depth, not authority.
    """

    # Altitude selection thresholds
    ALTITUDE_THRESHOLDS = {
        Altitude.L1_ACKNOWLEDGE: (0.0, 0.2),
        Altitude.L2_FASTLANE: (0.2, 0.4),
        Altitude.L3_CONSIDERED: (0.4, 0.6),
        Altitude.L4_EXPLORATORY: (0.6, 0.8),
        Altitude.L5_SYNTHESIS: (0.8, 1.0),
    }

    def __init__(self, commitment: Optional[CommitmentLease] = None):
        self._commitment = commitment
        self._last_assessment: Optional[HRMAssessment] = None

    def set_commitment(self, commitment: Optional[CommitmentLease]):
        """Update active commitment."""
        self._commitment = commitment

    def assess(
        self,
        user_input: str,
        perception: Optional[PerceptionReport] = None,
        progress: Optional[ProgressState] = None
    ) -> HRMAssessment:
        """
        Assess appropriate response depth.

        Returns HRMAssessment with recommended altitude.
        """
        # Calculate dimension scores
        horizon = self._assess_horizon(user_input, perception)
        risk = self._assess_risk(user_input, perception)
        moment = self._assess_moment(user_input, perception, progress)

        # Composite score (weighted average)
        composite = (horizon * 0.3 + risk * 0.4 + moment * 0.3)

        # Select altitude
        altitude = self._select_altitude(composite)

        # Get constraints from commitment
        constraints = self._get_constraints()

        # Build rationale
        rationale = self._build_rationale(horizon, risk, moment, altitude)

        assessment = HRMAssessment(
            recommended_altitude=altitude,
            horizon_score=horizon,
            risk_score=risk,
            moment_score=moment,
            rationale=rationale,
            constraints=constraints
        )

        self._last_assessment = assessment
        return assessment

    def _assess_horizon(
        self,
        user_input: str,
        perception: Optional[PerceptionReport]
    ) -> float:
        """Assess time-based importance (0-1)."""
        score = 0.5  # Default to medium

        # Long-term indicators
        long_term_signals = [
            "future", "long-term", "eventually", "goal",
            "plan", "strategy", "career", "life"
        ]

        # Short-term indicators
        short_term_signals = [
            "now", "today", "quick", "urgent",
            "immediately", "asap", "right now"
        ]

        lower = user_input.lower()

        # Check for long-term signals
        if any(signal in lower for signal in long_term_signals):
            score += 0.3

        # Check for short-term signals
        if any(signal in lower for signal in short_term_signals):
            score -= 0.2

        # Use perception if available
        if perception and perception.inferred_intent:
            if "planning" in perception.inferred_intent.lower():
                score += 0.2
            if "quick" in perception.inferred_intent.lower():
                score -= 0.2

        return max(0.0, min(1.0, score))

    def _assess_risk(
        self,
        user_input: str,
        perception: Optional[PerceptionReport]
    ) -> float:
        """Assess potential for harm/misalignment (0-1)."""
        score = 0.3  # Default to low-medium

        # High-risk indicators
        high_risk_signals = [
            "important", "critical", "serious", "worried",
            "concerned", "afraid", "scared", "anxious",
            "decision", "choice", "uncertain"
        ]

        # Low-risk indicators
        low_risk_signals = [
            "just", "simple", "easy", "quick",
            "casual", "curious", "wondering"
        ]

        lower = user_input.lower()

        # Check for high-risk signals
        for signal in high_risk_signals:
            if signal in lower:
                score += 0.15

        # Check for low-risk signals
        for signal in low_risk_signals:
            if signal in lower:
                score -= 0.1

        # Use perception emotional state
        if perception and perception.emotional_state:
            if perception.emotional_state in ["anxious", "stressed", "overwhelmed"]:
                score += 0.3
            elif perception.emotional_state in ["calm", "relaxed", "confident"]:
                score -= 0.1

        return max(0.0, min(1.0, score))

    def _assess_moment(
        self,
        user_input: str,
        perception: Optional[PerceptionReport],
        progress: Optional[ProgressState]
    ) -> float:
        """Assess immediate user state needs (0-1)."""
        score = 0.5  # Default to medium

        # Check input length as proxy for complexity
        word_count = len(user_input.split())
        if word_count > 50:
            score += 0.2
        elif word_count < 10:
            score -= 0.2

        # Check for question markers
        if "?" in user_input:
            score += 0.1
        if user_input.count("?") > 2:
            score += 0.1

        # Use perception urgency
        if perception and perception.urgency:
            if perception.urgency == "high":
                score += 0.2
            elif perception.urgency == "low":
                score -= 0.2

        # Check progress state
        if progress:
            if progress.blockers:
                score += 0.2
            if progress.momentum == "stalled":
                score += 0.1

        return max(0.0, min(1.0, score))

    def _select_altitude(self, composite_score: float) -> Altitude:
        """Select altitude based on composite score."""
        for altitude, (low, high) in self.ALTITUDE_THRESHOLDS.items():
            if low <= composite_score < high:
                return altitude
        return Altitude.L5_SYNTHESIS

    def _get_constraints(self) -> list[str]:
        """Get constraints from active commitment."""
        if not self._commitment:
            return []

        constraints = []

        # Add non-goals as constraints
        if self._commitment.non_goals:
            constraints.extend([f"Avoid: {ng}" for ng in self._commitment.non_goals])

        # Add horizon authority constraint
        if self._commitment.horizon_authority == "near":
            constraints.append("Focus on immediate, actionable responses")
        elif self._commitment.horizon_authority == "far":
            constraints.append("Consider long-term implications")

        return constraints

    def _build_rationale(
        self,
        horizon: float,
        risk: float,
        moment: float,
        altitude: Altitude
    ) -> str:
        """Build human-readable rationale."""
        parts = []

        if horizon > 0.6:
            parts.append("long-term importance")
        elif horizon < 0.4:
            parts.append("immediate focus")

        if risk > 0.6:
            parts.append("high stakes")
        elif risk < 0.3:
            parts.append("low risk")

        if moment > 0.6:
            parts.append("complex situation")
        elif moment < 0.4:
            parts.append("straightforward request")

        if not parts:
            parts.append("balanced assessment")

        return f"{altitude.value} selected based on: {', '.join(parts)}"

    def get_last_assessment(self) -> Optional[HRMAssessment]:
        """Get most recent assessment."""
        return self._last_assessment
