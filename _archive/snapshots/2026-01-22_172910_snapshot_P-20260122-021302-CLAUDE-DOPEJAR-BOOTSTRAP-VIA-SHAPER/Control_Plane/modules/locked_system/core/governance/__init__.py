"""Governance - Authority components.

Only governance can:
- Transition stances
- Create/renew/expire commitments
- Grant/revoke delegations
- Process gate proposals
"""
from locked_system.core.governance.stance import StanceMachine, Stance
from locked_system.core.governance.gates import GateController, GateResult
from locked_system.core.governance.commitment import CommitmentManager
from locked_system.core.governance.delegation import DelegationManager, DelegationLease

__all__ = [
    'StanceMachine', 'Stance',
    'GateController', 'GateResult',
    'CommitmentManager',
    'DelegationManager', 'DelegationLease',
]
