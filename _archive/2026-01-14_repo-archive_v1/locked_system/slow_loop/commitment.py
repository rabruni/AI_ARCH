"""Commitment Manager - Lease-based commitment with expiry.

One active commitment at a time.
Commitments expire unless renewed.
"""
from typing import Optional
from locked_system.memory.slow import SlowMemory, CommitmentLease
from locked_system.proposals.buffer import GateProposal, Severity


class CommitmentManager:
    """
    Manages commitment leases.

    Key invariants:
    - One active commitment at a time
    - Commitments expire unless renewed
    - Only gate-triggered changes allowed
    """

    def __init__(self, slow_memory: SlowMemory):
        self.memory = slow_memory

    def get_current(self) -> Optional[CommitmentLease]:
        """Get current commitment."""
        return self.memory.get_commitment()

    def has_active_commitment(self) -> bool:
        """Check if there's an active, non-expired commitment."""
        return self.memory.has_commitment()

    def create(
        self,
        frame: str,
        horizon_authority: str = "mid",
        success_criteria: list = None,
        non_goals: list = None,
        lease_expiry: str = "20 turns",
        renewal_prompt: str = "Continue with this focus?",
        turns: int = 20
    ) -> CommitmentLease:
        """
        Create a new commitment (gate-controlled).

        Returns the new commitment.
        """
        commitment = CommitmentLease(
            frame=frame,
            horizon_authority=horizon_authority,
            success_criteria=success_criteria or [],
            non_goals=non_goals or [],
            lease_expiry=lease_expiry,
            renewal_prompt=renewal_prompt,
            turns_remaining=turns
        )
        self.memory.set_commitment(commitment)
        return commitment

    def renew(self, turns: int = 20):
        """Renew current commitment (gate-controlled)."""
        self.memory.renew_commitment(turns)

    def expire(self):
        """Expire/clear current commitment (gate-controlled)."""
        self.memory.clear_commitment()

    def decrement_turn(self):
        """Decrement turn counter. Called each turn."""
        self.memory.decrement_commitment()

    def check_expiry(self) -> Optional[GateProposal]:
        """
        Check if commitment has expired.

        Returns GateProposal if expired, None otherwise.
        """
        commitment = self.get_current()
        if commitment and commitment.is_expired():
            return GateProposal(
                reason=f"Commitment expired: {commitment.frame}",
                severity=Severity.HIGH,
                suggested_gate="evaluation",
                source="decay_manager"
            )
        return None

    def get_summary(self) -> dict:
        """Get commitment summary for context."""
        commitment = self.get_current()
        if not commitment:
            return {"active": False}

        return {
            "active": True,
            "frame": commitment.frame,
            "horizon": commitment.horizon_authority,
            "success_criteria": commitment.success_criteria,
            "non_goals": commitment.non_goals,
            "turns_remaining": commitment.turns_remaining,
            "renewal_prompt": commitment.renewal_prompt
        }
