"""Personality Injector - Enhance prompts with The Assist's personality.

This module provides the personality layer that makes The Assist unique:
- Donna/Pepper cognitive partner model
- Intuition-first interaction style
- Non-sycophantic, challenging partner behavior
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class PersonalityConfig:
    """Configuration for The Assist's personality."""
    system_prompt_path: Path
    intro_greeting: Optional[str] = None
    connect_prompt: Optional[str] = None

    def __post_init__(self):
        self.system_prompt_path = Path(self.system_prompt_path)


def load_personality_prompt(config: PersonalityConfig) -> str:
    """Load the personality system prompt from file."""
    if config.system_prompt_path.exists():
        return config.system_prompt_path.read_text()
    # Fallback minimal personality
    return """You are The Assist - a cognitive partner focused on helping the user think clearly.
Be genuine, direct, and occasionally challenge assumptions. Not sycophantic."""


def create_prompt_enhancer(
    config: PersonalityConfig
) -> Callable[[str], str]:
    """
    Create a prompt enhancer function that injects personality.

    The returned function takes a base prompt and returns it enhanced
    with The Assist's personality context.

    Args:
        config: PersonalityConfig with system prompt path

    Returns:
        Callable that enhances prompts with personality
    """
    personality = load_personality_prompt(config)

    def enhance_prompt(base_prompt: str) -> str:
        """Enhance a prompt with The Assist's personality."""
        if not base_prompt:
            return personality

        # Personality goes first, then the specific instruction
        return f"{personality}\n\n---\n\n{base_prompt}"

    return enhance_prompt
