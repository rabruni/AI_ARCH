"""Lane Data Models - Canonical lane structures.

Based on spec_lanes.md V1 specification.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import uuid4


class LaneKind(Enum):
    """Types of work lanes (V1 enums)."""
    WRITING = "writing"
    FINANCE = "finance"
    RESEARCH = "research"
    OPS = "ops"
    PERSONAL_ADMIN = "personal_admin"


class LaneStatus(Enum):
    """Lane lifecycle status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class LaneLease:
    """Lease information for a lane."""
    mode: str  # "evaluation" | "execution"
    expires_at_utc: datetime
    goal: str

    def is_expired(self) -> bool:
        """Check if lease has expired."""
        return datetime.utcnow() >= self.expires_at_utc

    def to_dict(self) -> dict:
        return {
            'mode': self.mode,
            'expires_at_utc': self.expires_at_utc.isoformat(),
            'goal': self.goal,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LaneLease':
        return cls(
            mode=data['mode'],
            expires_at_utc=datetime.fromisoformat(data['expires_at_utc']),
            goal=data['goal'],
        )


@dataclass
class LanePolicy:
    """Policy settings for a lane."""
    allow_interrupts: bool = True
    interrupt_requires_gate: bool = True
    allow_micro_checks: bool = True
    micro_check_max_seconds: int = 60

    def to_dict(self) -> dict:
        return {
            'allow_interrupts': self.allow_interrupts,
            'interrupt_requires_gate': self.interrupt_requires_gate,
            'allow_micro_checks': self.allow_micro_checks,
            'micro_check_max_seconds': self.micro_check_max_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LanePolicy':
        return cls(
            allow_interrupts=data.get('allow_interrupts', True),
            interrupt_requires_gate=data.get('interrupt_requires_gate', True),
            allow_micro_checks=data.get('allow_micro_checks', True),
            micro_check_max_seconds=data.get('micro_check_max_seconds', 60),
        )


@dataclass
class LaneSnapshot:
    """Snapshot for pause/resume functionality."""
    bookmark: str = ""  # 1-paragraph summary
    next_steps: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'bookmark': self.bookmark,
            'next_steps': self.next_steps,
            'open_questions': self.open_questions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LaneSnapshot':
        return cls(
            bookmark=data.get('bookmark', ''),
            next_steps=data.get('next_steps', []),
            open_questions=data.get('open_questions', []),
        )


@dataclass
class LaneBudgets:
    """Budget limits for a lane."""
    max_tool_requests_per_turn: int = 3
    max_panel_agents: int = 3
    max_chain_depth: int = 3

    def to_dict(self) -> dict:
        return {
            'max_tool_requests_per_turn': self.max_tool_requests_per_turn,
            'max_panel_agents': self.max_panel_agents,
            'max_chain_depth': self.max_chain_depth,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LaneBudgets':
        return cls(
            max_tool_requests_per_turn=data.get('max_tool_requests_per_turn', 3),
            max_panel_agents=data.get('max_panel_agents', 3),
            max_chain_depth=data.get('max_chain_depth', 3),
        )


@dataclass
class Lane:
    """
    A lane is a unit of active work with a lease and a snapshot.

    Canonical structure from spec_lanes.md.
    """
    lane_id: str
    kind: LaneKind
    status: LaneStatus
    lease: LaneLease
    policy: LanePolicy = field(default_factory=LanePolicy)
    snapshot: LaneSnapshot = field(default_factory=LaneSnapshot)
    budgets: LaneBudgets = field(default_factory=LaneBudgets)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        kind: LaneKind,
        goal: str,
        mode: str = "execution",
        expires_hours: int = 4,
        policy: LanePolicy = None,
        budgets: LaneBudgets = None,
    ) -> 'Lane':
        """Factory method to create a new lane."""
        from datetime import timedelta

        lane_id = f"lane_{uuid4().hex[:8]}"
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        return cls(
            lane_id=lane_id,
            kind=kind,
            status=LaneStatus.ACTIVE,
            lease=LaneLease(
                mode=mode,
                expires_at_utc=expires_at,
                goal=goal,
            ),
            policy=policy or LanePolicy(),
            budgets=budgets or LaneBudgets(),
        )

    def is_active(self) -> bool:
        """Check if lane is currently active."""
        return self.status == LaneStatus.ACTIVE

    def is_lease_expired(self) -> bool:
        """Check if lane lease has expired."""
        return self.lease.is_expired()

    def pause(self, bookmark: str, next_steps: List[str] = None, open_questions: List[str] = None):
        """Pause the lane with a snapshot."""
        self.status = LaneStatus.PAUSED
        self.snapshot = LaneSnapshot(
            bookmark=bookmark,
            next_steps=next_steps or [],
            open_questions=open_questions or [],
        )
        self.updated_at = datetime.utcnow()

    def resume(self):
        """Resume a paused lane."""
        if self.status != LaneStatus.PAUSED:
            raise ValueError(f"Cannot resume lane in status {self.status}")
        self.status = LaneStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def complete(self, final_summary: str = None):
        """Complete and seal the lane."""
        self.status = LaneStatus.COMPLETED
        if final_summary:
            self.snapshot.bookmark = final_summary
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'lane_id': self.lane_id,
            'kind': self.kind.value,
            'status': self.status.value,
            'lease': self.lease.to_dict(),
            'policy': self.policy.to_dict(),
            'snapshot': self.snapshot.to_dict(),
            'budgets': self.budgets.to_dict(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Lane':
        """Deserialize from dictionary."""
        return cls(
            lane_id=data['lane_id'],
            kind=LaneKind(data['kind']),
            status=LaneStatus(data['status']),
            lease=LaneLease.from_dict(data['lease']),
            policy=LanePolicy.from_dict(data.get('policy', {})),
            snapshot=LaneSnapshot.from_dict(data.get('snapshot', {})),
            budgets=LaneBudgets.from_dict(data.get('budgets', {})),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
        )
