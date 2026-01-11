"""Slow Memory - Persistent state for slow loop."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal
import json


@dataclass
class CommitmentLease:
    """Active commitment with expiry."""
    frame: str
    horizon_authority: str = "mid"
    success_criteria: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    lease_expiry: str = "20 turns"
    renewal_prompt: str = "Continue with this focus?"
    turns_remaining: int = 20

    def is_expired(self) -> bool:
        return self.turns_remaining <= 0

    def to_dict(self) -> dict:
        return {
            "frame": self.frame,
            "horizon_authority": self.horizon_authority,
            "success_criteria": self.success_criteria,
            "non_goals": self.non_goals,
            "lease_expiry": self.lease_expiry,
            "renewal_prompt": self.renewal_prompt,
            "turns_remaining": self.turns_remaining
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CommitmentLease":
        return cls(**data)


@dataclass
class Decision:
    """Binding decision record."""
    id: str
    decision: str
    rationale: list[str]
    tradeoffs: str
    confidence: str
    revisit_triggers: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "decision": self.decision, "rationale": self.rationale,
            "tradeoffs": self.tradeoffs, "confidence": self.confidence,
            "revisit_triggers": self.revisit_triggers, "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Decision":
        data = data.copy()
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class BootstrapSnapshot:
    """Bootstrap state snapshot."""
    bootstrap_timestamp: datetime
    ladder_position: Literal["top", "middle", "bottom"]
    user_state_summary: str
    stabilizers: str
    one_step_gap: str
    microstep_candidate: str
    consent_state: Literal["listen_only", "propose_structure", "ready_for_commitment"]

    def to_dict(self) -> dict:
        return {
            "bootstrap_timestamp": self.bootstrap_timestamp.isoformat(),
            "ladder_position": self.ladder_position,
            "user_state_summary": self.user_state_summary,
            "stabilizers": self.stabilizers,
            "one_step_gap": self.one_step_gap,
            "microstep_candidate": self.microstep_candidate,
            "consent_state": self.consent_state
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BootstrapSnapshot":
        data = data.copy()
        if "bootstrap_timestamp" in data:
            data["bootstrap_timestamp"] = datetime.fromisoformat(data["bootstrap_timestamp"])
        return cls(**data)


class SlowMemory:
    """Persistent storage for slow loop state."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._commitment_file = self.memory_dir / "commitment.json"
        self._decisions_file = self.memory_dir / "decisions.json"
        self._bootstrap_file = self.memory_dir / "bootstrap.json"
        self._commitment: Optional[CommitmentLease] = None
        self._decisions: list[Decision] = []
        self._bootstrap: Optional[BootstrapSnapshot] = None
        self._load()

    def _load(self):
        if self._commitment_file.exists():
            try:
                data = json.loads(self._commitment_file.read_text())
                self._commitment = CommitmentLease.from_dict(data)
            except:
                self._commitment = None
        if self._decisions_file.exists():
            try:
                data = json.loads(self._decisions_file.read_text())
                self._decisions = [Decision.from_dict(d) for d in data]
            except:
                self._decisions = []
        if self._bootstrap_file.exists():
            try:
                data = json.loads(self._bootstrap_file.read_text())
                self._bootstrap = BootstrapSnapshot.from_dict(data)
            except:
                self._bootstrap = None

    def _save_commitment(self):
        if self._commitment:
            self._commitment_file.write_text(json.dumps(self._commitment.to_dict(), indent=2))
        elif self._commitment_file.exists():
            self._commitment_file.unlink()

    def _save_decisions(self):
        data = [d.to_dict() for d in self._decisions]
        self._decisions_file.write_text(json.dumps(data, indent=2))

    def _save_bootstrap(self):
        if self._bootstrap:
            self._bootstrap_file.write_text(json.dumps(self._bootstrap.to_dict(), indent=2))
        elif self._bootstrap_file.exists():
            self._bootstrap_file.unlink()

    def get_commitment(self) -> Optional[CommitmentLease]:
        return self._commitment

    def has_commitment(self) -> bool:
        return self._commitment is not None and not self._commitment.is_expired()

    def set_commitment(self, commitment: CommitmentLease):
        self._commitment = commitment
        self._save_commitment()

    def renew_commitment(self, turns: int = 20):
        if self._commitment:
            self._commitment.turns_remaining = turns
            self._save_commitment()

    def decrement_commitment(self):
        if self._commitment:
            self._commitment.turns_remaining -= 1
            self._save_commitment()

    def clear_commitment(self):
        self._commitment = None
        self._save_commitment()

    def add_decision(self, decision: Decision):
        self._decisions.append(decision)
        self._save_decisions()

    def get_decisions(self) -> list[Decision]:
        return self._decisions.copy()

    def get_recent_decisions(self, n: int = 5) -> list[Decision]:
        return self._decisions[-n:]

    def get_bootstrap(self) -> Optional[BootstrapSnapshot]:
        return self._bootstrap

    def set_bootstrap(self, snapshot: BootstrapSnapshot):
        self._bootstrap = snapshot
        self._save_bootstrap()

    def clear_bootstrap(self):
        self._bootstrap = None
        self._save_bootstrap()
