"""Tests for the Front-Door Agent subsystem.

Tests cover:
- Signal-to-gate mapping (including emotional triggers)
- Response compression under overload
- Patch proposals require write approval
- Multi-lane scenario: writing active, finance interrupt
- Emotional overload triggers evaluation gate
"""

import pytest

from locked_system.front_door import (
    FrontDoorAgent,
    SignalDetector,
    DetectedSignal,
    BundleProposer,
    Bundle,
    BundleType,
    EmotionalTelemetry,
    TelemetryResponse,
)
from locked_system.front_door.signals import SignalType
from locked_system.agents import AgentContext, AgentPacket


class TestSignalDetector:
    """Tests for SignalDetector."""

    def test_detect_formal_work(self):
        """Test detection of formal work signals."""
        detector = SignalDetector()

        # Various formal work patterns
        inputs = [
            "Let's start working on the report",
            "I need to write a document",
            "Let's get into the project",
            "Working on a new feature",
        ]

        for user_input in inputs:
            signal = detector.detect(user_input)
            assert signal.type == SignalType.FORMAL_WORK, f"Failed for: {user_input}"
            assert signal.suggested_gate == "work_declaration"

    def test_detect_interrupt(self):
        """Test detection of interrupt signals."""
        detector = SignalDetector()

        inputs = [
            "Quick question about something",
            "Before I forget, can you check this?",
            "Something came up urgently",
        ]

        for user_input in inputs:
            signal = detector.detect(user_input)
            assert signal.type == SignalType.INTERRUPT, f"Failed for: {user_input}"
            assert signal.suggested_gate == "lane_switch"

    def test_detect_urgency(self):
        """Test detection of urgency signals."""
        detector = SignalDetector()

        signal = detector.detect("This is urgent, I need help right now")
        assert signal.type == SignalType.URGENCY
        assert signal.suggested_gate == "lane_switch"

    def test_detect_emotional_overload_from_text(self):
        """Test detection of emotional overload from text patterns."""
        detector = SignalDetector()

        signal = detector.detect("I'm so frustrated, this doesn't make sense and I'm stuck")
        assert signal.type == SignalType.EMOTIONAL_OVERLOAD
        assert signal.suggested_gate == "evaluation"

    def test_detect_emotional_overload_from_signals(self):
        """Test detection of overload from emotional signals."""
        detector = SignalDetector()

        signal = detector.detect(
            "help me understand",
            emotional_signals={"frustration": "high"}
        )
        assert signal.type == SignalType.EMOTIONAL_OVERLOAD

    def test_detect_completion(self):
        """Test detection of completion signals."""
        detector = SignalDetector()

        inputs = [
            "I'm done with this",
            "That's all for now",
            "Let's wrap up",
        ]

        for user_input in inputs:
            signal = detector.detect(user_input)
            assert signal.type == SignalType.COMPLETION, f"Failed for: {user_input}"

    def test_detect_question(self):
        """Test detection of questions."""
        detector = SignalDetector()

        signal = detector.detect("What time is it?")
        assert signal.type == SignalType.QUESTION

    def test_detect_work_type(self):
        """Test work type detection."""
        detector = SignalDetector()

        assert detector.detect_work_type("write a document") == "writing"
        assert detector.detect_work_type("check the budget") == "finance"
        assert detector.detect_work_type("research the topic") == "research"
        assert detector.detect_work_type("deploy the service") == "ops"


class TestEmotionalTelemetry:
    """Tests for EmotionalTelemetry."""

    def test_overload_triggers_evaluation(self):
        """Test that overload triggers evaluation gate."""
        telemetry = EmotionalTelemetry()

        response = telemetry.process({"frustration": "high"})
        assert response.trigger_evaluation is True
        assert response.compress_options is True

        response = telemetry.process({"cognitive_load": "overloaded"})
        assert response.trigger_evaluation is True

    def test_flow_recommends_defer(self):
        """Test that flow state recommends defer."""
        telemetry = EmotionalTelemetry()

        response = telemetry.process({"flow": "true"})
        assert response.recommend_defer is True

    def test_critical_urgency_overrides_flow(self):
        """Test that critical urgency overrides flow protection."""
        telemetry = EmotionalTelemetry()

        response = telemetry.process({"flow": "true", "urgency": "critical"})
        assert response.recommend_defer is False
        assert response.urgency_weight == 2.0

    def test_overloaded_compresses_options(self):
        """Test that cognitive overload compresses options."""
        telemetry = EmotionalTelemetry()

        response = telemetry.process({"cognitive_load": "overloaded"})
        assert response.max_options == 2

    def test_apply_to_options(self):
        """Test applying telemetry to options list."""
        telemetry = EmotionalTelemetry()

        options = [
            {"label": "Option 1"},
            {"label": "Defer"},
            {"label": "Option 3"},
            {"label": "Option 4"},
        ]

        # With flow, defer should be first
        result = telemetry.apply_to_options(options, {"flow": "true"})
        assert "Defer" in result[0].get("label", "")

        # With overload, should be limited
        result = telemetry.apply_to_options(options, {"cognitive_load": "overloaded"})
        assert len(result) == 2


class TestBundleProposer:
    """Tests for BundleProposer."""

    def test_propose_writer_bundle(self):
        """Test proposing writer bundle."""
        proposer = BundleProposer()

        bundle = proposer.propose("writing")
        assert bundle is not None
        assert bundle.type == BundleType.WRITER
        assert bundle.primary_agent == "writer"
        assert "fs.write_file" in bundle.default_tools

    def test_propose_finance_bundle(self):
        """Test proposing finance bundle."""
        proposer = BundleProposer()

        bundle = proposer.propose("finance")
        assert bundle is not None
        assert bundle.type == BundleType.FINANCE
        assert bundle.primary_agent == "analyst"

    def test_propose_unknown_returns_none(self):
        """Test unknown work type returns None."""
        proposer = BundleProposer()

        bundle = proposer.propose("unknown_type")
        assert bundle is None

    def test_list_bundles(self):
        """Test listing all bundles."""
        proposer = BundleProposer()

        bundles = proposer.list_bundles()
        assert len(bundles) >= 4  # writer, finance, research, monitor


class TestFrontDoorAgent:
    """Tests for FrontDoorAgent."""

    def test_process_formal_work(self):
        """Test processing formal work input."""
        agent = FrontDoorAgent()

        context = AgentContext(
            user_input="Let's start working on the documentation",
            turn=1,
        )

        packet = agent.process(context)

        assert packet is not None
        assert packet.has_gate_requests()
        gates = packet.get_gate_requests()
        assert any(g.gate == "work_declaration" for g in gates)

    def test_process_with_emotional_overload(self):
        """Test that emotional overload triggers evaluation."""
        agent = FrontDoorAgent()

        context = AgentContext(
            user_input="Help me with this",
            emotional_signals={"frustration": "high"},
            turn=1,
        )

        packet = agent.process(context)

        gates = packet.get_gate_requests()
        assert any(g.gate == "evaluation" for g in gates)
        assert "overwhelming" in packet.message.lower() or "check in" in packet.message.lower()

    def test_process_interrupt_in_flow(self):
        """Test interrupt recommendation in flow state."""
        agent = FrontDoorAgent()

        context = AgentContext(
            user_input="Quick question about something else",
            emotional_signals={"flow": "true"},
            turn=1,
        )

        packet = agent.process(context)

        # Should recommend defer
        assert "defer" in packet.message.lower() or "later" in packet.message.lower()

    def test_generate_orientation(self):
        """Test orientation message generation."""
        agent = FrontDoorAgent()

        context = AgentContext(
            user_input="What's going on?",
            system_context={
                'lane_context': {
                    'lane_id': 'lane_123',
                    'lease_goal': 'Write docs',
                    'lease_mode': 'execution',
                }
            },
            turn=1,
        )

        message = agent.generate_orientation_message(context)

        assert "lane_123" in message
        assert "Write docs" in message

    def test_can_read_allowed_paths(self):
        """Test allowlist for config reading."""
        agent = FrontDoorAgent()

        assert agent.can_read_path("./core/config.yaml")
        assert agent.can_read_path("./docs/readme.md")
        assert not agent.can_read_path("/etc/passwd")
        assert not agent.can_read_path("~/Documents/personal.txt")


class TestIntegration:
    """Integration tests for front-door agent."""

    def test_multi_lane_finance_interrupt(self):
        """Test: writing lane active, finance interrupt triggers lane switch gate."""
        agent = FrontDoorAgent()

        # Simulating active writing lane
        context = AgentContext(
            user_input="Quick check on the budget numbers",
            system_context={
                'lane_context': {
                    'lane_id': 'lane_writing',
                    'lease_goal': 'Write documentation',
                    'lease_mode': 'execution',
                }
            },
            turn=1,
        )

        packet = agent.process(context)

        # Should detect interrupt and propose lane switch
        gates = packet.get_gate_requests()
        assert any(g.gate == "lane_switch" for g in gates)

    def test_emotional_overload_compressed_options(self):
        """Test: emotional overload triggers evaluation and compressed options."""
        agent = FrontDoorAgent()

        context = AgentContext(
            user_input="I don't understand what's happening",
            emotional_signals={"cognitive_load": "overloaded", "frustration": "high"},
            turn=1,
        )

        packet = agent.process(context)

        # Should propose evaluation gate
        gates = packet.get_gate_requests()
        assert any(g.gate == "evaluation" for g in gates)

        # Agent should acknowledge the situation
        assert any(word in packet.message.lower() for word in ["overwhelming", "pause", "check"])

    def test_front_door_never_executes_directly(self):
        """Test that front-door only proposes, never executes."""
        agent = FrontDoorAgent()

        context = AgentContext(
            user_input="Write a file to disk",
            turn=1,
        )

        packet = agent.process(context)

        # Should have no tool requests (only gate requests)
        tool_requests = packet.get_tool_requests()
        assert len(tool_requests) == 0

    def test_emotional_telemetry_routing_only(self):
        """Test that emotional signals affect routing only."""
        agent = FrontDoorAgent()

        # High urgency should affect priority but not grant authority
        context = AgentContext(
            user_input="I need help with something",
            emotional_signals={"urgency": "critical"},
            turn=1,
        )

        packet = agent.process(context)

        # Urgency is recorded in traces but doesn't bypass gates
        assert packet.traces.get('emotional_signals', {}).get('urgency') == 'critical'

        # Still no tool execution
        assert len(packet.get_tool_requests()) == 0
