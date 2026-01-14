"""Signals Subsystem - Unified system status indicators.

Provides real-time visibility into system state:
- Altitude (HRM thinking level)
- Trust (accumulated user trust)
- Learning (state persistence activity)
- Progress (commitment progress direction)
- Sentiment (detected user sentiment)
- Alignment (frame alignment)
- Health (system health)

All signals are:
- Visible: Users can inspect anytime
- Computed: Derived from observable events
- Non-manipulable: System can't game its own trust score
"""

from locked_system.signals.state import SignalState, SignalSnapshot
from locked_system.signals.collector import SignalCollector
from locked_system.signals.computer import SignalComputer
from locked_system.signals.display import SignalDisplay

__all__ = [
    'SignalState',
    'SignalSnapshot',
    'SignalCollector',
    'SignalComputer',
    'SignalDisplay',
]
