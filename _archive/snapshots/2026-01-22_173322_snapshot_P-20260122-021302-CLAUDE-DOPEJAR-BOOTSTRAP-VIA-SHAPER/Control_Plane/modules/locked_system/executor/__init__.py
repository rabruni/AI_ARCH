"""Executor Subsystem - Execution pipeline orchestration.

Pipeline:
1. AgentRuntime invokes agent → AgentPacket
2. PacketFirewall validates packet
3. Executor collects proposals (gate requests, tool requests, lane actions)
4. DecisionPipeline evaluates proposals
5. Executor applies required gates (may return gate prompt)
6. ToolRuntime executes approved tools
7. Executor synthesizes response + writes AuditEvents

Key invariants:
- Never execute tools if a required gate is pending
- Never apply writes without WriteApprovalGate success
- Deterministic ordering of proposals (stable sort)
- All outputs tagged with lane_id, turn_id, agent_id, proposal_id
"""

from locked_system.executor.pipeline import (
    Executor,
    ExecutorConfig,
    SystemResponse,
    TurnState,
)
from locked_system.executor.gates import (
    GateController,
    WriteApprovalGate,
    GatePrompt,
    GateStatus,
)

__all__ = [
    'Executor',
    'ExecutorConfig',
    'SystemResponse',
    'TurnState',
    'GateController',
    'WriteApprovalGate',
    'GatePrompt',
    'GateStatus',
]
