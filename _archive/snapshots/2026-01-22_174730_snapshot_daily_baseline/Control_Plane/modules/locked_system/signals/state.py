"""Signal State - Core data structures for system signals."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class Trend(Enum):
    """Direction of change."""
    UP = "up"
    FLAT = "flat"
    DOWN = "down"


class Sentiment(Enum):
    """Detected user sentiment."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class HealthStatus(Enum):
    """System health status."""
    HEALTHY = "healthy"
    CONCERNING = "concerning"
    CRITICAL = "critical"


@dataclass
class SignalSnapshot:
    """Point-in-time signal reading."""
    timestamp: datetime
    signal_type: str
    value: any
    source: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SignalState:
    """Current state of all system signals."""

    # Core signals
    altitude: str = "L2"                    # L1/L2/L3/L4
    altitude_reason: str = ""               # Why at this altitude

    stance: str = "sensemaking"             # Current stance

    # Trust (computed from events)
    trust: float = 0.5                      # 0.0-1.0
    trust_trend: Trend = Trend.FLAT         # Direction
    trust_events: int = 0                   # Events contributing to score

    # Learning activity
    learning_active: bool = False           # Currently writing state?
    learning_target: str = ""               # What's being written
    writes_this_session: int = 0            # Write count

    # Progress toward commitment
    progress: Trend = Trend.FLAT            # Direction
    progress_score: float = 0.5             # 0.0-1.0

    # User sentiment
    sentiment: Sentiment = Sentiment.NEUTRAL
    sentiment_confidence: float = 0.0       # How confident in reading

    # Alignment to commitment frame
    alignment: float = 1.0                  # 0.0-1.0
    alignment_drift: bool = False           # Significant drift detected?

    # Health (from continuous eval)
    health: HealthStatus = HealthStatus.HEALTHY
    health_dimensions: dict = field(default_factory=dict)

    # Metadata
    turn: int = 0
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'altitude': self.altitude,
            'altitude_reason': self.altitude_reason,
            'stance': self.stance,
            'trust': self.trust,
            'trust_trend': self.trust_trend.value,
            'trust_events': self.trust_events,
            'learning_active': self.learning_active,
            'learning_target': self.learning_target,
            'writes_this_session': self.writes_this_session,
            'progress': self.progress.value,
            'progress_score': self.progress_score,
            'sentiment': self.sentiment.value,
            'sentiment_confidence': self.sentiment_confidence,
            'alignment': self.alignment,
            'alignment_drift': self.alignment_drift,
            'health': self.health.value,
            'health_dimensions': self.health_dimensions,
            'turn': self.turn,
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SignalState':
        """Create from dictionary."""
        state = cls()
        state.altitude = data.get('altitude', 'L2')
        state.altitude_reason = data.get('altitude_reason', '')
        state.stance = data.get('stance', 'sensemaking')
        state.trust = data.get('trust', 0.5)
        state.trust_trend = Trend(data.get('trust_trend', 'flat'))
        state.trust_events = data.get('trust_events', 0)
        state.learning_active = data.get('learning_active', False)
        state.learning_target = data.get('learning_target', '')
        state.writes_this_session = data.get('writes_this_session', 0)
        state.progress = Trend(data.get('progress', 'flat'))
        state.progress_score = data.get('progress_score', 0.5)
        state.sentiment = Sentiment(data.get('sentiment', 'neutral'))
        state.sentiment_confidence = data.get('sentiment_confidence', 0.0)
        state.alignment = data.get('alignment', 1.0)
        state.alignment_drift = data.get('alignment_drift', False)
        state.health = HealthStatus(data.get('health', 'healthy'))
        state.health_dimensions = data.get('health_dimensions', {})
        state.turn = data.get('turn', 0)
        if 'updated_at' in data:
            state.updated_at = datetime.fromisoformat(data['updated_at'])
        return state
