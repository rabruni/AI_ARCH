"""Tests for locked_system.core.types module.

Tests cover:
- Enum definitions and values
- HRMError creation and factory methods
- Data class instantiation and methods
- Error recovery suggestions
"""

import pytest
from datetime import datetime

from locked_system.core.types import (
    Stance, GateType, ReducerType, AltitudeLevel,
    Complexity, Stakes, ConflictLevel, BlastRadius,
    ErrorCode, HRMError, recover_from_error,
    TurnInput, Event, Commitment, WriteSignals,
    AgentOutput, InputClassification, AltitudeClassification,
)


class TestEnums:
    """Tests for enum definitions."""

    def test_stance_values(self):
        """Test Stance enum values."""
        assert Stance.SENSEMAKING.value == "sensemaking"
        assert Stance.DISCOVERY.value == "discovery"
        assert Stance.EXECUTION.value == "execution"
        assert Stance.EVALUATION.value == "evaluation"
        assert len(Stance) == 4

    def test_gate_type_values(self):
        """Test GateType enum values."""
        assert GateType.FRAMING.value == "framing"
        assert GateType.COMMITMENT.value == "commitment"
        assert GateType.EVALUATION.value == "evaluation"
        assert GateType.EMERGENCY.value == "emergency"
        assert len(GateType) == 6

    def test_reducer_type_values(self):
        """Test ReducerType enum values."""
        assert ReducerType.PASS_THROUGH.value == "pass_through"
        assert ReducerType.MERGE.value == "merge"
        assert ReducerType.VOTE.value == "vote"
        assert ReducerType.SYNTHESIZE.value == "synthesize"
        assert len(ReducerType) == 4

    def test_altitude_level_values(self):
        """Test AltitudeLevel enum values."""
        assert AltitudeLevel.L4_IDENTITY.value == "identity"
        assert AltitudeLevel.L3_STRATEGY.value == "strategy"
        assert AltitudeLevel.L2_OPERATIONS.value == "operations"
        assert AltitudeLevel.L1_MOMENT.value == "moment"

    def test_error_code_categories(self):
        """Test ErrorCode categories exist."""
        # Gate errors
        assert ErrorCode.GATE_DENIED
        assert ErrorCode.STANCE_VIOLATION
        # Write errors
        assert ErrorCode.WRITE_DENIED
        assert ErrorCode.CONFLICT_DETECTED
        # Agent errors
        assert ErrorCode.AGENT_VIOLATION
        assert ErrorCode.AGENT_TIMEOUT
        # LLM errors
        assert ErrorCode.RATE_LIMIT
        assert ErrorCode.TOKEN_LIMIT


class TestHRMError:
    """Tests for HRMError exception class."""

    def test_basic_creation(self):
        """Test basic HRMError creation."""
        error = HRMError(
            code=ErrorCode.GATE_DENIED,
            message="Test message",
            recoverable=True
        )
        assert error.code == ErrorCode.GATE_DENIED
        assert error.message == "Test message"
        assert error.recoverable is True
        assert "[gate_denied] Test message" in str(error)

    def test_gate_denied_factory(self):
        """Test gate_denied factory method."""
        error = HRMError.gate_denied("commitment", "No active commitment")
        assert error.code == ErrorCode.GATE_DENIED
        assert "No active commitment" in error.message
        assert error.context["gate"] == "commitment"
        assert error.recoverable is True

    def test_stance_violation_factory(self):
        """Test stance_violation factory method."""
        error = HRMError.stance_violation("sensemaking", "execute")
        assert error.code == ErrorCode.STANCE_VIOLATION
        assert "execute" in error.message
        assert "sensemaking" in error.message
        assert error.context["stance"] == "sensemaking"
        assert error.context["action"] == "execute"

    def test_write_denied_factory(self):
        """Test write_denied factory method."""
        error = HRMError.write_denied("semantic", "Low source quality")
        assert error.code == ErrorCode.WRITE_DENIED
        assert error.context["target"] == "semantic"

    def test_agent_violation_factory(self):
        """Test agent_violation factory method."""
        error = HRMError.agent_violation("Agent tried to make decision")
        assert error.code == ErrorCode.AGENT_VIOLATION
        assert error.recoverable is False

    def test_rate_limit_factory(self):
        """Test rate_limit factory method."""
        error = HRMError.rate_limit(5000)
        assert error.code == ErrorCode.RATE_LIMIT
        assert error.retry_after_ms == 5000
        assert error.recoverable is True

    def test_provider_error_factory(self):
        """Test provider_error factory method."""
        error = HRMError.provider_error(503, "Service unavailable")
        assert error.code == ErrorCode.PROVIDER_ERROR
        assert error.recoverable is True  # 5xx are recoverable
        assert error.context["status_code"] == 503

        error2 = HRMError.provider_error(400, "Bad request")
        assert error2.recoverable is False  # 4xx are not recoverable

    def test_error_is_exception(self):
        """Test that HRMError can be raised as exception."""
        with pytest.raises(HRMError) as exc_info:
            raise HRMError.gate_denied("test", "Test error")
        assert exc_info.value.code == ErrorCode.GATE_DENIED


class TestRecoverFromError:
    """Tests for recover_from_error function."""

    def test_unrecoverable_error(self):
        """Test unrecoverable error returns abort."""
        error = HRMError.agent_violation("Bad agent")
        recovery = recover_from_error(error)
        assert recovery["action"] == "abort"

    def test_rate_limit_recovery(self):
        """Test rate limit suggests retry with delay."""
        error = HRMError.rate_limit(3000)
        recovery = recover_from_error(error)
        assert recovery["action"] == "retry"
        assert recovery["delay_ms"] == 3000

    def test_gate_denied_recovery(self):
        """Test gate denied suggests fallback."""
        error = HRMError.gate_denied("commitment", "No commitment")
        recovery = recover_from_error(error)
        assert recovery["action"] == "fallback"

    def test_escalation_recovery(self):
        """Test escalation required suggests escalate."""
        error = HRMError(
            code=ErrorCode.ESCALATION_REQUIRED,
            message="Need higher authority"
        )
        recovery = recover_from_error(error)
        assert recovery["action"] == "escalate"


class TestTurnInput:
    """Tests for TurnInput data class."""

    def test_creation(self):
        """Test TurnInput creation."""
        turn = TurnInput(
            user_input="Hello",
            session_id="sess_123",
            turn_number=1
        )
        assert turn.user_input == "Hello"
        assert turn.session_id == "sess_123"
        assert turn.turn_number == 1
        assert isinstance(turn.timestamp, datetime)
        assert turn.metadata == {}


class TestEvent:
    """Tests for Event data class."""

    def test_create_factory(self):
        """Test Event.create factory method."""
        event = Event.create(
            event_type="test_event",
            payload={"key": "value"},
            problem_id="prob_1"
        )
        assert event.id.startswith("evt_")
        assert event.event_type == "test_event"
        assert event.payload == {"key": "value"}
        assert event.problem_id == "prob_1"
        assert isinstance(event.timestamp, datetime)


class TestCommitment:
    """Tests for Commitment data class."""

    def test_is_active(self):
        """Test is_active method."""
        commitment = Commitment(
            id="cmt_1",
            problem_id="prob_1",
            description="Test",
            turns_remaining=5,
            turns_total=10,
            created_at=datetime.now()
        )
        assert commitment.is_active() is True

        commitment.turns_remaining = 0
        assert commitment.is_active() is False

        commitment.turns_remaining = 5
        commitment.status = "completed"
        assert commitment.is_active() is False

    def test_tick(self):
        """Test tick method decrements turns."""
        commitment = Commitment(
            id="cmt_1",
            problem_id="prob_1",
            description="Test",
            turns_remaining=3,
            turns_total=5,
            created_at=datetime.now()
        )

        assert commitment.tick() is True  # 3 -> 2
        assert commitment.turns_remaining == 2

        assert commitment.tick() is True  # 2 -> 1
        assert commitment.tick() is False  # 1 -> 0, no longer active
        assert commitment.turns_remaining == 0


class TestWriteSignals:
    """Tests for WriteSignals data class."""

    def test_creation(self):
        """Test WriteSignals creation."""
        signals = WriteSignals(
            progress_delta=0.5,
            conflict_level=ConflictLevel.LOW,
            source_quality=0.8,
            alignment_score=0.7,
            blast_radius=BlastRadius.LOCAL
        )
        assert signals.progress_delta == 0.5
        assert signals.conflict_level == ConflictLevel.LOW
        assert signals.blast_radius == BlastRadius.LOCAL


class TestAgentOutput:
    """Tests for AgentOutput data class."""

    def test_contains_decision(self):
        """Test contains_decision detection."""
        output1 = AgentOutput(
            agent_id="agent_1",
            output_type="proposal",
            content="I suggest we..."
        )
        assert output1.contains_decision() is False

        output2 = AgentOutput(
            agent_id="agent_1",
            output_type="proposal",
            content="DECISION: We will do X"
        )
        assert output2.contains_decision() is True

    def test_is_valid_packet(self):
        """Test is_valid_packet validation."""
        valid = AgentOutput(
            agent_id="agent_1",
            output_type="proposal",
            content="Test"
        )
        assert valid.is_valid_packet() is True

        invalid = AgentOutput(
            agent_id="",
            output_type="proposal",
            content="Test"
        )
        assert invalid.is_valid_packet() is False

        invalid2 = AgentOutput(
            agent_id="agent_1",
            output_type="invalid_type",
            content="Test"
        )
        assert invalid2.is_valid_packet() is False


class TestInputClassification:
    """Tests for InputClassification data class."""

    def test_should_escalate_complexity(self):
        """Test escalation trigger on complexity."""
        classification = InputClassification(
            complexity=Complexity.COMPLEX,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near"
        )
        assert classification.should_escalate() is True

    def test_should_escalate_uncertainty(self):
        """Test escalation trigger on high uncertainty."""
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.8,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near"
        )
        assert classification.should_escalate() is True

    def test_should_escalate_conflict(self):
        """Test escalation trigger on conflict."""
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.HIGH,
            stakes=Stakes.LOW,
            horizon="near"
        )
        assert classification.should_escalate() is True

    def test_should_escalate_stakes(self):
        """Test escalation trigger on high stakes."""
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.HIGH,
            horizon="near"
        )
        assert classification.should_escalate() is True

    def test_no_escalation_simple_case(self):
        """Test no escalation for simple cases."""
        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near"
        )
        assert classification.should_escalate() is False
