"""Fast Memory - Ephemeral state for fast loop."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal
import json


@dataclass
class ProgressState:
    """Current progress within commitment."""
    milestones_completed: list[str] = field(default_factory=list)
    milestones_total: int = 0
    blockers: list[str] = field(default_factory=list)
    momentum: Literal["accelerating", "steady", "stalled"] = "steady"
    last_update: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "milestones_completed": self.milestones_completed,
            "milestones_total": self.milestones_total,
            "blockers": self.blockers,
            "momentum": self.momentum,
            "last_update": self.last_update.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressState":
        data = data.copy()
        if "last_update" in data:
            data["last_update"] = datetime.fromisoformat(data["last_update"])
        return cls(**data)


@dataclass
class InteractionSignals:
    """Per-turn interaction signals."""
    user_input_length: int = 0
    response_length: int = 0
    altitude_used: str = "L3"
    stance_used: str = "sensemaking"
    had_commitment: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "user_input_length": self.user_input_length,
            "response_length": self.response_length,
            "altitude_used": self.altitude_used,
            "stance_used": self.stance_used,
            "had_commitment": self.had_commitment,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InteractionSignals":
        data = data.copy()
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class FastMemory:
    """Session-level fast memory."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._progress_file = self.memory_dir / "progress.json"
        self._interactions_file = self.memory_dir / "interactions.json"
        self._progress: ProgressState = ProgressState()
        self._interactions: list[InteractionSignals] = []
        self._load()

    def _load(self):
        if self._progress_file.exists():
            try:
                data = json.loads(self._progress_file.read_text())
                self._progress = ProgressState.from_dict(data)
            except:
                self._progress = ProgressState()
        if self._interactions_file.exists():
            try:
                data = json.loads(self._interactions_file.read_text())
                self._interactions = [InteractionSignals.from_dict(i) for i in data]
            except:
                self._interactions = []

    def _save_progress(self):
        self._progress_file.write_text(json.dumps(self._progress.to_dict(), indent=2))

    def _save_interactions(self):
        recent = self._interactions[-100:]
        data = [i.to_dict() for i in recent]
        self._interactions_file.write_text(json.dumps(data, indent=2))

    def get_progress(self) -> ProgressState:
        return self._progress

    def update_progress(self, milestone_completed: Optional[str] = None,
                       blocker_added: Optional[str] = None,
                       blocker_removed: Optional[str] = None,
                       momentum: Optional[str] = None):
        if milestone_completed:
            self._progress.milestones_completed.append(milestone_completed)
        if blocker_added:
            self._progress.blockers.append(blocker_added)
        if blocker_removed and blocker_removed in self._progress.blockers:
            self._progress.blockers.remove(blocker_removed)
        if momentum:
            self._progress.momentum = momentum
        self._progress.last_update = datetime.now()
        self._save_progress()

    def reset_progress(self, total_milestones: int = 0):
        self._progress = ProgressState(milestones_total=total_milestones)
        self._save_progress()

    def record_interaction(self, signals: InteractionSignals):
        self._interactions.append(signals)
        self._save_interactions()

    def get_recent_interactions(self, n: int = 10) -> list[InteractionSignals]:
        return self._interactions[-n:]

    def get_interaction_summary(self) -> dict:
        recent = self._interactions[-20:]
        if not recent:
            return {"count": 0, "avg_input_length": 0, "avg_response_length": 0, "altitude_distribution": {}}
        altitudes = {}
        for i in recent:
            altitudes[i.altitude_used] = altitudes.get(i.altitude_used, 0) + 1
        return {
            "count": len(recent),
            "avg_input_length": sum(i.user_input_length for i in recent) / len(recent),
            "avg_response_length": sum(i.response_length for i in recent) / len(recent),
            "altitude_distribution": altitudes
        }
