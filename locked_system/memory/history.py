"""History - Gate transition and conversation history."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json


@dataclass
class GateTransition:
    """Record of a gate transition."""
    gate: str
    from_stance: str
    to_stance: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "gate": self.gate, "from_stance": self.from_stance,
            "to_stance": self.to_stance, "reason": self.reason,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GateTransition":
        data = data.copy()
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class History:
    """Historical record of session."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._gates_file = self.memory_dir / "gate_history.json"
        self._gate_transitions: list[GateTransition] = []
        self._load()

    def _load(self):
        if self._gates_file.exists():
            try:
                data = json.loads(self._gates_file.read_text())
                self._gate_transitions = [GateTransition.from_dict(g) for g in data]
            except:
                self._gate_transitions = []

    def _save_gates(self):
        data = [g.to_dict() for g in self._gate_transitions]
        self._gates_file.write_text(json.dumps(data, indent=2))

    def add_gate_transition(self, transition: GateTransition):
        self._gate_transitions.append(transition)
        self._save_gates()

    def get_gate_transitions(self) -> list[GateTransition]:
        return self._gate_transitions.copy()

    def get_recent_transitions(self, n: int = 10) -> list[GateTransition]:
        return self._gate_transitions[-n:]
