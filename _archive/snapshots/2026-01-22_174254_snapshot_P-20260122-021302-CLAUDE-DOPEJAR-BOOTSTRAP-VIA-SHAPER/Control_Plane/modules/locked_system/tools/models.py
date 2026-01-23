"""Tool Data Models - Canonical structures for tool system.

Based on spec_tools.md V1 specification.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import uuid4


class SideEffect(Enum):
    """Types of side effects a tool can have."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    NETWORK = "network"
    EXTERNAL = "external"


class Decision(Enum):
    """Policy decision outcomes."""
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass
class ToolSpec:
    """
    Declarative tool specification (contract).

    Defines what a tool does, its requirements, and schemas.
    """
    id: str
    version: str
    side_effect: SideEffect
    required_scopes: List[str]
    connector: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    timeout_ms: int = 30000
    requires_approval: bool = False  # Auto-set True for writes

    def __post_init__(self):
        # All writes require approval
        if self.side_effect == SideEffect.WRITE:
            self.requires_approval = True

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'version': self.version,
            'side_effect': self.side_effect.value,
            'required_scopes': self.required_scopes,
            'connector': self.connector,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'description': self.description,
            'timeout_ms': self.timeout_ms,
            'requires_approval': self.requires_approval,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ToolSpec':
        return cls(
            id=data['id'],
            version=data.get('version', '1.0'),
            side_effect=SideEffect(data.get('side_effect', 'none')),
            required_scopes=data.get('required_scopes', []),
            connector=data['connector'],
            input_schema=data.get('input_schema', {}),
            output_schema=data.get('output_schema', {}),
            description=data.get('description', ''),
            timeout_ms=data.get('timeout_ms', 30000),
        )


@dataclass
class ToolInvocationRequest:
    """
    Request to invoke a tool.

    Created by agents, evaluated by DecisionPipeline, executed by ToolRuntime.
    """
    tool_id: str
    args: Dict[str, Any]
    requested_by: Dict[str, Any]  # {agent_id, turn}
    lane_id: Optional[str] = None
    turn_id: Optional[str] = None
    proposal_id: str = field(default_factory=lambda: f"prop_{uuid4().hex[:8]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            'tool_id': self.tool_id,
            'args': self.args,
            'requested_by': self.requested_by,
            'lane_id': self.lane_id,
            'turn_id': self.turn_id,
            'proposal_id': self.proposal_id,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class ToolResult:
    """
    Result from tool execution.

    Contains success/failure, value, and audit correlation.
    """
    ok: bool
    value: Optional[Any] = None
    error: Optional[str] = None
    audit_id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:8]}")
    execution_ms: int = 0

    def to_dict(self) -> dict:
        return {
            'ok': self.ok,
            'value': self.value,
            'error': self.error,
            'audit_id': self.audit_id,
            'execution_ms': self.execution_ms,
        }

    @classmethod
    def success(cls, value: Any, audit_id: str = None, execution_ms: int = 0) -> 'ToolResult':
        return cls(
            ok=True,
            value=value,
            audit_id=audit_id or f"evt_{uuid4().hex[:8]}",
            execution_ms=execution_ms,
        )

    @classmethod
    def failure(cls, error: str, audit_id: str = None) -> 'ToolResult':
        return cls(
            ok=False,
            error=error,
            audit_id=audit_id or f"evt_{uuid4().hex[:8]}",
        )


@dataclass
class AuditEvent:
    """
    Audit trail for tool invocations.

    Records decision, execution, and context.
    """
    id: str
    decision: Decision
    reason: str
    tool_id: str
    request_id: str
    lane_id: Optional[str] = None
    agent_id: Optional[str] = None
    turn_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    execution_result: Optional[Dict[str, Any]] = None
    emotional_signals: Optional[Dict[str, str]] = None  # Metadata only, never auth

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'decision': self.decision.value,
            'reason': self.reason,
            'tool_id': self.tool_id,
            'request_id': self.request_id,
            'lane_id': self.lane_id,
            'agent_id': self.agent_id,
            'turn_id': self.turn_id,
            'timestamp': self.timestamp.isoformat(),
            'execution_result': self.execution_result,
            'emotional_signals': self.emotional_signals,
        }

    @classmethod
    def allow(
        cls,
        tool_id: str,
        request_id: str,
        reason: str = "ok",
        **kwargs
    ) -> 'AuditEvent':
        return cls(
            id=f"evt_{uuid4().hex[:8]}",
            decision=Decision.ALLOW,
            reason=reason,
            tool_id=tool_id,
            request_id=request_id,
            **kwargs,
        )

    @classmethod
    def deny(
        cls,
        tool_id: str,
        request_id: str,
        reason: str,
        **kwargs
    ) -> 'AuditEvent':
        return cls(
            id=f"evt_{uuid4().hex[:8]}",
            decision=Decision.DENY,
            reason=reason,
            tool_id=tool_id,
            request_id=request_id,
            **kwargs,
        )


@dataclass
class Obligation:
    """
    Obligation from policy evaluation.

    Actions that must be taken as part of allowing a request.
    """
    type: str  # "approval_required", "step_up", "audit", etc.
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {'type': self.type, 'payload': self.payload}


@dataclass
class PolicyDecision:
    """
    Decision from the DecisionPipeline.

    Contains allow/deny plus any obligations.
    """
    allowed: bool
    reason: str
    obligations: List[Obligation] = field(default_factory=list)
    needs_approval: bool = False

    def to_dict(self) -> dict:
        return {
            'allowed': self.allowed,
            'reason': self.reason,
            'obligations': [o.to_dict() for o in self.obligations],
            'needs_approval': self.needs_approval,
        }
