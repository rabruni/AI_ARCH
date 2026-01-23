"""Tests for the Executor subsystem.

Tests cover:
- Firewall rejects forbidden packets
- Gate blocks tool execution until satisfied
- Write tool denied without approval
- End-to-end turn execution
- Audit event emission
"""

import pytest
import tempfile
from pathlib import Path

from locked_system.executor import (
    Executor,
    ExecutorConfig,
    SystemResponse,
    TurnState,
    GateController,
    WriteApprovalGate,
    GatePrompt,
    GateStatus,
)
from locked_system.agents import (
    AgentPacket,
    AgentContext,
    AgentRuntime,
    AgentLoader,
    PacketFirewall,
    Proposal,
    ProposalType,
)
from locked_system.tools import (
    ToolRuntime,
    ToolRegistry,
    DecisionPipeline,
    PolicyContext,
    SideEffect,
    create_default_runtime,
)
from locked_system.lanes import LaneStore, LaneKind


class TestGateController:
    """Tests for GateController."""

    def test_write_approval_flow(self):
        """Test write approval gate flow."""
        controller = GateController()

        # Request approval
        prompt = controller.require_write_approval(
            "fs.write_file",
            {"path": "test.txt", "content": "hello"},
        )

        assert controller.has_pending_gates()
        assert not controller.is_write_approved("fs.write_file")

        # Approve
        result = controller.resolve_gate(prompt.gate_id, {"type": "approve"})

        assert result.status == GateStatus.APPROVED
        assert controller.is_write_approved("fs.write_file")
        assert not controller.has_pending_gates()

    def test_write_denial_flow(self):
        """Test write denial."""
        controller = GateController()

        prompt = controller.require_write_approval(
            "fs.write_file",
            {"path": "test.txt", "content": "hello"},
        )

        result = controller.resolve_gate(prompt.gate_id, {"type": "deny"})

        assert result.status == GateStatus.DENIED
        assert not controller.is_write_approved("fs.write_file")

    def test_multiple_gates(self):
        """Test handling multiple pending gates."""
        controller = GateController()

        prompt1 = controller.require_write_approval("tool1", {"arg": "val1"})
        prompt2 = controller.require_write_approval("tool2", {"arg": "val2"})

        assert len(controller.get_pending_prompts()) == 2

        controller.resolve_gate(prompt1.gate_id, {"type": "approve"})
        assert len(controller.get_pending_prompts()) == 1

        controller.resolve_gate(prompt2.gate_id, {"type": "deny"})
        assert len(controller.get_pending_prompts()) == 0


class TestWriteApprovalGate:
    """Tests for WriteApprovalGate."""

    def test_prompt_generation(self):
        """Test gate generates proper prompt."""
        gate = WriteApprovalGate(
            tool_id="fs.write_file",
            tool_args={"path": "test.txt", "content": "Hello"},
            description="Write to test file",
        )

        prompt = gate.generate_prompt()

        assert prompt.gate_type == "write_approval"
        assert "fs.write_file" in prompt.message
        assert len(prompt.options) >= 2

    def test_long_content_truncated(self):
        """Test long content is truncated in prompt."""
        long_content = "x" * 200
        gate = WriteApprovalGate(
            tool_id="fs.write_file",
            tool_args={"path": "test.txt", "content": long_content},
        )

        prompt = gate.generate_prompt()

        # Content in display should be truncated
        assert "..." in str(prompt.message)

    def test_approve_execution(self):
        """Test approve results in APPROVED status."""
        gate = WriteApprovalGate(
            tool_id="fs.write_file",
            tool_args={"path": "test.txt"},
        )

        result = gate.execute({"type": "approve"})
        assert result.status == GateStatus.APPROVED

    def test_deny_execution(self):
        """Test deny results in DENIED status."""
        gate = WriteApprovalGate(
            tool_id="fs.write_file",
            tool_args={"path": "test.txt"},
        )

        result = gate.execute({"type": "deny"})
        assert result.status == GateStatus.DENIED


class TestExecutorPipeline:
    """Tests for Executor pipeline."""

    @pytest.fixture
    def executor_with_workspace(self):
        """Create executor with temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test content")

            # Create executor with custom tool runtime
            tool_runtime = create_default_runtime(base_path=tmpdir)
            tool_runtime._connectors["local_fs"]._allowed_roots = [Path(tmpdir).resolve()]

            # Create agent runtime
            loader = AgentLoader()
            loader.initialize_defaults()
            agent_runtime = AgentRuntime(loader=loader)

            # Create simple processor
            def simple_processor(ctx: AgentContext) -> AgentPacket:
                return AgentPacket(
                    message=f"Processing: {ctx.user_input}",
                    proposals=[],
                    traces={"agent_id": "front_door"},
                )

            agent_runtime.register_processor("front_door", simple_processor)

            executor = Executor(
                agent_runtime=agent_runtime,
                tool_runtime=tool_runtime,
                config=ExecutorConfig(default_scopes=["fs.read", "fs.write"]),
            )

            yield executor, tmpdir

    def test_basic_step(self, executor_with_workspace):
        """Test basic turn execution."""
        executor, tmpdir = executor_with_workspace

        response = executor.step("Hello")

        assert response is not None
        assert "Processing: Hello" in response.message
        assert not response.has_pending_gates()

    def test_step_with_read_tool(self, executor_with_workspace):
        """Test step that reads a file."""
        executor, tmpdir = executor_with_workspace

        # Create processor that requests file read
        def read_processor(ctx: AgentContext) -> AgentPacket:
            return AgentPacket(
                message="Reading file",
                proposals=[Proposal.tool_request("fs.read_file", {"path": "test.txt"})],
                traces={"agent_id": "front_door"},
            )

        executor._agent_runtime.register_processor("front_door", read_processor)

        response = executor.step("Read the file")

        assert len(response.tool_results) == 1
        assert response.tool_results[0].ok
        assert "Test content" in response.tool_results[0].value.get("content", "")

    def test_write_requires_approval(self, executor_with_workspace):
        """Test that write operations require approval."""
        executor, tmpdir = executor_with_workspace

        # Use writer agent which has fs.write_file permission
        def write_processor(ctx: AgentContext) -> AgentPacket:
            return AgentPacket(
                message="Writing file",
                proposals=[Proposal.tool_request("fs.write_file", {
                    "path": "new.txt",
                    "content": "New content",
                })],
                traces={"agent_id": "writer"},
            )

        executor._agent_runtime.register_processor("writer", write_processor)

        response = executor.step("Write a file", agent_id="writer")

        # Should have pending gate
        assert response.has_pending_gates()
        assert len(response.tool_results) == 0  # Not executed yet

        # File should NOT exist
        assert not (Path(tmpdir) / "new.txt").exists()

    def test_write_after_approval(self, executor_with_workspace):
        """Test write succeeds after approval."""
        executor, tmpdir = executor_with_workspace

        # Use writer agent which has fs.write_file permission
        def write_processor(ctx: AgentContext) -> AgentPacket:
            return AgentPacket(
                message="Writing file",
                proposals=[Proposal.tool_request("fs.write_file", {
                    "path": "new.txt",
                    "content": "New content",
                })],
                traces={"agent_id": "writer"},
            )

        executor._agent_runtime.register_processor("writer", write_processor)

        # First step - triggers approval gate
        response1 = executor.step("Write a file", agent_id="writer")
        assert response1.has_pending_gates()

        # Get gate and approve
        gate_prompt = response1.pending_gates[0]
        executor.resolve_gate(gate_prompt.gate_id, {"type": "approve"})

        # Second step - should execute write
        response2 = executor.step("Write a file", agent_id="writer")
        assert not response2.has_pending_gates()
        assert len(response2.tool_results) == 1
        assert response2.tool_results[0].ok

        # File should now exist
        assert (Path(tmpdir) / "new.txt").exists()

    def test_turn_state_tracking(self, executor_with_workspace):
        """Test turn state is tracked correctly."""
        executor, tmpdir = executor_with_workspace

        response = executor.step("Test input")

        assert response.turn_state is not None
        assert response.turn_state.user_input == "Test input"
        assert response.turn_state.turn_id.startswith("turn_")


class TestFirewallIntegration:
    """Tests for firewall integration in executor."""

    def test_firewall_blocks_forbidden_claims(self):
        """Test that firewall blocks packets with forbidden claims."""
        loader = AgentLoader()
        loader.initialize_defaults()
        agent_runtime = AgentRuntime(loader=loader)

        # Create processor that claims execution
        def bad_processor(ctx: AgentContext) -> AgentPacket:
            return AgentPacket(
                message="I have executed the delete command.",
                proposals=[],
                traces={"agent_id": "front_door"},
            )

        agent_runtime.register_processor("front_door", bad_processor)

        executor = Executor(agent_runtime=agent_runtime)

        response = executor.step("Do something")

        # Should be blocked
        assert "blocked" in response.message.lower()


class TestAuditIntegration:
    """Tests for audit trail."""

    def test_audit_events_emitted(self):
        """Test audit events are emitted for tool execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Content")

            tool_runtime = create_default_runtime(base_path=tmpdir)
            tool_runtime._connectors["local_fs"]._allowed_roots = [Path(tmpdir).resolve()]

            loader = AgentLoader()
            loader.initialize_defaults()
            agent_runtime = AgentRuntime(loader=loader)

            def read_processor(ctx: AgentContext) -> AgentPacket:
                return AgentPacket(
                    message="Reading",
                    proposals=[Proposal.tool_request("fs.read_file", {"path": "test.txt"})],
                    traces={"agent_id": "front_door"},
                )

            agent_runtime.register_processor("front_door", read_processor)

            executor = Executor(
                agent_runtime=agent_runtime,
                tool_runtime=tool_runtime,
                config=ExecutorConfig(default_scopes=["fs.read"]),
            )

            # Execute
            response = executor.step("Read")

            # Check audit
            audit_log = executor.get_audit_log()
            assert len(audit_log) >= 1
            assert response.audit_ids


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_turn_read_tool(self):
        """Test: agent proposes read → decision allows → tool runs → audit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "data.txt"
            test_file.write_text("Important data")

            tool_runtime = create_default_runtime(base_path=tmpdir)
            tool_runtime._connectors["local_fs"]._allowed_roots = [Path(tmpdir).resolve()]

            loader = AgentLoader()
            loader.initialize_defaults()
            agent_runtime = AgentRuntime(loader=loader)

            def analyzer(ctx: AgentContext) -> AgentPacket:
                return AgentPacket(
                    message="Analyzing the data file.",
                    proposals=[Proposal.tool_request("fs.read_file", {"path": "data.txt"})],
                    traces={"agent_id": "front_door"},
                )

            agent_runtime.register_processor("front_door", analyzer)

            executor = Executor(
                agent_runtime=agent_runtime,
                tool_runtime=tool_runtime,
                config=ExecutorConfig(default_scopes=["fs.read"]),
            )

            response = executor.step("Analyze the data")

            # Verify
            assert "Analyzing" in response.message
            assert len(response.tool_results) == 1
            assert response.tool_results[0].ok
            assert "Important data" in response.tool_results[0].value["content"]
            assert len(response.audit_ids) == 1

    def test_write_approval_flow_complete(self):
        """Test: write → approval gate → approve → execute → verify."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_runtime = create_default_runtime(base_path=tmpdir)
            tool_runtime._connectors["local_fs"]._allowed_roots = [Path(tmpdir).resolve()]

            loader = AgentLoader()
            loader.initialize_defaults()
            agent_runtime = AgentRuntime(loader=loader)

            # Use writer agent which has fs.write_file permission
            def writer(ctx: AgentContext) -> AgentPacket:
                return AgentPacket(
                    message="Creating document.",
                    proposals=[Proposal.tool_request("fs.write_file", {
                        "path": "doc.txt",
                        "content": "Document content",
                    })],
                    traces={"agent_id": "writer"},
                )

            agent_runtime.register_processor("writer", writer)

            executor = Executor(
                agent_runtime=agent_runtime,
                tool_runtime=tool_runtime,
                config=ExecutorConfig(default_scopes=["fs.read", "fs.write"]),
            )

            # Step 1: Request write
            response1 = executor.step("Create a document", agent_id="writer")

            # Should have gate prompt
            assert response1.has_pending_gates()
            gate = response1.pending_gates[0]
            assert gate.gate_type == "write_approval"

            # No file yet
            assert not (Path(tmpdir) / "doc.txt").exists()

            # Step 2: Approve
            executor.resolve_gate(gate.gate_id, {"type": "approve"})

            # Step 3: Re-execute
            response2 = executor.step("Create a document", agent_id="writer")

            # Should succeed
            assert not response2.has_pending_gates()
            assert len(response2.tool_results) == 1
            assert response2.tool_results[0].ok

            # File should exist
            assert (Path(tmpdir) / "doc.txt").exists()
            assert (Path(tmpdir) / "doc.txt").read_text() == "Document content"
