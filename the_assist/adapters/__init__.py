"""Adapters module for The Assist.

This module provides adapters that bridge The Assist's unique models
(Intent, Altitude) with the locked_system framework models (Commitment, HRM).
"""
from the_assist.adapters.intent_to_commitment import (
    intent_to_commitment,
    intent_to_behavioral_constraints,
    map_stance_to_locked_stance,
)

__all__ = [
    "intent_to_commitment",
    "intent_to_behavioral_constraints",
    "map_stance_to_locked_stance",
]
