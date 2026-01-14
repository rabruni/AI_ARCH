"""Core - Foundation layer for DoPeJar HRM system.

New simplified architecture:
- types.py: Core enums, HRMError, data types
- trace.py: EpisodicTrace for event logging
- memory_bus.py: Unified memory access
- focus.py: FocusHRM for governance
- orchestrator.py: MapReduce orchestrator

Legacy modules (still available):
- governance/: Stance, gates, commitment, delegation
- execution/: HRM, executor, continuous_eval, prompt_compiler

Invariant: No component outside core can decide. They can only propose.
"""
# ─────────────────────────────────────────────────────────────
# New simplified types
# ─────────────────────────────────────────────────────────────
from locked_system.core.types import (
    Stance,
    GateType,
    ReducerType,
    AltitudeLevel,
    Complexity,
    Stakes,
    ConflictLevel,
    BlastRadius,
    ErrorCode,
    HRMError,
    recover_from_error,
    TurnInput,
    Event,
    Commitment,
    WriteSignals,
    AgentOutput,
    InputClassification,
    AltitudeClassification,
)

from locked_system.core.trace import (
    EpisodicTrace,
    get_trace,
    set_trace,
)

from locked_system.core.memory_bus import (
    MemoryBus,
    WriteGate,
    Tier,
)

from locked_system.core.focus import (
    FocusState,
    FocusHRM,
    StanceMachine,
    GateController,
)

from locked_system.core.orchestrator import (
    Orchestrator,
    ExecutionContext,
    OrchestratorResult,
    Reducer,
    PassThroughReducer,
    MergeReducer,
    VotingReducer,
    get_reducer,
    run_pipeline,
    run_parallel,
    run_voting,
)

# ─────────────────────────────────────────────────────────────
# Legacy imports (backward compatibility)
# ─────────────────────────────────────────────────────────────
try:
    from locked_system.core.governance.stance import StanceMachine as LegacyStanceMachine
    from locked_system.core.governance.gates import GateController as LegacyGateController, GateResult
    from locked_system.core.governance.commitment import CommitmentManager
    from locked_system.core.governance.delegation import DelegationManager, DelegationLease
    from locked_system.core.execution.hrm import HRM, Altitude, HRMAssessment
    from locked_system.core.execution.executor import Executor
    from locked_system.core.execution.continuous_eval import ContinuousEvaluator
    from locked_system.core.execution.prompt_compiler import PromptCompiler
except ImportError:
    # New modules not yet created - skip legacy imports
    pass

__all__ = [
    # Core types
    'Stance', 'GateType', 'ReducerType', 'AltitudeLevel',
    'Complexity', 'Stakes', 'ConflictLevel', 'BlastRadius', 'ErrorCode',
    'HRMError', 'recover_from_error',
    'TurnInput', 'Event', 'Commitment', 'WriteSignals',
    'AgentOutput', 'InputClassification', 'AltitudeClassification',
    # Trace
    'EpisodicTrace', 'get_trace', 'set_trace',
    # Memory
    'MemoryBus', 'WriteGate', 'Tier',
    # Focus
    'FocusState', 'FocusHRM', 'StanceMachine', 'GateController',
    # Orchestrator
    'Orchestrator', 'ExecutionContext', 'OrchestratorResult',
    'Reducer', 'PassThroughReducer', 'MergeReducer', 'VotingReducer',
    'get_reducer', 'run_pipeline', 'run_parallel', 'run_voting',
]
