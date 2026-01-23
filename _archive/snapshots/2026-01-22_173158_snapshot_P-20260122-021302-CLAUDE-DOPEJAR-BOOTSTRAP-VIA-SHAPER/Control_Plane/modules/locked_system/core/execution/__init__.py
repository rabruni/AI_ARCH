"""Execution - Response generation within governance bounds.

Execution layer:
- HRM: Depth control (not authority)
- Executor: Response generation
- ContinuousEval: Quality assessment (proposal-only)
- PromptCompiler: Enforces prompt precedence
"""
from locked_system.core.execution.hrm import HRM, Altitude, HRMAssessment
from locked_system.core.execution.executor import Executor, ExecutionContext, ExecutionResult
from locked_system.core.execution.continuous_eval import ContinuousEvaluator
from locked_system.core.execution.prompt_compiler import PromptCompiler

__all__ = [
    'HRM', 'Altitude', 'HRMAssessment',
    'Executor', 'ExecutionContext', 'ExecutionResult',
    'ContinuousEvaluator',
    'PromptCompiler',
]
