"""Sensing - Perception Layer.

Components:
- Perception: User state sensor
- Contrast: Gap detection between inferred need and observed behavior
"""
from locked_system.sensing.perception import PerceptionSensor
from locked_system.sensing.contrast import ContrastDetector

__all__ = ['PerceptionSensor', 'ContrastDetector']
