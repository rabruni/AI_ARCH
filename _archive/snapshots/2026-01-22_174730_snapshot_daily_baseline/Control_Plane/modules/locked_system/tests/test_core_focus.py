"""Tests for locked_system.core.focus module.

Tests cover:
- FocusState management
- StanceMachine transitions
- GateController approvals
- FocusHRM unified operations
"""

import pytest
from datetime import datetime

from locked_system.core.types import Stance, GateType
from locked_system.core.focus import (
    QueuedProblem, FocusState, StanceMachine, GateController, FocusHRM,
)
from locked_system.core.trace import EpisodicTrace


class TestFocusState:
    """Tests for FocusState data class."""

    def test_default_state(self):
        """Test default FocusState values."""
        state = FocusState()
        assert state.stance == Stance.SENSEMAKING
        assert state.active_problem_id is None
        assert state.commitment is None
        assert state.queue == []
        assert not state.has_commitment()

    def test_commit_creates_commitment(self):
        """Test commit method."""
        state = FocusState()
        commitment = state.commit("prob_1", "Test problem", turns=10)

        assert commitment is not None
        assert commitment.id.startswith("cmt_")
        assert commitment.problem_id == "prob_1"
        assert commitment.turns_remaining == 10
        assert state.active_problem_id == "prob_1"
        assert state.has_commitment()

    def test_tick_decrements_commitment(self):
        """Test tick method."""
        state = FocusState()
        state.commit("prob_1", "Test", turns=3)

        assert state.tick() is True  # 3 -> 2
        assert state.tick() is True  # 2 -> 1
        assert state.tick() is False  # 1 -> 0

    def test_release_clears_commitment(self):
        """Test release method."""
        state = FocusState()
        state.commit("prob_1", "Test")
        state.release("completed")

        assert state.commitment is None
        assert not state.has_commitment()

    def test_queue_problem(self):
        """Test problem queueing."""
        state = FocusState()
        state.queue_problem("prob_1", "First problem", priority=5)
        state.queue_problem("prob_2", "Second problem", priority=8)

        assert len(state.queue) == 2

    def test_dequeue_by_priority(self):
        """Test dequeue returns highest priority first."""
        state = FocusState()
        state.queue_problem("low", "Low priority", priority=3)
        state.queue_problem("high", "High priority", priority=9)
        state.queue_problem("medium", "Medium priority", priority=5)

        next_problem = state.dequeue_next()
        assert next_problem.problem_id == "high"
        assert next_problem.priority == 9

    def test_switch_queues_current(self):
        """Test switch queues current problem."""
        state = FocusState()
        state.active_problem_id = "old_prob"

        state.switch("new_prob", "New problem")

        assert state.active_problem_id == "new_prob"
        # Old problem should be queued
        assert len(state.queue) == 1
        assert state.queue[0].problem_id == "old_prob"

    def test_mark_progress(self):
        """Test progress marking."""
        state = FocusState()
        state.active_problem_id = "prob_1"
        state.mark_progress()

        assert "prob_1" in state.last_progress

    def test_get_staleness(self):
        """Test staleness calculation."""
        state = FocusState()
        # No progress recorded = 0 staleness
        assert state.get_staleness("prob_1") == 0.0

        state.mark_progress("prob_1")
        # Just marked = low staleness
        assert state.get_staleness("prob_1") < 0.1


class TestStanceMachine:
    """Tests for StanceMachine."""

    def test_initial_stance(self):
        """Test default initial stance."""
        machine = StanceMachine()
        assert machine.current == Stance.SENSEMAKING

    def test_custom_initial_stance(self):
        """Test custom initial stance."""
        machine = StanceMachine(initial=Stance.EXECUTION)
        assert machine.current == Stance.EXECUTION

    def test_valid_transition_framing_gate(self):
        """Test valid transitions through framing gate."""
        machine = StanceMachine(initial=Stance.SENSEMAKING)

        # SENSEMAKING -> DISCOVERY via framing is valid
        assert machine.can_transition(Stance.DISCOVERY, GateType.FRAMING)

        success = machine.transition(Stance.DISCOVERY, GateType.FRAMING, "Exploring options")
        assert success is True
        assert machine.current == Stance.DISCOVERY

    def test_valid_transition_commitment_gate(self):
        """Test valid transitions through commitment gate."""
        machine = StanceMachine(initial=Stance.SENSEMAKING)

        # SENSEMAKING -> EXECUTION via commitment is valid
        assert machine.can_transition(Stance.EXECUTION, GateType.COMMITMENT)

        success = machine.transition(Stance.EXECUTION, GateType.COMMITMENT, "Committed to task")
        assert success is True
        assert machine.current == Stance.EXECUTION

    def test_invalid_transition_rejected(self):
        """Test invalid transitions are rejected."""
        machine = StanceMachine(initial=Stance.SENSEMAKING)

        # SENSEMAKING -> EVALUATION via framing is NOT valid
        assert not machine.can_transition(Stance.EVALUATION, GateType.FRAMING)

        success = machine.transition(Stance.EVALUATION, GateType.FRAMING, "Invalid")
        assert success is False
        assert machine.current == Stance.SENSEMAKING  # Unchanged

    def test_emergency_gate_forces_sensemaking(self):
        """Test emergency gate forces SENSEMAKING from any state."""
        machine = StanceMachine(initial=Stance.EXECUTION)

        assert machine.can_transition(Stance.SENSEMAKING, GateType.EMERGENCY)
        machine.force_sensemaking("Error occurred")
        assert machine.current == Stance.SENSEMAKING

    def test_get_allowed_actions(self):
        """Test allowed actions per stance."""
        machine = StanceMachine(initial=Stance.SENSEMAKING)
        actions = machine.get_allowed_actions()
        assert "question" in actions
        assert "clarify" in actions

        machine._current = Stance.EXECUTION
        actions = machine.get_allowed_actions()
        assert "execute" in actions
        assert "deliver" in actions

    def test_transition_logs_to_trace(self):
        """Test transitions are logged to trace."""
        trace = EpisodicTrace()
        machine = StanceMachine(initial=Stance.SENSEMAKING, trace=trace)

        machine.transition(Stance.EXECUTION, GateType.COMMITMENT, "Test")

        events = trace.query(event_type="stance_change")
        assert len(events) == 1
        assert events[0].payload["from"] == "sensemaking"
        assert events[0].payload["to"] == "execution"


class TestGateController:
    """Tests for GateController."""

    def test_framing_gate_always_allowed(self):
        """Test framing gate is generally allowed."""
        controller = GateController()
        assert controller.attempt(GateType.FRAMING, {}) is True

    def test_commitment_gate_requires_fields(self):
        """Test commitment gate requires problem_id and description."""
        controller = GateController()

        # Missing fields
        assert controller.attempt(GateType.COMMITMENT, {}) is False

        # With required fields
        assert controller.attempt(GateType.COMMITMENT, {
            "problem_id": "prob_1",
            "description": "Test"
        }) is True

    def test_evaluation_gate_requires_result(self):
        """Test evaluation gate requires result or commitment."""
        controller = GateController()

        assert controller.attempt(GateType.EVALUATION, {}) is False
        assert controller.attempt(GateType.EVALUATION, {"result": "done"}) is True
        assert controller.attempt(GateType.EVALUATION, {"commitment": "cmt_1"}) is True

    def test_emergency_gate_always_allowed(self):
        """Test emergency gate is always allowed."""
        controller = GateController()
        assert controller.attempt(GateType.EMERGENCY, {}) is True

    def test_write_approval_requires_signals(self):
        """Test write approval gate requires signals."""
        controller = GateController()

        assert controller.attempt(GateType.WRITE_APPROVAL, {}) is False
        assert controller.attempt(GateType.WRITE_APPROVAL, {"signals": {}}) is True

    def test_custom_evaluator(self):
        """Test custom gate evaluator registration."""
        controller = GateController()

        def strict_evaluator(context):
            return context.get("password") == "secret"

        controller.register(GateType.FRAMING, strict_evaluator)

        assert controller.attempt(GateType.FRAMING, {}) is False
        assert controller.attempt(GateType.FRAMING, {"password": "wrong"}) is False
        assert controller.attempt(GateType.FRAMING, {"password": "secret"}) is True

    def test_gate_logs_to_trace(self):
        """Test gate attempts are logged."""
        trace = EpisodicTrace()
        controller = GateController(trace=trace)

        controller.attempt(GateType.COMMITMENT, {"problem_id": "p1", "description": "d"})

        events = trace.query(event_type="gate_attempt")
        assert len(events) == 1
        assert events[0].payload["gate"] == "commitment"
        assert events[0].payload["approved"] is True


class TestFocusHRM:
    """Tests for FocusHRM unified class."""

    def test_initial_state(self):
        """Test initial FocusHRM state."""
        hrm = FocusHRM()
        assert hrm.current_stance == Stance.SENSEMAKING
        assert not hrm.has_commitment

    def test_attempt_stance_transition(self):
        """Test stance transition through gate."""
        hrm = FocusHRM()

        # Need to provide full gate context for commitment gate
        # The gate requires problem_id and description
        success = hrm.attempt_stance_transition(
            Stance.DISCOVERY,  # Valid transition from SENSEMAKING via FRAMING
            GateType.FRAMING,
            "Exploring options"
        )
        assert success is True
        assert hrm.current_stance == Stance.DISCOVERY

    def test_create_commitment(self):
        """Test commitment creation."""
        hrm = FocusHRM()

        commitment = hrm.create_commitment("prob_1", "Test problem", turns=5)

        assert commitment is not None
        assert hrm.has_commitment
        # Should auto-transition to EXECUTION
        assert hrm.current_stance == Stance.EXECUTION

    def test_create_commitment_fails_without_gate(self):
        """Test commitment fails if gate context invalid."""
        hrm = FocusHRM()

        # Override gate to be strict
        def strict_gate(context):
            return context.get("approved") is True

        hrm.gate_controller.register(GateType.COMMITMENT, strict_gate)

        commitment = hrm.create_commitment("prob_1", "Test")
        assert commitment is None  # Gate denied

    def test_tick_and_release(self):
        """Test commitment tick and release."""
        hrm = FocusHRM()
        hrm.create_commitment("prob_1", "Test", turns=2)

        assert hrm.tick() is True  # 2 -> 1
        assert hrm.tick() is False  # 1 -> 0

        hrm.release_commitment("completed")
        assert not hrm.has_commitment

    def test_queue_and_switch(self):
        """Test problem queue and switch."""
        hrm = FocusHRM()
        hrm.state.active_problem_id = "original"

        hrm.queue_problem("queued_1", "Later problem", priority=3)
        hrm.switch_problem("urgent", "Urgent problem")

        assert hrm.state.active_problem_id == "urgent"
        # Original should be queued
        assert len(hrm.state.queue) == 2

    def test_validate_action(self):
        """Test action validation for current stance."""
        hrm = FocusHRM()

        # In SENSEMAKING
        assert hrm.validate_action("question") is True
        assert hrm.validate_action("execute") is False

    def test_get_allowed_actions(self):
        """Test getting allowed actions."""
        hrm = FocusHRM()
        actions = hrm.get_allowed_actions()
        assert "question" in actions
        assert "clarify" in actions


class TestFocusHRMIntegration:
    """Integration tests for FocusHRM."""

    def test_full_workflow(self):
        """Test full focus workflow."""
        trace = EpisodicTrace()
        hrm = FocusHRM(trace=trace)

        # Start in sensemaking
        assert hrm.current_stance == Stance.SENSEMAKING

        # Create commitment (transitions to execution)
        commitment = hrm.create_commitment("feature_x", "Implement feature X", turns=3)
        assert hrm.current_stance == Stance.EXECUTION
        assert hrm.has_commitment

        # Work through turns
        hrm.tick()  # 3 -> 2
        hrm.tick()  # 2 -> 1

        # Queue interruption
        hrm.queue_problem("bug_urgent", "Urgent bug", priority=9)

        # Complete commitment
        hrm.tick()  # 1 -> 0
        hrm.release_commitment("completed")

        assert not hrm.has_commitment

        # Check events were logged
        stance_changes = trace.query(event_type="stance_change")
        assert len(stance_changes) >= 1

    def test_emergency_recovery(self):
        """Test emergency recovery to sensemaking."""
        hrm = FocusHRM()

        # Get into execution
        hrm.create_commitment("task", "Do task")
        assert hrm.current_stance == Stance.EXECUTION

        # Emergency - force back to sensemaking
        hrm.stance_machine.force_sensemaking("Error occurred")
        assert hrm.current_stance == Stance.SENSEMAKING
