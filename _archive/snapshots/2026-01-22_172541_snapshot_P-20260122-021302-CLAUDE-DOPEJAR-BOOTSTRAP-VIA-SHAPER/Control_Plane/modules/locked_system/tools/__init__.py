"""Tools Subsystem - Syscall-like tool execution with default-deny.

Provides:
- ToolSpec: Declarative tool contracts
- Connector: Driver interface for tool execution
- ToolRuntime: Policy Enforcement Point (PEP)
- DecisionPipeline: Policy Decision Point (PDP)

Key invariants:
- Default deny: all access must be explicitly allowed
- Agents propose, core executes
- ALL writes require explicit user approval
- Developer workspace only - no personal data
- Full audit trail
"""

from locked_system.tools.models import (
    ToolSpec,
    ToolInvocationRequest,
    ToolResult,
    AuditEvent,
    SideEffect,
    Decision,
    Obligation,
    PolicyDecision,
)
from locked_system.tools.registry import ToolRegistry
from locked_system.tools.connectors.base import Connector, ConnectorError
from locked_system.tools.connectors.local_fs import LocalFSConnector
from locked_system.tools.runtime import ToolRuntime, ExecutionContext, create_default_runtime
from locked_system.tools.decision import DecisionPipeline, PolicyContext

__all__ = [
    'ToolSpec',
    'ToolInvocationRequest',
    'ToolResult',
    'AuditEvent',
    'SideEffect',
    'Decision',
    'Obligation',
    'PolicyDecision',
    'ToolRegistry',
    'Connector',
    'ConnectorError',
    'LocalFSConnector',
    'ToolRuntime',
    'ExecutionContext',
    'create_default_runtime',
    'DecisionPipeline',
    'PolicyContext',
]
