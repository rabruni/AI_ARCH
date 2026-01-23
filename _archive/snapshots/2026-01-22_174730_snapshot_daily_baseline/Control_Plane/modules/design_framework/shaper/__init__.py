"""Shaper v2: Artifact-first, deterministic shaping system.

Operates at two altitudes:
- L3: WORK_ITEM (implementation contract)
- L4: SPEC (product/architecture spec)
"""

from .models import ShaperModel, SpecModel
from .router import detect_altitude, AltitudeRoute
from .state_machine import ShaperStateMachine, MODES
from .renderers import render_work_item, render_spec
from .context_builder import ContextWindow, build_context_window
from .output_safety import resolve_output_path, write_output

__all__ = [
    "ShaperModel",
    "SpecModel",
    "detect_altitude",
    "AltitudeRoute",
    "ShaperStateMachine",
    "MODES",
    "render_work_item",
    "render_spec",
    "ContextWindow",
    "build_context_window",
    "resolve_output_path",
    "write_output",
]
