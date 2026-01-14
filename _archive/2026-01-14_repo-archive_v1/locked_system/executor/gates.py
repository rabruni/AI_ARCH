"""Executor Gates - Checkpoint handlers for the execution pipeline.

Gates are structured checkpoints that:
- Request user input
- Update lane state
- Produce obligations for the executor

Gate types:
- WorkDeclarationGate: Creates/activates lanes
- LaneSwitchGate: Pause current, switch/create/defer
- EvaluationGate: Handle lease expiry
- WriteApprovalGate: Require user approval for writes
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timezone
from uuid import uuid4


class GateStatus(Enum):
    """Gate status."""
    PENDING = "pending"       # Awaiting user input
    APPROVED = "approved"     # User approved
    DENIED = "denied"         # User denied
    SKIPPED = "skipped"       # Gate not required


@dataclass
class GatePrompt:
    """
    Prompt shown to user for a gate.

    When a gate requires user input, this is returned instead of
    executing the tool/action.
    """
    gate_type: str
    message: str
    options: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    gate_id: str = field(default_factory=lambda: f"gate_{uuid4().hex[:8]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            'gate_type': self.gate_type,
            'message': self.message,
            'options': self.options,
            'context': self.context,
            'gate_id': self.gate_id,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class GateResult:
    """Result from gate execution."""
    status: GateStatus
    gate_id: str
    gate_type: str
    obligations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'status': self.status.value,
            'gate_id': self.gate_id,
            'gate_type': self.gate_type,
            'obligations': self.obligations,
            'metadata': self.metadata,
        }


@dataclass
class WriteApprovalGate:
    """
    Gate requiring user approval for write operations.

    All writes require explicit approval - this is non-negotiable in V1.
    """
    tool_id: str
    tool_args: Dict[str, Any]
    description: str = ""
    gate_id: str = field(default_factory=lambda: f"write_{uuid4().hex[:8]}")

    def generate_prompt(self) -> GatePrompt:
        """Generate approval prompt for user."""
        # Sanitize args for display (hide long content)
        display_args = {}
        for k, v in self.tool_args.items():
            if isinstance(v, str) and len(v) > 100:
                display_args[k] = v[:100] + "..."
            else:
                display_args[k] = v

        return GatePrompt(
            gate_type="write_approval",
            message=f"Allow write operation?\n\nTool: {self.tool_id}\nArgs: {display_args}",
            options=[
                {"type": "approve", "label": "Approve"},
                {"type": "deny", "label": "Deny"},
                {"type": "inspect", "label": "Show full content"},
            ],
            context={
                "tool_id": self.tool_id,
                "args": self.tool_args,
                "description": self.description,
            },
            gate_id=self.gate_id,
        )

    def execute(self, user_response: Dict[str, Any]) -> GateResult:
        """Execute gate based on user response."""
        action = user_response.get("type", "deny")

        if action == "approve":
            return GateResult(
                status=GateStatus.APPROVED,
                gate_id=self.gate_id,
                gate_type="write_approval",
                obligations=[],
            )
        else:
            return GateResult(
                status=GateStatus.DENIED,
                gate_id=self.gate_id,
                gate_type="write_approval",
                metadata={"reason": "User denied write operation"},
            )


class GateController:
    """
    Manages gate lifecycle and enforcement.

    Responsibilities:
    - Track pending gates
    - Generate gate prompts
    - Process gate responses
    - Block execution until gates cleared
    """

    def __init__(self):
        self._pending_gates: Dict[str, GatePrompt] = {}
        self._completed_gates: Dict[str, GateResult] = {}
        self._approved_writes: set = set()  # tool_ids approved this session

    def has_pending_gates(self) -> bool:
        """Check if there are pending gates."""
        return len(self._pending_gates) > 0

    def get_pending_prompts(self) -> List[GatePrompt]:
        """Get all pending gate prompts."""
        return list(self._pending_gates.values())

    def add_pending_gate(self, prompt: GatePrompt) -> None:
        """Add a gate to pending."""
        self._pending_gates[prompt.gate_id] = prompt

    def resolve_gate(self, gate_id: str, user_response: Dict[str, Any]) -> Optional[GateResult]:
        """
        Resolve a pending gate with user response.

        Returns None if gate not found.
        """
        prompt = self._pending_gates.get(gate_id)
        if not prompt:
            return None

        # Execute gate based on type
        if prompt.gate_type == "write_approval":
            gate = WriteApprovalGate(
                tool_id=prompt.context.get("tool_id", ""),
                tool_args=prompt.context.get("args", {}),
                gate_id=gate_id,
            )
            result = gate.execute(user_response)

            if result.status == GateStatus.APPROVED:
                self._approved_writes.add(prompt.context.get("tool_id"))

        else:
            # Generic gate resolution
            action = user_response.get("type", "deny")
            result = GateResult(
                status=GateStatus.APPROVED if action == "approve" else GateStatus.DENIED,
                gate_id=gate_id,
                gate_type=prompt.gate_type,
            )

        # Move from pending to completed
        del self._pending_gates[gate_id]
        self._completed_gates[gate_id] = result

        return result

    def is_write_approved(self, tool_id: str) -> bool:
        """Check if a write tool has been approved."""
        return tool_id in self._approved_writes

    def require_write_approval(self, tool_id: str, args: dict, description: str = "") -> GatePrompt:
        """
        Create a write approval gate.

        Returns the gate prompt to show user.
        """
        gate = WriteApprovalGate(
            tool_id=tool_id,
            tool_args=args,
            description=description,
        )
        prompt = gate.generate_prompt()
        self.add_pending_gate(prompt)
        return prompt

    def clear_session(self) -> None:
        """Clear all gates (for new session)."""
        self._pending_gates.clear()
        self._completed_gates.clear()
        self._approved_writes.clear()

    def get_gate_history(self) -> List[GateResult]:
        """Get completed gates."""
        return list(self._completed_gates.values())
