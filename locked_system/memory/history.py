"""History - Non-Authoritative Audit Trail.

Session summaries and gate transitions.
Cannot become source of truth. Used for summarization/audit only.
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class SessionRecord:
    """A session record."""
    session_id: str
    start_time: datetime
    end_time: datetime
    summary: str
    turns: int
    final_stance: str
    commitment_active: bool


@dataclass
class GateTransition:
    """A gate transition record."""
    gate: Literal["framing", "commitment", "evaluation", "emergency"]
    from_stance: str
    to_stance: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


class History:
    """
    History manager.

    Non-authoritative. Audit and summarization only.
    """

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir / "history"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._sessions_file = self.memory_dir / "sessions.json"
        self._gates_file = self.memory_dir / "gates.json"

        self._sessions: list[SessionRecord] = []
        self._gates: list[GateTransition] = []

        self._load()

    def _load(self):
        """Load history from disk."""
        if self._sessions_file.exists():
            try:
                data = json.loads(self._sessions_file.read_text())
                self._sessions = [
                    SessionRecord(
                        **{
                            **s,
                            'start_time': datetime.fromisoformat(s['start_time']),
                            'end_time': datetime.fromisoformat(s['end_time'])
                        }
                    ) for s in data
                ]
            except (json.JSONDecodeError, KeyError):
                self._sessions = []

        if self._gates_file.exists():
            try:
                data = json.loads(self._gates_file.read_text())
                self._gates = [
                    GateTransition(
                        **{**g, 'timestamp': datetime.fromisoformat(g['timestamp'])}
                    ) for g in data
                ]
            except (json.JSONDecodeError, KeyError):
                self._gates = []

    def _save_sessions(self):
        """Save sessions to disk."""
        data = []
        for s in self._sessions[-50:]:  # Keep last 50 sessions
            d = asdict(s)
            d['start_time'] = d['start_time'].isoformat()
            d['end_time'] = d['end_time'].isoformat()
            data.append(d)
        self._sessions_file.write_text(json.dumps(data, indent=2))

    def _save_gates(self):
        """Save gate transitions to disk."""
        data = []
        for g in self._gates[-100:]:  # Keep last 100 transitions
            d = asdict(g)
            d['timestamp'] = d['timestamp'].isoformat()
            data.append(d)
        self._gates_file.write_text(json.dumps(data, indent=2))

    def add_session(self, session: SessionRecord):
        """Add a session record."""
        self._sessions.append(session)
        self._save_sessions()

    def add_gate_transition(self, transition: GateTransition):
        """Add a gate transition record."""
        self._gates.append(transition)
        self._save_gates()

    def get_recent_sessions(self, n: int = 5) -> list[SessionRecord]:
        """Get recent sessions."""
        return self._sessions[-n:]

    def get_recent_gates(self, n: int = 10) -> list[GateTransition]:
        """Get recent gate transitions."""
        return self._gates[-n:]

    def get_session_count(self) -> int:
        """Get total session count."""
        return len(self._sessions)
