"""Gate Controller - Controls gate transitions.

Three primary gates + emergency:
- Framing Gate: Clarifying what matters
- Commitment Gate: Deciding to move forward
- Evaluation Gate: Assessing outcomes
- Emergency Gate: Escape hatch (costly)
"""
from datetime import datetime
from typing import Optional, Literal
from dataclasses import dataclass

from locked_system.slow_loop.stance import StanceMachine, Stance
from locked_system.slow_loop.commitment import CommitmentManager
from locked_system.memory.slow import SlowMemory, Decision
from locked_system.memory.history import History, GateTransition
from locked_system.proposals.buffer import ProposalBuffer, GateProposal, Severity


@dataclass
class GateResult:
    """Result of a gate transition attempt."""
    success: bool
    gate: str
    from_stance: Stance
    to_stance: Stance
    reason: str
    actions_taken: list[str]


class GateController:
    """
    Controls gate transitions.

    Only authority for stance transitions.
    Enforces gate rules and writes to slow memory.
    """

    def __init__(
        self,
        stance_machine: StanceMachine,
        commitment_manager: CommitmentManager,
        slow_memory: SlowMemory,
        history: History,
        emergency_cooldown: int = 3
    ):
        self.stance = stance_machine
        self.commitment = commitment_manager
        self.memory = slow_memory
        self.history = history
        self.emergency_cooldown = emergency_cooldown
        self._turns_since_emergency = 999  # Start with no cooldown

    def process_proposals(
        self,
        buffer: ProposalBuffer,
        priority_order: list
    ) -> list[GateResult]:
        """
        Process proposals from buffer.

        Returns list of gate results.
        """
        results = []

        # Check for emergency first
        if buffer.has_emergency():
            emergency_proposals = [
                p for p in buffer.get_gate_proposals(priority_order)
                if p.severity == Severity.EMERGENCY
            ]
            for proposal in emergency_proposals:
                result = self.attempt_emergency(proposal.reason)
                results.append(result)
                if result.success:
                    break  # Only one emergency per turn

        # Process non-emergency proposals
        for proposal in buffer.get_gate_proposals(priority_order):
            if proposal.severity == Severity.EMERGENCY:
                continue  # Already handled

            result = self.attempt_gate(
                proposal.suggested_gate,
                proposal.reason
            )
            results.append(result)

        return results

    def attempt_gate(
        self,
        gate: Literal["framing", "commitment", "evaluation"],
        reason: str,
        target_stance: Optional[Stance] = None
    ) -> GateResult:
        """
        Attempt a gate transition.

        Returns GateResult indicating success/failure.
        """
        current_stance = self.stance.current
        actions = []

        if gate == "framing":
            return self._framing_gate(reason, target_stance)
        elif gate == "commitment":
            return self._commitment_gate(reason)
        elif gate == "evaluation":
            return self._evaluation_gate(reason, target_stance)
        else:
            return GateResult(
                success=False,
                gate=gate,
                from_stance=current_stance,
                to_stance=current_stance,
                reason=f"Unknown gate: {gate}",
                actions_taken=[]
            )

    def _framing_gate(
        self,
        reason: str,
        target_stance: Optional[Stance] = None
    ) -> GateResult:
        """
        Framing gate: Clarifying what matters.

        Allowed writes:
        - Draft/renew commitment lease
        - Add decision if it locks frame
        """
        current = self.stance.current
        target = target_stance or Stance.SENSEMAKING
        actions = []

        if self.stance.transition(target, "framing", reason):
            self._record_transition("framing", current, target, reason)
            actions.append(f"Transitioned to {target.value}")
            return GateResult(
                success=True,
                gate="framing",
                from_stance=current,
                to_stance=target,
                reason=reason,
                actions_taken=actions
            )
        else:
            return GateResult(
                success=False,
                gate="framing",
                from_stance=current,
                to_stance=current,
                reason=f"Invalid transition from {current.value} via framing gate",
                actions_taken=[]
            )

    def _commitment_gate(self, reason: str) -> GateResult:
        """
        Commitment gate: Deciding to move forward.

        Allowed writes:
        - Activate/renew commitment lease
        - Log binding decisions
        - Initialize progress state
        """
        current = self.stance.current
        target = Stance.EXECUTION
        actions = []

        if self.stance.transition(target, "commitment", reason):
            self._record_transition("commitment", current, target, reason)
            actions.append(f"Transitioned to {target.value}")
            return GateResult(
                success=True,
                gate="commitment",
                from_stance=current,
                to_stance=target,
                reason=reason,
                actions_taken=actions
            )
        else:
            return GateResult(
                success=False,
                gate="commitment",
                from_stance=current,
                to_stance=current,
                reason=f"Invalid transition from {current.value} via commitment gate",
                actions_taken=[]
            )

    def _evaluation_gate(
        self,
        reason: str,
        target_stance: Optional[Stance] = None
    ) -> GateResult:
        """
        Evaluation gate: Assessing outcomes.

        Allowed writes:
        - Renew/revise/expire commitment
        - Append decision supersessions
        - Update artifact status
        - Reset progress state
        """
        current = self.stance.current
        target = target_stance or Stance.EVALUATION
        actions = []

        if self.stance.transition(target, "evaluation", reason):
            self._record_transition("evaluation", current, target, reason)
            actions.append(f"Transitioned to {target.value}")
            return GateResult(
                success=True,
                gate="evaluation",
                from_stance=current,
                to_stance=target,
                reason=reason,
                actions_taken=actions
            )
        else:
            return GateResult(
                success=False,
                gate="evaluation",
                from_stance=current,
                to_stance=current,
                reason=f"Invalid transition from {current.value} via evaluation gate",
                actions_taken=[]
            )

    def attempt_emergency(self, reason: str) -> GateResult:
        """
        Attempt emergency gate.

        Costly:
        - Logs emergency decision
        - Resets commitment clock
        - Forces sensemaking
        - Cooldown period
        """
        current = self.stance.current
        actions = []

        # Check cooldown
        if self._turns_since_emergency < self.emergency_cooldown:
            return GateResult(
                success=False,
                gate="emergency",
                from_stance=current,
                to_stance=current,
                reason=f"Emergency cooldown: {self.emergency_cooldown - self._turns_since_emergency} turns remaining",
                actions_taken=[]
            )

        # Execute emergency
        self.stance.force_sensemaking(reason)
        actions.append("Forced to sensemaking")

        # Log emergency decision
        decision = Decision(
            id=f"emergency_{datetime.now().isoformat()}",
            decision="Emergency gate triggered",
            rationale=[reason],
            tradeoffs="Commitment paused, requires re-establishment",
            confidence="high",
            revisit_triggers=["User indicates ready to continue"]
        )
        self.memory.add_decision(decision)
        actions.append("Logged emergency decision")

        # Reset commitment clock (but don't clear commitment)
        if self.commitment.has_active_commitment():
            self.commitment.renew(20)  # Reset clock
            actions.append("Reset commitment clock")

        # Record transition
        self._record_transition("emergency", current, Stance.SENSEMAKING, reason)

        # Start cooldown
        self._turns_since_emergency = 0

        return GateResult(
            success=True,
            gate="emergency",
            from_stance=current,
            to_stance=Stance.SENSEMAKING,
            reason=reason,
            actions_taken=actions
        )

    def _record_transition(
        self,
        gate: str,
        from_stance: Stance,
        to_stance: Stance,
        reason: str
    ):
        """Record gate transition to history."""
        transition = GateTransition(
            gate=gate,
            from_stance=from_stance.value,
            to_stance=to_stance.value,
            reason=reason
        )
        self.history.add_gate_transition(transition)

    def tick(self):
        """Called each turn to update cooldowns."""
        self._turns_since_emergency += 1

    def get_state(self) -> dict:
        """Get gate controller state."""
        return {
            "current_stance": self.stance.current.value,
            "turns_since_emergency": self._turns_since_emergency,
            "emergency_available": self._turns_since_emergency >= self.emergency_cooldown
        }
