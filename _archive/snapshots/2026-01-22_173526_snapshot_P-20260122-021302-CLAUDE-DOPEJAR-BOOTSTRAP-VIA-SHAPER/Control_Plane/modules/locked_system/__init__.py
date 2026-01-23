"""Locked System - Two-Loop Cognitive Architecture

A reusable framework for AI agents that manages commitment over time so agents
don't solve the wrong problem well, don't think forever and never deliver,
and behave like trusted partners.

Architecture:
- Core: Governance (stance, gates, commitment, delegation) + Execution (HRM, executor, eval)
- Agents: Experience layers (style, domain, bootstrap)
- Capabilities: Gated tools (note_capture, memory_write)
- Memory: Durable state (Slow/Fast/Bridge tiers)

Key invariant: Evaluators and sensors propose only. Never decide.

Usage:
    from locked_system import LockedLoop, Config

    # Basic usage
    loop = LockedLoop(Config())
    result = loop.process("Hello")

    # With hooks for extensibility
    loop = LockedLoop(
        Config(system_prompt="path/to/prompt.md"),
        llm_callable=my_llm,
        on_gate_transition=lambda g, f, t: print(f"{g}: {f} -> {t}"),
        prompt_enhancer=lambda p: f"Be helpful.\n\n{p}"
    )
"""

# Core
from locked_system.loop import LockedLoop, LoopResult
from locked_system.config import Config

# Governance (from core)
from locked_system.core.governance.stance import StanceMachine, Stance
from locked_system.core.governance.commitment import CommitmentManager
from locked_system.core.governance.gates import GateController, GateResult
from locked_system.core.governance.delegation import DelegationManager, DelegationLease

# Execution (from core)
from locked_system.core.execution.hrm import HRM, Altitude, HRMAssessment
from locked_system.core.execution.executor import Executor, ExecutionContext, ExecutionResult
from locked_system.core.execution.continuous_eval import ContinuousEvaluator
from locked_system.core.execution.prompt_compiler import PromptCompiler, AgentContext

# Agents
from locked_system.agents import BaseAgent, DefaultAgent, load_agent

# Capabilities
from locked_system.capabilities import (
    CAPABILITIES,
    check_capability,
    NoteCaptureCapability,
    NoteType,
)

# Memory tiers
from locked_system.memory.slow import SlowMemory, CommitmentLease, Decision
from locked_system.memory.fast import FastMemory, ProgressState, InteractionSignals
from locked_system.memory.bridge import BridgeMemory, BridgeSignal
from locked_system.memory.history import History, GateTransition

# Proposals
from locked_system.proposals.buffer import (
    ProposalBuffer,
    GateProposal,
)

# Sensing
from locked_system.sensing.perception import PerceptionSensor, PerceptionContext, PerceptionReport
from locked_system.sensing.contrast import ContrastDetector, ContrastContext, ContrastReport

__all__ = [
    # Core
    'LockedLoop', 'LoopResult', 'Config',

    # Governance
    'StanceMachine', 'Stance',
    'CommitmentManager',
    'GateController', 'GateResult',
    'DelegationManager', 'DelegationLease',

    # Execution
    'HRM', 'Altitude', 'HRMAssessment',
    'Executor', 'ExecutionContext', 'ExecutionResult',
    'ContinuousEvaluator',
    'PromptCompiler', 'AgentContext',

    # Agents
    'BaseAgent', 'DefaultAgent', 'load_agent',

    # Capabilities
    'CAPABILITIES', 'check_capability',
    'NoteCaptureCapability', 'NoteType',

    # Memory
    'SlowMemory', 'CommitmentLease', 'Decision',
    'FastMemory', 'ProgressState', 'InteractionSignals',
    'BridgeMemory', 'BridgeSignal',
    'History', 'GateTransition',

    # Proposals
    'ProposalBuffer', 'GateProposal',

    # Sensing
    'PerceptionSensor', 'PerceptionContext', 'PerceptionReport',
    'ContrastDetector', 'ContrastContext', 'ContrastReport',
]

__version__ = '0.1.0'
