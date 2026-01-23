from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


MODES = ("IDLE", "SHAPING", "REVEALED", "FROZEN")


@dataclass
class ShaperStateMachine:
    phases: List[str] = field(default_factory=lambda: ["objective", "scope", "plan", "acceptance"])
    mode: str = "IDLE"
    phases_confirmed: Dict[str, bool] = field(default_factory=dict)
    revealed_once: bool = False

    def start_shaping(self) -> None:
        if self.mode == "IDLE":
            self.mode = "SHAPING"

    def reveal(self) -> None:
        self.revealed_once = True
        self.mode = "REVEALED"

    def converge(self) -> None:
        if not self.revealed_once:
            raise ValueError("Reveal required before converge.")
        self.mode = "REVEALED"

    def confirm_phase(self, phase: str) -> None:
        if phase not in self.phases:
            raise ValueError(f"Unknown phase: {phase}")
        self.phases_confirmed[phase] = True

    def can_freeze(self, altitude: str | None) -> bool:
        if not self.revealed_once:
            return False
        normalized = (altitude or "").strip().upper()
        if normalized == "L4":
            return all(self.phases_confirmed.get(phase, False) for phase in self.phases)
        return True

    def freeze(self, altitude: str | None) -> None:
        if not self.can_freeze(altitude):
            raise ValueError("Cannot freeze without all phases confirmed.")
        self.mode = "FROZEN"
