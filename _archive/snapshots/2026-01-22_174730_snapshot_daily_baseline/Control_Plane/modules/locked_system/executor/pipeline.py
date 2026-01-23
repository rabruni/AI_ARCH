"""Executor Pipeline - Main execution orchestration.

Implements the full execution pipeline:
1. Agent invocation → AgentPacket
2. Packet validation (firewall)
3. Proposal collection
4. Policy evaluation (DecisionPipeline)
5. Gate handling
6. Tool execution
7. Response synthesis
8. Audit emission
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable
from uuid import uuid4

from locked_system.agents import (
    AgentRuntime,
    AgentPacket,
    AgentContext,
    AgentLoader,
    PacketFirewall,
    Orchestrator,
    OrchestrationMode,
)
from locked_system.tools import (
    ToolRuntime,
    ToolRegistry,
    ToolInvocationRequest,
    ToolResult,
    AuditEvent,
    DecisionPipeline,
    PolicyContext,
    SideEffect,
    ExecutionContext,
)
from locked_system.lanes import (
    LaneStore,
    Lane,
)
from locked_system.executor.gates import (
    GateController,
    GatePrompt,
    GateResult,
    GateStatus,
)


@dataclass
class ExecutorConfig:
    """Configuration for the executor."""
    enable_firewall: bool = True
    enable_gates: bool = True
    default_scopes: List[str] = field(default_factory=lambda: ["fs.read"])
    audit_all: bool = True


@dataclass
class TurnState:
    """State for a single turn."""
    turn_id: str
    lane_id: Optional[str]
    agent_id: str
    user_input: str
    proposals_collected: int = 0
    tools_executed: int = 0
    gates_triggered: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            'turn_id': self.turn_id,
            'lane_id': self.lane_id,
            'agent_id': self.agent_id,
            'proposals_collected': self.proposals_collected,
            'tools_executed': self.tools_executed,
            'gates_triggered': self.gates_triggered,
            'started_at': self.started_at.isoformat(),
        }


@dataclass
class SystemResponse:
    """
    Final response from the executor.

    Contains:
    - message: The agent's message to user
    - tool_results: Results from executed tools
    - pending_gates: Gates awaiting user input
    - audit_ids: IDs of audit events for this turn
    """
    message: str
    tool_results: List[ToolResult] = field(default_factory=list)
    pending_gates: List[GatePrompt] = field(default_factory=list)
    audit_ids: List[str] = field(default_factory=list)
    turn_state: Optional[TurnState] = None
    lane_context: Optional[Dict[str, Any]] = None

    def has_pending_gates(self) -> bool:
        """Check if response has pending gates."""
        return len(self.pending_gates) > 0

    def to_dict(self) -> dict:
        return {
            'message': self.message,
            'tool_results': [r.to_dict() for r in self.tool_results],
            'pending_gates': [g.to_dict() for g in self.pending_gates],
            'audit_ids': self.audit_ids,
            'turn_state': self.turn_state.to_dict() if self.turn_state else None,
            'lane_context': self.lane_context,
        }


class Executor:
    """
    Main execution pipeline.

    Coordinates:
    - Agent invocation
    - Packet validation
    - Policy evaluation
    - Gate handling
    - Tool execution
    - Response synthesis
    """

    def __init__(
        self,
        agent_runtime: AgentRuntime = None,
        tool_runtime: ToolRuntime = None,
        lane_store: LaneStore = None,
        gate_controller: GateController = None,
        config: ExecutorConfig = None,
    ):
        self._agent_runtime = agent_runtime or self._create_default_agent_runtime()
        self._tool_runtime = tool_runtime or self._create_default_tool_runtime()
        self._lane_store = lane_store or LaneStore()
        self._gate_controller = gate_controller or GateController()
        self._config = config or ExecutorConfig()

        self._turn_counter = 0
        self._audit_callback: Optional[Callable[[AuditEvent], None]] = None

    def _create_default_agent_runtime(self) -> AgentRuntime:
        """Create default agent runtime."""
        loader = AgentLoader()
        loader.initialize_defaults()
        firewall = PacketFirewall()
        return AgentRuntime(loader=loader, firewall=firewall)

    def _create_default_tool_runtime(self) -> ToolRuntime:
        """Create default tool runtime."""
        from locked_system.tools import create_default_runtime
        return create_default_runtime()

    def step(
        self,
        user_input: str,
        agent_id: str = "front_door",
        emotional_signals: Dict[str, str] = None,
    ) -> SystemResponse:
        """
        Execute a single turn.

        Args:
            user_input: User's message
            agent_id: Agent to invoke (default: front_door)
            emotional_signals: Optional emotional telemetry

        Returns:
            SystemResponse with message, tool results, pending gates
        """
        self._turn_counter += 1
        turn_id = f"turn_{uuid4().hex[:8]}"

        # Get lane context
        lane_context = self._lane_store.get_lane_context()
        lane_id = lane_context.get('lane_id')

        # Create turn state
        turn_state = TurnState(
            turn_id=turn_id,
            lane_id=lane_id,
            agent_id=agent_id,
            user_input=user_input,
        )

        # Step 1: Create agent context
        agent_context = AgentContext(
            user_input=user_input,
            lane_id=lane_id,
            turn=self._turn_counter,
            emotional_signals=emotional_signals,
            system_context={
                'lane_context': lane_context,
            },
        )

        # Step 2: Invoke agent
        packet, firewall_result = self._agent_runtime.invoke(agent_id, agent_context)

        # Step 3: Check firewall result
        if firewall_result and not firewall_result.passed:
            # Firewall blocked - return error
            return SystemResponse(
                message=f"Request blocked: {[v.message for v in firewall_result.violations]}",
                turn_state=turn_state,
            )

        # Step 4: Collect proposals
        turn_state.proposals_collected = len(packet.proposals)

        # Step 5: Process proposals
        tool_results = []
        pending_gates = []
        audit_ids = []

        for proposal in packet.proposals:
            if proposal.type.value == "tool_request":
                result, gate_prompt = self._process_tool_request(
                    proposal, turn_state, lane_context, emotional_signals
                )

                if gate_prompt:
                    # Gate required - don't execute yet
                    pending_gates.append(gate_prompt)
                    turn_state.gates_triggered += 1
                elif result:
                    tool_results.append(result)
                    audit_ids.append(result.audit_id)
                    turn_state.tools_executed += 1

            elif proposal.type.value == "gate_request":
                # Handle gate request from agent
                gate_prompt = self._process_gate_request(proposal, turn_state)
                if gate_prompt:
                    pending_gates.append(gate_prompt)
                    turn_state.gates_triggered += 1

        # Step 6: Synthesize response
        return SystemResponse(
            message=packet.message,
            tool_results=tool_results,
            pending_gates=pending_gates,
            audit_ids=audit_ids,
            turn_state=turn_state,
            lane_context=lane_context,
        )

    def _process_tool_request(
        self,
        proposal,
        turn_state: TurnState,
        lane_context: dict,
        emotional_signals: dict = None,
    ) -> tuple[Optional[ToolResult], Optional[GatePrompt]]:
        """
        Process a tool request proposal.

        Returns (result, gate_prompt).
        - If gate required: (None, GatePrompt)
        - If executed: (ToolResult, None)
        - If denied: (ToolResult with error, None)
        """
        tool_id = proposal.tool_id
        args = proposal.tool_args

        # Check if tool requires write approval
        spec = self._tool_runtime._registry.get(tool_id)
        if spec and spec.side_effect == SideEffect.WRITE:
            if not self._gate_controller.is_write_approved(tool_id):
                # Need approval
                gate_prompt = self._gate_controller.require_write_approval(
                    tool_id, args, spec.description
                )
                return None, gate_prompt

        # Build execution context
        policy_context = PolicyContext(
            agent_id=turn_state.agent_id,
            granted_scopes=set(self._config.default_scopes),
            lane_id=turn_state.lane_id,
            lane_budgets=lane_context.get('budgets'),
        )

        # Add write approval if granted
        if self._gate_controller.is_write_approved(tool_id):
            policy_context.pending_approvals.add(tool_id)

        exec_context = ExecutionContext(
            policy_context=policy_context,
            emotional_signals=emotional_signals,
            lane_id=turn_state.lane_id,
            turn_id=turn_state.turn_id,
        )

        # Create invocation request
        request = ToolInvocationRequest(
            tool_id=tool_id,
            args=args,
            requested_by={'agent_id': turn_state.agent_id, 'turn': self._turn_counter},
            lane_id=turn_state.lane_id,
            turn_id=turn_state.turn_id,
            proposal_id=proposal.proposal_id,
        )

        # Execute
        result = self._tool_runtime.invoke(request, exec_context)
        return result, None

    def _process_gate_request(
        self,
        proposal,
        turn_state: TurnState,
    ) -> Optional[GatePrompt]:
        """Process a gate request from agent."""
        gate_type = proposal.gate
        payload = proposal.gate_payload

        # Create appropriate gate prompt
        if gate_type == "work_declaration":
            return GatePrompt(
                gate_type="work_declaration",
                message="Declare work mode?",
                options=[
                    {"type": "declare", "label": "Declare formal work"},
                    {"type": "skip", "label": "Continue casually"},
                ],
                context=payload,
            )

        elif gate_type == "lane_switch":
            return GatePrompt(
                gate_type="lane_switch",
                message="Switch lane context?",
                options=[
                    {"type": "switch", "label": "Switch lane"},
                    {"type": "defer", "label": "Defer for later"},
                    {"type": "cancel", "label": "Stay in current lane"},
                ],
                context=payload,
            )

        elif gate_type == "evaluation":
            return GatePrompt(
                gate_type="evaluation",
                message="Evaluation checkpoint reached",
                options=[
                    {"type": "continue", "label": "Continue"},
                    {"type": "pause", "label": "Pause work"},
                ],
                context=payload,
            )

        # Unknown gate type
        return None

    def resolve_gate(self, gate_id: str, user_response: dict) -> Optional[GateResult]:
        """
        Resolve a pending gate with user response.

        Call this after presenting gate prompt and getting user input.
        """
        return self._gate_controller.resolve_gate(gate_id, user_response)

    def continue_after_gate(
        self,
        gate_id: str,
        user_response: dict,
        original_input: str,
        agent_id: str = "front_door",
    ) -> SystemResponse:
        """
        Continue execution after gate is resolved.

        If gate was approved, re-executes the turn with approval in place.
        """
        result = self.resolve_gate(gate_id, user_response)

        if result and result.status == GateStatus.APPROVED:
            # Re-execute turn with approval
            return self.step(original_input, agent_id)

        # Gate denied - return without execution
        return SystemResponse(
            message="Operation cancelled by user.",
            pending_gates=[],
        )

    # --- Lane Management ---

    def get_active_lane(self) -> Optional[Lane]:
        """Get the currently active lane."""
        return self._lane_store.get_active()

    def create_lane(self, kind, goal: str, **kwargs) -> Lane:
        """Create a new lane."""
        return self._lane_store.create(kind=kind, goal=goal, **kwargs)

    # --- Audit ---

    def set_audit_callback(self, callback: Callable[[AuditEvent], None]) -> None:
        """Set callback for audit events."""
        self._audit_callback = callback
        self._tool_runtime.set_audit_callback(callback)

    def get_audit_log(self) -> List[AuditEvent]:
        """Get tool audit log."""
        return self._tool_runtime.get_audit_log()

    # --- State ---

    def get_turn_count(self) -> int:
        """Get current turn count."""
        return self._turn_counter

    def has_pending_gates(self) -> bool:
        """Check if there are pending gates."""
        return self._gate_controller.has_pending_gates()

    def get_pending_gates(self) -> List[GatePrompt]:
        """Get pending gate prompts."""
        return self._gate_controller.get_pending_prompts()
