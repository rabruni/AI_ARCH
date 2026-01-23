"""Tests for locked_system.core.trace module.

Tests cover:
- Event creation and serialization
- EpisodicTrace append and query
- Convenience logging methods
- Global trace management
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json

from locked_system.core.trace import (
    Event, EpisodicTrace, get_trace, set_trace,
)


class TestEvent:
    """Tests for Event data class."""

    def test_create_factory(self):
        """Test Event.create factory method."""
        event = Event.create(
            event_type="test_event",
            payload={"key": "value"},
            problem_id="prob_123"
        )

        assert event.id.startswith("evt_")
        assert len(event.id) == 16  # evt_ + 12 hex chars
        assert event.event_type == "test_event"
        assert event.payload == {"key": "value"}
        assert event.problem_id == "prob_123"
        assert isinstance(event.timestamp, datetime)

    def test_to_dict(self):
        """Test Event serialization."""
        event = Event.create(
            event_type="test",
            payload={"x": 1},
            refs=["ref_1", "ref_2"]
        )

        data = event.to_dict()
        assert data["event_type"] == "test"
        assert data["payload"] == {"x": 1}
        assert data["refs"] == ["ref_1", "ref_2"]
        assert "timestamp" in data

    def test_from_dict(self):
        """Test Event deserialization."""
        data = {
            "id": "evt_test123456",
            "event_type": "test",
            "timestamp": "2024-01-15T10:30:00",
            "payload": {"key": "value"},
            "refs": [],
            "problem_id": None,
            "session_id": "sess_1"
        }

        event = Event.from_dict(data)
        assert event.id == "evt_test123456"
        assert event.event_type == "test"
        assert event.session_id == "sess_1"

    def test_roundtrip(self):
        """Test to_dict/from_dict round-trip."""
        original = Event.create(
            event_type="roundtrip_test",
            payload={"nested": {"data": [1, 2, 3]}},
            problem_id="prob_1"
        )

        restored = Event.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.event_type == original.event_type
        assert restored.payload == original.payload
        assert restored.problem_id == original.problem_id


class TestEpisodicTrace:
    """Tests for EpisodicTrace class."""

    def test_append_event(self):
        """Test appending events."""
        trace = EpisodicTrace()
        event = Event.create("test", {"data": 1})

        event_id = trace.append(event)
        assert event_id == event.id
        assert trace.count == 1

    def test_log_convenience(self):
        """Test log convenience method."""
        trace = EpisodicTrace()

        event_id = trace.log(
            event_type="action_taken",
            payload={"action": "click"},
            problem_id="prob_1"
        )

        assert event_id.startswith("evt_")
        assert trace.count == 1

        events = trace.query(event_type="action_taken")
        assert len(events) == 1
        assert events[0].payload["action"] == "click"

    def test_session_id_auto_assigned(self):
        """Test that session_id is auto-assigned."""
        trace = EpisodicTrace(session_id="my_session")
        event = Event.create("test", {})

        trace.append(event)
        assert event.session_id == "my_session"

    def test_query_by_event_type(self):
        """Test querying by event type."""
        trace = EpisodicTrace()
        trace.log("type_a", {"n": 1})
        trace.log("type_b", {"n": 2})
        trace.log("type_a", {"n": 3})

        results = trace.query(event_type="type_a")
        assert len(results) == 2
        assert all(e.event_type == "type_a" for e in results)

    def test_query_by_problem_id(self):
        """Test querying by problem_id."""
        trace = EpisodicTrace()
        trace.log("test", {"n": 1}, problem_id="prob_1")
        trace.log("test", {"n": 2}, problem_id="prob_2")
        trace.log("test", {"n": 3}, problem_id="prob_1")

        results = trace.query(problem_id="prob_1")
        assert len(results) == 2
        assert all(e.problem_id == "prob_1" for e in results)

    def test_query_by_time_range(self):
        """Test querying by time range."""
        trace = EpisodicTrace()

        # Create events with different timestamps
        old_event = Event.create("old", {})
        old_event.timestamp = datetime.now() - timedelta(hours=2)
        trace.append(old_event)

        new_event = Event.create("new", {})
        trace.append(new_event)

        # Query for recent events only
        cutoff = datetime.now() - timedelta(hours=1)
        results = trace.query(start=cutoff)
        assert len(results) == 1
        assert results[0].event_type == "new"

    def test_query_with_limit(self):
        """Test query with limit."""
        trace = EpisodicTrace()
        for i in range(10):
            trace.log("test", {"n": i})

        results = trace.query(limit=3)
        assert len(results) == 3
        # Should return last 3
        assert results[0].payload["n"] == 7
        assert results[2].payload["n"] == 9

    def test_get_by_id(self):
        """Test getting event by ID."""
        trace = EpisodicTrace()
        event_id = trace.log("test", {"data": "found"})

        result = trace.get(event_id)
        assert result is not None
        assert result.payload["data"] == "found"

        assert trace.get("nonexistent_id") is None

    def test_get_recent(self):
        """Test get_recent method."""
        trace = EpisodicTrace()
        for i in range(20):
            trace.log("test", {"n": i})

        recent = trace.get_recent(5)
        assert len(recent) == 5
        assert recent[-1].payload["n"] == 19

    def test_since(self):
        """Test since method."""
        trace = EpisodicTrace()

        old = Event.create("old", {})
        old.timestamp = datetime.now() - timedelta(hours=1)
        trace.append(old)

        new = Event.create("new", {})
        trace.append(new)

        cutoff = datetime.now() - timedelta(minutes=30)
        results = trace.since(cutoff)
        assert len(results) == 1


class TestEpisodicTraceConvenienceMethods:
    """Tests for convenience logging methods."""

    def test_log_altitude_transition(self):
        """Test altitude transition logging."""
        trace = EpisodicTrace()
        event_id = trace.log_altitude_transition(
            from_level="L2",
            to_level="L3",
            reason="User asked strategic question"
        )

        event = trace.get(event_id)
        assert event.event_type == "altitude_transition"
        assert event.payload["from"] == "L2"
        assert event.payload["to"] == "L3"

    def test_log_stance_change(self):
        """Test stance change logging."""
        trace = EpisodicTrace()
        event_id = trace.log_stance_change(
            from_stance="sensemaking",
            to_stance="execution",
            via_gate="commitment"
        )

        event = trace.get(event_id)
        assert event.event_type == "stance_change"
        assert event.payload["via_gate"] == "commitment"

    def test_log_agent_activated(self):
        """Test agent activation logging."""
        trace = EpisodicTrace()
        event_id = trace.log_agent_activated(
            agents=["planner", "executor"],
            reducer="merge"
        )

        event = trace.get(event_id)
        assert event.event_type == "agent_activated"
        assert event.payload["agents"] == ["planner", "executor"]

    def test_log_decision(self):
        """Test decision logging."""
        trace = EpisodicTrace()
        event_id = trace.log_decision(
            decision_type="route",
            decision="delegate_to_expert",
            rationale="Complex domain question"
        )

        event = trace.get(event_id)
        assert event.event_type == "decision"
        assert event.payload["type"] == "route"

    def test_log_write(self):
        """Test write logging."""
        trace = EpisodicTrace()
        event_id = trace.log_write(
            target="semantic",
            key="pattern_123",
            approved=True
        )

        event = trace.get(event_id)
        assert event.event_type == "write_completed"
        assert event.payload["approved"] is True

    def test_log_error(self):
        """Test error logging."""
        trace = EpisodicTrace()
        event_id = trace.log_error(
            error_code="gate_denied",
            message="Commitment gate blocked",
            context={"gate": "commitment"}
        )

        event = trace.get(event_id)
        assert event.event_type == "error"
        assert event.payload["code"] == "gate_denied"

    def test_log_turn(self):
        """Test turn logging (truncates long content)."""
        trace = EpisodicTrace()
        long_input = "x" * 500

        event_id = trace.log_turn(
            turn_number=5,
            user_input=long_input,
            response_summary="Response here"
        )

        event = trace.get(event_id)
        assert event.event_type == "turn"
        assert len(event.payload["input"]) == 200  # Truncated


class TestEpisodicTracePersistence:
    """Tests for trace persistence."""

    def test_persistence_to_file(self):
        """Test that events are persisted to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trace.jsonl"

            # Create trace and add events
            trace1 = EpisodicTrace(storage_path=path, session_id="sess_1")
            trace1.log("event_1", {"data": 1})
            trace1.log("event_2", {"data": 2})

            # Verify file exists and has content
            assert path.exists()
            lines = path.read_text().strip().split("\n")
            assert len(lines) == 2

            # Create new trace from same file
            trace2 = EpisodicTrace(storage_path=path, session_id="sess_2")
            assert trace2.count == 2

    def test_load_from_existing_file(self):
        """Test loading from existing trace file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trace.jsonl"

            # Write some events manually
            events = [
                {"id": "evt_1", "event_type": "test", "timestamp": "2024-01-01T00:00:00",
                 "payload": {}, "refs": [], "problem_id": None, "session_id": "old"},
                {"id": "evt_2", "event_type": "test", "timestamp": "2024-01-01T00:01:00",
                 "payload": {}, "refs": [], "problem_id": None, "session_id": "old"},
            ]
            with open(path, 'w') as f:
                for e in events:
                    f.write(json.dumps(e) + "\n")

            # Load trace
            trace = EpisodicTrace(storage_path=path)
            assert trace.count == 2
            assert trace.get("evt_1") is not None


class TestGlobalTrace:
    """Tests for global trace management."""

    def test_get_trace_creates_default(self):
        """Test get_trace creates default instance."""
        set_trace(None)  # Reset
        trace = get_trace()
        assert trace is not None
        assert isinstance(trace, EpisodicTrace)

    def test_set_trace_replaces_global(self):
        """Test set_trace replaces global instance."""
        custom = EpisodicTrace(session_id="custom")
        set_trace(custom)

        retrieved = get_trace()
        assert retrieved.session_id == "custom"

    def test_get_trace_returns_same_instance(self):
        """Test get_trace returns same instance."""
        set_trace(None)  # Reset
        trace1 = get_trace()
        trace2 = get_trace()
        assert trace1 is trace2
