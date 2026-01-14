"""Front-Door Agent - Default user-facing cognitive router.

Responsibilities:
- Signal detection → propose gates
- Bundle proposals (writer/finance/monitor bundles)
- Orientation UX (active lane, lease status, bookmarks)

Security:
- May READ allowlisted config paths
- Must NEVER APPLY writes (WriteApprovalGate required)
- Emotional signals influence routing only (not authority)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from locked_system.agents import (
    AgentPacket,
    AgentContext,
    Proposal,
    ProposalType,
    AgentDefinition,
)
from locked_system.front_door.signals import SignalDetector, DetectedSignal, SignalType
from locked_system.front_door.bundles import BundleProposer, Bundle
from locked_system.front_door.emotional import EmotionalTelemetry, TelemetryResponse


@dataclass
class OrientationContext:
    """Orientation information for the user."""
    active_lane: Optional[Dict[str, Any]] = None
    paused_lanes: List[Dict[str, Any]] = field(default_factory=list)
    lease_status: Optional[str] = None
    bookmark: Optional[str] = None
    next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'active_lane': self.active_lane,
            'paused_lanes': self.paused_lanes,
            'lease_status': self.lease_status,
            'bookmark': self.bookmark,
            'next_steps': self.next_steps,
        }


class FrontDoorAgent:
    """
    Front-door agent - the default cognitive router.

    Handles:
    - Signal detection and gate proposals
    - Work type routing
    - Emotional telemetry processing
    - Orientation UX
    """

    # Allowlisted config paths for reading
    ALLOWED_CONFIG_PATHS = [
        "./core/*.yaml",
        "./agents/defs/*.yaml",
        "./capabilities/toolspecs/*.yaml",
        "./docs/*.md",
    ]

    def __init__(self):
        self._signal_detector = SignalDetector()
        self._bundle_proposer = BundleProposer()
        self._emotional_telemetry = EmotionalTelemetry()

    def process(self, context: AgentContext) -> AgentPacket:
        """
        Process user input and generate response packet.

        Returns:
            AgentPacket with message and proposals
        """
        user_input = context.user_input
        emotional_signals = context.emotional_signals or {}

        # Step 1: Detect signals
        signal = self._signal_detector.detect(user_input, emotional_signals)

        # Step 2: Process emotional telemetry
        telemetry_response = self._emotional_telemetry.process(emotional_signals)

        # Step 3: Build proposals based on signal
        proposals = []
        message_parts = []

        # Handle emotional overload first
        if telemetry_response.trigger_evaluation:
            proposals.append(Proposal.gate_request(
                "evaluation",
                {"trigger": "emotional_overload", "signals": emotional_signals}
            ))
            message_parts.append("I notice things might be feeling a bit overwhelming. Let's pause and check in.")

        # Handle signal-based proposals
        if signal.type == SignalType.FORMAL_WORK:
            proposals.append(Proposal.gate_request(
                "work_declaration",
                {"detected_type": self._signal_detector.detect_work_type(user_input)}
            ))
            work_type = self._signal_detector.detect_work_type(user_input)
            if work_type:
                bundle = self._bundle_proposer.propose(work_type)
                if bundle:
                    message_parts.append(f"Starting {work_type} work. I'll use the {bundle.name}.")
            else:
                message_parts.append("Starting new work session.")

        elif signal.type == SignalType.INTERRUPT:
            # Check if we should recommend defer (flow state)
            if telemetry_response.recommend_defer:
                proposals.append(Proposal.gate_request(
                    "lane_switch",
                    {"recommendation": "defer", "reason": "flow_state"}
                ))
                message_parts.append("You seem to be in flow. Would you like to defer this for later?")
            else:
                proposals.append(Proposal.gate_request(
                    "lane_switch",
                    {"recommendation": "switch"}
                ))
                message_parts.append("Switching context. Let me save your current progress first.")

        elif signal.type == SignalType.URGENCY:
            proposals.append(Proposal.gate_request(
                "lane_switch",
                {"recommendation": "switch", "urgency": "elevated"}
            ))
            message_parts.append("I understand this is urgent. Let me help you with this right away.")

        elif signal.type == SignalType.COMPLETION:
            proposals.append(Proposal.gate_request(
                "evaluation",
                {"action": "complete"}
            ))
            message_parts.append("Wrapping up. Let me help you close out this work session.")

        # Step 4: Generate response message
        if not message_parts:
            message_parts.append(f"I understand: {user_input}")

        # Step 5: Build orientation context
        orientation = self._build_orientation(context)
        if orientation.bookmark:
            message_parts.append(f"\n\nResuming from: {orientation.bookmark}")
            if orientation.next_steps:
                message_parts.append(f"Next steps: {', '.join(orientation.next_steps[:3])}")

        # Build final packet
        return AgentPacket(
            message="\n\n".join(message_parts),
            proposals=proposals,
            confidence=signal.confidence if signal.type != SignalType.NONE else 0.7,
            traces={
                'agent_id': 'front_door',
                'signal_detected': signal.type.value,
                'emotional_signals': emotional_signals,
            },
        )

    def _build_orientation(self, context: AgentContext) -> OrientationContext:
        """Build orientation context from system state."""
        lane_context = context.system_context.get('lane_context', {})

        return OrientationContext(
            active_lane=lane_context if lane_context.get('lane_id') else None,
            lease_status=lane_context.get('lease_mode'),
            bookmark=None,  # Would come from lane snapshot
            next_steps=[],
        )

    def generate_orientation_message(self, context: AgentContext) -> str:
        """Generate orientation message showing current state."""
        orientation = self._build_orientation(context)

        parts = []

        if orientation.active_lane:
            parts.append(f"Active lane: {orientation.active_lane.get('lane_id', 'unknown')}")
            parts.append(f"Goal: {orientation.active_lane.get('lease_goal', 'Not set')}")
            parts.append(f"Mode: {orientation.active_lane.get('lease_mode', 'unknown')}")

        if orientation.bookmark:
            parts.append(f"\nLast checkpoint: {orientation.bookmark}")

        if orientation.next_steps:
            parts.append(f"\nPlanned: {', '.join(orientation.next_steps)}")

        if not parts:
            parts.append("No active work session. Start with 'let's work on...'")

        return "\n".join(parts)

    def propose_bundle(self, work_type: str) -> Optional[Bundle]:
        """Propose a bundle for work type."""
        return self._bundle_proposer.propose(work_type)

    def detect_signal(self, user_input: str, emotional_signals: Dict[str, str] = None) -> DetectedSignal:
        """Detect signals in user input."""
        return self._signal_detector.detect(user_input, emotional_signals or {})

    def process_telemetry(self, signals: Dict[str, str]) -> TelemetryResponse:
        """Process emotional telemetry."""
        return self._emotional_telemetry.process(signals)

    # --- Read-only config access ---

    def can_read_path(self, path: str) -> bool:
        """Check if path is in allowlist for reading."""
        import fnmatch
        for pattern in self.ALLOWED_CONFIG_PATHS:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False
