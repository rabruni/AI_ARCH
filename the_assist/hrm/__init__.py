"""The Assist - HRM (Hierarchical Reasoning Model)

Four-layer architecture for cognitive partnership:
- L1 Intent: Define success, hold authority
- L2 Planner: Choose approach, manage tradeoffs
- L3 Executor: Do the work, report state
- L4 Evaluator: Compare to intent, trigger revision

Key principle: State flows up, meaning flows down.
"""

from the_assist.hrm.intent import IntentStore
from the_assist.hrm.planner import Planner
from the_assist.hrm.executor import Executor
from the_assist.hrm.evaluator import Evaluator
from the_assist.hrm.loop import HRMLoop

__all__ = ['IntentStore', 'Planner', 'Executor', 'Evaluator', 'HRMLoop']
