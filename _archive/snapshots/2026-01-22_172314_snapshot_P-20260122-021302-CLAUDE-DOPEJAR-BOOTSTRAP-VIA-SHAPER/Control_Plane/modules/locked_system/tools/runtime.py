"""Tool Runtime - Policy Enforcement Point (PEP).

Executes approved tools with full audit trail.

Pipeline:
1. Validate input schema
2. Check with DecisionPipeline (PDP)
3. Consent check (writes require approval)
4. Execute via Connector
5. Validate output schema
6. Emit audit event
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
import time

from locked_system.tools.models import (
    ToolSpec,
    ToolInvocationRequest,
    ToolResult,
    AuditEvent,
    Decision,
    PolicyDecision,
    SideEffect,
)
from locked_system.tools.registry import ToolRegistry
from locked_system.tools.decision import DecisionPipeline, PolicyContext
from locked_system.tools.connectors.base import Connector, ConnectorError


@dataclass
class ExecutionContext:
    """
    Context for tool execution.

    Contains all state needed to execute a tool request.
    """
    # Policy context
    policy_context: PolicyContext

    # Emotional signals (metadata only, never auth)
    emotional_signals: Optional[Dict[str, str]] = None

    # Lane tagging
    lane_id: Optional[str] = None
    turn_id: Optional[str] = None


class ToolRuntime:
    """
    Policy Enforcement Point (PEP) for tool execution.

    Responsibilities:
    - Validate input schemas
    - Enforce policy via DecisionPipeline
    - Require approval for writes
    - Execute via connectors
    - Validate output schemas
    - Emit audit events
    """

    def __init__(
        self,
        registry: ToolRegistry = None,
        decision_pipeline: DecisionPipeline = None,
    ):
        self._registry = registry or ToolRegistry()
        self._decision = decision_pipeline or DecisionPipeline()
        self._connectors: Dict[str, Connector] = {}
        self._audit_log: List[AuditEvent] = []
        self._audit_callback: Optional[Callable[[AuditEvent], None]] = None

    def register_connector(self, connector: Connector) -> None:
        """Register a connector for tool execution."""
        self._connectors[connector.name] = connector

    def set_audit_callback(self, callback: Callable[[AuditEvent], None]) -> None:
        """Set callback for audit events (e.g., for persistence)."""
        self._audit_callback = callback

    def invoke(
        self,
        request: ToolInvocationRequest,
        context: ExecutionContext,
    ) -> ToolResult:
        """
        Invoke a tool with full policy enforcement.

        Steps:
        1. Validate tool exists
        2. Validate input schema
        3. Evaluate policy
        4. Execute if approved
        5. Validate output
        6. Emit audit
        """
        start_time = time.time()

        # Step 1: Get tool spec
        spec = self._registry.get(request.tool_id)
        if not spec:
            return self._deny_and_audit(
                request, context,
                reason=f"Unknown tool: {request.tool_id}",
            )

        # Step 2: Validate input schema
        valid, error = self._registry.validate_request(request.tool_id, request.args)
        if not valid:
            return self._deny_and_audit(
                request, context,
                reason=f"Invalid arguments: {error}",
            )

        # Step 3: Evaluate policy
        decision = self._decision.evaluate(request, spec, context.policy_context)
        if not decision.allowed:
            result = self._deny_and_audit(
                request, context,
                reason=decision.reason,
                needs_approval=decision.needs_approval,
            )
            if decision.needs_approval:
                result.error = "APPROVAL_REQUIRED"
            return result

        # Step 4: Execute via connector
        connector = self._connectors.get(spec.connector)
        if not connector:
            return self._deny_and_audit(
                request, context,
                reason=f"Connector not found: {spec.connector}",
            )

        try:
            # Extract operation from tool_id (e.g., "fs.read_file" -> "read_file")
            operation = request.tool_id.split(".")[-1]

            # Execute
            result_data = connector.execute(operation, request.args)

            # Calculate execution time
            execution_ms = int((time.time() - start_time) * 1000)

            # Step 5: Create success result
            result = ToolResult.success(
                value=result_data,
                execution_ms=execution_ms,
            )

            # Step 6: Emit audit
            self._emit_audit(
                AuditEvent.allow(
                    tool_id=request.tool_id,
                    request_id=request.proposal_id,
                    reason="ok",
                    lane_id=context.lane_id,
                    agent_id=request.requested_by.get('agent_id'),
                    turn_id=context.turn_id,
                    execution_result={'ok': True},
                    emotional_signals=context.emotional_signals,
                )
            )

            return result

        except ConnectorError as e:
            return self._deny_and_audit(
                request, context,
                reason=f"Connector error: {str(e)}",
            )

        except Exception as e:
            return self._deny_and_audit(
                request, context,
                reason=f"Execution error: {str(e)}",
            )

    def invoke_batch(
        self,
        requests: List[ToolInvocationRequest],
        context: ExecutionContext,
    ) -> List[ToolResult]:
        """
        Invoke multiple tools in sequence.

        Results are in same order as requests.
        """
        results = []
        for request in requests:
            result = self.invoke(request, context)
            results.append(result)
        return results

    def _deny_and_audit(
        self,
        request: ToolInvocationRequest,
        context: ExecutionContext,
        reason: str,
        needs_approval: bool = False,
    ) -> ToolResult:
        """Create denial result and emit audit."""
        audit = AuditEvent.deny(
            tool_id=request.tool_id,
            request_id=request.proposal_id,
            reason=reason,
            lane_id=context.lane_id,
            agent_id=request.requested_by.get('agent_id'),
            turn_id=context.turn_id,
            emotional_signals=context.emotional_signals,
        )
        self._emit_audit(audit)

        return ToolResult.failure(error=reason, audit_id=audit.id)

    def _emit_audit(self, event: AuditEvent) -> None:
        """Emit an audit event."""
        self._audit_log.append(event)

        if self._audit_callback:
            self._audit_callback(event)

    def get_audit_log(self) -> List[AuditEvent]:
        """Get all audit events."""
        return self._audit_log.copy()

    def get_recent_audits(self, limit: int = 10) -> List[AuditEvent]:
        """Get recent audit events."""
        return self._audit_log[-limit:]

    def clear_audit_log(self) -> None:
        """Clear audit log (for testing)."""
        self._audit_log.clear()

    # --- Approval Handling ---

    def request_approval(
        self,
        request: ToolInvocationRequest,
        spec: ToolSpec,
    ) -> Dict[str, Any]:
        """
        Generate an approval request for user.

        Returns approval prompt data.
        """
        return {
            'type': 'write_approval',
            'tool_id': request.tool_id,
            'operation': spec.side_effect.value,
            'args': request.args,
            'description': spec.description,
            'message': f"Allow {spec.description}?",
            'proposal_id': request.proposal_id,
        }

    def invoke_with_approval(
        self,
        request: ToolInvocationRequest,
        context: ExecutionContext,
        user_approved: bool,
    ) -> ToolResult:
        """
        Invoke a tool after user approval decision.

        Call this after presenting approval prompt and getting user response.
        """
        if not user_approved:
            return self._deny_and_audit(
                request, context,
                reason="User denied approval",
            )

        # Grant approval for this specific tool
        context.policy_context.pending_approvals.add(request.tool_id)

        # Now invoke normally
        return self.invoke(request, context)


# --- Helper for creating runtime with defaults ---

def create_default_runtime(base_path: str = None) -> ToolRuntime:
    """
    Create a ToolRuntime with default configuration.

    Includes:
    - Default tool registry
    - Local filesystem connector
    - Default decision pipeline
    """
    from locked_system.tools.connectors.local_fs import LocalFSConnector

    registry = ToolRegistry()
    registry.initialize_defaults()

    decision = DecisionPipeline()

    runtime = ToolRuntime(
        registry=registry,
        decision_pipeline=decision,
    )

    # Register local_fs connector
    connector = LocalFSConnector(base_path=base_path)
    runtime.register_connector(connector)

    return runtime
