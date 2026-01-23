"""Signal Computer - Derives computed values from raw signals.

Computes:
- Trust score from weighted events
- Trend directions from history
- Aggregated health status
"""

from datetime import datetime, timedelta
from typing import List

from locked_system.signals.state import SignalState, Trend, Sentiment, HealthStatus
from locked_system.signals.collector import SignalCollector


class SignalComputer:
    """Computes derived signal values."""

    # Trust decay - older events count less
    TRUST_DECAY_HOURS = 24  # Events older than this decay
    TRUST_BASELINE = 0.5    # Starting trust level

    # Trend detection windows
    TREND_WINDOW_SIGNALS = 5  # Look at last N signals for trend

    def __init__(self, collector: SignalCollector):
        """Initialize with signal collector."""
        self.collector = collector

    def compute_trust(self) -> tuple[float, Trend, int]:
        """
        Compute current trust score from events.

        Returns (score, trend, event_count)

        Trust is computed as:
        - Start at baseline (0.5)
        - Add/subtract weighted events
        - Apply time decay to older events
        - Clamp to 0.0-1.0
        """
        events = self.collector.get_trust_events()
        if not events:
            return self.TRUST_BASELINE, Trend.FLAT, 0

        now = datetime.now()
        decay_cutoff = now - timedelta(hours=self.TRUST_DECAY_HOURS)

        # Compute weighted sum with decay
        score = self.TRUST_BASELINE
        recent_deltas = []

        for event in events:
            weight = event['weight']

            # Apply time decay
            event_time = event['timestamp']
            if event_time < decay_cutoff:
                # Linear decay for old events
                hours_old = (now - event_time).total_seconds() / 3600
                decay_factor = max(0.1, 1.0 - (hours_old / (self.TRUST_DECAY_HOURS * 2)))
                weight *= decay_factor

            score += weight
            recent_deltas.append(weight)

        # Clamp score
        score = max(0.0, min(1.0, score))

        # Compute trend from recent events
        trend = self._compute_trend(recent_deltas[-self.TREND_WINDOW_SIGNALS:])

        return score, trend, len(events)

    def compute_progress_trend(self) -> Trend:
        """Compute progress trend from recent progress signals."""
        history = self.collector.get_history('progress', n=self.TREND_WINDOW_SIGNALS)
        if not history:
            return Trend.FLAT

        scores = [s.metadata.get('score', 0.5) for s in history]
        return self._compute_trend_from_values(scores)

    def compute_alignment_drift(self) -> bool:
        """Check if alignment is drifting significantly."""
        history = self.collector.get_history('alignment', n=self.TREND_WINDOW_SIGNALS)
        if len(history) < 2:
            return False

        scores = [s.value for s in history]
        # Drift if alignment dropped more than 0.3 recently
        if len(scores) >= 2:
            recent_drop = scores[0] - scores[-1]  # Oldest to newest
            return recent_drop > 0.3

        return False

    def get_state(self) -> SignalState:
        """Get complete signal state with computed values."""
        current = self.collector.get_current_values()

        # Compute trust
        trust, trust_trend, trust_events = self.compute_trust()

        # Compute alignment drift
        alignment_drift = self.compute_alignment_drift()

        # Build state
        state = SignalState(
            altitude=current['altitude'],
            altitude_reason=current['altitude_reason'],
            stance=current['stance'],
            trust=trust,
            trust_trend=trust_trend,
            trust_events=trust_events,
            learning_active=current['learning_active'],
            learning_target=current['learning_target'],
            writes_this_session=current['writes_this_session'],
            progress=current['progress'],
            progress_score=current['progress_score'],
            sentiment=current['sentiment'],
            sentiment_confidence=current['sentiment_confidence'],
            alignment=current['alignment'],
            alignment_drift=alignment_drift,
            health=HealthStatus(current['health']) if current['health'] in [e.value for e in HealthStatus] else HealthStatus.HEALTHY,
            health_dimensions=current['health_dimensions'],
            turn=current['turn'],
            updated_at=datetime.now(),
        )

        return state

    def _compute_trend(self, deltas: List[float]) -> Trend:
        """Compute trend direction from a list of deltas."""
        if not deltas:
            return Trend.FLAT

        # Sum recent deltas
        total = sum(deltas)

        if total > 0.05:
            return Trend.UP
        elif total < -0.05:
            return Trend.DOWN
        return Trend.FLAT

    def _compute_trend_from_values(self, values: List[float]) -> Trend:
        """Compute trend from a series of values."""
        if len(values) < 2:
            return Trend.FLAT

        # Simple: compare first half average to second half average
        mid = len(values) // 2
        first_half = sum(values[:mid]) / max(1, mid)
        second_half = sum(values[mid:]) / max(1, len(values) - mid)

        diff = second_half - first_half

        if diff > 0.1:
            return Trend.UP
        elif diff < -0.1:
            return Trend.DOWN
        return Trend.FLAT
