"""State Machine for Shaper v2.

Modes: IDLE, SHAPING, REVEALED, FROZEN

Transitions:
- IDLE → SHAPING upon first ingest
- SHAPING → REVEALED on reveal
- REVEALED → SHAPING if any edit occurs (invalidates reveal)
- REVEALED → FROZEN on freeze (if all required fields present)
- FROZEN → IDLE after reset
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Union

from .models import ShaperModel, SpecModel


MODES = ("IDLE", "SHAPING", "REVEALED", "FROZEN")

# L3 phases for phase confirmation
L3_PHASES = ["objective", "scope", "plan", "acceptance"]

# L4 phases for phase confirmation
L4_PHASES = ["overview", "problem", "non_goals", "phases", "success_criteria"]


@dataclass
class ShaperStateMachine:
    """State machine managing the shaping lifecycle.

    Enforces:
    - Reveal required before freeze
    - Freeze blocked if required fields missing
    - Edit after reveal invalidates reveal
    - L4 phases must be confirmed before freeze
    - Single active model instance
    """

    mode: str = "IDLE"
    phases_confirmed: Dict[str, bool] = field(default_factory=dict)
    _revealed: bool = False
    _altitude: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"Invalid mode: {self.mode}")

    @property
    def is_idle(self) -> bool:
        return self.mode == "IDLE"

    @property
    def is_shaping(self) -> bool:
        return self.mode == "SHAPING"

    @property
    def is_revealed(self) -> bool:
        return self.mode == "REVEALED"

    @property
    def is_frozen(self) -> bool:
        return self.mode == "FROZEN"

    def start_shaping(self, altitude: str) -> None:
        """Transition from IDLE to SHAPING.

        Args:
            altitude: "L3" or "L4"

        Raises:
            ValueError: If not in IDLE mode or invalid altitude.
        """
        if self.mode != "IDLE":
            # Allow re-start if already shaping same altitude
            if self.mode == "SHAPING" and self._altitude == altitude:
                return
            if self.mode != "SHAPING":
                raise ValueError(f"Cannot start shaping from {self.mode} mode.")

        if altitude not in ("L3", "L4"):
            raise ValueError(f"Invalid altitude: {altitude}")

        self._altitude = altitude
        self.mode = "SHAPING"
        self._revealed = False

        # Initialize phase confirmation based on altitude
        if altitude == "L3":
            self.phases_confirmed = {phase: False for phase in L3_PHASES}
        else:
            self.phases_confirmed = {phase: False for phase in L4_PHASES}

    def confirm_phase(self, phase: str) -> None:
        """Confirm a phase has been reviewed/provided.

        Args:
            phase: Phase name to confirm.

        Raises:
            ValueError: If phase is unknown for current altitude.
        """
        if phase not in self.phases_confirmed:
            raise ValueError(f"Unknown phase: {phase}")
        self.phases_confirmed[phase] = True

    def on_edit(self) -> None:
        """Handle edit event - invalidates reveal if in REVEALED mode."""
        if self.mode == "REVEALED":
            self.mode = "SHAPING"
            self._revealed = False

    def reveal(self) -> None:
        """Transition to REVEALED mode.

        Raises:
            ValueError: If not in SHAPING mode.
        """
        if self.mode not in ("SHAPING", "REVEALED"):
            raise ValueError(f"Cannot reveal from {self.mode} mode.")

        self.mode = "REVEALED"
        self._revealed = True

    def can_freeze(self, model: Union[ShaperModel, SpecModel]) -> bool:
        """Check if freeze is allowed.

        Args:
            model: The model to check for completeness.

        Returns:
            True if freeze is allowed.
        """
        # Must be revealed
        if not self._revealed:
            return False

        # Must have no missing required fields
        if model.missing_sections():
            return False

        # L4 requires phases_confirmed
        if self._altitude == "L4":
            if isinstance(model, SpecModel) and not model.phases_confirmed:
                return False

        return True

    def freeze(self, model: Union[ShaperModel, SpecModel]) -> None:
        """Transition to FROZEN mode.

        Args:
            model: The model to freeze.

        Raises:
            ValueError: If freeze conditions not met.
        """
        if not self._revealed:
            raise ValueError("Reveal required before freeze.")

        missing = model.missing_sections()
        if missing:
            raise ValueError(f"Cannot freeze. Missing: {', '.join(missing)}")

        if self._altitude == "L4":
            if isinstance(model, SpecModel) and not model.phases_confirmed:
                raise ValueError("L4 phases must be confirmed before freeze.")

        self.mode = "FROZEN"

    def reset(self) -> None:
        """Reset state machine for new session."""
        self.mode = "IDLE"
        self.phases_confirmed.clear()
        self._revealed = False
        self._altitude = None


class ShaperSession:
    """Complete shaping session managing model and state machine together.

    Ensures single active model instance and coordinated state.
    """

    def __init__(self) -> None:
        self.state_machine = ShaperStateMachine()
        self._model: Union[ShaperModel, SpecModel, None] = None

    @property
    def model(self) -> Union[ShaperModel, SpecModel, None]:
        return self._model

    @property
    def altitude(self) -> str | None:
        return self.state_machine._altitude

    def start(self, altitude: str) -> None:
        """Start a new shaping session.

        Args:
            altitude: "L3" or "L4"
        """
        if self._model is not None:
            raise ValueError("Session already active. Call reset() first.")

        self.state_machine.start_shaping(altitude)

        if altitude == "L3":
            self._model = ShaperModel()
        else:
            self._model = SpecModel()

    def ingest(self, text: str) -> None:
        """Ingest input into the active model.

        Triggers edit event on state machine.
        """
        if self._model is None:
            raise ValueError("No active session. Call start() first.")

        self.state_machine.on_edit()
        self._model.ingest(text)

    def reveal(self) -> None:
        """Reveal current state."""
        self._model.revealed_once = True
        self.state_machine.reveal()

    def can_freeze(self) -> bool:
        """Check if session can be frozen."""
        if self._model is None:
            return False
        return self.state_machine.can_freeze(self._model)

    def freeze(self) -> None:
        """Freeze the session."""
        if self._model is None:
            raise ValueError("No active session.")
        self.state_machine.freeze(self._model)

    def reset(self) -> None:
        """Reset session for new shaping."""
        if self._model is not None:
            self._model.reset()
        self._model = None
        self.state_machine.reset()
