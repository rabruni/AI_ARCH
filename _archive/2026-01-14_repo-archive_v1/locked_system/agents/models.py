"""Agent Data Models - Canonical structures for the agents system.

Based on spec_agents.md V1 specification.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import uuid4


class ProposalType(Enum):
    """Types of proposals an agent can make."""
    TOOL_REQUEST = "tool_request"
    GATE_REQUEST = "gate_request"
    LANE_ACTION = "lane_action"
    MESSAGE = "message"


@dataclass
class PromptProfile:
    """Prompt configuration for an agent."""
    style: str = "balanced"  # balanced, concise, verbose
    tone: str = "direct"     # direct, warm, formal
    max_words: int = 500

    def to_dict(self) -> dict:
        return {
            'style': self.style,
            'tone': self.tone,
            'max_words': self.max_words,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PromptProfile':
        return cls(
            style=data.get('style', 'balanced'),
            tone=data.get('tone', 'direct'),
            max_words=data.get('max_words', 500),
        )


@dataclass
class AgentDefinition:
    """
    YAML-based agent definition.

    Location: agents/defs/*.yaml
    """
    agent_id: str
    version: str
    role: str
    lifecycle: str  # "ephemeral" | "session"
    routing_tags: List[str]
    prompt_profile: PromptProfile
    requested_scopes: List[str]        # Requests only (not grants)
    allowed_tool_requests: List[str]   # Tools this agent may request
    allowed_gate_requests: List[str]   # Gates this agent may request

    def to_dict(self) -> dict:
        return {
            'agent_id': self.agent_id,
            'version': self.version,
            'role': self.role,
            'lifecycle': self.lifecycle,
            'routing_tags': self.routing_tags,
            'prompt_profile': self.prompt_profile.to_dict(),
            'requested_scopes': self.requested_scopes,
            'allowed_tool_requests': self.allowed_tool_requests,
            'allowed_gate_requests': self.allowed_gate_requests,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentDefinition':
        return cls(
            agent_id=data['agent_id'],
            version=data.get('version', '1.0'),
            role=data.get('role', 'Agent'),
            lifecycle=data.get('lifecycle', 'session'),
            routing_tags=data.get('routing_tags', []),
            prompt_profile=PromptProfile.from_dict(data.get('prompt_profile', {})),
            requested_scopes=data.get('requested_scopes', []),
            allowed_tool_requests=data.get('allowed_tool_requests', []),
            allowed_gate_requests=data.get('allowed_gate_requests', []),
        )


@dataclass
class Proposal:
    """
    A single proposal from an agent.

    Agents propose actions; executor decides and executes.
    """
    type: ProposalType
    tool_id: Optional[str] = None       # For tool_request
    tool_args: Dict[str, Any] = field(default_factory=dict)
    gate: Optional[str] = None          # For gate_request
    gate_payload: Dict[str, Any] = field(default_factory=dict)
    lane_action: Optional[str] = None   # For lane_action: pause, resume, switch
    lane_payload: Dict[str, Any] = field(default_factory=dict)
    proposal_id: str = field(default_factory=lambda: f"prop_{uuid4().hex[:8]}")

    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'tool_id': self.tool_id,
            'tool_args': self.tool_args,
            'gate': self.gate,
            'gate_payload': self.gate_payload,
            'lane_action': self.lane_action,
            'lane_payload': self.lane_payload,
            'proposal_id': self.proposal_id,
        }

    @classmethod
    def tool_request(cls, tool_id: str, args: dict = None) -> 'Proposal':
        """Create a tool request proposal."""
        return cls(
            type=ProposalType.TOOL_REQUEST,
            tool_id=tool_id,
            tool_args=args or {},
        )

    @classmethod
    def gate_request(cls, gate: str, payload: dict = None) -> 'Proposal':
        """Create a gate request proposal."""
        return cls(
            type=ProposalType.GATE_REQUEST,
            gate=gate,
            gate_payload=payload or {},
        )

    @classmethod
    def lane_action(cls, action: str, payload: dict = None) -> 'Proposal':
        """Create a lane action proposal."""
        return cls(
            type=ProposalType.LANE_ACTION,
            lane_action=action,
            lane_payload=payload or {},
        )


@dataclass
class AgentPacket:
    """
    Structured output from an agent.

    This is the ONLY output format agents produce.
    Contains message + proposals + traces for audit.
    """
    message: str
    proposals: List[Proposal] = field(default_factory=list)
    confidence: float = 0.8  # 0.0 - 1.0
    traces: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        # Ensure traces has required fields
        if 'agent_id' not in self.traces:
            self.traces['agent_id'] = 'unknown'
        if 'turn' not in self.traces:
            self.traces['turn'] = 0

    def add_tool_request(self, tool_id: str, args: dict = None):
        """Add a tool request proposal."""
        self.proposals.append(Proposal.tool_request(tool_id, args))

    def add_gate_request(self, gate: str, payload: dict = None):
        """Add a gate request proposal."""
        self.proposals.append(Proposal.gate_request(gate, payload))

    def has_tool_requests(self) -> bool:
        """Check if packet has tool requests."""
        return any(p.type == ProposalType.TOOL_REQUEST for p in self.proposals)

    def has_gate_requests(self) -> bool:
        """Check if packet has gate requests."""
        return any(p.type == ProposalType.GATE_REQUEST for p in self.proposals)

    def get_tool_requests(self) -> List[Proposal]:
        """Get all tool request proposals."""
        return [p for p in self.proposals if p.type == ProposalType.TOOL_REQUEST]

    def get_gate_requests(self) -> List[Proposal]:
        """Get all gate request proposals."""
        return [p for p in self.proposals if p.type == ProposalType.GATE_REQUEST]

    def to_dict(self) -> dict:
        return {
            'message': self.message,
            'proposals': [p.to_dict() for p in self.proposals],
            'confidence': self.confidence,
            'traces': self.traces,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class AgentContext:
    """
    Context provided to an agent for processing.

    Includes user input, lane state, and optional emotional signals.
    """
    user_input: str
    lane_id: Optional[str] = None
    turn: int = 0
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    emotional_signals: Optional[Dict[str, str]] = None
    system_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'user_input': self.user_input,
            'lane_id': self.lane_id,
            'turn': self.turn,
            'conversation_history': self.conversation_history,
            'emotional_signals': self.emotional_signals,
            'system_context': self.system_context,
        }
