"""Packet Firewall - Validates agent outputs before processing.

Enforces:
- No tool execution claims without audit
- No write attempts without approval gate
- No stance/commitment mutation attempts
- Orchestration budget limits
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from locked_system.agents.models import AgentPacket, AgentDefinition, Proposal, ProposalType


@dataclass
class FirewallViolation:
    """A violation detected by the firewall."""
    code: str
    message: str
    proposal_id: Optional[str] = None
    severity: str = "error"  # error, warning

    def to_dict(self) -> dict:
        return {
            'code': self.code,
            'message': self.message,
            'proposal_id': self.proposal_id,
            'severity': self.severity,
        }


@dataclass
class FirewallResult:
    """Result of firewall validation."""
    passed: bool
    violations: List[FirewallViolation] = field(default_factory=list)
    sanitized_packet: Optional[AgentPacket] = None

    def to_dict(self) -> dict:
        return {
            'passed': self.passed,
            'violations': [v.to_dict() for v in self.violations],
        }


class PacketFirewall:
    """
    Validates agent packets before they reach the executor.

    Enforced by core - agents cannot bypass this.
    """

    # Forbidden patterns in messages
    FORBIDDEN_PATTERNS = [
        "I have executed",
        "I performed",
        "I wrote to",
        "I deleted",
        "I modified",
        "File saved",
        "Changes applied",
    ]

    # Protected gates that agents cannot directly request
    PROTECTED_GATES = [
        "stance_override",
        "commitment_force",
        "authority_grant",
    ]

    def __init__(
        self,
        max_proposals_per_packet: int = 10,
        max_tool_requests: int = 5,
    ):
        self._max_proposals = max_proposals_per_packet
        self._max_tool_requests = max_tool_requests

    def validate(
        self,
        packet: AgentPacket,
        definition: AgentDefinition = None,
    ) -> FirewallResult:
        """
        Validate an agent packet.

        Checks:
        1. No forbidden claims (side effect claims without audit)
        2. No protected gate requests
        3. Tool requests within allowed set (if definition provided)
        4. Budget limits
        """
        violations = []

        # Check 1: Forbidden patterns in message
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern.lower() in packet.message.lower():
                violations.append(FirewallViolation(
                    code="FORBIDDEN_CLAIM",
                    message=f"Message contains forbidden claim: '{pattern}'",
                    severity="error",
                ))

        # Check 2: Proposal count limits
        if len(packet.proposals) > self._max_proposals:
            violations.append(FirewallViolation(
                code="PROPOSAL_LIMIT",
                message=f"Too many proposals: {len(packet.proposals)} > {self._max_proposals}",
                severity="error",
            ))

        # Check 3: Tool request limits
        tool_requests = packet.get_tool_requests()
        if len(tool_requests) > self._max_tool_requests:
            violations.append(FirewallViolation(
                code="TOOL_REQUEST_LIMIT",
                message=f"Too many tool requests: {len(tool_requests)} > {self._max_tool_requests}",
                severity="error",
            ))

        # Check 4: Protected gates
        for proposal in packet.get_gate_requests():
            if proposal.gate in self.PROTECTED_GATES:
                violations.append(FirewallViolation(
                    code="PROTECTED_GATE",
                    message=f"Cannot request protected gate: {proposal.gate}",
                    proposal_id=proposal.proposal_id,
                    severity="error",
                ))

        # Check 5: Allowed tools/gates (if definition provided)
        if definition:
            for proposal in tool_requests:
                if proposal.tool_id not in definition.allowed_tool_requests:
                    violations.append(FirewallViolation(
                        code="UNAUTHORIZED_TOOL",
                        message=f"Agent {definition.agent_id} cannot request tool: {proposal.tool_id}",
                        proposal_id=proposal.proposal_id,
                        severity="error",
                    ))

            for proposal in packet.get_gate_requests():
                if proposal.gate not in definition.allowed_gate_requests:
                    violations.append(FirewallViolation(
                        code="UNAUTHORIZED_GATE",
                        message=f"Agent {definition.agent_id} cannot request gate: {proposal.gate}",
                        proposal_id=proposal.proposal_id,
                        severity="error",
                    ))

        # Check 6: Required traces
        if 'agent_id' not in packet.traces:
            violations.append(FirewallViolation(
                code="MISSING_TRACE",
                message="Packet missing agent_id in traces",
                severity="warning",
            ))

        # Determine pass/fail
        errors = [v for v in violations if v.severity == "error"]
        passed = len(errors) == 0

        # Create sanitized packet if passed
        sanitized = None
        if passed:
            sanitized = self._sanitize(packet, definition)

        return FirewallResult(
            passed=passed,
            violations=violations,
            sanitized_packet=sanitized,
        )

    def _sanitize(
        self,
        packet: AgentPacket,
        definition: AgentDefinition = None,
    ) -> AgentPacket:
        """
        Create a sanitized copy of the packet.

        Removes any unauthorized proposals (if definition provided).
        """
        proposals = packet.proposals.copy()

        if definition:
            # Filter to allowed tools/gates only
            allowed_proposals = []
            for proposal in proposals:
                if proposal.type == ProposalType.TOOL_REQUEST:
                    if proposal.tool_id in definition.allowed_tool_requests:
                        allowed_proposals.append(proposal)
                elif proposal.type == ProposalType.GATE_REQUEST:
                    if proposal.gate in definition.allowed_gate_requests:
                        allowed_proposals.append(proposal)
                else:
                    # Lane actions and messages pass through
                    allowed_proposals.append(proposal)
            proposals = allowed_proposals

        return AgentPacket(
            message=packet.message,
            proposals=proposals,
            confidence=packet.confidence,
            traces=packet.traces.copy(),
            created_at=packet.created_at,
        )

    def validate_handoff(
        self,
        source_packet: AgentPacket,
        target_agent_id: str,
    ) -> FirewallResult:
        """
        Validate a handoff between agents (for chain orchestration).

        Ensures only structured handoff data is passed, no prompt smuggling.
        """
        violations = []

        # Check message doesn't contain instruction smuggling
        smuggling_patterns = [
            "ignore previous",
            "disregard instructions",
            "override",
            "you are now",
            "forget everything",
        ]

        for pattern in smuggling_patterns:
            if pattern.lower() in source_packet.message.lower():
                violations.append(FirewallViolation(
                    code="PROMPT_SMUGGLING",
                    message=f"Potential prompt smuggling detected: '{pattern}'",
                    severity="error",
                ))

        # Handoffs should only pass structured data
        if len(source_packet.proposals) > 3:
            violations.append(FirewallViolation(
                code="EXCESSIVE_HANDOFF",
                message="Handoff contains too many proposals",
                severity="warning",
            ))

        passed = len([v for v in violations if v.severity == "error"]) == 0

        return FirewallResult(
            passed=passed,
            violations=violations,
        )
