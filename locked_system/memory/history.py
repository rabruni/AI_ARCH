"""History - Gate transition and conversation history.

Stores:
- Gate transitions
- Conversation turns
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
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
            "gate": self.gate,
            "from_stance": self.from_stance,
            "to_stance": self.to_stance,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GateTransition":
        data = data.copy()
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class ConversationTurn:
    """Single conversation turn."""
    role: str  # "user" or "assistant"
    content: str
    stance: str
    altitude: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "stance": self.stance,
            "altitude": self.altitude,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationTurn":
        data = data.copy()
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class History:
    """
    Historical record of session.

    Stores gate transitions and conversation turns.
    """

    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._gates_file = self.memory_dir / "gate_history.json"
        self._conversation_file = self.memory_dir / "conversation_history.json"

        self._gate_transitions: list[GateTransition] = []
        self._conversation: list[ConversationTurn] = []

        self._load()

    def _load(self):
        """Load state from disk."""
        # Load gate transitions
        if self._gates_file.exists():
            try:
                data = json.loads(self._gates_file.read_text())
                self._gate_transitions = [GateTransition.from_dict(g) for g in data]
            except (json.JSONDecodeError, TypeError):
                self._gate_transitions = []

        # Load conversation
        if self._conversation_file.exists():
            try:
                data = json.loads(self._conversation_file.read_text())
                self._conversation = [ConversationTurn.from_dict(c) for c in data]
            except (json.JSONDecodeError, TypeError):
                self._conversation = []

    def _save_gates(self):
        """Save gate transitions to disk."""
        data = [g.to_dict() for g in self._gate_transitions]
        self._gates_file.write_text(json.dumps(data, indent=2))

    def _save_conversation(self):
        """Save conversation to disk."""
        # Keep last 500 turns
        recent = self._conversation[-500:]
        data = [c.to_dict() for c in recent]
        self._conversation_file.write_text(json.dumps(data, indent=2))

    # Gate transition methods
    def add_gate_transition(self, transition: GateTransition):
        """Record a gate transition."""
        self._gate_transitions.append(transition)
        self._save_gates()

    def get_gate_transitions(self) -> list[GateTransition]:
        """Get all gate transitions."""
        return self._gate_transitions.copy()

    def get_recent_transitions(self, n: int = 10) -> list[GateTransition]:
        """Get n most recent transitions."""
        return self._gate_transitions[-n:]

    def get_transitions_by_gate(self, gate: str) -> list[GateTransition]:
        """Get transitions through a specific gate."""
        return [t for t in self._gate_transitions if t.gate == gate]

    # Conversation methods
    def add_turn(self, turn: ConversationTurn):
        """Add a conversation turn."""
        self._conversation.append(turn)
        self._save_conversation()

    def get_conversation(self) -> list[ConversationTurn]:
        """Get full conversation history."""
        return self._conversation.copy()

    def get_recent_turns(self, n: int = 20) -> list[ConversationTurn]:
        """Get n most recent turns."""
        return self._conversation[-n:]

    def get_turns_since_gate(self, gate: str) -> list[ConversationTurn]:
        """Get turns since last instance of a gate type."""
        transitions = self.get_transitions_by_gate(gate)
        if not transitions:
            return self._conversation.copy()

        last_transition = transitions[-1]
        result = []
        for turn in self._conversation:
            if turn.timestamp > last_transition.timestamp:
                result.append(turn)
        return result

    def clear_session(self):
        """Clear current session history."""
        self._conversation = []
        self._save_conversation()
