"""Proposal Buffer - Central routing for all proposals.

All sensing, evaluation, and agent outputs flow through here.
Only Slow Loop can read and act on proposals.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


@dataclass
class GateProposal:
    """Proposal to trigger a gate transition."""
    reason: str
    severity: Severity
    suggested_gate: Literal["framing", "commitment", "evaluation", "emergency"]
    source: Literal["continuous_eval", "task_agent", "decay_manager", "user_signal", "perception", "contrast"]
    timestamp: datetime = field(default_factory=datetime.now)

    def priority_score(self, priority_order: list) -> tuple:
        """Return sortable priority score."""
        severity_order = {
            Severity.EMERGENCY: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3
        }
        source_order = {s: i for i, s in enumerate(priority_order)}
        return (
            severity_order.get(self.severity, 99),
            source_order.get(self.source, 99),
            self.timestamp
        )


@dataclass
class PerceptionReport:
    """Structured situation assessment from Perception sensor."""
    emotional_state: str  # neutral, anxious, frustrated, calm, excited, sad, confused
    urgency: Literal["low", "medium", "high"]
    inferred_intent: str  # seeking_information, requesting_action, expressing_state, planning, venting
    context_cues: list[str]  # verbose_input, terse_input, repetition_detected, etc.
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ContrastReport:
    """Gap analysis between user need and assistant behavior."""
    inferred_user_need: str
    observed_behavior: str
    gap_severity: Literal["low", "medium", "high", "critical"]
    gap_details: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BootstrapTransitionProposal:
    """Proposal for Bootstrap mode transition."""
    recommended_transition: Literal[
        "remain_listen_only",
        "offer_structure",
        "offer_work_order",
        "offer_north_stars",
        "abbreviated_checkin"
    ]
    reason: str
    consent_state: Literal["listen_only", "propose_structure", "ready_for_commitment"]
    timestamp: datetime = field(default_factory=datetime.now)


class ProposalBuffer:
    """
    Central buffer for all proposals.

    Append-only during turn.
    Read by Slow Loop at: gateway pass, end of turn, explicit request.
    Cleared after Slow Loop reads.
    """

    def __init__(self):
        self._gate_proposals: list[GateProposal] = []
        self._perception_reports: list[PerceptionReport] = []
        self._contrast_reports: list[ContrastReport] = []
        self._bootstrap_proposals: list[BootstrapTransitionProposal] = []

    def add_gate_proposal(self, proposal: GateProposal):
        """Add a gate proposal."""
        self._gate_proposals.append(proposal)

    def add_perception_report(self, report: PerceptionReport):
        """Add a perception report."""
        self._perception_reports.append(report)

    def add_contrast_report(self, report: ContrastReport):
        """Add a contrast report."""
        self._contrast_reports.append(report)

    def add_bootstrap_proposal(self, proposal: BootstrapTransitionProposal):
        """Add a bootstrap transition proposal."""
        self._bootstrap_proposals.append(proposal)

    def get_gate_proposals(self, priority_order: list) -> list[GateProposal]:
        """Get gate proposals sorted by priority."""
        return sorted(
            self._gate_proposals,
            key=lambda p: p.priority_score(priority_order)
        )

    def get_latest_perception(self) -> Optional[PerceptionReport]:
        """Get most recent perception report."""
        return self._perception_reports[-1] if self._perception_reports else None

    def get_latest_contrast(self) -> Optional[ContrastReport]:
        """Get most recent contrast report."""
        return self._contrast_reports[-1] if self._contrast_reports else None

    def get_latest_bootstrap_proposal(self) -> Optional[BootstrapTransitionProposal]:
        """Get most recent bootstrap proposal."""
        return self._bootstrap_proposals[-1] if self._bootstrap_proposals else None

    def has_emergency(self) -> bool:
        """Check if any emergency proposals exist."""
        return any(p.severity == Severity.EMERGENCY for p in self._gate_proposals)

    def has_proposals(self) -> bool:
        """Check if any gate proposals exist."""
        return bool(self._gate_proposals)

    def clear(self):
        """Clear all proposals after Slow Loop reads."""
        self._gate_proposals.clear()
        self._perception_reports.clear()
        self._contrast_reports.clear()
        self._bootstrap_proposals.clear()

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return (
            not self._gate_proposals and
            not self._perception_reports and
            not self._contrast_reports and
            not self._bootstrap_proposals
        )
