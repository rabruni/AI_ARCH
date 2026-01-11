"""Bridge Memory - Cross-loop coordination.

Stores:
- Proposals awaiting slow loop processing
- Signals from fast loop to slow loop
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


@dataclass
class BridgeSignal:
    """Signal from fast loop to slow loop."""
    signal_type: str  # "stance_proposal", "commitment_concern", "emergency_flag"
    source: str       # Which component raised it
    content: str
    severity: str = "normal"  # "normal", "high", "emergency"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "signal_type": self.signal_type,
            "source": self.source,
            "content": self.content,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BridgeSignal":
        data = data.copy()
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class BridgeMemory:
    """
    Bridge between fast and slow loops.

    Fast loop writes signals here.
    Slow loop reads and clears them.
    """

    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._signals_file = self.memory_dir / "bridge_signals.json"
        self._signals: list[BridgeSignal] = []

        self._load()

    def _load(self):
        """Load state from disk."""
        if self._signals_file.exists():
            try:
                data = json.loads(self._signals_file.read_text())
                self._signals = [BridgeSignal.from_dict(s) for s in data]
            except (json.JSONDecodeError, TypeError):
                self._signals = []

    def _save(self):
        """Save state to disk."""
        data = [s.to_dict() for s in self._signals]
        self._signals_file.write_text(json.dumps(data, indent=2))

    def add_signal(self, signal: BridgeSignal):
        """Add a signal from fast loop."""
        self._signals.append(signal)
        self._save()

    def get_pending_signals(self) -> list[BridgeSignal]:
        """Get all pending signals."""
        return self._signals.copy()

    def get_signals_by_type(self, signal_type: str) -> list[BridgeSignal]:
        """Get signals of a specific type."""
        return [s for s in self._signals if s.signal_type == signal_type]

    def has_emergency(self) -> bool:
        """Check if there's an emergency signal."""
        return any(s.severity == "emergency" for s in self._signals)

    def clear_signals(self):
        """Clear all processed signals."""
        self._signals = []
        self._save()

    def clear_signal(self, signal: BridgeSignal):
        """Clear a specific signal."""
        self._signals = [s for s in self._signals if s != signal]
        self._save()
