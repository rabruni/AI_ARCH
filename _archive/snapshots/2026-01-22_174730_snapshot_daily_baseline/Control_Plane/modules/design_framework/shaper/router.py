"""Altitude Router for Shaper v2.

Determines whether input should be shaped as L3 (WORK_ITEM) or L4 (SPEC).
Returns UNCLEAR when clarification is required.

Altitude is immutable after first successful ingest.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AltitudeRoute:
    """Result of altitude detection.

    Attributes:
        altitude: "L3", "L4", or "UNCLEAR"
        clarification: Prompt to show user when UNCLEAR
    """

    altitude: str
    clarification: str | None = None


# Keywords that signal L4 (spec-level) intent
L4_SIGNALS = frozenset([
    "spec",
    "specification",
    "architecture",
    "vision",
    "strategy",
    "north star",
    "mission",
    "product",
    "roadmap",
    "design doc",
    "rfc",
    "adr",
    "overview",
    "problem statement",
    "non-goals",
    "success criteria",
])

# Keywords that signal L3 (work-item-level) intent
L3_SIGNALS = frozenset([
    "work item",
    "task",
    "ticket",
    "implement",
    "fix",
    "bug",
    "feature",
    "code",
    "patch",
    "pr",
    "pull request",
    "steps",
    "plan",
    "acceptance",
    "test",
    # L3 field names (strong signal of work item intent)
    "objective",
    "scope",
])

CLARIFICATION_PROMPT = "Clarify target altitude: L3 (work item) or L4 (spec)."


def detect_altitude(text: str) -> AltitudeRoute:
    """Detect altitude from input text using keyword signals.

    Returns:
        AltitudeRoute with altitude L3, L4, or UNCLEAR.
        If UNCLEAR, clarification prompt is provided.
    """
    if not text or not text.strip():
        return AltitudeRoute("UNCLEAR", CLARIFICATION_PROMPT)

    lowered = text.strip().lower()

    # Check for explicit altitude declaration
    if "altitude: l4" in lowered or "altitude:l4" in lowered:
        return AltitudeRoute("L4")
    if "altitude: l3" in lowered or "altitude:l3" in lowered:
        return AltitudeRoute("L3")

    # Score based on keyword signals
    l4_score = sum(1 for signal in L4_SIGNALS if signal in lowered)
    l3_score = sum(1 for signal in L3_SIGNALS if signal in lowered)

    if l4_score > l3_score:
        return AltitudeRoute("L4")
    if l3_score > l4_score:
        return AltitudeRoute("L3")

    # Ambiguous - require clarification
    return AltitudeRoute("UNCLEAR", CLARIFICATION_PROMPT)


class AltitudeRouter:
    """Stateful altitude router with immutability after first ingest.

    Once altitude is set via first successful ingest, it cannot be changed
    without a full reset.
    """

    def __init__(self) -> None:
        self._altitude: str | None = None
        self._locked: bool = False

    @property
    def altitude(self) -> str | None:
        """Current locked altitude, or None if not yet determined."""
        return self._altitude

    @property
    def is_locked(self) -> bool:
        """True if altitude has been locked after first ingest."""
        return self._locked

    def detect(self, text: str) -> AltitudeRoute:
        """Detect altitude from text.

        If already locked, returns the locked altitude regardless of text.
        """
        if self._locked:
            return AltitudeRoute(self._altitude)
        return detect_altitude(text)

    def lock(self, altitude: str) -> None:
        """Lock the altitude after first successful ingest.

        Args:
            altitude: Must be "L3" or "L4".

        Raises:
            ValueError: If altitude is invalid or already locked to different value.
        """
        if altitude not in ("L3", "L4"):
            raise ValueError(f"Invalid altitude: {altitude}. Must be L3 or L4.")

        if self._locked and self._altitude != altitude:
            raise ValueError(
                f"Altitude already locked to {self._altitude}. "
                f"Cannot change to {altitude} without reset."
            )

        self._altitude = altitude
        self._locked = True

    def reset(self) -> None:
        """Reset router state for new session."""
        self._altitude = None
        self._locked = False

    def try_lock(self, text: str) -> AltitudeRoute:
        """Attempt to detect and lock altitude from text.

        Returns:
            AltitudeRoute. If UNCLEAR, altitude is not locked.
        """
        route = self.detect(text)
        if route.altitude in ("L3", "L4"):
            self.lock(route.altitude)
        return route
