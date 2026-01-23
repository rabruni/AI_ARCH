"""Tests for the Lanes subsystem.

Tests cover:
- Lane lifecycle transitions
- Gate triggers and outputs
- Budget enforcement
- Single active lane invariant
- Pause/resume with bookmarks
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from locked_system.lanes import (
    Lane, LaneKind, LaneStatus, LaneLease, LanePolicy, LaneSnapshot, LaneBudgets,
    LaneStore, WorkDeclarationGate, LaneSwitchGate, LaneSwitchDecision, EvaluationGate, GateResult,
)


class TestLaneModels:
    """Tests for Lane data models."""

    def test_lane_create_factory(self):
        """Test Lane.create() factory method."""
        lane = Lane.create(
            kind=LaneKind.WRITING,
            goal="Write documentation",
            mode="execution",
            expires_hours=2,
        )

        assert lane.lane_id.startswith("lane_")
        assert lane.kind == LaneKind.WRITING
        assert lane.status == LaneStatus.ACTIVE
        assert lane.lease.mode == "execution"
        assert lane.lease.goal == "Write documentation"
        assert not lane.is_lease_expired()

    def test_lane_lease_expiry(self):
        """Test lease expiry detection."""
        # Create lane with already-expired lease
        lane = Lane.create(kind=LaneKind.RESEARCH, goal="Test", expires_hours=0)
        # Manually set past expiry
        lane.lease.expires_at_utc = datetime.utcnow() - timedelta(hours=1)

        assert lane.is_lease_expired()

    def test_lane_pause_resume_lifecycle(self):
        """Test pause/resume with snapshot."""
        lane = Lane.create(kind=LaneKind.WRITING, goal="Test")

        # Pause with bookmark
        lane.pause(
            bookmark="Working on chapter 3",
            next_steps=["Finish section 3.2", "Review section 3.1"],
            open_questions=["What format for diagrams?"],
        )

        assert lane.status == LaneStatus.PAUSED
        assert lane.snapshot.bookmark == "Working on chapter 3"
        assert len(lane.snapshot.next_steps) == 2
        assert len(lane.snapshot.open_questions) == 1

        # Resume
        lane.resume()
        assert lane.status == LaneStatus.ACTIVE

    def test_lane_complete(self):
        """Test lane completion."""
        lane = Lane.create(kind=LaneKind.WRITING, goal="Test")
        lane.complete("Successfully completed all documentation")

        assert lane.status == LaneStatus.COMPLETED
        assert lane.snapshot.bookmark == "Successfully completed all documentation"

    def test_cannot_resume_non_paused_lane(self):
        """Test that resume fails on non-paused lanes."""
        lane = Lane.create(kind=LaneKind.WRITING, goal="Test")

        with pytest.raises(ValueError, match="Cannot resume lane"):
            lane.resume()

    def test_lane_serialization(self):
        """Test to_dict/from_dict round-trip."""
        lane = Lane.create(kind=LaneKind.FINANCE, goal="Budget review")
        lane.pause("Reviewing Q1", ["Check expenses"])

        data = lane.to_dict()
        restored = Lane.from_dict(data)

        assert restored.lane_id == lane.lane_id
        assert restored.kind == lane.kind
        assert restored.status == lane.status
        assert restored.snapshot.bookmark == lane.snapshot.bookmark


class TestLaneStore:
    """Tests for LaneStore."""

    def test_create_lane(self):
        """Test lane creation in store."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        assert lane.lane_id in store._lanes
        assert store.get_active() == lane
        assert store.has_active()

    def test_single_active_lane_invariant(self):
        """Test that only one lane can be active at a time."""
        store = LaneStore()
        lane1 = store.create(kind=LaneKind.WRITING, goal="Lane 1")
        lane2 = store.create(kind=LaneKind.FINANCE, goal="Lane 2")

        # Lane 2 should be paused since lane 1 is active
        assert lane1.status == LaneStatus.ACTIVE
        assert lane2.status == LaneStatus.PAUSED
        assert store.get_active().lane_id == lane1.lane_id

    def test_pause_and_resume(self):
        """Test pause and resume in store."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        store.pause(lane.lane_id, bookmark="Mid-work", next_steps=["Continue"])
        assert not store.has_active()
        assert lane.status == LaneStatus.PAUSED

        store.resume(lane.lane_id)
        assert store.has_active()
        assert lane.status == LaneStatus.ACTIVE

    def test_cannot_activate_without_pausing_current(self):
        """Test that activating a lane requires pausing current first."""
        store = LaneStore()
        lane1 = store.create(kind=LaneKind.WRITING, goal="Lane 1")
        lane2 = store.create(kind=LaneKind.FINANCE, goal="Lane 2")

        # Try to activate lane2 without pausing lane1
        with pytest.raises(ValueError, match="is active"):
            store.activate(lane2.lane_id)

    def test_complete_lane(self):
        """Test lane completion."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        store.complete(lane.lane_id, "Done")
        assert lane.status == LaneStatus.COMPLETED
        assert not store.has_active()

    def test_paused_lane_limit(self):
        """Test that paused lane limit is enforced."""
        store = LaneStore()
        store.MAX_PAUSED_LANES = 2  # Lower for test

        # Create and pause lanes up to limit
        store.create(kind=LaneKind.WRITING, goal="Lane 1")
        store.pause(store.get_active().lane_id, bookmark="b1")  # paused: 1

        store.create(kind=LaneKind.FINANCE, goal="Lane 2")
        store.pause(store.get_active().lane_id, bookmark="b2")  # paused: 2

        # Next creation should fail (2 paused lanes = at limit)
        with pytest.raises(ValueError, match="paused lanes"):
            store.create(kind=LaneKind.RESEARCH, goal="Lane 3")

    def test_budget_check(self):
        """Test budget enforcement."""
        store = LaneStore()
        lane = store.create(
            kind=LaneKind.WRITING,
            goal="Test",
            budgets=LaneBudgets(max_tool_requests_per_turn=2),
        )

        assert store.check_budget(lane.lane_id, 2) is True
        assert store.check_budget(lane.lane_id, 3) is False

    def test_expired_lease_detection(self):
        """Test expired lease detection."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test", expires_hours=0)
        # Manually expire
        lane.lease.expires_at_utc = datetime.utcnow() - timedelta(hours=1)

        expired = store.check_expired_leases()
        assert len(expired) == 1
        assert expired[0].lane_id == lane.lane_id

    def test_renew_lease(self):
        """Test lease renewal."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test", expires_hours=1)
        old_expires = lane.lease.expires_at_utc

        store.renew_lease(lane.lane_id, expires_hours=4)
        assert lane.lease.expires_at_utc > old_expires

    def test_get_lane_context(self):
        """Test lane context for tagging."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        ctx = store.get_lane_context()
        assert ctx['lane_id'] == lane.lane_id
        assert ctx['budgets'] is not None
        assert ctx['lease_goal'] == "Test"

    def test_remove_completed_lane(self):
        """Test removing completed lanes."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")
        store.complete(lane.lane_id)

        assert store.remove(lane.lane_id) is True
        assert store.get(lane.lane_id) is None


class TestWorkDeclarationGate:
    """Tests for WorkDeclarationGate."""

    def test_generate_prompt(self):
        """Test gate prompt generation."""
        gate = WorkDeclarationGate(
            detected_kind=LaneKind.WRITING,
            detected_goal="Write spec document",
        )

        prompt = gate.generate_prompt()
        assert "Write spec document" in prompt['message']
        assert len(prompt['options']) > 0
        assert prompt['defaults']['kind'] == LaneKind.WRITING

    def test_execute_create(self):
        """Test creating new lane via gate."""
        store = LaneStore()
        gate = WorkDeclarationGate(
            detected_kind=LaneKind.WRITING,
            detected_goal="Test",
        )

        result = gate.execute(store, {'type': 'create', 'kind': LaneKind.WRITING, 'goal': 'Test'})

        assert result.approved
        assert result.decision == 'create'
        assert result.lane_id is not None
        assert store.get(result.lane_id) is not None

    def test_execute_resume(self):
        """Test resuming paused lane via gate."""
        store = LaneStore()

        # Create and pause a lane
        lane = store.create(kind=LaneKind.WRITING, goal="Existing work")
        store.pause(lane.lane_id, bookmark="Was here")

        # Gate to resume
        gate = WorkDeclarationGate(detected_kind=LaneKind.WRITING)
        result = gate.execute(store, {'type': 'resume', 'lane_id': lane.lane_id})

        assert result.approved
        assert result.decision == 'resume'
        assert 'present_bookmark' in result.obligations
        assert result.metadata['bookmark'] == "Was here"


class TestLaneSwitchGate:
    """Tests for LaneSwitchGate."""

    def test_generate_prompt_recommends_defer_in_flow(self):
        """Test that flow=true recommends defer."""
        gate = LaneSwitchGate(
            current_lane_id="lane_1",
            interrupt_goal="Check email",
            emotional_signals={'flow': 'true'},
        )

        prompt = gate.generate_prompt(None)
        assert prompt['recommendation'] == 'defer'
        assert any('defer' in opt['label'].lower() and 'recommended' in opt['label'].lower()
                   for opt in prompt['options'])

    def test_generate_prompt_recommends_switch_on_critical(self):
        """Test that urgency=critical recommends switch."""
        gate = LaneSwitchGate(
            current_lane_id="lane_1",
            interrupt_goal="Emergency",
            interrupt_urgency="critical",
        )

        prompt = gate.generate_prompt(None)
        assert prompt['recommendation'] == 'switch'

    def test_execute_defer(self):
        """Test defer decision."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        gate = LaneSwitchGate(
            current_lane_id=lane.lane_id,
            interrupt_goal="Check something",
        )

        result = gate.execute(store, {'decision': LaneSwitchDecision.DEFER})

        assert result.approved
        assert result.decision == 'defer'
        assert result.lane_id == lane.lane_id
        assert 'schedule_deferred' in result.obligations

    def test_execute_micro_check(self):
        """Test micro-check decision."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        gate = LaneSwitchGate(
            current_lane_id=lane.lane_id,
            is_micro_check_eligible=True,
        )

        result = gate.execute(store, {'decision': LaneSwitchDecision.MICRO_CHECK})

        assert result.approved
        assert result.decision == 'micro_check'
        assert 'enforce_read_only' in result.obligations
        assert 'time_limit_60s' in result.obligations

    def test_execute_switch_requires_bookmark(self):
        """Test that switching requires bookmark."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        gate = LaneSwitchGate(
            current_lane_id=lane.lane_id,
            interrupt_kind=LaneKind.FINANCE,
        )

        # Without bookmark should fail
        result = gate.execute(store, {'decision': LaneSwitchDecision.SWITCH, 'create_new': True})
        assert not result.approved
        assert 'Bookmark required' in result.metadata.get('error', '')

    def test_execute_switch_with_bookmark(self):
        """Test successful switch with bookmark."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        gate = LaneSwitchGate(
            current_lane_id=lane.lane_id,
            interrupt_kind=LaneKind.FINANCE,
            interrupt_goal="Check budget",
        )

        result = gate.execute(
            store,
            {'decision': LaneSwitchDecision.SWITCH, 'create_new': True},
            bookmark="Pausing writing work",
            next_steps=["Continue from here"],
        )

        assert result.approved
        assert result.decision == 'switch_create'
        assert result.lane_id != lane.lane_id  # New lane created

        # Old lane should be paused
        assert lane.status == LaneStatus.PAUSED
        assert lane.snapshot.bookmark == "Pausing writing work"


class TestEvaluationGate:
    """Tests for EvaluationGate."""

    def test_generate_prompt(self):
        """Test evaluation gate prompt."""
        gate = EvaluationGate(
            lane_id="lane_1",
            current_goal="Write docs",
            expired_at=datetime.utcnow(),
        )

        lane = Lane.create(kind=LaneKind.WRITING, goal="Write docs")
        prompt = gate.generate_prompt(lane)

        assert "Write docs" in prompt['message']
        assert "expired" in prompt['message']
        assert any(opt['type'] == 'renew' for opt in prompt['options'])
        assert any(opt['type'] == 'complete' for opt in prompt['options'])

    def test_execute_renew(self):
        """Test lease renewal via gate."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")
        old_expires = lane.lease.expires_at_utc

        gate = EvaluationGate(
            lane_id=lane.lane_id,
            current_goal="Test",
            expired_at=datetime.utcnow(),
        )

        result = gate.execute(store, {'type': 'renew', 'hours': 4})

        assert result.approved
        assert result.decision == 'renew'
        assert lane.lease.expires_at_utc > old_expires

    def test_execute_complete(self):
        """Test lane completion via gate."""
        store = LaneStore()
        lane = store.create(kind=LaneKind.WRITING, goal="Test")

        gate = EvaluationGate(
            lane_id=lane.lane_id,
            current_goal="Test",
            expired_at=datetime.utcnow(),
        )

        result = gate.execute(store, {'type': 'complete'}, final_summary="All done")

        assert result.approved
        assert result.decision == 'complete'
        assert lane.status == LaneStatus.COMPLETED


class TestIntegration:
    """Integration tests for lanes subsystem."""

    def test_writing_lane_finance_interrupt_flow(self):
        """Test: writing lane active, finance interrupt triggers LaneSwitchGate."""
        store = LaneStore()

        # Start writing lane
        writing_lane = store.create(kind=LaneKind.WRITING, goal="Document writing")
        assert store.get_active() == writing_lane

        # Finance interrupt arrives
        gate = LaneSwitchGate(
            current_lane_id=writing_lane.lane_id,
            current_kind=LaneKind.WRITING,
            interrupt_kind=LaneKind.FINANCE,
            interrupt_goal="Review invoice",
            interrupt_urgency="elevated",
        )

        # User chooses to switch
        result = gate.execute(
            store,
            {'decision': LaneSwitchDecision.SWITCH, 'create_new': True},
            bookmark="Stopped at section 3",
            next_steps=["Complete section 3", "Review section 2"],
        )

        assert result.approved

        # Verify state
        assert writing_lane.status == LaneStatus.PAUSED
        assert writing_lane.snapshot.bookmark == "Stopped at section 3"

        finance_lane = store.get_active()
        assert finance_lane.kind == LaneKind.FINANCE
        assert finance_lane.lease.goal == "Review invoice"

    def test_resume_restores_bookmark(self):
        """Test: resume restores bookmark and continues."""
        store = LaneStore()

        # Create, work, pause
        lane = store.create(kind=LaneKind.RESEARCH, goal="Market research")
        store.pause(
            lane.lane_id,
            bookmark="Analyzing competitor X",
            next_steps=["Compare pricing", "Check features"],
            open_questions=["What's their market share?"],
        )

        # Resume via WorkDeclarationGate
        gate = WorkDeclarationGate(detected_kind=LaneKind.RESEARCH)
        result = gate.execute(store, {'type': 'resume', 'lane_id': lane.lane_id})

        assert result.approved
        assert result.decision == 'resume'
        assert 'present_bookmark' in result.obligations
        assert result.metadata['bookmark'] == "Analyzing competitor X"
        assert result.metadata['next_steps'] == ["Compare pricing", "Check features"]

        # Lane should be active again
        assert lane.status == LaneStatus.ACTIVE
        assert store.get_active() == lane
