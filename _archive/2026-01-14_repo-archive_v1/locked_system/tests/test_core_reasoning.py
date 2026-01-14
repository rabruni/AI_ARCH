"""Tests for locked_system.core.reasoning module.

Tests cover:
- InputClassifier classification
- ActionSelector selection
- ActionRouter routing
- Convenience functions
"""

import pytest

from locked_system.core.types import (
    Complexity, Stakes, ConflictLevel, Stance, InputClassification,
)
from locked_system.core.reasoning import (
    InputClassifier, ActionSelector, ActionRouter,
    ActionType, ActionPlan, RouteDecision, ClassificationResult,
    classify_input, route_input,
)
from locked_system.core.trace import EpisodicTrace


class TestInputClassifier:
    """Tests for InputClassifier."""

    def test_classify_simple_input(self):
        """Test classification of simple input."""
        classifier = InputClassifier()
        result = classifier.classify("What is the weather today?")

        assert isinstance(result, ClassificationResult)
        assert result.classification.complexity == Complexity.SIMPLE

    def test_classify_complex_input(self):
        """Test classification of complex input."""
        classifier = InputClassifier()
        result = classifier.classify(
            "Help me think through the trade-offs between multiple options for this complex problem"
        )

        assert result.classification.complexity == Complexity.COMPLEX

    def test_classify_high_stakes(self):
        """Test classification of high stakes input."""
        classifier = InputClassifier()
        result = classifier.classify(
            "I need to send this important payment before the deadline"
        )

        assert result.classification.stakes == Stakes.HIGH

    def test_classify_low_stakes(self):
        """Test classification of low stakes input."""
        classifier = InputClassifier()
        result = classifier.classify(
            "I'm just curious about something random"
        )

        assert result.classification.stakes == Stakes.LOW

    def test_detect_domains(self):
        """Test domain detection."""
        classifier = InputClassifier()

        # Productivity domain
        result = classifier.classify("Help me organize my tasks and schedule a meeting")
        assert "productivity" in result.classification.domain

        # Technical domain
        result = classifier.classify("There's a bug in my code, I'm getting an error")
        assert "technical" in result.classification.domain

        # Emotional domain
        result = classifier.classify("I'm feeling stressed and overwhelmed")
        assert "emotional" in result.classification.domain

    def test_estimate_uncertainty(self):
        """Test uncertainty estimation."""
        classifier = InputClassifier()

        # High uncertainty
        result = classifier.classify("Maybe I should? I'm not sure if it's okay?")
        assert result.classification.uncertainty > 0.3

        # Low uncertainty
        result = classifier.classify("Show me the file contents")
        assert result.classification.uncertainty < 0.3

    def test_detect_conflict(self):
        """Test conflict detection."""
        classifier = InputClassifier()

        # With conflict markers
        result = classifier.classify("But I disagree, that's wrong, however I think...")
        assert result.classification.conflict != ConflictLevel.NONE

        # Without conflict
        result = classifier.classify("Please help me with this task")
        assert result.classification.conflict == ConflictLevel.NONE

    def test_determine_horizon(self):
        """Test time horizon detection."""
        classifier = InputClassifier()

        # Immediate
        result = classifier.classify("I need this right now, immediately!")
        assert result.classification.horizon == "immediate"

        # Far
        result = classifier.classify("Eventually someday in the long term future")
        assert result.classification.horizon == "far"

    def test_pattern_matches_returned(self):
        """Test that pattern matches are included."""
        classifier = InputClassifier()
        result = classifier.classify("Help me prioritize my important tasks")

        assert len(result.pattern_matches) > 0
        assert any("stakes" in m or "domain" in m for m in result.pattern_matches)

    def test_logs_to_trace(self):
        """Test classification logs to trace."""
        trace = EpisodicTrace()
        classifier = InputClassifier(trace=trace)

        classifier.classify("Test input")

        events = trace.query(event_type="input_classified")
        assert len(events) == 1


class TestActionSelector:
    """Tests for ActionSelector."""

    def test_select_clarify_in_sensemaking(self):
        """Test selector returns CLARIFY in sensemaking stance."""
        selector = ActionSelector()
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near"
        )

        plan = selector.select(classification, Stance.SENSEMAKING)

        assert plan.action_type == ActionType.CLARIFY

    def test_select_delegate_in_discovery(self):
        """Test selector returns DELEGATE in discovery stance."""
        selector = ActionSelector()
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near"
        )

        plan = selector.select(classification, Stance.DISCOVERY)

        assert plan.action_type == ActionType.DELEGATE

    def test_select_respond_in_execution(self):
        """Test selector returns RESPOND in execution stance."""
        selector = ActionSelector()
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near"
        )

        plan = selector.select(classification, Stance.EXECUTION)

        assert plan.action_type == ActionType.RESPOND

    def test_select_escalate_when_needed(self):
        """Test selector returns ESCALATE when classification requires it."""
        selector = ActionSelector()
        classification = InputClassification(
            complexity=Complexity.COMPLEX,  # Triggers escalation
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.HIGH,
            horizon="near"
        )

        plan = selector.select(classification, Stance.EXECUTION)

        assert plan.action_type == ActionType.ESCALATE
        assert plan.altitude_target is not None

    def test_select_agents_by_domain(self):
        """Test agent selection based on domain."""
        selector = ActionSelector()
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near",
            domain=["productivity", "thinking"]
        )

        plan = selector.select(classification, Stance.SENSEMAKING)

        assert "task_manager" in plan.agents or "calendar" in plan.agents

    def test_build_constraints_high_stakes(self):
        """Test constraints added for high stakes."""
        selector = ActionSelector()
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.HIGH,
            horizon="near"
        )

        plan = selector.select(classification, Stance.EXECUTION)

        assert "verify_before_action" in plan.constraints

    def test_register_custom_agents(self):
        """Test custom agent registration."""
        selector = ActionSelector()
        selector.register_agents("custom_domain", ["custom_agent_1", "custom_agent_2"])

        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near",
            domain=["custom_domain"]
        )

        plan = selector.select(classification, Stance.SENSEMAKING)

        assert "custom_agent_1" in plan.agents

    def test_logs_to_trace(self):
        """Test selection logs to trace."""
        trace = EpisodicTrace()
        selector = ActionSelector(trace=trace)
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near"
        )

        selector.select(classification, Stance.SENSEMAKING)

        events = trace.query(event_type="action_selected")
        assert len(events) == 1


class TestActionRouter:
    """Tests for ActionRouter."""

    def test_route_returns_decision(self):
        """Test router returns RouteDecision."""
        router = ActionRouter()
        decision = router.route(
            "Help me with this task",
            Stance.SENSEMAKING,
            "L2"
        )

        assert isinstance(decision, RouteDecision)
        assert isinstance(decision.classification, InputClassification)
        assert isinstance(decision.action_plan, ActionPlan)

    def test_route_requires_gate_for_escalation(self):
        """Test escalation requires gate."""
        router = ActionRouter()
        decision = router.route(
            "This is a complex high-stakes critical important decision",
            Stance.EXECUTION,
            "L2"
        )

        if decision.action_plan.action_type == ActionType.ESCALATE:
            assert decision.requires_gate is True
            assert decision.gate_type is not None

    def test_route_with_context(self):
        """Test routing with additional context."""
        router = ActionRouter()
        decision = router.route(
            "Continue with the previous task",
            Stance.EXECUTION,
            "L2",
            context={"previous_task": "writing"}
        )

        assert decision is not None

    def test_logs_to_trace(self):
        """Test routing logs to trace."""
        trace = EpisodicTrace()
        router = ActionRouter(trace=trace)

        router.route("Test input", Stance.SENSEMAKING)

        events = trace.query(event_type="route_decision")
        assert len(events) == 1


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_classify_input(self):
        """Test classify_input convenience function."""
        classification = classify_input("What should I prioritize today?")

        assert isinstance(classification, InputClassification)
        assert classification.stakes is not None

    def test_route_input(self):
        """Test route_input convenience function."""
        decision = route_input(
            "Help me organize my work",
            Stance.SENSEMAKING,
            "L2"
        )

        assert isinstance(decision, RouteDecision)
        assert decision.action_plan is not None


class TestReasoningIntegration:
    """Integration tests for reasoning module."""

    def test_full_routing_flow(self):
        """Test complete routing flow."""
        trace = EpisodicTrace()
        router = ActionRouter(trace=trace)

        # Complex high-stakes input
        decision = router.route(
            "I need to make an important decision about investing money in this critical project",
            Stance.SENSEMAKING,
            "L2"
        )

        # Should detect high stakes
        assert decision.classification.stakes == Stakes.HIGH

        # Should require some kind of gate or verification
        assert (decision.requires_gate or
                "verify_before_action" in decision.action_plan.constraints)

        # Should have appropriate agents
        assert len(decision.action_plan.agents) > 0

    def test_domain_specific_routing(self):
        """Test domain-specific routing."""
        router = ActionRouter()

        # Technical input
        tech_decision = router.route(
            "There's a bug in the code causing an error",
            Stance.EXECUTION,
            "L2"
        )
        assert "technical" in tech_decision.classification.domain

        # Emotional input
        emotional_decision = router.route(
            "I'm feeling stressed and overwhelmed",
            Stance.SENSEMAKING,
            "L2"
        )
        assert "emotional" in emotional_decision.classification.domain
