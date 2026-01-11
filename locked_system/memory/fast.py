"""Fast Memory - Non-Authoritative, Continuous, Decays.

Contains:
- Progress State (current stage, next actions, blockers)
- Interaction Signals (per-turn metrics for continuous eval)
- Interaction Preferences (accumulated user preferences)

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
    momentum: str = "building"  # building, stalled, accelerating
    milestones_completed: int = 0
    milestones_total: int = 0
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
    """Per-turn interaction metrics (for continuous eval)."""
    user_input_length: int
    response_length: int
    altitude_used: str
    stance_used: str
    had_commitment: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class InteractionPreferences:
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
        self._preferences_file = self.memory_dir / "preferences.json"

        self._progress: Optional[ProgressState] = None
        self._recent_signals: list[InteractionSignals] = []
        self._preferences: Optional[InteractionPreferences] = None

        self._load()

    def _load(self):
        """Load state from disk."""
        if self._progress_file.exists():
            try:
                data = json.loads(self._progress_file.read_text())
                if data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    self._progress = ProgressState(**data)
            except (json.JSONDecodeError, KeyError, TypeError):
                self._progress = None

        if self._signals_file.exists():
            try:
                data = json.loads(self._signals_file.read_text())
                if data:
                    self._recent_signals = []
                    for item in data:
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                        self._recent_signals.append(InteractionSignals(**item))
            except (json.JSONDecodeError, KeyError, TypeError):
                self._recent_signals = []

        if self._preferences_file.exists():
            try:
                data = json.loads(self._preferences_file.read_text())
                if data:
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    self._preferences = InteractionPreferences(**data)
            except (json.JSONDecodeError, KeyError, TypeError):
                self._preferences = None

    def _save_progress(self):
        """Save progress to disk."""
        if self._progress:
            data = asdict(self._progress)
            data['updated_at'] = data['updated_at'].isoformat()
            self._progress_file.write_text(json.dumps(data, indent=2))

    def _save_signals(self):
        """Save recent signals to disk."""
        data = []
        for sig in self._recent_signals[-20:]:  # Keep last 20
            item = asdict(sig)
            item['timestamp'] = item['timestamp'].isoformat()
            data.append(item)
        self._signals_file.write_text(json.dumps(data, indent=2))

    def _save_preferences(self):
        """Save preferences to disk."""
        if self._preferences:
            data = asdict(self._preferences)
            data['updated_at'] = data['updated_at'].isoformat()
            self._preferences_file.write_text(json.dumps(data, indent=2))

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

    # Per-turn signal methods

    def record_interaction(self, signals: InteractionSignals):
        """Record per-turn interaction signals."""
        self._recent_signals.append(signals)
        # Keep only last 20
        if len(self._recent_signals) > 20:
            self._recent_signals = self._recent_signals[-20:]
        self._save_signals()

    def get_recent_signals(self, n: int = 5) -> list[InteractionSignals]:
        """Get recent interaction signals."""
        return self._recent_signals[-n:]

    def clear_signals(self):
        """Clear interaction signals."""
        self._recent_signals = []
        if self._signals_file.exists():
            self._signals_file.unlink()

    # Preferences methods

    def get_preferences(self) -> Optional[InteractionPreferences]:
        """Get interaction preferences."""
        return self._preferences

    def set_preferences(self, preferences: InteractionPreferences):
        """Set interaction preferences."""
        self._preferences = preferences
        self._save_preferences()

    def add_preference(self, preference: str):
        """Add a user preference."""
        if not self._preferences:
            self._preferences = InteractionPreferences(
                user_preferences=[],
                friction_signals=[],
                effective_patterns=[],
                avoidances=[]
            )
        if preference not in self._preferences.user_preferences:
            self._preferences.user_preferences.append(preference)
            self._preferences.updated_at = datetime.now()
            self._save_preferences()

    def add_friction(self, signal: str):
        """Add a friction signal."""
        if not self._preferences:
            self._preferences = InteractionPreferences(
                user_preferences=[],
                friction_signals=[],
                effective_patterns=[],
                avoidances=[]
            )
        if signal not in self._preferences.friction_signals:
            self._preferences.friction_signals.append(signal)
            self._preferences.updated_at = datetime.now()
            self._save_preferences()

    def add_effective_pattern(self, pattern: str):
        """Add an effective pattern."""
        if not self._preferences:
            self._preferences = InteractionPreferences(
                user_preferences=[],
                friction_signals=[],
                effective_patterns=[],
                avoidances=[]
            )
        if pattern not in self._preferences.effective_patterns:
            self._preferences.effective_patterns.append(pattern)
            self._preferences.updated_at = datetime.now()
            self._save_preferences()

    def add_avoidance(self, avoidance: str):
        """Add an avoidance pattern."""
        if not self._preferences:
            self._preferences = InteractionPreferences(
                user_preferences=[],
                friction_signals=[],
                effective_patterns=[],
                avoidances=[]
            )
        if avoidance not in self._preferences.avoidances:
            self._preferences.avoidances.append(avoidance)
            self._preferences.updated_at = datetime.now()
            self._save_preferences()

    def clear_preferences(self):
        """Clear preferences."""
        self._preferences = None
        if self._preferences_file.exists():
            self._preferences_file.unlink()
