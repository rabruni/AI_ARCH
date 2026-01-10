"""The Assist - HRM (Hierarchical Reasoning Model)

Four-layer architecture for cognitive partnership:
- L1 Intent: Define success, hold authority
- L2 Planner: Choose approach, manage tradeoffs
- L3 Executor: Do the work, report state
- L4 Evaluator: Compare to intent, trigger revision

Key principle: State flows up, meaning flows down.

Reusable components:
- AltitudeGovernor: Manages altitude transitions for any agent
- AltitudePolicy: Configurable rules per agent/use case
- SessionHistory: Lightweight session memory for continuity
"""

from the_assist.hrm.intent import IntentStore
from the_assist.hrm.planner import Planner
from the_assist.hrm.executor import Executor
from the_assist.hrm.evaluator import Evaluator
from the_assist.hrm.loop import HRMLoop
from the_assist.hrm.history import SessionHistory
from the_assist.hrm.altitude import (
    AltitudeGovernor,
    AltitudePolicy,
    AltitudeContext,
    ValidationResult,
    Level,
    RequestType,
    check_altitude,
    detect_altitude
)

__all__ = [
    'IntentStore', 'Planner', 'Executor', 'Evaluator', 'HRMLoop',
    'SessionHistory',
    'AltitudeGovernor', 'AltitudePolicy', 'AltitudeContext',
    'ValidationResult', 'Level', 'RequestType',
    'check_altitude', 'detect_altitude'
]
