"""Personality module for The Assist.

This module contains the personality layer that makes The Assist unique.
It provides prompt injection, greeting customization, and behavioral traits
that work with the locked_system framework.
"""
from the_assist.personality.injector import (
    create_prompt_enhancer,
    load_personality_prompt,
    PersonalityConfig,
)

__all__ = [
    "create_prompt_enhancer",
    "load_personality_prompt",
    "PersonalityConfig",
]
