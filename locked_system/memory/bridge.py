"""Bridge Memory - Cross-loop coordination."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json


@dataclass
class BridgeSignal:
    """Signal from fast loop to slow loop."""
    signal_type: str
    source: str
    content: str
    severity: str = "normal"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {"signal_type": self.signal_type, "source": self.source,
                "content": self.content, "severity": self.severity,
                "timestamp": self.timestamp.isoformat()}

    @classmethod
    def from_dict(cls, data: dict) -> "BridgeSignal":
        data = data.copy()
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class BridgeMemory:
    """Bridge between fast and slow loops."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._signals_file = self.memory_dir / "bridge_signals.json"
        self._signals: list[BridgeSignal] = []
        self._load()

    def _load(self):
        if self._signals_file.exists():
            try:
                self._signals = [BridgeSignal.from_dict(s) for s in json.loads(self._signals_file.read_text())]
            except:
                self._signals = []

    def _save(self):
        self._signals_file.write_text(json.dumps([s.to_dict() for s in self._signals], indent=2))

    def add_signal(self, signal: BridgeSignal):
        self._signals.append(signal)
        self._save()

    def get_pending_signals(self) -> list[BridgeSignal]:
        return self._signals.copy()

    def has_emergency(self) -> bool:
        return any(s.severity == "emergency" for s in self._signals)

    def clear_signals(self):
        self._signals = []
        self._save()
