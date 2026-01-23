"""Core Types - Shared types across DoPeJar system.

Simplified spec: No Protocols, plain classes, single HRMError.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class Stance(Enum):
    """The four stances (2x2: exploration/exploitation x accuracy/momentum)."""
    SENSEMAKING = "sensemaking"   # Exploration + Accuracy
    DISCOVERY = "discovery"       # Exploration + Momentum
    EXECUTION = "execution"       # Exploitation + Momentum
    EVALUATION = "evaluation"     # Exploitation + Accuracy


class GateType(Enum):
    """Gate types for stance transitions."""
    FRAMING = "framing"
    COMMITMENT = "commitment"
    EVALUATION = "evaluation"
    EMERGENCY = "emergency"
    WRITE_APPROVAL = "write_approval"
    AGENT_APPROVAL = "agent_approval"


class ReducerType(Enum):
    """Reducer strategies for MapReduce orchestration."""
    PASS_THROUGH = "pass_through"   # Pipeline: pass output to next
    MERGE = "merge"                 # Parallel: combine all outputs
    VOTE = "vote"                   # Voting: tally and select winner
    SYNTHESIZE = "synthesize"       # Hierarchical: lead synthesizes


class AltitudeLevel(Enum):
    """Altitude levels (L4 = highest abstraction)."""
    L4_IDENTITY = "identity"        # Why we exist, values
    L3_STRATEGY = "strategy"        # Priorities, projects, goals
    L2_OPERATIONS = "operations"    # This week, today, tasks
    L1_MOMENT = "moment"            # Right now, this conversation


class Complexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class Stakes(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConflictLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BlastRadius(Enum):
    """Scope of impact for writes."""
    LOCAL = "local"           # This problem only
    CROSS_PROBLEM = "cross"   # Affects multiple problems
    GLOBAL = "global"         # System-wide impact


# ─────────────────────────────────────────────────────────────
# Error Handling - Single Error Type
# ─────────────────────────────────────────────────────────────

class ErrorCode(Enum):
    """All error codes in one place."""
    # Gate errors
    GATE_DENIED = "gate_denied"
    STANCE_VIOLATION = "stance_violation"

    # Write errors
    WRITE_DENIED = "write_denied"
    CONFLICT_DETECTED = "conflict_detected"

    # Reasoning errors
    ESCALATION_REQUIRED = "escalation_required"
    STRATEGY_FAILED = "strategy_failed"

    # Agent errors
    AGENT_VIOLATION = "agent_violation"
    AGENT_TIMEOUT = "agent_timeout"

    # LLM errors
    RATE_LIMIT = "rate_limit"
    TOKEN_LIMIT = "token_limit"
    CONTENT_FILTERED = "content_filtered"
    PROVIDER_ERROR = "provider_error"

    # System errors
    VALIDATION_FAILED = "validation_failed"
    INTERNAL_ERROR = "internal_error"


@dataclass
class HRMError(Exception):
    """
    Single exception type for all HRM errors.

    Usage:
        raise HRMError.gate_denied("commitment", "No active commitment")
        raise HRMError.rate_limit(retry_after_ms=5000)

    Handling:
        try:
            result = do_thing()
        except HRMError as e:
            if e.code == ErrorCode.RATE_LIMIT:
                time.sleep(e.retry_after_ms / 1000)
                retry()
            elif e.recoverable:
                fallback()
            else:
                raise
    """
    code: ErrorCode
    message: str
    recoverable: bool = True
    retry_after_ms: Optional[int] = None
    context: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"

    def __post_init__(self):
        super().__init__(str(self))

    # Factory methods
    @classmethod
    def gate_denied(cls, gate: str, reason: str) -> 'HRMError':
        return cls(
            code=ErrorCode.GATE_DENIED,
            message=reason,
            recoverable=True,
            context={"gate": gate}
        )

    @classmethod
    def stance_violation(cls, stance: str, action: str) -> 'HRMError':
        return cls(
            code=ErrorCode.STANCE_VIOLATION,
            message=f"Action '{action}' not allowed in stance '{stance}'",
            recoverable=True,
            context={"stance": stance, "action": action}
        )

    @classmethod
    def write_denied(cls, target: str, reason: str) -> 'HRMError':
        return cls(
            code=ErrorCode.WRITE_DENIED,
            message=reason,
            recoverable=True,
            context={"target": target}
        )

    @classmethod
    def agent_violation(cls, reason: str) -> 'HRMError':
        return cls(
            code=ErrorCode.AGENT_VIOLATION,
            message=reason,
            recoverable=False
        )

    @classmethod
    def rate_limit(cls, retry_after_ms: int) -> 'HRMError':
        return cls(
            code=ErrorCode.RATE_LIMIT,
            message="Rate limit exceeded",
            recoverable=True,
            retry_after_ms=retry_after_ms
        )

    @classmethod
    def provider_error(cls, status_code: int, message: str) -> 'HRMError':
        return cls(
            code=ErrorCode.PROVIDER_ERROR,
            message=message,
            recoverable=status_code >= 500,
            context={"status_code": status_code}
        )


def recover_from_error(error: HRMError) -> dict:
    """Suggest recovery action for an error."""
    if not error.recoverable:
        return {"action": "abort", "delay_ms": 0}

    if error.code == ErrorCode.RATE_LIMIT:
        return {"action": "retry", "delay_ms": error.retry_after_ms or 1000}

    if error.code in (ErrorCode.GATE_DENIED, ErrorCode.STANCE_VIOLATION):
        return {"action": "fallback", "delay_ms": 0}

    if error.code == ErrorCode.ESCALATION_REQUIRED:
        return {"action": "escalate", "delay_ms": 0}

    return {"action": "retry", "delay_ms": 1000}


# ─────────────────────────────────────────────────────────────
# Core Data Types
# ─────────────────────────────────────────────────────────────

@dataclass
class TurnInput:
    """Input for a single turn of interaction."""
    user_input: str
    session_id: str
    turn_number: int
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class Event:
    """
    Universal event for Episodic Trace.

    All cross-HRM notifications become Event appends.
    Consumers query the trace instead of registering callbacks.
    """
    id: str
    event_type: str  # altitude_transition | stance_change | agent_activated | etc.
    timestamp: datetime
    payload: dict
    refs: list[str] = field(default_factory=list)  # Links to other events
    problem_id: Optional[str] = None

    @classmethod
    def create(cls, event_type: str, payload: dict, problem_id: str = None) -> 'Event':
        import uuid
        return cls(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=datetime.now(),
            payload=payload,
            problem_id=problem_id
        )


@dataclass
class Commitment:
    """Lease-based focus with TTL."""
    id: str
    problem_id: str
    description: str
    turns_remaining: int
    turns_total: int
    created_at: datetime
    status: str = "active"  # active | completed | abandoned

    def is_active(self) -> bool:
        return self.status == "active" and self.turns_remaining > 0

    def tick(self) -> bool:
        """Decrement turn counter. Returns True if still active."""
        if self.turns_remaining > 0:
            self.turns_remaining -= 1
        return self.is_active()


@dataclass
class WriteSignals:
    """Signals for WriteGate evaluation."""
    progress_delta: float         # How much progress this represents (0-1)
    conflict_level: ConflictLevel
    source_quality: float         # 0.0 - 1.0
    alignment_score: float        # 0.0 - 1.0
    blast_radius: BlastRadius


@dataclass
class AgentOutput:
    """Output from an agent execution."""
    agent_id: str
    output_type: str              # proposal | data | artifact
    content: Any
    requested_capabilities: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def contains_decision(self) -> bool:
        """Check if output contains a decision instead of proposal."""
        decision_markers = ["DECISION:", "I have decided", "Final answer:"]
        content_str = str(self.content)
        return any(m in content_str for m in decision_markers)

    def is_valid_packet(self) -> bool:
        """Check if output has valid structure."""
        return bool(self.agent_id) and self.output_type in ("proposal", "data", "artifact")


@dataclass
class InputClassification:
    """Classification of input for strategy selection."""
    complexity: Complexity
    uncertainty: float            # 0.0 - 1.0
    conflict: ConflictLevel
    stakes: Stakes
    horizon: str                  # immediate | near | far
    domain: list[str] = field(default_factory=list)
    confidence: float = 0.5

    def should_escalate(self) -> bool:
        """Returns True if any dimension indicates escalation needed."""
        return (
            self.complexity == Complexity.COMPLEX or
            self.uncertainty > 0.7 or
            self.conflict != ConflictLevel.NONE or
            self.stakes == Stakes.HIGH
        )


@dataclass
class AltitudeClassification:
    """Classification result from Altitude HRM."""
    level: AltitudeLevel
    confidence: float
    signals: list[str]
    suggested_stance: Optional[Stance] = None
    allows_agents: bool = True
