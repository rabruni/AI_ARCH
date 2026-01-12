"""Core - Governance layer for locked_system.

The core owns all authority:
- Stance transitions (governance/)
- Gate control (governance/)
- Commitment leases (governance/)
- Delegation management (governance/)
- Prompt compilation (execution/)

Invariant: No component outside core can decide. They can only propose.
"""
from locked_system.core.governance.stance import StanceMachine, Stance
from locked_system.core.governance.gates import GateController, GateResult
from locked_system.core.governance.commitment import CommitmentManager
from locked_system.core.governance.delegation import DelegationManager, DelegationLease
from locked_system.core.execution.hrm import HRM, Altitude, HRMAssessment
from locked_system.core.execution.executor import Executor, ExecutionContext, ExecutionResult
from locked_system.core.execution.continuous_eval import ContinuousEvaluator
from locked_system.core.execution.prompt_compiler import PromptCompiler

__all__ = [
    # Governance
    'StanceMachine', 'Stance',
    'GateController', 'GateResult',
    'CommitmentManager',
    'DelegationManager', 'DelegationLease',
    # Execution
    'HRM', 'Altitude', 'HRMAssessment',
    'Executor', 'ExecutionContext', 'ExecutionResult',
    'ContinuousEvaluator',
    'PromptCompiler',
]
