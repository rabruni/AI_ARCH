"""Agent Runtime - Wrapper for agent invocation.

Produces validated AgentPackets from agent processing.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone

from locked_system.agents.models import (
    AgentDefinition,
    AgentPacket,
    AgentContext,
    Proposal,
    ProposalType,
)
from locked_system.agents.loader import AgentLoader
from locked_system.agents.firewall import PacketFirewall, FirewallResult


@dataclass
class RuntimeConfig:
    """Configuration for agent runtime."""
    default_timeout_ms: int = 30000
    enable_firewall: bool = True
    max_retries: int = 1


class AgentRuntime:
    """
    Runtime wrapper for agent invocation.

    Responsibilities:
    - Load agent definitions
    - Invoke agents with context
    - Validate output through firewall
    - Pass emotional signals unchanged
    """

    def __init__(
        self,
        loader: AgentLoader = None,
        firewall: PacketFirewall = None,
        config: RuntimeConfig = None,
    ):
        self._loader = loader or AgentLoader()
        self._firewall = firewall or PacketFirewall()
        self._config = config or RuntimeConfig()
        self._turn_counter = 0

        # Agent processors (mock LLM for now)
        self._processors: Dict[str, Callable[[AgentContext], AgentPacket]] = {}

    def register_processor(
        self,
        agent_id: str,
        processor: Callable[[AgentContext], AgentPacket],
    ) -> None:
        """
        Register a processor function for an agent.

        In production, this would be an LLM call.
        For testing, can be mock functions.
        """
        self._processors[agent_id] = processor

    def invoke(
        self,
        agent_id: str,
        context: AgentContext,
    ) -> tuple[AgentPacket, FirewallResult]:
        """
        Invoke an agent and return validated packet.

        Returns (packet, firewall_result).
        If firewall fails, packet is the original (unvalidated).
        """
        self._turn_counter += 1

        # Get agent definition
        definition = self._loader.get(agent_id)
        if not definition:
            # Return error packet if agent not found
            return self._error_packet(f"Agent not found: {agent_id}"), None

        # Build context with emotional signals (passed through unchanged)
        enriched_context = AgentContext(
            user_input=context.user_input,
            lane_id=context.lane_id,
            turn=self._turn_counter,
            conversation_history=context.conversation_history,
            emotional_signals=context.emotional_signals,  # Unchanged passthrough
            system_context=context.system_context,
        )

        # Invoke processor
        processor = self._processors.get(agent_id)
        if processor:
            packet = processor(enriched_context)
        else:
            # Default behavior: create simple response packet
            packet = self._default_process(definition, enriched_context)

        # Ensure traces
        packet.traces['agent_id'] = agent_id
        packet.traces['version'] = definition.version
        packet.traces['turn'] = self._turn_counter
        if context.lane_id:
            packet.traces['lane_id'] = context.lane_id

        # Validate through firewall
        if self._config.enable_firewall:
            result = self._firewall.validate(packet, definition)
            if result.passed and result.sanitized_packet:
                return result.sanitized_packet, result
            return packet, result

        return packet, None

    def _default_process(
        self,
        definition: AgentDefinition,
        context: AgentContext,
    ) -> AgentPacket:
        """Default processing when no custom processor registered."""
        # Simple echo response for testing
        return AgentPacket(
            message=f"[{definition.role}] Received: {context.user_input}",
            proposals=[],
            confidence=0.8,
            traces={'agent_id': definition.agent_id},
        )

    def _error_packet(self, message: str) -> AgentPacket:
        """Create an error packet."""
        return AgentPacket(
            message=f"Error: {message}",
            proposals=[],
            confidence=0.0,
            traces={'agent_id': 'error', 'error': True},
        )

    def get_definition(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent definition."""
        return self._loader.get(agent_id)

    def list_agents(self) -> list:
        """List all available agents."""
        return self._loader.list_all()

    # --- Convenience methods for testing ---

    def create_packet(
        self,
        agent_id: str,
        message: str,
        proposals: list = None,
        confidence: float = 0.8,
    ) -> AgentPacket:
        """Helper to create a packet manually (for testing)."""
        return AgentPacket(
            message=message,
            proposals=proposals or [],
            confidence=confidence,
            traces={'agent_id': agent_id, 'turn': self._turn_counter},
        )
