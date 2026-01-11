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


# Default greeting for The Assist (Donna/Pepper style)
DEFAULT_INTRO_GREETING = (
    "Hey! I'm your Assist - think of me as a cognitive partner, not just a task manager. "
    "I'm here to help you think, remember what matters, and challenge you when needed. "
    "We'll build trust over time. First though - what would you like me to call you?"
)

DEFAULT_CONNECT_PROMPT = (
    "What are two things you're really into right now? "
    "Could be projects, hobbies, ideas - whatever's got your attention."
)


def get_personality_defaults() -> dict:
    """Get default personality configuration values."""
    return {
        "intro_greeting": DEFAULT_INTRO_GREETING,
        "connect_prompt": DEFAULT_CONNECT_PROMPT,
    }
