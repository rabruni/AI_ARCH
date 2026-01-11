"""Locked System Configuration"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """System configuration."""

    # Model settings
    model: str = "claude-sonnet-4-20250514"
    perception_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2000

    # Memory paths
    memory_dir: Path = field(default_factory=lambda: Path("./memory"))

    # Bootstrap settings
    bootstrap_soft_timeout_turns: int = 10

    # Emergency settings
    emergency_cooldown_turns: int = 3

    # Proposal processing
    proposal_priority_order: list = field(default_factory=lambda: [
        "user_signal",
        "decay_manager",
        "perception",
        "continuous_eval",
        "task_agent"
    ])

    # Lease defaults
    default_lease_turns: int = 20

    # API key (from environment)
    @property
    def api_key(self) -> Optional[str]:
        return os.environ.get("ANTHROPIC_API_KEY")

    def __post_init__(self):
        self.memory_dir = Path(self.memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        (self.memory_dir / "slow").mkdir(exist_ok=True)
        (self.memory_dir / "fast").mkdir(exist_ok=True)
        (self.memory_dir / "bridge").mkdir(exist_ok=True)
        (self.memory_dir / "history").mkdir(exist_ok=True)
