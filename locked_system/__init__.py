"""Locked System - Two-Loop Cognitive Architecture

A reusable framework for AI agents that manages commitment over time so agents
don't solve the wrong problem well, don't think forever and never deliver,
and behave like trusted partners.

Architecture:
- Slow Loop: Authority (Perception → Commitment → Stance → Gates)
- Fast Loop: Execution (HRM → Execute → Continuous Eval)
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
        on_bootstrap_complete=lambda name: print(f"Welcome {name}"),
        prompt_enhancer=lambda p: f"Be helpful.\n\n{p}"
    )
"""

# Core
from locked_system.loop import LockedLoop, LoopResult
from locked_system.config import Config

# Slow loop components
from locked_system.slow_loop.stance import StanceMachine, Stance
from locked_system.slow_loop.commitment import CommitmentManager
from locked_system.slow_loop.gates import GateController, GateResult
from locked_system.slow_loop.bootstrap import Bootstrap, BootstrapStage

# Fast loop components
from locked_system.fast_loop.hrm import HRM, Altitude, HRMAssessment
from locked_system.fast_loop.executor import Executor, ExecutionContext, ExecutionResult
from locked_system.fast_loop.continuous_eval import ContinuousEvaluator

# Memory tiers
from locked_system.memory.slow import SlowMemory, CommitmentLease, Decision, BootstrapSnapshot
from locked_system.memory.fast import FastMemory, ProgressState, InteractionSignals
from locked_system.memory.bridge import BridgeMemory, BridgeSignal
from locked_system.memory.history import History, GateTransition

# Proposals
from locked_system.proposals.buffer import (
    ProposalBuffer,
    GateProposal,
    BootstrapTransitionProposal
)

# Sensing
from locked_system.sensing.perception import PerceptionSensor, PerceptionContext, PerceptionReport
from locked_system.sensing.contrast import ContrastDetector, ContrastContext, ContrastReport

__all__ = [
    # Core
    'LockedLoop', 'LoopResult', 'Config',

    # Slow loop
    'StanceMachine', 'Stance',
    'CommitmentManager',
    'GateController', 'GateResult',
    'Bootstrap', 'BootstrapStage',

    # Fast loop
    'HRM', 'Altitude', 'HRMAssessment',
    'Executor', 'ExecutionContext', 'ExecutionResult',
    'ContinuousEvaluator',

    # Memory
    'SlowMemory', 'CommitmentLease', 'Decision', 'BootstrapSnapshot',
    'FastMemory', 'ProgressState', 'InteractionSignals',
    'BridgeMemory', 'BridgeSignal',
    'History', 'GateTransition',

    # Proposals
    'ProposalBuffer', 'GateProposal', 'BootstrapTransitionProposal',

    # Sensing
    'PerceptionSensor', 'PerceptionContext', 'PerceptionReport',
    'ContrastDetector', 'ContrastContext', 'ContrastReport',
]

__version__ = '0.1.0'
