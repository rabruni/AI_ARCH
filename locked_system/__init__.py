"""Locked System - Two-Loop Cognitive Architecture

A system that manages commitment over time so agents don't solve the wrong
problem well, don't think forever and never deliver, and behave like
trusted partners.

Architecture:
- Slow Loop: Authority (Perception → Commitment → Stance → Gates)
- Fast Loop: Execution (HRM → Execute → Continuous Eval)
- Memory: Durable state (Slow/Fast/Bridge tiers)

Key invariant: Evaluators and sensors propose only. Never decide.
"""

from locked_system.loop import LockedLoop
from locked_system.config import Config

__all__ = ['LockedLoop', 'Config']
__version__ = '0.1.0'
