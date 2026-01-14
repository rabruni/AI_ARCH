"""MapReduce Orchestrator - Single execution engine for all agent orchestration.

Simplification: 4 orchestration modes → Map + Reduce pattern.

All modes become:
- Pipeline:     Map(serial) + PassThroughReducer
- Parallel:     Map(parallel) + MergeReducer
- Voting:       Map(parallel) + VotingReducer
- Hierarchical: Planning step → Map(parallel) + SynthesisReducer

Benefits:
- One timeout implementation
- One cancellation implementation
- One retry strategy
- One test suite
"""
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional
from datetime import datetime

from locked_system.core.types import (
    AgentOutput,
    HRMError,
    ReducerType,
    Stance,
)


# ─────────────────────────────────────────────────────────────
# Execution Context
# ─────────────────────────────────────────────────────────────

@dataclass
class ExecutionContext:
    """Context for agent execution."""
    problem_id: str
    commitment_id: Optional[str]
    stance: Stance
    reducer: ReducerType
    reducer_config: dict = field(default_factory=dict)
    user_input: str = ""
    previous_output: Optional[AgentOutput] = None


@dataclass
class OrchestratorResult:
    """Result from orchestration."""
    success: bool
    result: Optional[Any] = None
    error: Optional[HRMError] = None
    agents_invoked: List[str] = field(default_factory=list)
    duration_ms: int = 0


# ─────────────────────────────────────────────────────────────
# Reducers
# ─────────────────────────────────────────────────────────────

class Reducer(ABC):
    """Base class for reducers."""

    @abstractmethod
    def reduce(self, outputs: List[AgentOutput]) -> Any:
        """Reduce multiple outputs to one result."""
        pass


class PassThroughReducer(Reducer):
    """For pipeline mode: return last output."""

    def reduce(self, outputs: List[AgentOutput]) -> Any:
        return outputs[-1].content if outputs else None


class MergeReducer(Reducer):
    """For parallel mode: merge all outputs."""

    def __init__(self, strategy: str = "concatenate"):
        self.strategy = strategy  # concatenate | dedupe | select_best

    def reduce(self, outputs: List[AgentOutput]) -> Any:
        if not outputs:
            return []

        if self.strategy == "concatenate":
            return [o.content for o in outputs]

        elif self.strategy == "dedupe":
            seen = set()
            result = []
            for o in outputs:
                key = str(o.content)
                if key not in seen:
                    seen.add(key)
                    result.append(o.content)
            return result

        elif self.strategy == "select_best":
            return max(outputs, key=lambda o: o.metadata.get("confidence", 0)).content

        return [o.content for o in outputs]


class VotingReducer(Reducer):
    """For voting mode: tally votes and select winner."""

    def __init__(self, threshold: float = 0.6, tiebreaker: str = "first"):
        self.threshold = threshold
        self.tiebreaker = tiebreaker  # first | escalate

    def reduce(self, outputs: List[AgentOutput]) -> Any:
        if not outputs:
            raise HRMError.gate_denied("voting", "No outputs to vote on")

        # Count votes
        votes: dict[str, int] = {}
        for o in outputs:
            key = str(o.content)
            votes[key] = votes.get(key, 0) + 1

        # Find winner
        total = len(outputs)
        for answer, count in sorted(votes.items(), key=lambda x: -x[1]):
            if count / total >= self.threshold:
                return answer

        # No consensus
        if self.tiebreaker == "first":
            return outputs[0].content
        else:
            raise HRMError.gate_denied("voting", "No consensus reached, escalation required")


class SynthesisReducer(Reducer):
    """For hierarchical mode: synthesize outputs using LLM."""

    def __init__(self, lead_agent: str, synthesize_fn: Callable[[List[AgentOutput]], str]):
        self.lead_agent = lead_agent
        self.synthesize_fn = synthesize_fn

    def reduce(self, outputs: List[AgentOutput]) -> Any:
        return self.synthesize_fn(outputs)


def get_reducer(reducer_type: ReducerType, config: dict = None) -> Reducer:
    """Factory for reducers."""
    config = config or {}

    if reducer_type == ReducerType.PASS_THROUGH:
        return PassThroughReducer()

    elif reducer_type == ReducerType.MERGE:
        return MergeReducer(strategy=config.get("strategy", "concatenate"))

    elif reducer_type == ReducerType.VOTE:
        return VotingReducer(
            threshold=config.get("threshold", 0.6),
            tiebreaker=config.get("tiebreaker", "first")
        )

    elif reducer_type == ReducerType.SYNTHESIZE:
        # Synthesis requires a callable - use default if not provided
        def default_synthesize(outputs: List[AgentOutput]) -> str:
            return "\n\n".join(str(o.content) for o in outputs)

        return SynthesisReducer(
            lead_agent=config.get("lead", "default"),
            synthesize_fn=config.get("synthesize_fn", default_synthesize)
        )

    raise ValueError(f"Unknown reducer type: {reducer_type}")


# ─────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────

class Orchestrator:
    """
    Single execution engine for all agent orchestration.

    Uses MapReduce pattern:
    1. Map: Run agents (parallel or serial)
    2. Validate: Check each output (inlined firewall)
    3. Reduce: Combine outputs using reducer
    """

    def __init__(
        self,
        agent_runner: Callable[[str, ExecutionContext], AgentOutput],
        timeout_ms: int = 30000,
        max_workers: int = 4
    ):
        """
        Args:
            agent_runner: Function that runs an agent and returns AgentOutput
            timeout_ms: Timeout for parallel execution
            max_workers: Max parallel workers
        """
        self.agent_runner = agent_runner
        self.timeout_ms = timeout_ms
        self.max_workers = max_workers

    def execute(
        self,
        agents: List[str],
        reducer: Reducer,
        context: ExecutionContext,
        parallel: bool = True
    ) -> OrchestratorResult:
        """
        Execute agents using MapReduce pattern.

        Args:
            agents: List of agent IDs to run
            reducer: How to combine outputs
            context: Execution context
            parallel: Run agents in parallel (True) or serial (False)

        Returns:
            OrchestratorResult with combined output
        """
        start = datetime.now()

        try:
            # Map phase: run all agents
            outputs = self._map(agents, context, parallel)

            # Validate phase: check each output (inlined firewall)
            validated = [self._validate(o) for o in outputs]

            # Reduce phase: combine outputs
            result = reducer.reduce(validated)

            duration = int((datetime.now() - start).total_seconds() * 1000)

            return OrchestratorResult(
                success=True,
                result=result,
                agents_invoked=agents,
                duration_ms=duration
            )

        except HRMError as e:
            duration = int((datetime.now() - start).total_seconds() * 1000)
            return OrchestratorResult(
                success=False,
                error=e,
                agents_invoked=agents,
                duration_ms=duration
            )

    def _map(
        self,
        agents: List[str],
        context: ExecutionContext,
        parallel: bool
    ) -> List[AgentOutput]:
        """Run agents (parallel or serial)."""
        if parallel and len(agents) > 1:
            return self._map_parallel(agents, context)
        else:
            return self._map_serial(agents, context)

    def _map_parallel(
        self,
        agents: List[str],
        context: ExecutionContext
    ) -> List[AgentOutput]:
        """Run agents in parallel with timeout."""
        outputs = []

        with ThreadPoolExecutor(max_workers=min(len(agents), self.max_workers)) as executor:
            futures = {
                executor.submit(self.agent_runner, agent, context): agent
                for agent in agents
            }

            try:
                for future in as_completed(futures, timeout=self.timeout_ms / 1000):
                    agent_id = futures[future]
                    try:
                        output = future.result()
                        outputs.append(output)
                    except Exception as e:
                        # Create error output for failed agent
                        outputs.append(AgentOutput(
                            agent_id=agent_id,
                            output_type="data",
                            content=f"Error: {e}",
                            metadata={"error": True}
                        ))
            except TimeoutError:
                # Partial results on timeout
                raise HRMError(
                    code=HRMError.ErrorCode.AGENT_TIMEOUT if hasattr(HRMError, 'ErrorCode') else "agent_timeout",
                    message=f"Timeout after {self.timeout_ms}ms",
                    recoverable=True,
                    context={"completed": len(outputs), "total": len(agents)}
                )

        return outputs

    def _map_serial(
        self,
        agents: List[str],
        context: ExecutionContext
    ) -> List[AgentOutput]:
        """Run agents serially, each gets previous output."""
        outputs = []
        current_context = context

        for agent in agents:
            output = self.agent_runner(agent, current_context)
            outputs.append(output)

            # Update context with previous output for pipeline
            current_context = ExecutionContext(
                problem_id=context.problem_id,
                commitment_id=context.commitment_id,
                stance=context.stance,
                reducer=context.reducer,
                reducer_config=context.reducer_config,
                user_input=context.user_input,
                previous_output=output
            )

        return outputs

    def _validate(self, output: AgentOutput) -> AgentOutput:
        """
        Validate agent output (inlined firewall).

        Rules:
        1. Agents cannot make decisions (only proposals)
        2. Valid output packet structure
        """
        if output.contains_decision():
            raise HRMError.agent_violation("Agents cannot make decisions, only proposals")

        if not output.is_valid_packet():
            raise HRMError.agent_violation(f"Invalid output from agent {output.agent_id}")

        return output


# ─────────────────────────────────────────────────────────────
# Convenience functions
# ─────────────────────────────────────────────────────────────

def run_pipeline(
    orchestrator: Orchestrator,
    agents: List[str],
    context: ExecutionContext
) -> OrchestratorResult:
    """Run agents in pipeline (serial, pass-through)."""
    return orchestrator.execute(
        agents=agents,
        reducer=PassThroughReducer(),
        context=context,
        parallel=False
    )


def run_parallel(
    orchestrator: Orchestrator,
    agents: List[str],
    context: ExecutionContext,
    merge_strategy: str = "concatenate"
) -> OrchestratorResult:
    """Run agents in parallel and merge results."""
    return orchestrator.execute(
        agents=agents,
        reducer=MergeReducer(strategy=merge_strategy),
        context=context,
        parallel=True
    )


def run_voting(
    orchestrator: Orchestrator,
    agents: List[str],
    context: ExecutionContext,
    threshold: float = 0.6
) -> OrchestratorResult:
    """Run agents in parallel and vote on result."""
    return orchestrator.execute(
        agents=agents,
        reducer=VotingReducer(threshold=threshold),
        context=context,
        parallel=True
    )
