"""Slow Memory - Authoritative, Gate-Written Only.

Contains:
- Commitment Lease (one active at a time)
- Decision Log (append-only)
- Principles (rarely changes)
- Bootstrap Snapshot (pre-commitment state)
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal


@dataclass
class CommitmentLease:
    """Active commitment with expiry."""
    frame: str  # Problem definition we're committed to
    horizon_authority: Literal["short", "mid", "long"]
    success_criteria: list[str]  # 1-3 bullets
    non_goals: list[str]  # 1-3 bullets
    lease_expiry: str  # time | milestone | signal description
    renewal_prompt: str  # One sentence to re-confirm
    created_at: datetime = field(default_factory=datetime.now)
    turns_remaining: int = 20  # Default lease length in turns

    def decrement(self):
        """Decrement turn counter."""
        self.turns_remaining = max(0, self.turns_remaining - 1)

    def is_expired(self) -> bool:
        """Check if lease has expired."""
        return self.turns_remaining <= 0

    def renew(self, turns: int = 20):
        """Renew the lease."""
        self.turns_remaining = turns


@dataclass
class Decision:
    """A logged decision (append-only)."""
    id: str
    decision: str
    rationale: list[str]  # 1-3 bullets
    tradeoffs: str
    confidence: Literal["low", "med", "high"]
    revisit_triggers: list[str]
    timestamp: datetime = field(default_factory=datetime.now)
    supersedes: Optional[str] = None  # ID of previous decision if any


@dataclass
class BootstrapSnapshot:
    """State captured during Bootstrap."""
    bootstrap_timestamp: datetime
    ladder_position: Literal["top", "middle", "bottom"]
    user_state_summary: str
    stabilizers: str
    one_step_gap: str
    microstep_candidate: str
    consent_state: Literal["listen_only", "propose_structure", "ready_for_commitment"]
    derived_north_star_candidates: list[str] = field(default_factory=list)
    delivery_fit_notes: str = ""


class SlowMemory:
    """
    Slow memory manager.

    Gate-written only. Changes require explicit gate transitions.
    """

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir / "slow"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._commitment_file = self.memory_dir / "commitment.json"
        self._decisions_file = self.memory_dir / "decisions.json"
        self._principles_file = self.memory_dir / "principles.json"
        self._bootstrap_file = self.memory_dir / "bootstrap.json"

        self._commitment: Optional[CommitmentLease] = None
        self._decisions: list[Decision] = []
        self._principles: dict = {}
        self._bootstrap: Optional[BootstrapSnapshot] = None

        self._load()

    def _load(self):
        """Load state from disk."""
        if self._commitment_file.exists():
            try:
                data = json.loads(self._commitment_file.read_text())
                if data:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    self._commitment = CommitmentLease(**data)
            except (json.JSONDecodeError, KeyError):
                self._commitment = None

        if self._decisions_file.exists():
            try:
                data = json.loads(self._decisions_file.read_text())
                self._decisions = [
                    Decision(
                        **{**d, 'timestamp': datetime.fromisoformat(d['timestamp'])}
                    ) for d in data
                ]
            except (json.JSONDecodeError, KeyError):
                self._decisions = []

        if self._principles_file.exists():
            try:
                self._principles = json.loads(self._principles_file.read_text())
            except json.JSONDecodeError:
                self._principles = {}

        if self._bootstrap_file.exists():
            try:
                data = json.loads(self._bootstrap_file.read_text())
                if data:
                    data['bootstrap_timestamp'] = datetime.fromisoformat(data['bootstrap_timestamp'])
                    self._bootstrap = BootstrapSnapshot(**data)
            except (json.JSONDecodeError, KeyError):
                self._bootstrap = None

    def _save_commitment(self):
        """Save commitment to disk."""
        if self._commitment:
            data = asdict(self._commitment)
            data['created_at'] = data['created_at'].isoformat()
            self._commitment_file.write_text(json.dumps(data, indent=2))
        else:
            self._commitment_file.write_text("{}")

    def _save_decisions(self):
        """Save decisions to disk."""
        data = []
        for d in self._decisions:
            dd = asdict(d)
            dd['timestamp'] = dd['timestamp'].isoformat()
            data.append(dd)
        self._decisions_file.write_text(json.dumps(data, indent=2))

    def _save_bootstrap(self):
        """Save bootstrap snapshot to disk."""
        if self._bootstrap:
            data = asdict(self._bootstrap)
            data['bootstrap_timestamp'] = data['bootstrap_timestamp'].isoformat()
            self._bootstrap_file.write_text(json.dumps(data, indent=2))

    # Commitment methods
    def get_commitment(self) -> Optional[CommitmentLease]:
        """Get current commitment."""
        return self._commitment

    def has_commitment(self) -> bool:
        """Check if commitment exists and is valid."""
        return self._commitment is not None and not self._commitment.is_expired()

    def set_commitment(self, commitment: CommitmentLease):
        """Set new commitment (gate-controlled)."""
        self._commitment = commitment
        self._save_commitment()

    def decrement_commitment(self):
        """Decrement commitment turn counter."""
        if self._commitment:
            self._commitment.decrement()
            self._save_commitment()

    def renew_commitment(self, turns: int = 20):
        """Renew current commitment."""
        if self._commitment:
            self._commitment.renew(turns)
            self._save_commitment()

    def clear_commitment(self):
        """Clear commitment (gate-controlled)."""
        self._commitment = None
        self._save_commitment()

    # Decision methods
    def add_decision(self, decision: Decision):
        """Add a decision (append-only)."""
        self._decisions.append(decision)
        self._save_decisions()

    def get_decisions(self, limit: int = 10) -> list[Decision]:
        """Get recent decisions."""
        return self._decisions[-limit:]

    def get_decision_by_id(self, id: str) -> Optional[Decision]:
        """Get decision by ID."""
        for d in self._decisions:
            if d.id == id:
                return d
        return None

    # Bootstrap methods
    def get_bootstrap(self) -> Optional[BootstrapSnapshot]:
        """Get bootstrap snapshot."""
        return self._bootstrap

    def set_bootstrap(self, snapshot: BootstrapSnapshot):
        """Set bootstrap snapshot."""
        self._bootstrap = snapshot
        self._save_bootstrap()

    def has_bootstrap(self) -> bool:
        """Check if bootstrap exists."""
        return self._bootstrap is not None

    # Principles methods
    def get_principles(self) -> dict:
        """Get principles."""
        return self._principles

    def set_principles(self, principles: dict):
        """Set principles (rare, evaluation gate only)."""
        self._principles = principles
        self._principles_file.write_text(json.dumps(principles, indent=2))
