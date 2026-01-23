"""Tests for locked_system.core.orchestrator module.

Tests cover:
- Reducer implementations
- Orchestrator execution
- Validation (inlined firewall)
- Convenience functions
"""

import pytest
from datetime import datetime

from locked_system.core.types import (
    AgentOutput, HRMError, ErrorCode, ReducerType, Stance,
)
from locked_system.core.orchestrator import (
    ExecutionContext, OrchestratorResult,
    Reducer, PassThroughReducer, MergeReducer, VotingReducer, SynthesisReducer,
    get_reducer, Orchestrator,
    run_pipeline, run_parallel, run_voting,
)


class TestReducers:
    """Tests for Reducer implementations."""

    def test_pass_through_reducer(self):
        """Test PassThroughReducer returns last output content."""
        reducer = PassThroughReducer()
        outputs = [
            AgentOutput(agent_id="a1", output_type="data", content="first"),
            AgentOutput(agent_id="a2", output_type="data", content="second"),
            AgentOutput(agent_id="a3", output_type="data", content="third"),
        ]

        result = reducer.reduce(outputs)
        assert result == "third"

    def test_pass_through_empty(self):
        """Test PassThroughReducer handles empty list."""
        reducer = PassThroughReducer()
        result = reducer.reduce([])
        assert result is None

    def test_merge_reducer_concatenate(self):
        """Test MergeReducer concatenates outputs."""
        reducer = MergeReducer(strategy="concatenate")
        outputs = [
            AgentOutput(agent_id="a1", output_type="data", content="Part A"),
            AgentOutput(agent_id="a2", output_type="data", content="Part B"),
        ]

        result = reducer.reduce(outputs)
        assert result == ["Part A", "Part B"]

    def test_merge_reducer_dedupe(self):
        """Test MergeReducer deduplicates outputs."""
        reducer = MergeReducer(strategy="dedupe")
        outputs = [
            AgentOutput(agent_id="a1", output_type="data", content="Same"),
            AgentOutput(agent_id="a2", output_type="data", content="Same"),
            AgentOutput(agent_id="a3", output_type="data", content="Different"),
        ]

        result = reducer.reduce(outputs)
        assert len(result) == 2
        assert "Same" in result
        assert "Different" in result

    def test_voting_reducer_winner(self):
        """Test VotingReducer selects winner."""
        reducer = VotingReducer(threshold=0.5)
        outputs = [
            AgentOutput(agent_id="a1", output_type="proposal", content="Option A"),
            AgentOutput(agent_id="a2", output_type="proposal", content="Option A"),
            AgentOutput(agent_id="a3", output_type="proposal", content="Option B"),
        ]

        result = reducer.reduce(outputs)
        assert result == "Option A"

    def test_voting_reducer_tiebreaker_first(self):
        """Test VotingReducer tiebreaker returns first."""
        reducer = VotingReducer(threshold=0.8, tiebreaker="first")
        outputs = [
            AgentOutput(agent_id="a1", output_type="proposal", content="A"),
            AgentOutput(agent_id="a2", output_type="proposal", content="B"),
        ]

        # No consensus (50% each < 80% threshold), returns first
        result = reducer.reduce(outputs)
        assert result == "A"

    def test_voting_reducer_empty_raises(self):
        """Test VotingReducer raises on empty."""
        reducer = VotingReducer()
        with pytest.raises(HRMError):
            reducer.reduce([])

    def test_synthesis_reducer(self):
        """Test SynthesisReducer calls synthesize function."""
        def synth_fn(outputs):
            return f"Synthesized {len(outputs)} outputs"

        reducer = SynthesisReducer(lead_agent="lead", synthesize_fn=synth_fn)
        outputs = [
            AgentOutput(agent_id="a1", output_type="data", content="Point 1"),
            AgentOutput(agent_id="a2", output_type="data", content="Point 2"),
        ]

        result = reducer.reduce(outputs)
        assert result == "Synthesized 2 outputs"

    def test_get_reducer_factory(self):
        """Test get_reducer factory function."""
        assert isinstance(get_reducer(ReducerType.PASS_THROUGH), PassThroughReducer)
        assert isinstance(get_reducer(ReducerType.MERGE), MergeReducer)
        assert isinstance(get_reducer(ReducerType.VOTE), VotingReducer)
        assert isinstance(get_reducer(ReducerType.SYNTHESIZE), SynthesisReducer)

    def test_get_reducer_with_config(self):
        """Test get_reducer with config."""
        reducer = get_reducer(ReducerType.VOTE, {"threshold": 0.8})
        assert isinstance(reducer, VotingReducer)
        assert reducer.threshold == 0.8

    def test_get_reducer_unknown_raises(self):
        """Test get_reducer raises on unknown type."""
        with pytest.raises(ValueError):
            get_reducer("unknown")


class TestExecutionContext:
    """Tests for ExecutionContext."""

    def test_creation(self):
        """Test ExecutionContext creation."""
        context = ExecutionContext(
            problem_id="prob_1",
            commitment_id="cmt_1",
            stance=Stance.EXECUTION,
            reducer=ReducerType.PASS_THROUGH,
            user_input="test input"
        )

        assert context.problem_id == "prob_1"
        assert context.commitment_id == "cmt_1"
        assert context.stance == Stance.EXECUTION
        assert context.reducer == ReducerType.PASS_THROUGH
        assert context.user_input == "test input"

    def test_default_values(self):
        """Test ExecutionContext default values."""
        context = ExecutionContext(
            problem_id="prob_1",
            commitment_id=None,
            stance=Stance.SENSEMAKING,
            reducer=ReducerType.MERGE
        )

        assert context.reducer_config == {}
        assert context.user_input == ""
        assert context.previous_output is None


class TestOrchestratorResult:
    """Tests for OrchestratorResult."""

    def test_success_result(self):
        """Test successful result."""
        result = OrchestratorResult(success=True, result="output data")

        assert result.success is True
        assert result.result == "output data"
        assert result.error is None

    def test_failure_result(self):
        """Test failure result."""
        error = HRMError.agent_violation("Test error")
        result = OrchestratorResult(success=False, error=error)

        assert result.success is False
        assert result.error == error


class TestOrchestrator:
    """Tests for Orchestrator class."""

    def _make_mock_runner(self, results=None):
        """Create a mock agent runner."""
        call_count = [0]
        results = results or []

        def mock_runner(agent_id, context):
            idx = call_count[0]
            call_count[0] += 1
            if idx < len(results):
                return results[idx]
            return AgentOutput(
                agent_id=agent_id,
                output_type="data",
                content=f"result_{idx}"
            )

        return mock_runner, call_count

    def test_execute_serial(self):
        """Test serial execution."""
        mock_runner, call_count = self._make_mock_runner()
        orchestrator = Orchestrator(agent_runner=mock_runner)

        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.PASS_THROUGH
        )

        result = orchestrator.execute(
            agents=["a1", "a2"],
            reducer=PassThroughReducer(),
            context=context,
            parallel=False
        )

        assert result.success is True
        assert call_count[0] == 2

    def test_execute_parallel(self):
        """Test parallel execution."""
        mock_runner, call_count = self._make_mock_runner()
        orchestrator = Orchestrator(agent_runner=mock_runner)

        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.MERGE
        )

        result = orchestrator.execute(
            agents=["a1", "a2", "a3"],
            reducer=MergeReducer(),
            context=context,
            parallel=True
        )

        assert result.success is True
        assert call_count[0] == 3

    def test_validation_rejects_decisions(self):
        """Test inlined firewall rejects agent decisions."""
        def bad_runner(agent_id, context):
            return AgentOutput(
                agent_id=agent_id,
                output_type="proposal",
                content="DECISION: I have decided to do X"
            )

        orchestrator = Orchestrator(agent_runner=bad_runner)

        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.PASS_THROUGH
        )

        result = orchestrator.execute(
            agents=["bad_agent"],
            reducer=PassThroughReducer(),
            context=context
        )

        assert result.success is False
        assert result.error is not None
        assert result.error.code == ErrorCode.AGENT_VIOLATION

    def test_validation_accepts_proposals(self):
        """Test validation accepts valid proposals."""
        def good_runner(agent_id, context):
            return AgentOutput(
                agent_id=agent_id,
                output_type="proposal",
                content="I suggest we consider X"
            )

        orchestrator = Orchestrator(agent_runner=good_runner)

        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.PASS_THROUGH
        )

        result = orchestrator.execute(
            agents=["good_agent"],
            reducer=PassThroughReducer(),
            context=context
        )

        assert result.success is True

    def test_serial_passes_previous_output(self):
        """Test serial execution passes previous output to next agent."""
        received_contexts = []

        def tracking_runner(agent_id, context):
            received_contexts.append(context)
            return AgentOutput(
                agent_id=agent_id,
                output_type="data",
                content=f"output_from_{agent_id}"
            )

        orchestrator = Orchestrator(agent_runner=tracking_runner)

        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.PASS_THROUGH
        )

        orchestrator.execute(
            agents=["step1", "step2", "step3"],
            reducer=PassThroughReducer(),
            context=context,
            parallel=False
        )

        # First agent has no previous output
        assert received_contexts[0].previous_output is None

        # Second agent has first's output
        assert received_contexts[1].previous_output is not None
        assert received_contexts[1].previous_output.content == "output_from_step1"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def _make_orchestrator(self):
        """Create orchestrator with mock runner."""
        def mock_runner(agent_id, context):
            return AgentOutput(
                agent_id=agent_id,
                output_type="data",
                content=f"result_{agent_id}"
            )
        return Orchestrator(agent_runner=mock_runner)

    def test_run_pipeline(self):
        """Test run_pipeline function."""
        orchestrator = self._make_orchestrator()
        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.PASS_THROUGH
        )

        result = run_pipeline(orchestrator, ["step1", "step2"], context)
        assert isinstance(result, OrchestratorResult)
        assert result.success is True

    def test_run_parallel(self):
        """Test run_parallel function."""
        orchestrator = self._make_orchestrator()
        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.MERGE
        )

        result = run_parallel(orchestrator, ["w1", "w2", "w3"], context)
        assert isinstance(result, OrchestratorResult)
        assert result.success is True

    def test_run_voting(self):
        """Test run_voting function."""
        def same_answer_runner(agent_id, context):
            return AgentOutput(
                agent_id=agent_id,
                output_type="proposal",
                content="consensus_answer"
            )

        orchestrator = Orchestrator(agent_runner=same_answer_runner)
        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.VOTE
        )

        result = run_voting(orchestrator, ["v1", "v2", "v3"], context)
        assert isinstance(result, OrchestratorResult)
        assert result.success is True
        assert result.result == "consensus_answer"


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator."""

    def test_full_pipeline_flow(self):
        """Test complete pipeline execution."""
        results = []

        def accumulating_runner(agent_id, context):
            n = len(results) + 1
            output = AgentOutput(
                agent_id=agent_id,
                output_type="data",
                content=f"Step {n} complete"
            )
            results.append(output)
            return output

        orchestrator = Orchestrator(agent_runner=accumulating_runner)

        context = ExecutionContext(
            problem_id="pipeline_test",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.PASS_THROUGH,
            user_input="process this"
        )

        result = orchestrator.execute(
            agents=["s1", "s2", "s3"],
            reducer=PassThroughReducer(),
            context=context,
            parallel=False
        )

        assert result.success is True
        assert len(results) == 3
        assert result.result == "Step 3 complete"

    def test_error_handling(self):
        """Test error handling in orchestration."""
        def failing_runner(agent_id, context):
            raise ValueError("Agent internal error")

        orchestrator = Orchestrator(agent_runner=failing_runner)

        context = ExecutionContext(
            problem_id="p1",
            commitment_id=None,
            stance=Stance.EXECUTION,
            reducer=ReducerType.MERGE
        )

        # Parallel execution catches errors per-agent
        # Note: Need >1 agent for parallel mode (otherwise falls back to serial)
        result = orchestrator.execute(
            agents=["bad_agent1", "bad_agent2"],
            reducer=MergeReducer(),
            context=context,
            parallel=True
        )

        # Error is captured in output, not thrown
        assert result.success is True  # Continues despite error
        # Errors are captured as error outputs
        assert len(result.result) == 2
        assert all("Error:" in r for r in result.result)
