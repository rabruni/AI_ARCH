"""Agents - Experience layers.

Agents provide:
- Bootstrap content (onboarding experience)
- Style profiles (tone, verbosity)
- Domain focus (specialization)
- Proposal strategies

Agents CANNOT:
- Self-authorize capabilities
- Change stance without gate
- Override core laws
"""
from locked_system.agents.base.agent import (
    BaseAgent,
    AgentContext,
    AgentResponse,
    DefaultAgent,
    load_agent,
)

__all__ = [
    'BaseAgent',
    'AgentContext',
    'AgentResponse',
    'DefaultAgent',
    'load_agent',
]
