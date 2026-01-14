"""Orchestrator - Multi-agent orchestration modes.

Supports:
- single: One agent responds (default)
- router: Front-door routes to specialist
- panel: Multiple agents respond, merged deterministically
- chain: Agents hand off in sequence with structured data
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Callable

from locked_system.agents.models import (
    AgentDefinition,
    AgentPacket,
    AgentContext,
    Proposal,
)
from locked_system.agents.runtime import AgentRuntime
from locked_system.agents.firewall import PacketFirewall


class OrchestrationMode(Enum):
    """Orchestration modes."""
    SINGLE = "single"
    ROUTER = "router"
    PANEL = "panel"
    CHAIN = "chain"


@dataclass
class OrchestrationBudget:
    """Budget limits for orchestration."""
    max_agents: int = 3          # Max agents in panel
    max_chain_depth: int = 3     # Max depth in chain
    max_proposals_total: int = 10  # Total proposals across all agents


@dataclass
class OrchestrationResult:
    """Result from orchestration."""
    mode: OrchestrationMode
    final_packet: AgentPacket
    agent_packets: List[AgentPacket] = field(default_factory=list)
    agents_invoked: List[str] = field(default_factory=list)
    budget_used: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'mode': self.mode.value,
            'final_packet': self.final_packet.to_dict(),
            'agents_invoked': self.agents_invoked,
            'budget_used': self.budget_used,
        }


class Orchestrator:
    """
    Multi-agent orchestrator.

    Enforces:
    - Budget limits (max agents, chain depth, proposals)
    - Deterministic panel merge
    - Structured handoffs in chains
    """

    def __init__(
        self,
        runtime: AgentRuntime,
        budget: OrchestrationBudget = None,
        firewall: PacketFirewall = None,
    ):
        self._runtime = runtime
        self._budget = budget or OrchestrationBudget()
        self._firewall = firewall or PacketFirewall()

    def orchestrate(
        self,
        mode: OrchestrationMode,
        context: AgentContext,
        agent_ids: List[str] = None,
        router_agent_id: str = "front_door",
    ) -> OrchestrationResult:
        """
        Orchestrate agents in the specified mode.

        Args:
            mode: Orchestration mode
            context: User context
            agent_ids: Agents to use (for panel/chain)
            router_agent_id: Router agent (for router mode)
        """
        if mode == OrchestrationMode.SINGLE:
            return self._single(context, agent_ids[0] if agent_ids else router_agent_id)

        elif mode == OrchestrationMode.ROUTER:
            return self._router(context, router_agent_id)

        elif mode == OrchestrationMode.PANEL:
            return self._panel(context, agent_ids or [router_agent_id])

        elif mode == OrchestrationMode.CHAIN:
            return self._chain(context, agent_ids or [router_agent_id])

        raise ValueError(f"Unknown mode: {mode}")

    def _single(self, context: AgentContext, agent_id: str) -> OrchestrationResult:
        """Single agent mode."""
        packet, _ = self._runtime.invoke(agent_id, context)

        return OrchestrationResult(
            mode=OrchestrationMode.SINGLE,
            final_packet=packet,
            agent_packets=[packet],
            agents_invoked=[agent_id],
            budget_used={'agents': 1, 'proposals': len(packet.proposals)},
        )

    def _router(self, context: AgentContext, router_id: str) -> OrchestrationResult:
        """
        Router mode: Front-door routes to specialist.

        The router analyzes the request and delegates to the best agent.
        """
        # First, invoke the router
        router_packet, _ = self._runtime.invoke(router_id, context)

        # Check if router suggests delegation
        delegation = self._extract_delegation(router_packet)

        if delegation and delegation != router_id:
            # Invoke the delegated agent
            specialist_packet, _ = self._runtime.invoke(delegation, context)

            return OrchestrationResult(
                mode=OrchestrationMode.ROUTER,
                final_packet=specialist_packet,
                agent_packets=[router_packet, specialist_packet],
                agents_invoked=[router_id, delegation],
                budget_used={'agents': 2, 'proposals': len(specialist_packet.proposals)},
            )

        # No delegation, router handles it
        return OrchestrationResult(
            mode=OrchestrationMode.ROUTER,
            final_packet=router_packet,
            agent_packets=[router_packet],
            agents_invoked=[router_id],
            budget_used={'agents': 1, 'proposals': len(router_packet.proposals)},
        )

    def _panel(self, context: AgentContext, agent_ids: List[str]) -> OrchestrationResult:
        """
        Panel mode: Multiple agents respond, merge deterministically.

        Merges by:
        1. Sort agents alphabetically for determinism
        2. Concatenate messages
        3. Merge proposals (deduplicate by tool_id)
        4. Average confidence
        """
        # Enforce budget
        limited_ids = agent_ids[:self._budget.max_agents]

        # Sort for determinism
        sorted_ids = sorted(limited_ids)

        # Invoke all agents
        packets = []
        for agent_id in sorted_ids:
            packet, _ = self._runtime.invoke(agent_id, context)
            packets.append(packet)

        # Merge packets
        merged = self._merge_packets(packets, sorted_ids)

        return OrchestrationResult(
            mode=OrchestrationMode.PANEL,
            final_packet=merged,
            agent_packets=packets,
            agents_invoked=sorted_ids,
            budget_used={'agents': len(sorted_ids), 'proposals': len(merged.proposals)},
        )

    def _chain(self, context: AgentContext, agent_ids: List[str]) -> OrchestrationResult:
        """
        Chain mode: Agents hand off in sequence.

        Each agent receives:
        - Original context
        - Structured handoff from previous agent

        Handoffs are validated to prevent prompt smuggling.
        """
        # Enforce budget
        limited_ids = agent_ids[:self._budget.max_chain_depth]

        packets = []
        current_context = context
        handoff_data = {}

        for agent_id in limited_ids:
            # Enrich context with handoff
            enriched = AgentContext(
                user_input=current_context.user_input,
                lane_id=current_context.lane_id,
                turn=current_context.turn,
                conversation_history=current_context.conversation_history,
                emotional_signals=current_context.emotional_signals,
                system_context={
                    **current_context.system_context,
                    'handoff': handoff_data,
                },
            )

            packet, _ = self._runtime.invoke(agent_id, enriched)
            packets.append(packet)

            # Validate handoff for next agent
            if len(packets) < len(limited_ids):
                handoff_result = self._firewall.validate_handoff(packet, limited_ids[len(packets)])
                if not handoff_result.passed:
                    # Stop chain on handoff violation
                    break

            # Extract handoff data for next agent
            handoff_data = self._extract_handoff(packet)

        # Final packet is the last one
        final = packets[-1] if packets else self._runtime._error_packet("No agents in chain")

        return OrchestrationResult(
            mode=OrchestrationMode.CHAIN,
            final_packet=final,
            agent_packets=packets,
            agents_invoked=limited_ids[:len(packets)],
            budget_used={'agents': len(packets), 'proposals': len(final.proposals)},
        )

    def _merge_packets(
        self,
        packets: List[AgentPacket],
        agent_ids: List[str],
    ) -> AgentPacket:
        """Merge multiple packets deterministically."""
        if not packets:
            return AgentPacket(message="No responses", proposals=[])

        # Concatenate messages
        messages = []
        for i, packet in enumerate(packets):
            messages.append(f"[{agent_ids[i]}]: {packet.message}")
        merged_message = "\n\n".join(messages)

        # Merge proposals (dedupe by tool_id for tool requests)
        seen_tools = set()
        merged_proposals = []
        for packet in packets:
            for proposal in packet.proposals:
                if proposal.tool_id:
                    if proposal.tool_id not in seen_tools:
                        seen_tools.add(proposal.tool_id)
                        merged_proposals.append(proposal)
                else:
                    merged_proposals.append(proposal)

        # Enforce total proposal limit
        merged_proposals = merged_proposals[:self._budget.max_proposals_total]

        # Average confidence
        avg_confidence = sum(p.confidence for p in packets) / len(packets)

        return AgentPacket(
            message=merged_message,
            proposals=merged_proposals,
            confidence=avg_confidence,
            traces={
                'mode': 'panel',
                'agents': agent_ids,
            },
        )

    def _extract_delegation(self, packet: AgentPacket) -> Optional[str]:
        """Extract delegation target from router packet."""
        # Look for delegation in traces or proposals
        if 'delegate_to' in packet.traces:
            return packet.traces['delegate_to']

        # Check proposals for routing suggestion
        for proposal in packet.proposals:
            if proposal.gate == 'delegate':
                return proposal.gate_payload.get('target_agent')

        return None

    def _extract_handoff(self, packet: AgentPacket) -> Dict[str, Any]:
        """Extract structured handoff data from packet."""
        # Extract only structured data, not the full message
        handoff = {
            'summary': packet.message[:200] if packet.message else '',
            'proposals': [p.to_dict() for p in packet.proposals[:3]],
            'confidence': packet.confidence,
        }

        # Include any explicit handoff data
        if 'handoff' in packet.traces:
            handoff.update(packet.traces['handoff'])

        return handoff
