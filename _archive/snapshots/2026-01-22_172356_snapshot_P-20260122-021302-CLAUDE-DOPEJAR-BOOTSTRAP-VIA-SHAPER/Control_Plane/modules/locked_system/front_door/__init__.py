"""Front-Door Agent - Default user-facing cognitive router.

The front-door agent handles:
- Signal detection → gate proposals
- Bundle proposals (writer, finance, monitor)
- Orientation UX (active lane, lease status, bookmarks)
- Emotional telemetry as routing input (not therapy)

Key invariants:
- Front-door is proposal-only (never executes tools directly)
- May READ allowlisted config paths
- Must NEVER APPLY writes (WriteApprovalGate required)
- Emotional signals influence routing only (not authority)
"""

from locked_system.front_door.agent import FrontDoorAgent
from locked_system.front_door.signals import SignalDetector, DetectedSignal
from locked_system.front_door.bundles import BundleProposer, Bundle, BundleType
from locked_system.front_door.emotional import EmotionalTelemetry, TelemetryResponse

__all__ = [
    'FrontDoorAgent',
    'SignalDetector',
    'DetectedSignal',
    'BundleProposer',
    'Bundle',
    'BundleType',
    'EmotionalTelemetry',
    'TelemetryResponse',
]
