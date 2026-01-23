"""Decision Pipeline - Policy Decision Point (PDP).

Evaluates tool invocation requests against policies and produces allow/deny decisions.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set

from locked_system.tools.models import (
    ToolSpec,
    ToolInvocationRequest,
    SideEffect,
    Obligation,
    PolicyDecision,
)


@dataclass
class PolicyContext:
    """
    Context for policy evaluation.

    Contains all information needed to make a policy decision.
    """
    # Principal (who is requesting)
    agent_id: Optional[str] = None
    principal_context: Optional[Dict[str, Any]] = None  # IAM stub

    # Scope grants
    granted_scopes: Set[str] = field(default_factory=set)

    # Lane context
    lane_id: Optional[str] = None
    lane_budgets: Optional[Dict[str, int]] = None
    tool_requests_this_turn: int = 0

    # Emotional signals (metadata only, never authorization)
    emotional_signals: Optional[Dict[str, str]] = None

    # Approval state
    pending_approvals: Set[str] = field(default_factory=set)  # tool_ids approved by user
    write_approval_granted: bool = False


class DecisionPipeline:
    """
    Policy Decision Point (PDP).

    Evaluates proposals under:
    - Constitution constraints
    - Lane lease + policy
    - Scope grants
    - Consent policy (writes require approval)
    """

    def __init__(self, constitution: Dict[str, Any] = None):
        """
        Initialize the decision pipeline.

        Args:
            constitution: Core policy constraints
        """
        self._constitution = constitution or {}

    def evaluate(
        self,
        request: ToolInvocationRequest,
        spec: ToolSpec,
        context: PolicyContext,
    ) -> PolicyDecision:
        """
        Evaluate a tool invocation request.

        Returns PolicyDecision with allow/deny and obligations.
        """
        # Check 1: Tool must be known
        if not spec:
            return PolicyDecision(
                allowed=False,
                reason=f"Unknown tool: {request.tool_id}",
            )

        # Check 2: Required scopes must be granted
        missing_scopes = set(spec.required_scopes) - context.granted_scopes
        if missing_scopes:
            return PolicyDecision(
                allowed=False,
                reason=f"Missing required scopes: {missing_scopes}",
            )

        # Check 3: Lane budget enforcement
        if context.lane_budgets:
            max_requests = context.lane_budgets.get('max_tool_requests_per_turn', 999)
            if context.tool_requests_this_turn >= max_requests:
                return PolicyDecision(
                    allowed=False,
                    reason=f"Lane budget exceeded: {context.tool_requests_this_turn}/{max_requests} requests",
                )

        # Check 4: Write approval requirement
        if spec.side_effect == SideEffect.WRITE:
            if not context.write_approval_granted and request.tool_id not in context.pending_approvals:
                return PolicyDecision(
                    allowed=False,
                    reason="Write operations require explicit user approval",
                    needs_approval=True,
                    obligations=[
                        Obligation(
                            type="approval_required",
                            payload={
                                "tool_id": request.tool_id,
                                "operation": "write",
                                "args": request.args,
                            }
                        )
                    ],
                )

        # Check 5: Network/external constraints (future)
        if spec.side_effect in (SideEffect.NETWORK, SideEffect.EXTERNAL):
            # For V1, deny network/external by default
            return PolicyDecision(
                allowed=False,
                reason="Network/external operations not allowed in V1",
            )

        # Check 6: Constitution constraints (extensible)
        const_check = self._check_constitution(request, spec, context)
        if not const_check[0]:
            return PolicyDecision(allowed=False, reason=const_check[1])

        # All checks passed
        obligations = []

        # Always require audit
        obligations.append(Obligation(type="audit", payload={}))

        return PolicyDecision(
            allowed=True,
            reason="ok",
            obligations=obligations,
        )

    def _check_constitution(
        self,
        request: ToolInvocationRequest,
        spec: ToolSpec,
        context: PolicyContext,
    ) -> tuple[bool, str]:
        """
        Check request against constitution constraints.

        Returns (allowed, reason).
        """
        # Constitution-level denials
        denied_tools = self._constitution.get('denied_tools', [])
        if request.tool_id in denied_tools:
            return False, f"Tool {request.tool_id} denied by constitution"

        # Path restrictions (if applicable)
        if 'path' in request.args:
            denied_paths = self._constitution.get('denied_paths', [])
            for denied in denied_paths:
                if request.args['path'].startswith(denied):
                    return False, f"Path {request.args['path']} denied by constitution"

        return True, ""

    def evaluate_batch(
        self,
        requests: List[ToolInvocationRequest],
        specs: Dict[str, ToolSpec],
        context: PolicyContext,
    ) -> List[PolicyDecision]:
        """
        Evaluate multiple requests.

        Uses deterministic ordering (stable sort by proposal_id).
        """
        # Sort for determinism
        sorted_requests = sorted(requests, key=lambda r: r.proposal_id)

        decisions = []
        for request in sorted_requests:
            spec = specs.get(request.tool_id)
            decision = self.evaluate(request, spec, context)
            decisions.append(decision)

            # Update context for subsequent evaluations
            if decision.allowed:
                context.tool_requests_this_turn += 1

        return decisions

    def grant_scope(self, context: PolicyContext, scope: str) -> None:
        """Grant a scope to the context."""
        context.granted_scopes.add(scope)

    def grant_write_approval(self, context: PolicyContext, tool_id: str = None) -> None:
        """
        Grant write approval.

        If tool_id is None, grants blanket write approval (use carefully).
        """
        if tool_id:
            context.pending_approvals.add(tool_id)
        else:
            context.write_approval_granted = True
