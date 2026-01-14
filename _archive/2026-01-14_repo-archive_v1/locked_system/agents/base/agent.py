"""Base Agent - Experience layer base class.

Agents provide:
- Style profiles (tone, verbosity)
- Domain focus (specialization)
- Bootstrap content (onboarding)
- Proposed questions

Agents CANNOT:
- Self-authorize capabilities
- Override governance
- Bypass gates
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from locked_system.proposals.buffer import GateProposal, Severity


@dataclass
class AgentContext:
    """What an agent can provide (sandboxed, not authority)."""
    name: str
    style_profile: dict = field(default_factory=dict)
    domain_focus: list[str] = field(default_factory=list)
    bootstrap_content: str = ""
    proposed_questions: list[str] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Result of agent processing."""
    context: AgentContext
    proposals: list[GateProposal] = field(default_factory=list)
    capability_requests: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Base class for experience-layer agents.

    Agents customize the user experience without having authority.
    They can propose gate transitions but cannot decide.
    They can request capabilities but cannot self-authorize.
    """

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self._active = False

    @abstractmethod
    def get_context(self) -> AgentContext:
        """
        Get agent context for prompt compilation.

        This is sandboxed and cannot override core behavior.
        """
        pass

    def activate(self):
        """Activate this agent."""
        self._active = True

    def deactivate(self):
        """Deactivate this agent."""
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def propose_gate(
        self,
        reason: str,
        gate: str,
        severity: Severity = Severity.LOW
    ) -> GateProposal:
        """
        Propose a gate transition.

        Agents can propose but only gates can decide.
        """
        return GateProposal(
            reason=reason,
            severity=severity,
            suggested_gate=gate,
            source=f"agent:{self.agent_id}"
        )

    def request_capability(self, capability_id: str) -> dict:
        """
        Request a capability delegation.

        Returns a request dict that should be submitted to governance.
        """
        return {
            "type": "capability_request",
            "grantee": self.agent_id,
            "capability": capability_id,
            "source": f"agent:{self.agent_id}"
        }

    def on_response(self, response: str, context: dict):
        """
        Hook called after response generation.

        Override to react to responses (logging, learning, etc.)
        """
        pass

    def on_gate_transition(self, gate: str, result: dict):
        """
        Hook called after gate transition.

        Override to react to governance decisions.
        """
        pass


class DefaultAgent(BaseAgent):
    """
    Default agent with minimal styling.

    Used when no specific agent is configured.
    """

    def __init__(self):
        super().__init__("default", "Default Agent")

    def get_context(self) -> AgentContext:
        return AgentContext(
            name=self.name,
            style_profile={
                "tone": "helpful",
                "verbosity": "concise",
            },
            domain_focus=[],
            bootstrap_content="",
            proposed_questions=[],
        )


def load_agent(agent_id: str) -> BaseAgent:
    """
    Load an agent by ID.

    Returns DefaultAgent if agent_id not found.
    """
    # Registry of available agents
    agents = {
        "default": DefaultAgent,
    }

    agent_class = agents.get(agent_id, DefaultAgent)
    return agent_class()
