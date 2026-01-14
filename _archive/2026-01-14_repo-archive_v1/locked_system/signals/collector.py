"""Signal Collector - Gathers signals from system components.

Components emit signals here. The collector:
- Validates signals
- Timestamps them
- Stores in rolling buffer
- Notifies computer of updates
"""

from datetime import datetime
from typing import Optional, Callable, List
from collections import deque

from locked_system.signals.state import SignalSnapshot, Trend, Sentiment


class SignalCollector:
    """Collects signals from system components."""

    # Trust event weights
    TRUST_WEIGHTS = {
        'delegation_granted': 0.15,      # User granted a capability
        'delegation_revoked': -0.20,     # User revoked (stronger negative)
        'commitment_completed': 0.10,    # Delivered on promise
        'commitment_abandoned': -0.15,   # Broke promise
        'emergency_triggered': -0.25,    # User hit emergency brake
        'session_continued': 0.02,       # Each turn of continued engagement
        'positive_feedback': 0.10,       # Explicit positive
        'negative_feedback': -0.10,      # Explicit negative
        'consent_granted': 0.05,         # User granted memory consent
        'consent_revoked': -0.10,        # User revoked consent
    }

    def __init__(self, max_history: int = 1000):
        """Initialize collector with rolling buffer."""
        self.max_history = max_history
        self._snapshots: deque = deque(maxlen=max_history)
        self._trust_events: List[dict] = []
        self._on_signal: Optional[Callable] = None

        # Current state (updated by each signal)
        self._altitude = "L2"
        self._altitude_reason = ""
        self._stance = "sensemaking"
        self._learning_active = False
        self._learning_target = ""
        self._writes_this_session = 0
        self._sentiment = Sentiment.NEUTRAL
        self._sentiment_confidence = 0.0
        self._progress = Trend.FLAT
        self._progress_score = 0.5
        self._alignment = 1.0
        self._health = "healthy"
        self._health_dimensions = {}
        self._turn = 0

    def set_on_signal(self, callback: Callable[[SignalSnapshot], None]):
        """Set callback for signal notifications."""
        self._on_signal = callback

    def _record(self, signal_type: str, value: any, source: str, metadata: dict = None):
        """Record a signal snapshot."""
        snapshot = SignalSnapshot(
            timestamp=datetime.now(),
            signal_type=signal_type,
            value=value,
            source=source,
            metadata=metadata or {}
        )
        self._snapshots.append(snapshot)

        if self._on_signal:
            self._on_signal(snapshot)

    # === Altitude Signals ===

    def record_altitude(self, level: str, reason: str = "", source: str = "hrm"):
        """Record altitude change from HRM."""
        if level not in ("L1", "L2", "L3", "L4"):
            level = "L2"  # Default

        self._altitude = level
        self._altitude_reason = reason
        self._record("altitude", level, source, {"reason": reason})

    # === Stance Signals ===

    def record_stance(self, stance: str, source: str = "stance_machine"):
        """Record stance change."""
        self._stance = stance
        self._record("stance", stance, source)

    # === Trust Signals ===

    def record_trust_event(self, event: str, source: str = "system"):
        """Record an event that affects trust score."""
        if event not in self.TRUST_WEIGHTS:
            return

        weight = self.TRUST_WEIGHTS[event]
        self._trust_events.append({
            'timestamp': datetime.now(),
            'event': event,
            'weight': weight,
            'source': source
        })
        self._record("trust_event", event, source, {"weight": weight})

    def get_trust_events(self, n: int = None) -> List[dict]:
        """Get recent trust events."""
        if n is None:
            return list(self._trust_events)
        return list(self._trust_events[-n:])

    # === Learning/Write Signals ===

    def record_write_start(self, target: str, source: str = "system"):
        """Record start of state write (learning activity)."""
        self._learning_active = True
        self._learning_target = target
        self._record("write_start", target, source)

    def record_write_end(self, target: str, success: bool = True, source: str = "system"):
        """Record end of state write."""
        self._learning_active = False
        if success:
            self._writes_this_session += 1
        self._record("write_end", target, source, {"success": success})

    # === Sentiment Signals ===

    def record_sentiment(self, sentiment: str, confidence: float = 0.5, source: str = "perception"):
        """Record detected user sentiment."""
        try:
            self._sentiment = Sentiment(sentiment)
        except ValueError:
            self._sentiment = Sentiment.NEUTRAL
        self._sentiment_confidence = max(0.0, min(1.0, confidence))
        self._record("sentiment", sentiment, source, {"confidence": confidence})

    # === Progress Signals ===

    def record_progress(self, direction: str, score: float = 0.5, source: str = "evaluator"):
        """Record progress toward commitment."""
        try:
            self._progress = Trend(direction)
        except ValueError:
            self._progress = Trend.FLAT
        self._progress_score = max(0.0, min(1.0, score))
        self._record("progress", direction, source, {"score": score})

    # === Alignment Signals ===

    def record_alignment(self, score: float, drift: bool = False, source: str = "evaluator"):
        """Record alignment to commitment frame."""
        self._alignment = max(0.0, min(1.0, score))
        self._record("alignment", score, source, {"drift": drift})

    # === Health Signals ===

    def record_health(self, status: str, dimensions: dict = None, source: str = "continuous_eval"):
        """Record health status update."""
        self._health = status
        if dimensions:
            self._health_dimensions = dimensions
        self._record("health", status, source, {"dimensions": dimensions or {}})

    # === Turn Signals ===

    def record_turn(self, turn: int, source: str = "loop"):
        """Record turn advancement."""
        self._turn = turn
        # Each turn of continued engagement is a small trust signal
        self.record_trust_event('session_continued', source)
        self._record("turn", turn, source)

    # === State Access ===

    def get_current_values(self) -> dict:
        """Get current signal values for computer."""
        return {
            'altitude': self._altitude,
            'altitude_reason': self._altitude_reason,
            'stance': self._stance,
            'learning_active': self._learning_active,
            'learning_target': self._learning_target,
            'writes_this_session': self._writes_this_session,
            'sentiment': self._sentiment,
            'sentiment_confidence': self._sentiment_confidence,
            'progress': self._progress,
            'progress_score': self._progress_score,
            'alignment': self._alignment,
            'health': self._health,
            'health_dimensions': self._health_dimensions,
            'turn': self._turn,
            'trust_events': self._trust_events,
        }

    def get_history(self, signal_type: str = None, n: int = 100) -> List[SignalSnapshot]:
        """Get signal history, optionally filtered by type."""
        snapshots = list(self._snapshots)
        if signal_type:
            snapshots = [s for s in snapshots if s.signal_type == signal_type]
        return snapshots[-n:]

    def clear_session(self):
        """Clear session-specific data (keeps trust events)."""
        self._writes_this_session = 0
        self._learning_active = False
        self._learning_target = ""
