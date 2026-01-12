"""Locked System Configuration.

This module defines all configurable parameters for the Locked System.
Configuration can be:
1. Instantiated with defaults: Config()
2. Loaded from YAML: Config.from_yaml("config.yaml")
3. Customized inline: Config(model="claude-opus-4-20250514", default_lease_turns=30)

All paths are relative to the current working directory unless absolute.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class Config:
    """
    System configuration for the Locked System.

    Attributes:
        model: Primary model for response generation.
            Used by Executor for main responses.
            Default: "claude-sonnet-4-20250514"

        perception_model: Model for perception sensing.
            Can be lighter-weight than main model.
            Default: "claude-sonnet-4-20250514"

        max_tokens: Maximum tokens for response generation.
            Actual response may be shorter based on HRM altitude.
            Default: 2000

        memory_dir: Base directory for all memory persistence.
            Creates subdirectories: slow/, fast/, bridge/, history/
            Default: "./memory"

        system_prompt: Path to system prompt file or prompt string.
            If Path, reads content from file. If str, uses directly.
            Default: None (generic behavior)

        slow_memory_path: Full path to slow memory file.
            Derived from memory_dir. Contains commitments, decisions.

        emergency_cooldown_turns: Minimum turns between emergency gates.
            Prevents abuse of emergency escape hatch.
            Emergency gate is intentionally costly.
            Default: 3

        proposal_priority_order: Priority for processing proposals.
            First in list = highest priority. Used when multiple
            proposals arrive in same turn.
            Default: user_signal > decay_manager > perception > continuous_eval > task_agent

        default_lease_turns: Default commitment duration in turns.
            Commitments expire after this many turns unless renewed.
            Can be overridden per-commitment.
            Default: 20
    """

    # Model settings
    model: str = "claude-sonnet-4-20250514"
    perception_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2000

    # Memory paths
    memory_dir: Path = field(default_factory=lambda: Path("./memory"))

    # Pluggable personality/prompt settings
    # Default: use the locked_system data-plane prompt
    system_prompt: Optional[Path | str] = field(
        default_factory=lambda: Path(__file__).parent / "prompts" / "system.md"
    )

    # Emergency settings
    emergency_cooldown_turns: int = 3

    # Proposal processing priority (first = highest priority)
    proposal_priority_order: list = field(default_factory=lambda: [
        "user_signal",      # Explicit user requests (highest)
        "decay_manager",    # Commitment expiry signals
        "perception",       # User state observations
        "continuous_eval",  # Quality concerns
        "task_agent"        # Child task proposals (lowest)
    ])

    # Lease defaults
    default_lease_turns: int = 20

    @property
    def slow_memory_path(self) -> Path:
        """Path to slow memory persistence file."""
        return self.memory_dir / "slow" / "slow_memory.json"

    @property
    def fast_memory_path(self) -> Path:
        """Path to fast memory persistence file."""
        return self.memory_dir / "fast" / "fast_memory.json"

    @property
    def bridge_memory_path(self) -> Path:
        """Path to bridge memory persistence file."""
        return self.memory_dir / "bridge" / "artifacts.json"

    @property
    def history_path(self) -> Path:
        """Path to history persistence file."""
        return self.memory_dir / "history" / "history.json"

    @property
    def api_key(self) -> Optional[str]:
        """Anthropic API key from environment."""
        return os.environ.get("ANTHROPIC_API_KEY")

    def get_system_prompt_content(self) -> Optional[str]:
        """Get system prompt content (loads from file if Path)."""
        if self.system_prompt is None:
            return None
        if isinstance(self.system_prompt, Path):
            if self.system_prompt.exists():
                return self.system_prompt.read_text()
            return None
        return self.system_prompt  # Already a string

    def __post_init__(self):
        """Initialize directories after dataclass creation."""
        self.memory_dir = Path(self.memory_dir)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create memory directories if they don't exist."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        (self.memory_dir / "slow").mkdir(exist_ok=True)
        (self.memory_dir / "fast").mkdir(exist_ok=True)
        (self.memory_dir / "bridge").mkdir(exist_ok=True)
        (self.memory_dir / "history").mkdir(exist_ok=True)

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """
        Load configuration from YAML file.

        Requires PyYAML: pip install pyyaml

        Example YAML:
        ```yaml
        model: claude-opus-4-20250514
        max_tokens: 4000
        memory_dir: /data/locked_system/memory
        default_lease_turns: 30
        emergency_cooldown_turns: 5
        ```

        Args:
            path: Path to YAML configuration file

        Returns:
            Config instance with loaded values

        Raises:
            ImportError: If PyYAML is not installed
        """
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML required for YAML config. Install with: pip install pyyaml")

        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}

        # Convert memory_dir to Path if present
        if 'memory_dir' in data:
            data['memory_dir'] = Path(data['memory_dir'])

        return cls(**data)

    def to_yaml(self, path: str):
        """
        Save configuration to YAML file.

        Requires PyYAML: pip install pyyaml

        Args:
            path: Path to save YAML configuration

        Raises:
            ImportError: If PyYAML is not installed
        """
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML required for YAML config. Install with: pip install pyyaml")

        data = {
            'model': self.model,
            'perception_model': self.perception_model,
            'max_tokens': self.max_tokens,
            'memory_dir': str(self.memory_dir),
            'system_prompt': str(self.system_prompt) if isinstance(self.system_prompt, Path) else self.system_prompt,
            'emergency_cooldown_turns': self.emergency_cooldown_turns,
            'proposal_priority_order': self.proposal_priority_order,
            'default_lease_turns': self.default_lease_turns,
        }
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def validate(self) -> list[str]:
        """
        Validate configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.max_tokens < 100:
            errors.append("max_tokens should be at least 100")

        if self.default_lease_turns < 1:
            errors.append("default_lease_turns must be positive")

        if self.emergency_cooldown_turns < 1:
            errors.append("emergency_cooldown_turns must be positive")

        if not self.proposal_priority_order:
            errors.append("proposal_priority_order cannot be empty")

        return errors
