"""Fast Memory - Non-Authoritative, Continuous, Decays.

Contains:
- Progress State (current stage, next actions, blockers)
- Interaction Signals (user preferences, friction, patterns)

Can be written continuously but cannot override slow memory.
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ProgressState:
    """Current work progress (ephemeral, decays)."""
    current_stage: str
    next_actions: list[str]  # 1-5 items
    blockers: list[str]  # 0-3 items
    recent_wins: list[str]  # last 1-3 completed
    staleness_clock: int = 10  # Turns until stale
    updated_at: datetime = field(default_factory=datetime.now)

    def decrement_staleness(self):
        """Decrement staleness clock."""
        self.staleness_clock = max(0, self.staleness_clock - 1)

    def is_stale(self) -> bool:
        """Check if progress is stale."""
        return self.staleness_clock <= 0

    def refresh(self, turns: int = 10):
        """Refresh staleness clock."""
        self.staleness_clock = turns
        self.updated_at = datetime.now()


@dataclass
class InteractionSignals:
    """Learned interaction preferences (non-authoritative)."""
    user_preferences: list[str]  # brevity, structure, no code, etc.
    friction_signals: list[str]  # overwhelm, impatience, confusion
    effective_patterns: list[str]  # what worked
    avoidances: list[str]  # what harms flow
    updated_at: datetime = field(default_factory=datetime.now)


class FastMemory:
    """
    Fast memory manager.

    Continuous writes allowed. Non-authoritative.
    Cannot override slow memory. Decays naturally.
    """

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir / "fast"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._progress_file = self.memory_dir / "progress.json"
        self._signals_file = self.memory_dir / "signals.json"

        self._progress: Optional[ProgressState] = None
        self._signals: Optional[InteractionSignals] = None

        self._load()

    def _load(self):
        """Load state from disk."""
        if self._progress_file.exists():
            try:
                data = json.loads(self._progress_file.read_text())
                if data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    self._progress = ProgressState(**data)
            except (json.JSONDecodeError, KeyError):
                self._progress = None

        if self._signals_file.exists():
            try:
                data = json.loads(self._signals_file.read_text())
                if data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    self._signals = InteractionSignals(**data)
            except (json.JSONDecodeError, KeyError):
                self._signals = None

    def _save_progress(self):
        """Save progress to disk."""
        if self._progress:
            data = asdict(self._progress)
            data['updated_at'] = data['updated_at'].isoformat()
            self._progress_file.write_text(json.dumps(data, indent=2))

    def _save_signals(self):
        """Save signals to disk."""
        if self._signals:
            data = asdict(self._signals)
            data['updated_at'] = data['updated_at'].isoformat()
            self._signals_file.write_text(json.dumps(data, indent=2))

    # Progress methods
    def get_progress(self) -> Optional[ProgressState]:
        """Get current progress."""
        return self._progress

    def set_progress(self, progress: ProgressState):
        """Set progress state."""
        self._progress = progress
        self._save_progress()

    def update_progress(self, **kwargs):
        """Update progress fields."""
        if self._progress:
            for key, value in kwargs.items():
                if hasattr(self._progress, key):
                    setattr(self._progress, key, value)
            self._progress.updated_at = datetime.now()
            self._save_progress()

    def decrement_staleness(self):
        """Decrement progress staleness."""
        if self._progress:
            self._progress.decrement_staleness()
            self._save_progress()

    def clear_progress(self):
        """Clear progress state."""
        self._progress = None
        if self._progress_file.exists():
            self._progress_file.unlink()

    # Signals methods
    def get_signals(self) -> Optional[InteractionSignals]:
        """Get interaction signals."""
        return self._signals

    def set_signals(self, signals: InteractionSignals):
        """Set interaction signals."""
        self._signals = signals
        self._save_signals()

    def update_signals(self, **kwargs):
        """Update signal fields."""
        if not self._signals:
            self._signals = InteractionSignals(
                user_preferences=[],
                friction_signals=[],
                effective_patterns=[],
                avoidances=[]
            )
        for key, value in kwargs.items():
            if hasattr(self._signals, key):
                setattr(self._signals, key, value)
        self._signals.updated_at = datetime.now()
        self._save_signals()

    def add_preference(self, preference: str):
        """Add a user preference."""
        if not self._signals:
            self._signals = InteractionSignals(
                user_preferences=[],
                friction_signals=[],
                effective_patterns=[],
                avoidances=[]
            )
        if preference not in self._signals.user_preferences:
            self._signals.user_preferences.append(preference)
            self._save_signals()

    def add_friction(self, signal: str):
        """Add a friction signal."""
        if not self._signals:
            self._signals = InteractionSignals(
                user_preferences=[],
                friction_signals=[],
                effective_patterns=[],
                avoidances=[]
            )
        if signal not in self._signals.friction_signals:
            self._signals.friction_signals.append(signal)
            self._save_signals()

    def add_effective_pattern(self, pattern: str):
        """Add an effective pattern."""
        if not self._signals:
            self._signals = InteractionSignals(
                user_preferences=[],
                friction_signals=[],
                effective_patterns=[],
                avoidances=[]
            )
        if pattern not in self._signals.effective_patterns:
            self._signals.effective_patterns.append(pattern)
            self._save_signals()

    def clear_signals(self):
        """Clear signals."""
        self._signals = None
        if self._signals_file.exists():
            self._signals_file.unlink()
