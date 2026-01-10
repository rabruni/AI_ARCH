"""HRM Altitude Governance

Reusable altitude management for any HRM-based agent.

Altitude = level of abstraction in reasoning:
- L4: Identity (why we exist, values, north stars)
- L3: Strategy (priorities, projects, goals)
- L2: Operations (this week, today, tasks)
- L1: Moment (this conversation, right now)

Key principle: You cannot descend without establishing context above.

Usage by any agent:
    from hrm.altitude import AltitudeGovernor, AltitudePolicy

    # Use default policy
    governor = AltitudeGovernor()

    # Or custom policy
    policy = AltitudePolicy(
        require_context_for_descent=True,
        levels={"L4": {...}, "L3": {...}, ...}
    )
    governor = AltitudeGovernor(policy)

    # Check transitions
    governor.can_descend("L3", "L2", context)  # -> bool
    governor.validate(current, target, context)  # -> ValidationResult
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Level(Enum):
    """HRM Altitude Levels"""
    L4 = 4  # Identity
    L3 = 3  # Strategy
    L2 = 2  # Operations
    L1 = 1  # Moment

    @classmethod
    def from_str(cls, s: str) -> "Level":
        return cls[s.upper()]

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value


@dataclass
class LevelDefinition:
    """Definition of a single altitude level."""
    name: str
    description: str
    examples: list[str]
    requires_for_descent: list[str]  # What must be established to go lower
    signals: list[str]  # Keywords/phrases that indicate this level


@dataclass
class AltitudePolicy:
    """
    Configurable altitude policy for an agent.

    Agents can define their own policies or use defaults.
    """
    require_context_for_descent: bool = True  # Enforce "can't go tactical without strategic"
    allow_level_skip: bool = False  # Can you go L4 -> L2 directly?
    max_time_at_level: dict = field(default_factory=dict)  # Optional time limits
    levels: dict = field(default_factory=dict)  # Level definitions

    @classmethod
    def default(cls) -> "AltitudePolicy":
        """Default HRM altitude policy."""
        return cls(
            require_context_for_descent=True,
            allow_level_skip=False,
            levels={
                "L4": LevelDefinition(
                    name="Identity",
                    description="Why we exist. Values. North stars.",
                    examples=["What matters to you?", "What's your purpose?", "Who do you want to be?"],
                    requires_for_descent=[],  # L4 is top, no requirements
                    signals=["purpose", "values", "meaning", "identity", "north star", "who I am"]
                ),
                "L3": LevelDefinition(
                    name="Strategy",
                    description="Priorities. Projects. Goals.",
                    examples=["What are your priorities?", "What's the goal?", "What project matters?"],
                    requires_for_descent=["L4_connected"],  # Must connect to identity
                    signals=["priority", "goal", "project", "strategy", "plan", "objective"]
                ),
                "L2": LevelDefinition(
                    name="Operations",
                    description="This week. Today. Tasks.",
                    examples=["What's on your plate?", "What's due?", "What's the task?"],
                    requires_for_descent=["L3_established"],  # Must have strategic context
                    signals=["today", "this week", "task", "todo", "deadline", "meeting"]
                ),
                "L1": LevelDefinition(
                    name="Moment",
                    description="Right now. This conversation.",
                    examples=["What's on your mind?", "What just happened?", "How are you feeling?"],
                    requires_for_descent=[],  # L1 is bottom
                    signals=["right now", "just", "feeling", "moment"]
                )
            }
        )


@dataclass
class AltitudeContext:
    """
    Context for altitude decisions.

    Tracks what has been established in the conversation.
    """
    l4_connected: bool = False  # Has identity/values been discussed?
    l3_established: bool = False  # Has strategy been established?
    l2_grounded: bool = False  # Has operations context been set?
    current_level: str = "L3"  # Default starting level
    level_history: list = field(default_factory=list)  # Track transitions
    time_at_current: int = 0  # Exchanges at current level


@dataclass
class ValidationResult:
    """Result of altitude validation."""
    allowed: bool
    reason: str
    suggested_level: Optional[str] = None
    required_action: Optional[str] = None  # What to do if not allowed


class AltitudeGovernor:
    """
    Governs altitude transitions for an HRM agent.

    Reusable across any HRM-based system.
    """

    def __init__(self, policy: Optional[AltitudePolicy] = None):
        self.policy = policy or AltitudePolicy.default()
        self.context = AltitudeContext()

    def get_level(self, level_str: str) -> Level:
        """Parse level string to enum."""
        return Level.from_str(level_str)

    def detect_level(self, text: str) -> str:
        """
        Detect altitude level from text content.

        Returns the most likely level based on signals.
        """
        text_lower = text.lower()
        scores = {"L4": 0, "L3": 0, "L2": 0, "L1": 0}

        for level_key, level_def in self.policy.levels.items():
            for signal in level_def.signals:
                if signal in text_lower:
                    scores[level_key] += 1

        # Return highest scoring, default to L2
        if max(scores.values()) == 0:
            return "L2"
        return max(scores, key=scores.get)

    def can_descend(self, from_level: str, to_level: str) -> ValidationResult:
        """
        Check if descent from one level to another is allowed.

        Descent = going from higher abstraction to lower (L4 -> L3 -> L2 -> L1)
        """
        from_l = self.get_level(from_level)
        to_l = self.get_level(to_level)

        # Not a descent
        if to_l >= from_l:
            return ValidationResult(True, "Not a descent, allowed")

        # Check skip
        if not self.policy.allow_level_skip and (from_l.value - to_l.value) > 1:
            return ValidationResult(
                False,
                f"Cannot skip levels. Must go through intermediate levels.",
                suggested_level=f"L{from_l.value - 1}",
                required_action=f"Establish L{from_l.value - 1} context first"
            )

        # Check requirements
        if self.policy.require_context_for_descent:
            to_def = self.policy.levels.get(to_level)
            if to_def:
                for req in to_def.requires_for_descent:
                    if req == "L4_connected" and not self.context.l4_connected:
                        return ValidationResult(
                            False,
                            "Cannot discuss operations/tactics without connecting to identity/values",
                            suggested_level="L4",
                            required_action="First establish connection to north stars"
                        )
                    if req == "L3_established" and not self.context.l3_established:
                        return ValidationResult(
                            False,
                            "Cannot discuss tasks without strategic context",
                            suggested_level="L3",
                            required_action="First establish strategic priorities"
                        )

        return ValidationResult(True, "Descent allowed")

    def validate_transition(self, target_level: str) -> ValidationResult:
        """Validate a transition to target level from current."""
        return self.can_descend(self.context.current_level, target_level)

    def record_transition(self, new_level: str):
        """Record a level transition."""
        self.context.level_history.append({
            "from": self.context.current_level,
            "to": new_level,
            "time_at_previous": self.context.time_at_current
        })
        self.context.current_level = new_level
        self.context.time_at_current = 0

    def record_exchange(self):
        """Record an exchange at current level."""
        self.context.time_at_current += 1

    def mark_established(self, level: str):
        """Mark a level as established in context."""
        if level == "L4":
            self.context.l4_connected = True
        elif level == "L3":
            self.context.l3_established = True
        elif level == "L2":
            self.context.l2_grounded = True

    def get_context(self) -> AltitudeContext:
        """Get current altitude context."""
        return self.context

    def reset(self):
        """Reset context (e.g., new session)."""
        self.context = AltitudeContext()

    def build_prompt_injection(self) -> str:
        """
        Build prompt injection for any agent.

        Returns text to inject into agent prompts.
        """
        ctx = self.context
        lines = [
            f"ALTITUDE: Current={ctx.current_level}, Exchanges={ctx.time_at_current}",
            f"CONTEXT: L4_connected={ctx.l4_connected}, L3_established={ctx.l3_established}"
        ]

        # Add constraints
        if not ctx.l4_connected:
            lines.append("CONSTRAINT: Must connect to identity/values before tactical discussion")
        if not ctx.l3_established:
            lines.append("CONSTRAINT: Must establish strategic context before operations")

        return "\n".join(lines)

    def get_enforcement_rules(self) -> list[str]:
        """
        Get human-readable enforcement rules.

        Useful for documentation or agent prompts.
        """
        return [
            "L4 (Identity) can be discussed anytime",
            "L3 (Strategy) requires connection to L4 values",
            "L2 (Operations) requires L3 strategic context",
            "L1 (Moment) requires L2 operational grounding",
            "Cannot skip levels when descending",
            "Ascending is always allowed"
        ]


# ============================================================
# Convenience functions for quick usage
# ============================================================

_default_governor: Optional[AltitudeGovernor] = None


def get_governor() -> AltitudeGovernor:
    """Get or create default governor singleton."""
    global _default_governor
    if _default_governor is None:
        _default_governor = AltitudeGovernor()
    return _default_governor


def check_altitude(target: str) -> ValidationResult:
    """Quick check if target altitude is allowed."""
    return get_governor().validate_transition(target)


def detect_altitude(text: str) -> str:
    """Quick detect altitude from text."""
    return get_governor().detect_level(text)
