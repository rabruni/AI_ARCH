"""Tests for the Tools subsystem.

Tests cover:
- ToolSpec schema validation
- DecisionPipeline allow/deny logic
- WriteApprovalGate requirement for write tools
- Audit event emission
- Connector sandboxing
- Emotional telemetry as metadata only
"""

import pytest
import tempfile
import os
from pathlib import Path

from locked_system.tools import (
    ToolSpec,
    ToolInvocationRequest,
    ToolResult,
    AuditEvent,
    SideEffect,
    Decision,
    Obligation,
    PolicyDecision,
    ToolRegistry,
    LocalFSConnector,
    ConnectorError,
    ToolRuntime,
    ExecutionContext,
    DecisionPipeline,
    PolicyContext,
    create_default_runtime,
)


class TestToolSpec:
    """Tests for ToolSpec model."""

    def test_toolspec_creation(self):
        """Test ToolSpec creation."""
        spec = ToolSpec(
            id="fs.read_file",
            version="1.0",
            side_effect=SideEffect.READ,
            required_scopes=["fs.read"],
            connector="local_fs",
        )

        assert spec.id == "fs.read_file"
        assert spec.side_effect == SideEffect.READ
        assert spec.requires_approval is False

    def test_write_spec_auto_requires_approval(self):
        """Test that write tools auto-require approval."""
        spec = ToolSpec(
            id="fs.write_file",
            version="1.0",
            side_effect=SideEffect.WRITE,
            required_scopes=["fs.write"],
            connector="local_fs",
        )

        assert spec.requires_approval is True

    def test_toolspec_serialization(self):
        """Test ToolSpec to_dict/from_dict."""
        spec = ToolSpec(
            id="test.tool",
            version="2.0",
            side_effect=SideEffect.NETWORK,
            required_scopes=["network"],
            connector="http",
            description="Test tool",
        )

        data = spec.to_dict()
        restored = ToolSpec.from_dict(data)

        assert restored.id == spec.id
        assert restored.side_effect == spec.side_effect


class TestToolInvocationRequest:
    """Tests for ToolInvocationRequest."""

    def test_request_creation(self):
        """Test request creation with auto-generated IDs."""
        request = ToolInvocationRequest(
            tool_id="fs.read_file",
            args={"path": "test.txt"},
            requested_by={"agent_id": "front_door", "turn": 1},
        )

        assert request.tool_id == "fs.read_file"
        assert request.proposal_id.startswith("prop_")
        assert request.created_at is not None


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_and_get(self):
        """Test registering and retrieving tools."""
        registry = ToolRegistry()
        spec = ToolSpec(
            id="test.tool",
            version="1.0",
            side_effect=SideEffect.NONE,
            required_scopes=[],
            connector="test",
        )

        registry.register(spec)
        retrieved = registry.get("test.tool")

        assert retrieved is not None
        assert retrieved.id == "test.tool"

    def test_unknown_tool_returns_none(self):
        """Test that unknown tools return None."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_default_tools(self):
        """Test default tools are registered."""
        registry = ToolRegistry()
        registry.initialize_defaults()

        assert registry.exists("fs.read_file")
        assert registry.exists("fs.write_file")
        assert registry.exists("fs.list_directory")

    def test_validate_request(self):
        """Test request validation against schema."""
        registry = ToolRegistry()
        registry.initialize_defaults()

        # Valid request
        valid, error = registry.validate_request("fs.read_file", {"path": "test.txt"})
        assert valid is True

        # Missing required field
        valid, error = registry.validate_request("fs.read_file", {})
        assert valid is False
        assert "path" in error


class TestDecisionPipeline:
    """Tests for DecisionPipeline (PDP)."""

    def test_allow_read_with_scope(self):
        """Test read allowed when scope granted."""
        pipeline = DecisionPipeline()
        context = PolicyContext(granted_scopes={"fs.read"})

        spec = ToolSpec(
            id="fs.read_file",
            version="1.0",
            side_effect=SideEffect.READ,
            required_scopes=["fs.read"],
            connector="local_fs",
        )

        request = ToolInvocationRequest(
            tool_id="fs.read_file",
            args={"path": "test.txt"},
            requested_by={"agent_id": "test"},
        )

        decision = pipeline.evaluate(request, spec, context)
        assert decision.allowed is True

    def test_deny_without_scope(self):
        """Test denied when required scope missing."""
        pipeline = DecisionPipeline()
        context = PolicyContext(granted_scopes=set())  # No scopes

        spec = ToolSpec(
            id="fs.read_file",
            version="1.0",
            side_effect=SideEffect.READ,
            required_scopes=["fs.read"],
            connector="local_fs",
        )

        request = ToolInvocationRequest(
            tool_id="fs.read_file",
            args={"path": "test.txt"},
            requested_by={"agent_id": "test"},
        )

        decision = pipeline.evaluate(request, spec, context)
        assert decision.allowed is False
        assert "scopes" in decision.reason.lower()

    def test_write_requires_approval(self):
        """Test write tools require explicit approval."""
        pipeline = DecisionPipeline()
        context = PolicyContext(granted_scopes={"fs.write"})

        spec = ToolSpec(
            id="fs.write_file",
            version="1.0",
            side_effect=SideEffect.WRITE,
            required_scopes=["fs.write"],
            connector="local_fs",
        )

        request = ToolInvocationRequest(
            tool_id="fs.write_file",
            args={"path": "test.txt", "content": "hello"},
            requested_by={"agent_id": "test"},
        )

        decision = pipeline.evaluate(request, spec, context)
        assert decision.allowed is False
        assert decision.needs_approval is True
        assert any(o.type == "approval_required" for o in decision.obligations)

    def test_write_allowed_after_approval(self):
        """Test write allowed after approval granted."""
        pipeline = DecisionPipeline()
        context = PolicyContext(
            granted_scopes={"fs.write"},
            pending_approvals={"fs.write_file"},  # Approval granted
        )

        spec = ToolSpec(
            id="fs.write_file",
            version="1.0",
            side_effect=SideEffect.WRITE,
            required_scopes=["fs.write"],
            connector="local_fs",
        )

        request = ToolInvocationRequest(
            tool_id="fs.write_file",
            args={"path": "test.txt", "content": "hello"},
            requested_by={"agent_id": "test"},
        )

        decision = pipeline.evaluate(request, spec, context)
        assert decision.allowed is True

    def test_lane_budget_enforcement(self):
        """Test lane budget limits."""
        pipeline = DecisionPipeline()
        context = PolicyContext(
            granted_scopes={"fs.read"},
            lane_budgets={"max_tool_requests_per_turn": 2},
            tool_requests_this_turn=2,  # Already at limit
        )

        spec = ToolSpec(
            id="fs.read_file",
            version="1.0",
            side_effect=SideEffect.READ,
            required_scopes=["fs.read"],
            connector="local_fs",
        )

        request = ToolInvocationRequest(
            tool_id="fs.read_file",
            args={"path": "test.txt"},
            requested_by={"agent_id": "test"},
        )

        decision = pipeline.evaluate(request, spec, context)
        assert decision.allowed is False
        assert "budget" in decision.reason.lower()

    def test_network_denied_in_v1(self):
        """Test network operations denied in V1."""
        pipeline = DecisionPipeline()
        context = PolicyContext(granted_scopes={"network"})

        spec = ToolSpec(
            id="http.get",
            version="1.0",
            side_effect=SideEffect.NETWORK,
            required_scopes=["network"],
            connector="http",
        )

        request = ToolInvocationRequest(
            tool_id="http.get",
            args={"url": "http://example.com"},
            requested_by={"agent_id": "test"},
        )

        decision = pipeline.evaluate(request, spec, context)
        assert decision.allowed is False


class TestLocalFSConnector:
    """Tests for LocalFSConnector."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, World!")

            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "nested.txt").write_text("Nested content")

            yield tmpdir

    def test_read_file_in_workspace(self, temp_workspace):
        """Test reading file within allowed workspace."""
        connector = LocalFSConnector(
            allowed_roots=[temp_workspace],
            base_path=temp_workspace,
        )

        result = connector.execute("read_file", {"path": "test.txt"})
        assert result["content"] == "Hello, World!"

    def test_read_file_outside_workspace_denied(self, temp_workspace):
        """Test reading outside workspace is denied."""
        connector = LocalFSConnector(
            allowed_roots=[temp_workspace],
            base_path=temp_workspace,
        )

        with pytest.raises(ConnectorError):
            connector.execute("read_file", {"path": "/etc/passwd"})

    def test_path_traversal_denied(self, temp_workspace):
        """Test path traversal (..) is denied."""
        connector = LocalFSConnector(
            allowed_roots=[temp_workspace],
            base_path=temp_workspace,
        )

        with pytest.raises(ConnectorError):
            connector.execute("read_file", {"path": "../../../etc/passwd"})

    def test_write_file(self, temp_workspace):
        """Test writing file."""
        connector = LocalFSConnector(
            allowed_roots=[temp_workspace],
            base_path=temp_workspace,
        )

        result = connector.execute("write_file", {
            "path": "new_file.txt",
            "content": "New content",
        })

        assert result["bytes_written"] > 0
        assert (Path(temp_workspace) / "new_file.txt").read_text() == "New content"

    def test_list_directory(self, temp_workspace):
        """Test listing directory."""
        connector = LocalFSConnector(
            allowed_roots=[temp_workspace],
            base_path=temp_workspace,
        )

        result = connector.execute("list_directory", {"path": "."})
        assert "test.txt" in result["entries"]
        assert "subdir" in result["entries"]

    def test_blocklist_enforced(self, temp_workspace):
        """Test blocklist patterns are enforced."""
        connector = LocalFSConnector(
            allowed_roots=[temp_workspace, "~"],
            blocklist=["**/secrets*"],
            base_path=temp_workspace,
        )

        # Create a secrets file
        secrets_file = Path(temp_workspace) / "secrets.txt"
        secrets_file.write_text("secret data")

        with pytest.raises(ConnectorError):
            connector.execute("read_file", {"path": "secrets.txt"})


class TestToolRuntime:
    """Tests for ToolRuntime (PEP)."""

    @pytest.fixture
    def runtime_with_workspace(self):
        """Create runtime with temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test content")

            # Create runtime
            registry = ToolRegistry()
            registry.initialize_defaults()

            decision = DecisionPipeline()

            runtime = ToolRuntime(
                registry=registry,
                decision_pipeline=decision,
            )

            # Register connector with workspace
            connector = LocalFSConnector(
                allowed_roots=[tmpdir],
                base_path=tmpdir,
            )
            runtime.register_connector(connector)

            yield runtime, tmpdir

    def test_invoke_read_success(self, runtime_with_workspace):
        """Test successful read invocation."""
        runtime, tmpdir = runtime_with_workspace

        request = ToolInvocationRequest(
            tool_id="fs.read_file",
            args={"path": "test.txt"},
            requested_by={"agent_id": "test"},
        )

        context = ExecutionContext(
            policy_context=PolicyContext(granted_scopes={"fs.read"}),
        )

        result = runtime.invoke(request, context)

        assert result.ok is True
        assert result.value["content"] == "Test content"
        assert result.audit_id is not None

    def test_invoke_without_scope_denied(self, runtime_with_workspace):
        """Test invocation denied without required scope."""
        runtime, tmpdir = runtime_with_workspace

        request = ToolInvocationRequest(
            tool_id="fs.read_file",
            args={"path": "test.txt"},
            requested_by={"agent_id": "test"},
        )

        context = ExecutionContext(
            policy_context=PolicyContext(granted_scopes=set()),  # No scopes
        )

        result = runtime.invoke(request, context)

        assert result.ok is False
        assert "scopes" in result.error.lower()

    def test_invoke_write_needs_approval(self, runtime_with_workspace):
        """Test write invocation needs approval."""
        runtime, tmpdir = runtime_with_workspace

        request = ToolInvocationRequest(
            tool_id="fs.write_file",
            args={"path": "new.txt", "content": "hello"},
            requested_by={"agent_id": "test"},
        )

        context = ExecutionContext(
            policy_context=PolicyContext(granted_scopes={"fs.write"}),
        )

        result = runtime.invoke(request, context)

        assert result.ok is False
        assert result.error == "APPROVAL_REQUIRED"

    def test_invoke_write_after_approval(self, runtime_with_workspace):
        """Test write succeeds after approval."""
        runtime, tmpdir = runtime_with_workspace

        request = ToolInvocationRequest(
            tool_id="fs.write_file",
            args={"path": "new.txt", "content": "hello"},
            requested_by={"agent_id": "test"},
        )

        context = ExecutionContext(
            policy_context=PolicyContext(
                granted_scopes={"fs.write"},
                pending_approvals={"fs.write_file"},  # Approved!
            ),
        )

        result = runtime.invoke(request, context)

        assert result.ok is True
        assert (Path(tmpdir) / "new.txt").read_text() == "hello"

    def test_audit_events_emitted(self, runtime_with_workspace):
        """Test audit events are emitted."""
        runtime, tmpdir = runtime_with_workspace

        request = ToolInvocationRequest(
            tool_id="fs.read_file",
            args={"path": "test.txt"},
            requested_by={"agent_id": "test"},
        )

        context = ExecutionContext(
            policy_context=PolicyContext(granted_scopes={"fs.read"}),
        )

        runtime.invoke(request, context)

        audits = runtime.get_audit_log()
        assert len(audits) == 1
        assert audits[0].decision == Decision.ALLOW

    def test_emotional_signals_in_audit_metadata(self, runtime_with_workspace):
        """Test emotional signals included in audit as metadata only."""
        runtime, tmpdir = runtime_with_workspace

        request = ToolInvocationRequest(
            tool_id="fs.read_file",
            args={"path": "test.txt"},
            requested_by={"agent_id": "test"},
        )

        context = ExecutionContext(
            policy_context=PolicyContext(granted_scopes={"fs.read"}),
            emotional_signals={"urgency": "elevated", "flow": "true"},
        )

        runtime.invoke(request, context)

        audits = runtime.get_audit_log()
        assert audits[0].emotional_signals == {"urgency": "elevated", "flow": "true"}


class TestIntegration:
    """Integration tests for tools subsystem."""

    def test_end_to_end_read_flow(self):
        """Test: read within allowlist succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            test_file = Path(tmpdir) / "allowed.txt"
            test_file.write_text("Allowed content")

            runtime = create_default_runtime(base_path=tmpdir)
            runtime._connectors["local_fs"]._allowed_roots = [Path(tmpdir).resolve()]

            # Request
            request = ToolInvocationRequest(
                tool_id="fs.read_file",
                args={"path": "allowed.txt"},
                requested_by={"agent_id": "front_door", "turn": 1},
                lane_id="writing",
            )

            context = ExecutionContext(
                policy_context=PolicyContext(granted_scopes={"fs.read"}),
                lane_id="writing",
            )

            # Execute
            result = runtime.invoke(request, context)

            # Verify
            assert result.ok is True
            assert result.value["content"] == "Allowed content"
            assert len(runtime.get_audit_log()) == 1
            assert runtime.get_audit_log()[0].lane_id == "writing"

    def test_write_denied_without_approval_no_side_effects(self):
        """Test: denied writes produce zero side effects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = create_default_runtime(base_path=tmpdir)
            runtime._connectors["local_fs"]._allowed_roots = [Path(tmpdir).resolve()]

            target_file = Path(tmpdir) / "should_not_exist.txt"

            request = ToolInvocationRequest(
                tool_id="fs.write_file",
                args={"path": "should_not_exist.txt", "content": "bad content"},
                requested_by={"agent_id": "test"},
            )

            context = ExecutionContext(
                policy_context=PolicyContext(granted_scopes={"fs.write"}),
                # No approval!
            )

            result = runtime.invoke(request, context)

            # Verify denied
            assert result.ok is False

            # Verify no file created
            assert not target_file.exists()
