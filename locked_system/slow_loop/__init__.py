"""Slow Loop - Authority Layer.

Components:
- CommitmentManager: Manages commitment leases with expiry
- StanceMachine: Exclusive stance state machine (4 stances)
- GateController: Controls gate transitions
"""
from locked_system.slow_loop.commitment import CommitmentManager
from locked_system.slow_loop.stance import StanceMachine, Stance
from locked_system.slow_loop.gates import GateController

__all__ = [
    'CommitmentManager', 'StanceMachine', 'Stance',
    'GateController',
]
