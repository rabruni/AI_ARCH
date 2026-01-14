"""Focus HRM - Governance layer for attention and execution.

Simplification: FocusState unifies ProblemRegistry + Commitment.
Single object for arbiter to consult.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional

from locked_system.core.types import (
    Commitment,
    GateType,
    HRMError,
    Stance,
)
from locked_system.core.trace import EpisodicTrace


# ─────────────────────────────────────────────────────────────
# Focus State (unified registry + commitment)
# ─────────────────────────────────────────────────────────────

@dataclass
class QueuedProblem:
    """A problem waiting in queue."""
    problem_id: str
    description: str
    priority: int  # 1-10 (10 = highest)
    queued_at: datetime
    staleness: float = 0.0  # Increases over time


@dataclass
class FocusState:
    """
    Unified state for Focus HRM.

    Owns:
    - active_problem_id
    - commitment (optional)
    - stance
    - queue of candidate problems
    - progress tracking
    """
    stance: Stance = Stance.SENSEMAKING
    active_problem_id: Optional[str] = None
    commitment: Optional[Commitment] = None
    queue: List[QueuedProblem] = field(default_factory=list)
    last_progress: Dict[str, datetime] = field(default_factory=dict)

    def has_commitment(self) -> bool:
        return self.commitment is not None and self.commitment.is_active()

    def get_staleness(self, problem_id: str) -> float:
        """Get staleness score (0-1) for a problem."""
        if problem_id not in self.last_progress:
            return 0.0
        elapsed = (datetime.now() - self.last_progress[problem_id]).total_seconds()
        # 1 hour = 0.5 staleness, 2 hours = max
        return min(1.0, elapsed / 7200)

    def mark_progress(self, problem_id: str = None):
        """Mark progress on a problem."""
        pid = problem_id or self.active_problem_id
        if pid:
            self.last_progress[pid] = datetime.now()

    def switch(self, problem_id: str, description: str = ""):
        """Switch to a different problem."""
        # Queue current if active
        if self.active_problem_id and self.active_problem_id != problem_id:
            self.queue_problem(self.active_problem_id, "Switched away", priority=5)
        self.active_problem_id = problem_id
        self.mark_progress(problem_id)

    def queue_problem(self, problem_id: str, description: str, priority: int = 5):
        """Add problem to queue."""
        # Remove if already queued
        self.queue = [q for q in self.queue if q.problem_id != problem_id]
        self.queue.append(QueuedProblem(
            problem_id=problem_id,
            description=description,
            priority=priority,
            queued_at=datetime.now()
        ))

    def dequeue_next(self) -> Optional[QueuedProblem]:
        """Get next problem from queue (highest priority, then oldest)."""
        if not self.queue:
            return None
        # Sort by priority (desc), then queued_at (asc)
        self.queue.sort(key=lambda q: (-q.priority, q.queued_at))
        return self.queue.pop(0)

    def commit(
        self,
        problem_id: str,
        description: str,
        turns: int = 20
    ) -> Commitment:
        """Create a commitment to a problem."""
        import uuid
        self.commitment = Commitment(
            id=f"cmt_{uuid.uuid4().hex[:8]}",
            problem_id=problem_id,
            description=description,
            turns_remaining=turns,
            turns_total=turns,
            created_at=datetime.now()
        )
        self.active_problem_id = problem_id
        return self.commitment

    def tick(self) -> bool:
        """Decrement commitment turn counter. Returns True if still committed."""
        if self.commitment:
            return self.commitment.tick()
        return False

    def release(self, status: str = "completed"):
        """Release commitment."""
        if self.commitment:
            self.commitment.status = status
        self.commitment = None


# ─────────────────────────────────────────────────────────────
# Stance Machine (with trace integration)
# ─────────────────────────────────────────────────────────────

class StanceMachine:
    """
    4-state exclusive stance machine.

    Transitions only at gates.
    Logs all transitions to trace.
    """

    VALID_TRANSITIONS = {
        GateType.FRAMING: {
            Stance.SENSEMAKING: [Stance.SENSEMAKING, Stance.DISCOVERY],
            Stance.DISCOVERY: [Stance.SENSEMAKING, Stance.DISCOVERY],
            Stance.EXECUTION: [Stance.SENSEMAKING, Stance.DISCOVERY],
            Stance.EVALUATION: [Stance.SENSEMAKING, Stance.DISCOVERY],
        },
        GateType.COMMITMENT: {
            Stance.SENSEMAKING: [Stance.EXECUTION],
            Stance.DISCOVERY: [Stance.EXECUTION],
            Stance.EXECUTION: [Stance.EXECUTION],
            Stance.EVALUATION: [Stance.EXECUTION],
        },
        GateType.EVALUATION: {
            Stance.SENSEMAKING: [Stance.EVALUATION],
            Stance.DISCOVERY: [Stance.EVALUATION],
            Stance.EXECUTION: [Stance.EVALUATION],
            Stance.EVALUATION: [Stance.SENSEMAKING, Stance.EXECUTION],
        },
        GateType.EMERGENCY: {
            Stance.SENSEMAKING: [Stance.SENSEMAKING],
            Stance.DISCOVERY: [Stance.SENSEMAKING],
            Stance.EXECUTION: [Stance.SENSEMAKING],
            Stance.EVALUATION: [Stance.SENSEMAKING],
        },
    }

    def __init__(self, initial: Stance = Stance.SENSEMAKING, trace: EpisodicTrace = None):
        self._current = initial
        self.trace = trace

    @property
    def current(self) -> Stance:
        return self._current

    def can_transition(self, to_stance: Stance, gate: GateType) -> bool:
        valid = self.VALID_TRANSITIONS.get(gate, {}).get(self._current, [])
        return to_stance in valid

    def transition(self, to_stance: Stance, gate: GateType, reason: str) -> bool:
        """Attempt stance transition. Returns success."""
        if not self.can_transition(to_stance, gate):
            return False

        from_stance = self._current
        self._current = to_stance

        # Log to trace
        if self.trace:
            self.trace.log_stance_change(
                from_stance=from_stance.value,
                to_stance=to_stance.value,
                via_gate=gate.value
            )

        return True

    def force_sensemaking(self, reason: str):
        """Force transition to sensemaking (emergency)."""
        self.transition(Stance.SENSEMAKING, GateType.EMERGENCY, reason)

    def get_allowed_actions(self) -> List[str]:
        """Return actions allowed in current stance."""
        actions = {
            Stance.SENSEMAKING: ["question", "clarify", "explore", "reframe"],
            Stance.DISCOVERY: ["brainstorm", "prototype", "experiment", "diverge"],
            Stance.EXECUTION: ["execute", "deliver", "implement", "progress"],
            Stance.EVALUATION: ["assess", "compare", "measure", "decide"],
        }
        return actions[self._current]


# ─────────────────────────────────────────────────────────────
# Gate Controller
# ─────────────────────────────────────────────────────────────

class GateController:
    """Enforces checkpoints for state changes."""

    def __init__(self, trace: EpisodicTrace = None):
        self.evaluators: Dict[GateType, Callable] = {}
        self.trace = trace
        self._register_defaults()

    def _register_defaults(self):
        """Register default gate evaluators."""
        self.evaluators[GateType.FRAMING] = self._eval_framing
        self.evaluators[GateType.COMMITMENT] = self._eval_commitment
        self.evaluators[GateType.EVALUATION] = self._eval_evaluation
        self.evaluators[GateType.EMERGENCY] = self._eval_emergency
        self.evaluators[GateType.WRITE_APPROVAL] = self._eval_write
        self.evaluators[GateType.AGENT_APPROVAL] = self._eval_agent

    def attempt(self, gate: GateType, context: dict) -> bool:
        """Try to pass through a gate. Returns True if approved."""
        evaluator = self.evaluators.get(gate)
        if not evaluator:
            return False

        approved = evaluator(context)

        # Log to trace
        if self.trace:
            self.trace.log(
                event_type="gate_attempt",
                payload={
                    "gate": gate.value,
                    "approved": approved,
                    "context_keys": list(context.keys())
                }
            )

        return approved

    def register(self, gate: GateType, evaluator: Callable):
        """Register custom gate evaluator."""
        self.evaluators[gate] = evaluator

    # Default evaluators
    def _eval_framing(self, context: dict) -> bool:
        """Framing gate: allows reframing/exploration."""
        return True  # Usually allowed

    def _eval_commitment(self, context: dict) -> bool:
        """Commitment gate: requires problem and description."""
        return bool(context.get("problem_id") and context.get("description"))

    def _eval_evaluation(self, context: dict) -> bool:
        """Evaluation gate: requires something to evaluate."""
        return bool(context.get("result") or context.get("commitment"))

    def _eval_emergency(self, context: dict) -> bool:
        """Emergency gate: always allowed."""
        return True

    def _eval_write(self, context: dict) -> bool:
        """Write approval gate: requires signals."""
        signals = context.get("signals")
        return signals is not None

    def _eval_agent(self, context: dict) -> bool:
        """Agent approval gate: requires proposal."""
        return bool(context.get("proposal"))


# ─────────────────────────────────────────────────────────────
# Focus HRM (unified)
# ─────────────────────────────────────────────────────────────

class FocusHRM:
    """
    Focus HRM - Governance layer.

    Manages:
    - Stance transitions
    - Commitments
    - Gate approvals
    - Problem queue
    """

    def __init__(self, trace: EpisodicTrace = None):
        self.trace = trace
        self.state = FocusState()
        self.stance_machine = StanceMachine(trace=trace)
        self.gate_controller = GateController(trace=trace)

    @property
    def current_stance(self) -> Stance:
        return self.stance_machine.current

    @property
    def has_commitment(self) -> bool:
        return self.state.has_commitment()

    def attempt_stance_transition(
        self,
        to_stance: Stance,
        gate: GateType,
        reason: str
    ) -> bool:
        """Attempt stance transition through a gate."""
        if not self.gate_controller.attempt(gate, {"reason": reason}):
            return False
        return self.stance_machine.transition(to_stance, gate, reason)

    def create_commitment(
        self,
        problem_id: str,
        description: str,
        turns: int = 20
    ) -> Optional[Commitment]:
        """Create a commitment (requires commitment gate)."""
        context = {"problem_id": problem_id, "description": description}
        if not self.gate_controller.attempt(GateType.COMMITMENT, context):
            return None

        commitment = self.state.commit(problem_id, description, turns)

        # Transition to execution
        self.stance_machine.transition(
            Stance.EXECUTION,
            GateType.COMMITMENT,
            f"Committed to: {description}"
        )

        return commitment

    def tick(self) -> bool:
        """Tick commitment counter. Returns True if still committed."""
        still_active = self.state.tick()
        self.state.mark_progress()
        return still_active

    def release_commitment(self, status: str = "completed"):
        """Release current commitment."""
        self.state.release(status)

    def switch_problem(self, problem_id: str, description: str = ""):
        """Switch to a different problem."""
        self.state.switch(problem_id, description)

    def queue_problem(self, problem_id: str, description: str, priority: int = 5):
        """Queue a problem for later."""
        self.state.queue_problem(problem_id, description, priority)

    def get_allowed_actions(self) -> List[str]:
        """Get actions allowed in current stance."""
        return self.stance_machine.get_allowed_actions()

    def validate_action(self, action: str) -> bool:
        """Check if action is allowed in current stance."""
        allowed = self.get_allowed_actions()
        return action in allowed
