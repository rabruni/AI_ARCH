"""Delegation Manager - Explicit, scoped, time-bounded authority grants.

Capabilities require explicit delegation to use.
Delegations auto-expire unless renewed.
All grants are logged and auditable.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


@dataclass
class DelegationLease:
    """Explicit, scoped, time-bounded authority grant."""
    grantee: str                      # Agent or capability ID
    scope: list[str]                  # What's allowed: ["note_capture", "memory_write"]
    expires_turns: int                # Auto-expire after N turns
    expires_time: Optional[datetime] = None  # Or at specific time
    can_extend: bool = False          # Can grantee request extension?
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)

    def is_expired(self, current_turn: int = 0) -> bool:
        """Check if lease has expired."""
        if self.expires_turns <= 0:
            return True
        if self.expires_time and datetime.now() >= self.expires_time:
            return True
        return False

    def covers(self, capability: str) -> bool:
        """Check if this lease covers the given capability."""
        return capability in self.scope


class DelegationManager:
    """
    Manages delegation leases.

    Key invariants:
    - All capability use requires explicit delegation
    - Delegations are logged
    - Delegations auto-expire
    - Only gates can grant delegations
    """

    def __init__(self):
        self._leases: dict[str, DelegationLease] = {}  # id -> lease
        self._by_grantee: dict[str, list[str]] = {}    # grantee -> lease_ids
        self._log: list[dict] = []

    def grant(self, lease: DelegationLease) -> bool:
        """
        Grant a delegation lease.

        Returns True if granted successfully.
        """
        self._leases[lease.id] = lease

        if lease.grantee not in self._by_grantee:
            self._by_grantee[lease.grantee] = []
        self._by_grantee[lease.grantee].append(lease.id)

        self._log.append({
            "action": "grant",
            "lease_id": lease.id,
            "grantee": lease.grantee,
            "scope": lease.scope,
            "expires_turns": lease.expires_turns,
            "timestamp": datetime.now().isoformat()
        })

        return True

    def revoke(self, lease_id: str) -> bool:
        """
        Revoke a delegation lease.

        Returns True if revoked successfully.
        """
        if lease_id not in self._leases:
            return False

        lease = self._leases[lease_id]
        del self._leases[lease_id]

        if lease.grantee in self._by_grantee:
            self._by_grantee[lease.grantee] = [
                lid for lid in self._by_grantee[lease.grantee]
                if lid != lease_id
            ]

        self._log.append({
            "action": "revoke",
            "lease_id": lease_id,
            "grantee": lease.grantee,
            "timestamp": datetime.now().isoformat()
        })

        return True

    def check(self, grantee: str, capability: str) -> bool:
        """
        Check if grantee has delegation for capability.

        Returns True if authorized.
        """
        if grantee not in self._by_grantee:
            return False

        for lease_id in self._by_grantee[grantee]:
            lease = self._leases.get(lease_id)
            if lease and not lease.is_expired() and lease.covers(capability):
                return True

        return False

    def get_active_leases(self, grantee: str = None) -> list[DelegationLease]:
        """Get active (non-expired) leases, optionally filtered by grantee."""
        leases = []

        for lease in self._leases.values():
            if lease.is_expired():
                continue
            if grantee and lease.grantee != grantee:
                continue
            leases.append(lease)

        return leases

    def tick(self):
        """
        Called each turn to decrement/expire leases.

        Removes expired leases.
        """
        expired_ids = []

        for lease_id, lease in self._leases.items():
            lease.expires_turns -= 1
            if lease.is_expired():
                expired_ids.append(lease_id)

        for lease_id in expired_ids:
            self.revoke(lease_id)
            self._log.append({
                "action": "auto_expire",
                "lease_id": lease_id,
                "timestamp": datetime.now().isoformat()
            })

    def get_log(self, n: int = 10) -> list[dict]:
        """Get recent delegation log entries."""
        return self._log[-n:]

    def get_summary(self) -> dict:
        """Get delegation summary for context."""
        active = [l for l in self._leases.values() if not l.is_expired()]

        return {
            "active_leases": len(active),
            "grantees": list(set(l.grantee for l in active)),
            "capabilities_delegated": list(set(
                cap for l in active for cap in l.scope
            ))
        }
