"""Stance Machine - Exclusive stance state machine.

Four stances (2x2 matrix):
                Accuracy        Momentum
Exploration     Sensemaking     Discovery
Exploitation    Evaluation      Execution

Only one stance active at a time.
Transitions only at gates.
"""
from enum import Enum
from typing import Optional, Literal
from dataclasses import dataclass


class Stance(Enum):
    """The four stances."""
    SENSEMAKING = "sensemaking"   # Exploration + Accuracy
    DISCOVERY = "discovery"       # Exploration + Momentum
    EXECUTION = "execution"       # Exploitation + Momentum
    EVALUATION = "evaluation"     # Exploitation + Accuracy

    @property
    def is_exploration(self) -> bool:
        return self in (Stance.SENSEMAKING, Stance.DISCOVERY)

    @property
    def is_exploitation(self) -> bool:
        return self in (Stance.EXECUTION, Stance.EVALUATION)

    @property
    def is_accuracy(self) -> bool:
        return self in (Stance.SENSEMAKING, Stance.EVALUATION)

    @property
    def is_momentum(self) -> bool:
        return self in (Stance.DISCOVERY, Stance.EXECUTION)


@dataclass
class StanceTransition:
    """A stance transition record."""
    from_stance: Stance
    to_stance: Stance
    gate: str
    reason: str


class StanceMachine:
    """
    Stance state machine.

    Enforces exclusive stance and valid transitions.
    """

    # Valid transitions by gate
    VALID_TRANSITIONS = {
        "framing": {
            # Framing gate allows exploration stances
            Stance.SENSEMAKING: [Stance.SENSEMAKING, Stance.DISCOVERY],
            Stance.DISCOVERY: [Stance.SENSEMAKING, Stance.DISCOVERY],
            Stance.EXECUTION: [Stance.SENSEMAKING, Stance.DISCOVERY],  # Exit execution
            Stance.EVALUATION: [Stance.SENSEMAKING, Stance.DISCOVERY],
        },
        "commitment": {
            # Commitment gate locks into execution
            Stance.SENSEMAKING: [Stance.EXECUTION],
            Stance.DISCOVERY: [Stance.EXECUTION],
            Stance.EXECUTION: [Stance.EXECUTION],  # Stay in execution
            Stance.EVALUATION: [Stance.EXECUTION],
        },
        "evaluation": {
            # Evaluation gate enters evaluation stance
            Stance.SENSEMAKING: [Stance.EVALUATION],
            Stance.DISCOVERY: [Stance.EVALUATION],
            Stance.EXECUTION: [Stance.EVALUATION],
            Stance.EVALUATION: [Stance.SENSEMAKING, Stance.EXECUTION],  # Renew or revise
        },
        "emergency": {
            # Emergency always goes to sensemaking
            Stance.SENSEMAKING: [Stance.SENSEMAKING],
            Stance.DISCOVERY: [Stance.SENSEMAKING],
            Stance.EXECUTION: [Stance.SENSEMAKING],
            Stance.EVALUATION: [Stance.SENSEMAKING],
        },
    }

    def __init__(self, initial_stance: Stance = Stance.SENSEMAKING):
        self._current = initial_stance
        self._history: list[StanceTransition] = []

    @property
    def current(self) -> Stance:
        """Get current stance."""
        return self._current

    def can_transition(self, to_stance: Stance, gate: str) -> bool:
        """Check if transition is valid."""
        valid = self.VALID_TRANSITIONS.get(gate, {}).get(self._current, [])
        return to_stance in valid

    def transition(self, to_stance: Stance, gate: str, reason: str) -> bool:
        """
        Attempt stance transition.

        Returns True if successful, False if invalid.
        """
        if not self.can_transition(to_stance, gate):
            return False

        transition = StanceTransition(
            from_stance=self._current,
            to_stance=to_stance,
            gate=gate,
            reason=reason
        )
        self._history.append(transition)
        self._current = to_stance
        return True

    def force_sensemaking(self, reason: str):
        """Force transition to sensemaking (emergency)."""
        transition = StanceTransition(
            from_stance=self._current,
            to_stance=Stance.SENSEMAKING,
            gate="emergency",
            reason=reason
        )
        self._history.append(transition)
        self._current = Stance.SENSEMAKING

    def get_history(self, n: int = 5) -> list[StanceTransition]:
        """Get recent transition history."""
        return self._history[-n:]

    def get_behavioral_constraints(self) -> dict:
        """Get behavioral constraints for current stance."""
        constraints = {
            Stance.SENSEMAKING: {
                "mode": "exploration",
                "priority": "accuracy",
                "allowed": ["question", "clarify", "explore", "reframe"],
                "suppressed": ["execute", "commit", "optimize"],
                "description": "Understanding the problem space with precision"
            },
            Stance.DISCOVERY: {
                "mode": "exploration",
                "priority": "momentum",
                "allowed": ["brainstorm", "prototype", "experiment", "diverge"],
                "suppressed": ["commit", "optimize", "evaluate"],
                "description": "Generating options and possibilities"
            },
            Stance.EXECUTION: {
                "mode": "exploitation",
                "priority": "momentum",
                "allowed": ["execute", "deliver", "implement", "progress"],
                "suppressed": ["reframe", "explore", "question_frame"],
                "description": "Delivering on commitment with focus"
            },
            Stance.EVALUATION: {
                "mode": "exploitation",
                "priority": "accuracy",
                "allowed": ["assess", "compare", "measure", "decide"],
                "suppressed": ["execute", "explore", "commit"],
                "description": "Assessing outcomes against intent"
            },
        }
        return constraints[self._current]
