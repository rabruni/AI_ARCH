"""Agents Subsystem - Dynamic agent system with YAML definitions.

Provides:
- AgentDefinition: YAML-defined agent configurations
- AgentPacket: Structured agent output (proposals only)
- AgentRuntime: Agent invocation wrapper
- PacketFirewall: Validates agent outputs
- Orchestration modes: single, router, panel, chain

Key invariants:
- Agents are proposal-only (never execute tools directly)
- Packets must pass firewall validation
- Orchestration budgets enforced
- Emotional signals passed through unchanged
"""

# Legacy exports (for backward compatibility)
from locked_system.agents.base.agent import (
    BaseAgent,
    AgentContext as LegacyAgentContext,
    AgentResponse,
    DefaultAgent,
    load_agent,
)

# New spec-compliant exports
from locked_system.agents.models import (
    AgentDefinition,
    AgentPacket,
    Proposal,
    ProposalType,
    PromptProfile,
    AgentContext,
)
from locked_system.agents.loader import AgentLoader
from locked_system.agents.runtime import AgentRuntime, RuntimeConfig
from locked_system.agents.firewall import PacketFirewall, FirewallViolation, FirewallResult
from locked_system.agents.orchestrator import (
    Orchestrator,
    OrchestrationMode,
    OrchestrationResult,
    OrchestrationBudget,
)

__all__ = [
    # Legacy
    'BaseAgent',
    'LegacyAgentContext',
    'AgentResponse',
    'DefaultAgent',
    'load_agent',
    # New
    'AgentDefinition',
    'AgentPacket',
    'Proposal',
    'ProposalType',
    'PromptProfile',
    'AgentContext',
    'AgentLoader',
    'AgentRuntime',
    'RuntimeConfig',
    'PacketFirewall',
    'FirewallViolation',
    'FirewallResult',
    'Orchestrator',
    'OrchestrationMode',
    'OrchestrationResult',
    'OrchestrationBudget',
]
