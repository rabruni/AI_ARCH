"""Memory Consent - User consent for persistence operations.

Manages user consent for:
- Conversation history persistence
- Interaction signals (learning)
- Learned preferences

Consent is:
- Explicit (asked on first run)
- Revocable (can be changed anytime)
- Granular (per-category)
- Visible (inspectable via :memory)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


@dataclass
class ConsentPreferences:
    """User consent preferences for memory persistence."""

    # Conversation history - what was discussed
    conversation_history: bool = True

    # Interaction signals - session patterns, health metrics
    interaction_signals: bool = True

    # Learned preferences - style/pattern learning
    learned_preferences: bool = False  # Default off - most sensitive

    # Metadata
    first_consent_at: Optional[str] = None
    last_updated_at: Optional[str] = None
    consent_version: int = 1

    def to_dict(self) -> dict:
        return {
            'conversation_history': self.conversation_history,
            'interaction_signals': self.interaction_signals,
            'learned_preferences': self.learned_preferences,
            'first_consent_at': self.first_consent_at,
            'last_updated_at': self.last_updated_at,
            'consent_version': self.consent_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConsentPreferences':
        return cls(
            conversation_history=data.get('conversation_history', True),
            interaction_signals=data.get('interaction_signals', True),
            learned_preferences=data.get('learned_preferences', False),
            first_consent_at=data.get('first_consent_at'),
            last_updated_at=data.get('last_updated_at'),
            consent_version=data.get('consent_version', 1),
        )


class ConsentManager:
    """Manages memory consent preferences."""

    CONSENT_FILE = "consent.json"

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.consent_file = memory_dir / self.CONSENT_FILE
        self._preferences: Optional[ConsentPreferences] = None
        self._load()

    def _load(self):
        """Load consent preferences from disk."""
        if self.consent_file.exists():
            try:
                data = json.loads(self.consent_file.read_text())
                self._preferences = ConsentPreferences.from_dict(data)
            except (json.JSONDecodeError, TypeError):
                self._preferences = None
        else:
            self._preferences = None

    def _save(self):
        """Save consent preferences to disk."""
        if self._preferences:
            self._preferences.last_updated_at = datetime.now().isoformat()
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            self.consent_file.write_text(
                json.dumps(self._preferences.to_dict(), indent=2)
            )

    def needs_consent(self) -> bool:
        """Check if we need to ask for consent (first run)."""
        return self._preferences is None

    def grant_consent(
        self,
        conversation_history: bool = True,
        interaction_signals: bool = True,
        learned_preferences: bool = False
    ):
        """Record user consent choices."""
        now = datetime.now().isoformat()

        if self._preferences is None:
            self._preferences = ConsentPreferences(
                first_consent_at=now
            )

        self._preferences.conversation_history = conversation_history
        self._preferences.interaction_signals = interaction_signals
        self._preferences.learned_preferences = learned_preferences

        self._save()

    def revoke_all(self):
        """Revoke all consent."""
        if self._preferences:
            self._preferences.conversation_history = False
            self._preferences.interaction_signals = False
            self._preferences.learned_preferences = False
            self._save()

    def can_persist(self, category: str) -> bool:
        """Check if we have consent to persist a category."""
        if self._preferences is None:
            return False

        if category == 'conversation':
            return self._preferences.conversation_history
        elif category == 'signals':
            return self._preferences.interaction_signals
        elif category == 'preferences':
            return self._preferences.learned_preferences
        else:
            return False

    def get_preferences(self) -> Optional[ConsentPreferences]:
        """Get current consent preferences."""
        return self._preferences

    def get_summary(self) -> dict:
        """Get consent summary for display."""
        if self._preferences is None:
            return {
                'status': 'not_configured',
                'message': 'No consent preferences set'
            }

        return {
            'status': 'configured',
            'conversation_history': self._preferences.conversation_history,
            'interaction_signals': self._preferences.interaction_signals,
            'learned_preferences': self._preferences.learned_preferences,
            'first_consent_at': self._preferences.first_consent_at,
            'last_updated_at': self._preferences.last_updated_at,
        }


def format_consent_prompt() -> str:
    """Format the consent prompt for display."""
    return """
┌─────────────────────────────────────────────────────────────┐
│  MEMORY CONSENT                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Locked System can remember context across sessions.        │
│  This helps continuity but means storing data locally.      │
│                                                             │
│  What should I remember?                                    │
│                                                             │
│  [1] Conversation history  - What we discussed              │
│  [2] Interaction signals   - How our sessions went          │
│  [3] Learned preferences   - Patterns in your style         │
│                                                             │
│  You can change these anytime with :memory                  │
│  You can see stored data with :memory show                  │
│  You can clear everything with :memory clear                │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Enter choices (e.g., '12' for options 1 and 2, 'all', or 'none'):"""


def format_consent_status(preferences: ConsentPreferences) -> str:
    """Format consent status for display."""
    lines = []
    lines.append("MEMORY CONSENT STATUS")
    lines.append("")

    def status(enabled: bool) -> str:
        return "✓ enabled" if enabled else "✗ disabled"

    lines.append(f"  Conversation history:  {status(preferences.conversation_history)}")
    lines.append(f"  Interaction signals:   {status(preferences.interaction_signals)}")
    lines.append(f"  Learned preferences:   {status(preferences.learned_preferences)}")
    lines.append("")

    if preferences.first_consent_at:
        lines.append(f"  First consent: {preferences.first_consent_at[:10]}")
    if preferences.last_updated_at:
        lines.append(f"  Last updated:  {preferences.last_updated_at[:10]}")

    return '\n'.join(lines)
