from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AltitudeRoute:
    altitude: str | None
    clarification: str | None = None


def detect_altitude(text: str) -> AltitudeRoute:
    lowered = text.strip().lower()
    if not lowered:
        return AltitudeRoute("UNCLEAR", "Clarify the target altitude (L4/L3/L2/L1).")

    if any(word in lowered for word in ("vision", "north star", "mission", "strategy")):
        return AltitudeRoute("L4")
    if any(word in lowered for word in ("roadmap", "architecture", "approach")):
        return AltitudeRoute("L3")
    if any(word in lowered for word in ("plan", "steps", "sequence")):
        return AltitudeRoute("L2")
    if any(word in lowered for word in ("implement", "code", "fix", "patch", "debug")):
        return AltitudeRoute("L1")

    return AltitudeRoute("UNCLEAR", "Clarify the target altitude (L4/L3/L2/L1).")
