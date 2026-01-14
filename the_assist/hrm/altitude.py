"""HRM Altitude Governance

Reusable altitude management for any HRM-based agent.

Altitude = level of abstraction in reasoning:
- L4: Identity (why we exist, values, north stars)
- L3: Strategy (priorities, projects, goals)
- L2: Operations (this week, today, tasks)
- L1: Moment (this conversation, right now)

Key principle: You cannot descend without establishing context above.
Exception: L2-atomic requests get a fast lane (micro-anchor, not block).

Request Types:
- atomic: Safe, factual, no drift risk (calendar lookup, time check)
- derivative: Risk of drift, needs grounding (prioritization, planning)
- high_stakes: Requires verification (finance, irreversible actions)

Usage by any agent:
    from the_assist.hrm.altitude import AltitudeGovernor, AltitudePolicy

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

    # Classify request type
    req_type = governor.classify_request("What's on my calendar?")  # -> atomic

    # With trace integration (optional)
    from locked_system.core import EpisodicTrace
    trace = EpisodicTrace()
    governor = AltitudeGovernor(trace=trace)
"""
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from locked_system.core.trace import EpisodicTrace


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


class RequestType(Enum):
    """
    Request type classification for L2 fast lane.

    atomic: Safe, factual, no drift risk
    derivative: Risk of drift, needs grounding
    high_stakes: Requires verification/slowdown
    """
    ATOMIC = "atomic"
    DERIVATIVE = "derivative"
    HIGH_STAKES = "high_stakes"


# Classification patterns
ATOMIC_PATTERNS = [
    # Calendar/time
    "what's on my calendar", "what is on my calendar",
    "what time", "when is", "when does", "when do i",
    "what's my next", "what is my next", "next meeting",
    "list my", "show me", "show my",
    # Lookups
    "where is", "what's the", "what is the",
    "status of", "check on",
    # Simple commands
    "open", "read", "display",
]

DERIVATIVE_PATTERNS = [
    # Decision-making
    "what should i", "should i",
    "help me decide", "help me prioritize",
    "prioritize", "priority",
    "plan my", "planning",
    "what's most important", "what is most important",
    "how should i", "how do i approach",
    "what do you think",
    # Analysis
    "analyze", "evaluate", "assess",
    "compare", "trade-off", "tradeoff",
]

HIGH_STAKES_PATTERNS = [
    # Financial
    "invest", "investment", "transfer money", "move money",
    "pay", "payment", "transaction",
    "$", "dollars", "budget",
    # Irreversible
    "send", "submit", "publish", "post",
    "delete", "remove permanently",
    "approve", "sign off", "authorize",
    # Legal/medical
    "legal", "lawyer", "contract",
    "medical", "doctor", "health",
    "security", "password", "credential",
]

URGENCY_PATTERNS = [
    # Explicit urgency
    "just", "just tell me", "just show me",
    "stop", "enough", "move on",
    "please just", "i need",
    # Frustration
    "damn", "hell", "shit", "fuck",
    "already", "i said", "i asked",
]


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

    # Friction tracking
    friction_events: list = field(default_factory=list)  # Track redirections
    total_friction_score: int = 0  # Cumulative friction


@dataclass
class ValidationResult:
    """Result of altitude validation."""
    allowed: bool
    reason: str
    suggested_level: Optional[str] = None
    required_action: Optional[str] = None  # What to do if not allowed
    request_type: Optional[str] = None  # atomic | derivative | high_stakes
    use_micro_anchor: bool = False  # Use light anchor instead of block
    micro_anchor_text: Optional[str] = None  # The anchor text to use
    execute_first: bool = False  # Execute immediately, offer alignment after
    requires_verification: bool = False  # High-stakes slowdown


class AltitudeGovernor:
    """
    Governs altitude transitions for an HRM agent.

    Reusable across any HRM-based system.
    """

    def __init__(
        self,
        policy: Optional[AltitudePolicy] = None,
        trace: Optional["EpisodicTrace"] = None
    ):
        self.policy = policy or AltitudePolicy.default()
        self.context = AltitudeContext()
        self.trace = trace

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

    def classify_request(self, text: str) -> RequestType:
        """
        Classify request type for L2 fast lane decisions.

        Returns: ATOMIC, DERIVATIVE, or HIGH_STAKES
        """
        text_lower = text.lower()

        # Check high-stakes first (takes priority)
        for pattern in HIGH_STAKES_PATTERNS:
            if pattern in text_lower:
                return RequestType.HIGH_STAKES

        # Check derivative patterns
        for pattern in DERIVATIVE_PATTERNS:
            if pattern in text_lower:
                return RequestType.DERIVATIVE

        # Check atomic patterns
        for pattern in ATOMIC_PATTERNS:
            if pattern in text_lower:
                return RequestType.ATOMIC

        # Default to derivative (safer default - requires grounding)
        return RequestType.DERIVATIVE

    def detect_urgency(self, text: str) -> bool:
        """
        Detect if user is expressing urgency or frustration.

        If true, execute-first policy applies.
        """
        text_lower = text.lower()
        for pattern in URGENCY_PATTERNS:
            if pattern in text_lower:
                return True
        return False

    def can_descend(self, from_level: str, to_level: str, text: str = "") -> ValidationResult:
        """
        Check if descent from one level to another is allowed.

        Descent = going from higher abstraction to lower (L4 -> L3 -> L2 -> L1)

        Now includes L2 fast lane logic:
        - Atomic requests get micro-anchor, not block
        - Urgency/frustration triggers execute-first
        - High-stakes requests require verification
        """
        from_l = self.get_level(from_level)
        to_l = self.get_level(to_level)

        # Classify request if text provided
        request_type = self.classify_request(text) if text else RequestType.DERIVATIVE
        is_urgent = self.detect_urgency(text) if text else False

        # Not a descent - always allowed
        if to_l >= from_l:
            return ValidationResult(
                True, "Not a descent, allowed",
                request_type=request_type.value
            )

        # HIGH-STAKES: Always require verification (check BEFORE level-skip)
        if request_type == RequestType.HIGH_STAKES:
            return ValidationResult(
                True,  # Allow but with verification
                "High-stakes request - proceed with verification",
                request_type=request_type.value,
                requires_verification=True
            )

        # URGENCY/FRUSTRATION: Execute-first, overrides level-skip restriction
        if is_urgent:
            return ValidationResult(
                True,
                "Urgency detected - execute first, align after",
                request_type=request_type.value,
                execute_first=True,
                micro_anchor_text="Let me help with that. We can align to your priorities after if you'd like."
            )

        # Check level-skip (AFTER urgency/high-stakes overrides)
        if not self.policy.allow_level_skip and (from_l.value - to_l.value) > 1:
            return ValidationResult(
                False,
                f"Cannot skip levels. Must go through intermediate levels.",
                suggested_level=f"L{from_l.value - 1}",
                required_action=f"Establish L{from_l.value - 1} context first",
                request_type=request_type.value
            )

        # Check requirements for descent
        if self.policy.require_context_for_descent:
            to_def = self.policy.levels.get(to_level)
            if to_def:
                for req in to_def.requires_for_descent:
                    if req == "L4_connected" and not self.context.l4_connected:
                        # L2 ATOMIC FAST LANE
                        if to_level == "L2" and request_type == RequestType.ATOMIC:
                            return ValidationResult(
                                True,
                                "L2-atomic allowed with micro-anchor",
                                request_type=request_type.value,
                                use_micro_anchor=True,
                                micro_anchor_text="I'll answer directly. If you want, we can align it to priorities after."
                            )
                        return ValidationResult(
                            False,
                            "Cannot discuss operations/tactics without connecting to identity/values",
                            suggested_level="L4",
                            required_action="First establish connection to north stars",
                            request_type=request_type.value
                        )
                    if req == "L3_established" and not self.context.l3_established:
                        # L2 ATOMIC FAST LANE
                        if to_level == "L2" and request_type == RequestType.ATOMIC:
                            return ValidationResult(
                                True,
                                "L2-atomic allowed with micro-anchor",
                                request_type=request_type.value,
                                use_micro_anchor=True,
                                micro_anchor_text="I'll answer directly. If you want, we can align it to priorities after."
                            )
                        return ValidationResult(
                            False,
                            "Cannot discuss tasks without strategic context",
                            suggested_level="L3",
                            required_action="First establish strategic priorities",
                            request_type=request_type.value
                        )

        return ValidationResult(
            True, "Descent allowed",
            request_type=request_type.value
        )

    def validate_transition(self, target_level: str, text: str = "") -> ValidationResult:
        """Validate a transition to target level from current."""
        return self.can_descend(self.context.current_level, target_level, text)

    def record_transition(self, new_level: str, reason: str = ""):
        """Record a level transition."""
        from_level = self.context.current_level
        self.context.level_history.append({
            "from": from_level,
            "to": new_level,
            "time_at_previous": self.context.time_at_current
        })
        self.context.current_level = new_level
        self.context.time_at_current = 0

        # Log to trace if available
        if self.trace:
            self.trace.log_altitude_transition(
                from_level=from_level,
                to_level=new_level,
                reason=reason
            )

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

    def record_friction(self, requested_level: str, actual_level: str, was_blocked: bool):
        """
        Record a friction event.

        Friction = user asked for L2 but was redirected upward without satisfying L2.
        """
        if was_blocked and requested_level == "L2":
            event = {
                "requested": requested_level,
                "actual": actual_level,
                "blocked": was_blocked
            }
            self.context.friction_events.append(event)
            self.context.total_friction_score += 1

            # Log to trace if available
            if self.trace:
                self.trace.log(
                    event_type="altitude_friction",
                    payload={
                        **event,
                        "total_friction": self.context.total_friction_score
                    }
                )

    def get_friction_score(self) -> int:
        """Get cumulative friction score for this session."""
        return self.context.total_friction_score

    def is_friction_high(self, threshold: int = 3) -> bool:
        """Check if friction is high (system being preachy)."""
        return self.context.total_friction_score >= threshold

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
