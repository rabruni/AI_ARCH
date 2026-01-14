"""Continuous Evaluator - Quality Assessment Layer.

Non-authoritative evaluation that runs continuously.
Proposes gate transitions but never decides.
Distinct from gate-based evaluation (which is authoritative).
"""
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime

from locked_system.proposals.buffer import (
    ProposalBuffer, GateProposal, Severity, ContrastReport
)
from locked_system.memory.fast import ProgressState
from locked_system.memory.slow import CommitmentLease
from locked_system.fast_loop.executor import ExecutionResult


@dataclass
class QualitySignal:
    """A quality signal from continuous evaluation."""
    dimension: str
    score: float  # 0-1
    observation: str
    timestamp: datetime


@dataclass
class ContinuousEvalResult:
    """Result of continuous evaluation."""
    quality_signals: list[QualitySignal]
    proposed_actions: list[GateProposal]
    contrast_report: Optional[ContrastReport]
    overall_health: Literal["healthy", "concerning", "critical"]


class ContinuousEvaluator:
    """
    Continuous quality evaluator.

    Runs after each interaction to assess:
    - Response quality
    - Alignment with commitment
    - User state changes
    - Progress indicators

    Can only PROPOSE gate transitions, never execute them.
    """

    # Quality thresholds
    CONCERNING_THRESHOLD = 0.4
    CRITICAL_THRESHOLD = 0.2

    def __init__(self, proposal_buffer: ProposalBuffer):
        self.buffer = proposal_buffer
        self._signals_history: list[QualitySignal] = []

    def evaluate(
        self,
        execution_result: ExecutionResult,
        user_input: str,
        commitment: Optional[CommitmentLease],
        progress: Optional[ProgressState]
    ) -> ContinuousEvalResult:
        """
        Perform continuous evaluation.

        Returns ContinuousEvalResult with quality signals and proposals.
        """
        signals = []
        proposals = []

        # Evaluate multiple dimensions
        signals.append(self._eval_response_coherence(execution_result))
        signals.append(self._eval_commitment_alignment(execution_result, commitment))
        signals.append(self._eval_progress_trajectory(progress))
        signals.append(self._eval_user_engagement(user_input, execution_result))

        # Generate contrast report
        contrast = self._generate_contrast(user_input, execution_result, commitment)

        # Determine overall health
        avg_score = sum(s.score for s in signals) / len(signals)
        if avg_score < self.CRITICAL_THRESHOLD:
            health = "critical"
        elif avg_score < self.CONCERNING_THRESHOLD:
            health = "concerning"
        else:
            health = "healthy"

        # Generate proposals based on signals
        proposals = self._generate_proposals(signals, health, contrast)

        # Submit proposals to buffer
        for proposal in proposals:
            self.buffer.add_gate_proposal(proposal)

        if contrast:
            self.buffer.add_contrast_report(contrast)

        # Store signals for history
        self._signals_history.extend(signals)

        return ContinuousEvalResult(
            quality_signals=signals,
            proposed_actions=proposals,
            contrast_report=contrast,
            overall_health=health
        )

    def _eval_response_coherence(
        self,
        result: ExecutionResult
    ) -> QualitySignal:
        """Evaluate response coherence."""
        # Simple heuristics for coherence
        response = result.response
        score = 0.7  # Default to acceptable

        # Check for empty or very short responses
        if len(response) < 10:
            score = 0.2
            observation = "Response too short"
        elif len(response) > 2000:
            score = 0.5
            observation = "Response may be too long"
        else:
            observation = "Response length appropriate"

        return QualitySignal(
            dimension="coherence",
            score=score,
            observation=observation,
            timestamp=datetime.now()
        )

    def _eval_commitment_alignment(
        self,
        result: ExecutionResult,
        commitment: Optional[CommitmentLease]
    ) -> QualitySignal:
        """Evaluate alignment with active commitment."""
        if not commitment:
            return QualitySignal(
                dimension="commitment_alignment",
                score=0.5,  # Neutral when no commitment
                observation="No active commitment to align with",
                timestamp=datetime.now()
            )

        score = 0.7  # Default to acceptable
        observation = "Response appears aligned with commitment"

        # Check stance alignment
        stance_used = result.stance_used.value

        # Execution stance should be delivering on commitment
        if stance_used == "execution":
            score = 0.8
            observation = "Execution stance aligned with commitment delivery"

        # Check for non-goal violations (simplified)
        response_lower = result.response.lower()
        for non_goal in commitment.non_goals:
            if non_goal.lower() in response_lower:
                score = 0.3
                observation = f"Response may violate non-goal: {non_goal}"
                break

        return QualitySignal(
            dimension="commitment_alignment",
            score=score,
            observation=observation,
            timestamp=datetime.now()
        )

    def _eval_progress_trajectory(
        self,
        progress: Optional[ProgressState]
    ) -> QualitySignal:
        """Evaluate progress trajectory."""
        if not progress:
            return QualitySignal(
                dimension="progress",
                score=0.5,
                observation="No progress state to evaluate",
                timestamp=datetime.now()
            )

        score = 0.6  # Default
        observations = []

        # Check momentum
        if progress.momentum == "building":
            score += 0.2
            observations.append("momentum building")
        elif progress.momentum == "stalled":
            score -= 0.2
            observations.append("momentum stalled")

        # Check blockers
        if progress.blockers:
            score -= 0.1 * len(progress.blockers)
            observations.append(f"{len(progress.blockers)} blocker(s)")

        # Check completion rate
        if progress.milestones_total > 0:
            completion = progress.milestones_completed / progress.milestones_total
            if completion > 0.7:
                score += 0.2
                observations.append("good completion rate")
            elif completion < 0.3:
                score -= 0.1
                observations.append("low completion rate")

        return QualitySignal(
            dimension="progress",
            score=max(0.0, min(1.0, score)),
            observation="; ".join(observations) if observations else "Progress nominal",
            timestamp=datetime.now()
        )

    def _eval_user_engagement(
        self,
        user_input: str,
        result: ExecutionResult
    ) -> QualitySignal:
        """Evaluate user engagement signals."""
        score = 0.6  # Default
        observations = []

        # Check input length (proxy for engagement)
        words = len(user_input.split())
        if words > 30:
            score += 0.1
            observations.append("detailed input")
        elif words < 5:
            score -= 0.1
            observations.append("minimal input")

        # Check for question marks (seeking information)
        if "?" in user_input:
            observations.append("seeking information")

        # Check for frustration signals
        frustration_signals = ["but", "still", "again", "already", "not working"]
        if any(sig in user_input.lower() for sig in frustration_signals):
            score -= 0.2
            observations.append("possible frustration")

        # Check for positive signals
        positive_signals = ["thanks", "great", "perfect", "helpful"]
        if any(sig in user_input.lower() for sig in positive_signals):
            score += 0.2
            observations.append("positive feedback")

        return QualitySignal(
            dimension="engagement",
            score=max(0.0, min(1.0, score)),
            observation="; ".join(observations) if observations else "Engagement normal",
            timestamp=datetime.now()
        )

    def _generate_contrast(
        self,
        user_input: str,
        result: ExecutionResult,
        commitment: Optional[CommitmentLease]
    ) -> Optional[ContrastReport]:
        """Generate contrast report if gap detected."""
        # Simple gap detection
        gap_detected = False
        gap_description = ""
        severity = "low"

        # Check for mismatch between input complexity and response depth
        input_words = len(user_input.split())
        response_words = len(result.response.split())

        if input_words > 50 and response_words < 30:
            gap_detected = True
            gap_description = "Complex input received shallow response"
            severity = "medium"

        # Check for stance mismatch with user need
        if "help me understand" in user_input.lower() and result.stance_used.value == "execution":
            gap_detected = True
            gap_description = "User seeking understanding but got execution-focused response"
            severity = "medium"

        if not gap_detected:
            return None

        return ContrastReport(
            inferred_user_need=f"Based on input: {user_input[:50]}...",
            observed_behavior=f"Response in {result.stance_used.value} stance, {response_words} words",
            gap_severity=severity,
            timestamp=datetime.now()
        )

    def _generate_proposals(
        self,
        signals: list[QualitySignal],
        health: str,
        contrast: Optional[ContrastReport]
    ) -> list[GateProposal]:
        """Generate gate proposals based on signals."""
        proposals = []

        # Critical health triggers evaluation gate proposal
        if health == "critical":
            proposals.append(GateProposal(
                reason="Critical quality signals detected",
                severity=Severity.HIGH,
                suggested_gate="evaluation",
                source="continuous_eval"
            ))

        # Concerning health with contrast triggers framing gate proposal
        if health == "concerning" and contrast:
            proposals.append(GateProposal(
                reason=f"Quality concern with gap: {contrast.gap_severity}",
                severity=Severity.MEDIUM,
                suggested_gate="framing",
                source="continuous_eval"
            ))

        # Check for specific signal-based proposals
        for signal in signals:
            if signal.dimension == "commitment_alignment" and signal.score < 0.3:
                proposals.append(GateProposal(
                    reason=f"Commitment alignment issue: {signal.observation}",
                    severity=Severity.HIGH,
                    suggested_gate="evaluation",
                    source="continuous_eval"
                ))

            if signal.dimension == "progress" and signal.score < 0.3:
                proposals.append(GateProposal(
                    reason=f"Progress concern: {signal.observation}",
                    severity=Severity.MEDIUM,
                    suggested_gate="evaluation",
                    source="continuous_eval"
                ))

        return proposals

    def get_signal_trend(self, dimension: str, n: int = 5) -> list[float]:
        """Get recent signal trend for a dimension."""
        relevant = [s for s in self._signals_history if s.dimension == dimension]
        return [s.score for s in relevant[-n:]]

    def get_health_summary(self) -> dict:
        """Get summary of recent health signals."""
        if not self._signals_history:
            return {"status": "no_data", "signals": []}

        recent = self._signals_history[-20:]  # Last 20 signals
        avg_by_dimension = {}

        for signal in recent:
            if signal.dimension not in avg_by_dimension:
                avg_by_dimension[signal.dimension] = []
            avg_by_dimension[signal.dimension].append(signal.score)

        return {
            "status": "active",
            "dimension_averages": {
                dim: sum(scores) / len(scores)
                for dim, scores in avg_by_dimension.items()
            },
            "signal_count": len(self._signals_history)
        }
