"""Learning HRM - Pattern recognition, storage, and feedback.

Simplified spec: Plain classes, evidence-linked patterns, feedback loops.

Components:
- PatternStore: Store and retrieve learned patterns (wraps MemoryBus semantic)
- FeedbackLoop: Process outcomes, strengthen/weaken patterns
- PatternMatcher: Match current input to known patterns
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from enum import Enum

from locked_system.core.types import (
    Complexity,
    Stakes,
    ConflictLevel,
    BlastRadius,
    WriteSignals,
    InputClassification,
)
from locked_system.core.trace import EpisodicTrace
from locked_system.core.memory_bus import MemoryBus, SemanticEntry


# ─────────────────────────────────────────────────────────────
# Pattern Types
# ─────────────────────────────────────────────────────────────

class PatternType(Enum):
    """Types of patterns the system can learn."""
    INPUT_RESPONSE = "input_response"     # Input → good response
    STRATEGY = "strategy"                 # Context → good approach
    FAILURE = "failure"                   # What NOT to do
    USER_PREFERENCE = "user_preference"   # User-specific patterns
    ESCALATION = "escalation"             # When to escalate


@dataclass
class Pattern:
    """A learned pattern."""
    id: str
    pattern_type: PatternType
    description: str
    trigger_conditions: Dict[str, Any]    # When this pattern applies
    recommended_action: Dict[str, Any]    # What to do
    confidence: float                     # 0.0 - 1.0
    evidence_count: int                   # How many times confirmed
    created_at: datetime
    last_used: Optional[datetime] = None
    last_strengthened: Optional[datetime] = None

    def matches(self, context: Dict[str, Any]) -> float:
        """
        Check if pattern matches context.

        Returns match score (0.0 - 1.0).
        """
        score = 0.0
        matches = 0
        total = len(self.trigger_conditions)

        if total == 0:
            return 0.0

        for key, expected in self.trigger_conditions.items():
            actual = context.get(key)
            if actual is None:
                continue

            if isinstance(expected, list):
                if actual in expected:
                    matches += 1
            elif actual == expected:
                matches += 1
            elif isinstance(expected, str) and isinstance(actual, str):
                if expected.lower() in actual.lower():
                    matches += 0.5

        score = matches / total
        return score * self.confidence

    def to_semantic_entry(self, evidence_ids: List[str]) -> dict:
        """Convert to semantic entry format for storage."""
        return {
            "pattern_type": self.pattern_type.value,
            "description": self.description,
            "input_signature": self.trigger_conditions,
            "recommended_action": self.recommended_action,
            "confidence": self.confidence,
            "evidence_ids": evidence_ids,
        }


@dataclass
class PatternMatch:
    """Result of pattern matching."""
    pattern: Pattern
    match_score: float
    context_matched: Dict[str, Any]


# ─────────────────────────────────────────────────────────────
# Pattern Store
# ─────────────────────────────────────────────────────────────

class PatternStore:
    """
    Store and retrieve learned patterns.

    Wraps MemoryBus semantic tier for pattern storage.
    Patterns are evidence-linked and confidence-weighted.
    """

    def __init__(
        self,
        memory_bus: Optional[MemoryBus] = None,
        trace: Optional[EpisodicTrace] = None
    ):
        self.memory_bus = memory_bus
        self.trace = trace
        self._local_cache: Dict[str, Pattern] = {}

    def add_pattern(
        self,
        pattern_type: PatternType,
        description: str,
        trigger_conditions: Dict[str, Any],
        recommended_action: Dict[str, Any],
        evidence_ids: List[str],
        confidence: float = 0.5
    ) -> Optional[str]:
        """
        Add a new pattern.

        Returns pattern ID if stored, None if rejected by write gate.
        """
        import uuid
        pattern_id = f"pat_{uuid.uuid4().hex[:12]}"

        pattern = Pattern(
            id=pattern_id,
            pattern_type=pattern_type,
            description=description,
            trigger_conditions=trigger_conditions,
            recommended_action=recommended_action,
            confidence=confidence,
            evidence_count=len(evidence_ids),
            created_at=datetime.now()
        )

        # Try to store in memory bus if available
        if self.memory_bus:
            signals = WriteSignals(
                progress_delta=0.1,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.6,
                alignment_score=0.7,
                blast_radius=BlastRadius.LOCAL
            )

            stored_id = self.memory_bus.add_pattern(
                pattern_type=pattern_type.value,
                description=description,
                input_signature=trigger_conditions,
                recommended_action=recommended_action,
                confidence=confidence,
                evidence_ids=evidence_ids,
                signals=signals
            )

            if stored_id:
                pattern.id = stored_id
                self._local_cache[stored_id] = pattern

                if self.trace:
                    self.trace.log(
                        event_type="pattern_added",
                        payload={
                            "pattern_id": stored_id,
                            "pattern_type": pattern_type.value,
                            "confidence": confidence,
                        }
                    )

                return stored_id
            return None

        # Fallback to local cache only
        self._local_cache[pattern_id] = pattern
        return pattern_id

    def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Get pattern by ID."""
        if pattern_id in self._local_cache:
            return self._local_cache[pattern_id]

        if self.memory_bus:
            entry = self.memory_bus.get_pattern(pattern_id)
            if entry:
                return self._entry_to_pattern(entry)

        return None

    def search_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        min_confidence: float = 0.0
    ) -> List[Pattern]:
        """Search patterns with filters."""
        results = []

        # Check local cache
        for pattern in self._local_cache.values():
            if pattern_type and pattern.pattern_type != pattern_type:
                continue
            if pattern.confidence < min_confidence:
                continue
            results.append(pattern)

        # Check memory bus
        if self.memory_bus:
            type_str = pattern_type.value if pattern_type else None
            entries = self.memory_bus.search_patterns(type_str, min_confidence)
            for entry in entries:
                if entry.id not in self._local_cache:
                    pattern = self._entry_to_pattern(entry)
                    if pattern:
                        results.append(pattern)

        return sorted(results, key=lambda p: -p.confidence)

    def match_patterns(
        self,
        context: Dict[str, Any],
        min_score: float = 0.3
    ) -> List[PatternMatch]:
        """
        Find patterns matching the given context.

        Returns list of matches sorted by score.
        """
        matches = []
        all_patterns = self.search_patterns()

        for pattern in all_patterns:
            score = pattern.matches(context)
            if score >= min_score:
                matches.append(PatternMatch(
                    pattern=pattern,
                    match_score=score,
                    context_matched=context
                ))

        return sorted(matches, key=lambda m: -m.match_score)

    def strengthen_pattern(self, pattern_id: str, evidence_id: str) -> bool:
        """Strengthen a pattern with new evidence."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return False

        pattern.confidence = min(1.0, pattern.confidence + 0.05)
        pattern.evidence_count += 1
        pattern.last_strengthened = datetime.now()
        self._local_cache[pattern_id] = pattern

        if self.memory_bus:
            self.memory_bus.strengthen_pattern(pattern_id, evidence_id)

        if self.trace:
            self.trace.log(
                event_type="pattern_strengthened",
                payload={
                    "pattern_id": pattern_id,
                    "new_confidence": pattern.confidence,
                }
            )

        return True

    def weaken_pattern(self, pattern_id: str, reason: str) -> bool:
        """Weaken a pattern due to failure."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return False

        pattern.confidence = max(0.0, pattern.confidence - 0.1)
        self._local_cache[pattern_id] = pattern

        if self.memory_bus:
            self.memory_bus.weaken_pattern(pattern_id, reason)

        if self.trace:
            self.trace.log(
                event_type="pattern_weakened",
                payload={
                    "pattern_id": pattern_id,
                    "new_confidence": pattern.confidence,
                    "reason": reason,
                }
            )

        return True

    def _entry_to_pattern(self, entry: SemanticEntry) -> Optional[Pattern]:
        """Convert semantic entry to Pattern."""
        try:
            return Pattern(
                id=entry.id,
                pattern_type=PatternType(entry.pattern_type),
                description=entry.description,
                trigger_conditions=entry.input_signature,
                recommended_action=entry.recommended_action,
                confidence=entry.confidence,
                evidence_count=len(entry.evidence_ids),
                created_at=entry.created_at,
                last_strengthened=entry.last_strengthened_at
            )
        except (ValueError, KeyError):
            return None


# ─────────────────────────────────────────────────────────────
# Feedback Types
# ─────────────────────────────────────────────────────────────

class FeedbackType(Enum):
    """Types of feedback signals."""
    SUCCESS = "success"           # Action succeeded
    PARTIAL = "partial"           # Partially successful
    FAILURE = "failure"           # Action failed
    USER_POSITIVE = "user_positive"   # Explicit user approval
    USER_NEGATIVE = "user_negative"   # Explicit user disapproval
    TIMEOUT = "timeout"           # No response / timed out


@dataclass
class Feedback:
    """Feedback signal from an interaction."""
    feedback_type: FeedbackType
    context: Dict[str, Any]       # What led to this outcome
    action_taken: Dict[str, Any]  # What action was taken
    outcome: str                  # Description of outcome
    patterns_used: List[str]      # Pattern IDs that were used
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_positive(self) -> bool:
        return self.feedback_type in (
            FeedbackType.SUCCESS,
            FeedbackType.USER_POSITIVE
        )

    @property
    def is_negative(self) -> bool:
        return self.feedback_type in (
            FeedbackType.FAILURE,
            FeedbackType.USER_NEGATIVE
        )


# ─────────────────────────────────────────────────────────────
# Feedback Loop
# ─────────────────────────────────────────────────────────────

class FeedbackLoop:
    """
    Process feedback to strengthen/weaken patterns.

    The learning loop:
    1. Observe outcome
    2. Compare to prediction
    3. Strengthen/weaken patterns
    4. Optionally create new patterns
    """

    def __init__(
        self,
        pattern_store: PatternStore,
        trace: Optional[EpisodicTrace] = None,
        auto_create_patterns: bool = True,
        min_confidence_for_creation: float = 0.6
    ):
        self.pattern_store = pattern_store
        self.trace = trace
        self.auto_create_patterns = auto_create_patterns
        self.min_confidence_for_creation = min_confidence_for_creation
        self._recent_feedback: List[Feedback] = []

    def process_feedback(self, feedback: Feedback) -> Dict[str, Any]:
        """
        Process feedback signal.

        Updates pattern confidences and optionally creates new patterns.
        Returns summary of actions taken.
        """
        actions_taken = {
            "strengthened": [],
            "weakened": [],
            "created": [],
        }

        # Update patterns that were used
        for pattern_id in feedback.patterns_used:
            if feedback.is_positive:
                self.pattern_store.strengthen_pattern(
                    pattern_id,
                    f"feedback_{feedback.timestamp.isoformat()}"
                )
                actions_taken["strengthened"].append(pattern_id)
            elif feedback.is_negative:
                self.pattern_store.weaken_pattern(
                    pattern_id,
                    feedback.outcome
                )
                actions_taken["weakened"].append(pattern_id)

        # Consider creating new pattern for successful novel actions
        if self.auto_create_patterns and feedback.is_positive:
            new_pattern = self._maybe_create_pattern(feedback)
            if new_pattern:
                actions_taken["created"].append(new_pattern)

        # Track feedback
        self._recent_feedback.append(feedback)
        if len(self._recent_feedback) > 100:
            self._recent_feedback = self._recent_feedback[-100:]

        # Log to trace
        if self.trace:
            self.trace.log(
                event_type="feedback_processed",
                payload={
                    "feedback_type": feedback.feedback_type.value,
                    "is_positive": feedback.is_positive,
                    "actions_taken": actions_taken,
                }
            )

        return actions_taken

    def _maybe_create_pattern(self, feedback: Feedback) -> Optional[str]:
        """
        Consider creating a new pattern from successful feedback.

        Only creates if:
        1. No existing pattern matched well
        2. Action was novel
        3. Outcome was clearly positive
        """
        # Check if patterns were used (means existing patterns matched)
        if feedback.patterns_used:
            return None  # Not novel enough

        # Need enough context to create meaningful pattern
        if len(feedback.context) < 2:
            return None

        # Create pattern from successful novel action
        pattern_id = self.pattern_store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description=f"Learned from: {feedback.outcome[:100]}",
            trigger_conditions=self._extract_conditions(feedback.context),
            recommended_action=feedback.action_taken,
            evidence_ids=[f"feedback_{feedback.timestamp.isoformat()}"],
            confidence=0.4  # Start with modest confidence
        )

        return pattern_id

    def _extract_conditions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract generalizable conditions from context."""
        # Keep only simple, generalizable keys
        generalizable_keys = [
            "complexity", "stakes", "domain", "horizon",
            "stance", "altitude", "action_type"
        ]
        return {
            k: v for k, v in context.items()
            if k in generalizable_keys and v is not None
        }

    def get_recent_feedback(self, n: int = 10) -> List[Feedback]:
        """Get recent feedback signals."""
        return self._recent_feedback[-n:]

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        positive = sum(1 for f in self._recent_feedback if f.is_positive)
        negative = sum(1 for f in self._recent_feedback if f.is_negative)
        total = len(self._recent_feedback)

        return {
            "total_feedback": total,
            "positive_rate": positive / total if total > 0 else 0,
            "negative_rate": negative / total if total > 0 else 0,
            "pattern_count": len(self.pattern_store.search_patterns()),
        }


# ─────────────────────────────────────────────────────────────
# Pattern Matcher
# ─────────────────────────────────────────────────────────────

class PatternMatcher:
    """
    Match current context to known patterns.

    Provides pattern-based recommendations for actions.
    """

    def __init__(
        self,
        pattern_store: PatternStore,
        trace: Optional[EpisodicTrace] = None
    ):
        self.pattern_store = pattern_store
        self.trace = trace

    def find_recommendations(
        self,
        classification: InputClassification,
        current_context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Find pattern-based recommendations for the current context.

        Returns list of recommendations with confidence scores.
        """
        context = current_context or {}

        # Add classification to context
        context.update({
            "complexity": classification.complexity.value,
            "stakes": classification.stakes.value,
            "domain": classification.domain,
            "horizon": classification.horizon,
            "uncertainty": classification.uncertainty,
        })

        # Find matching patterns
        matches = self.pattern_store.match_patterns(context, min_score=0.3)

        recommendations = []
        for match in matches[:5]:  # Top 5 matches
            recommendations.append({
                "pattern_id": match.pattern.id,
                "pattern_type": match.pattern.pattern_type.value,
                "description": match.pattern.description,
                "recommended_action": match.pattern.recommended_action,
                "match_score": match.match_score,
                "pattern_confidence": match.pattern.confidence,
                "combined_score": match.match_score * match.pattern.confidence,
            })

        # Sort by combined score
        recommendations.sort(key=lambda r: -r["combined_score"])

        if self.trace and recommendations:
            self.trace.log(
                event_type="pattern_recommendations",
                payload={
                    "match_count": len(recommendations),
                    "top_score": recommendations[0]["combined_score"] if recommendations else 0,
                }
            )

        return recommendations

    def record_usage(self, pattern_id: str, outcome: str):
        """Record that a pattern was used and its outcome."""
        pattern = self.pattern_store.get_pattern(pattern_id)
        if pattern:
            pattern.last_used = datetime.now()
            self.pattern_store._local_cache[pattern_id] = pattern


# ─────────────────────────────────────────────────────────────
# Learning HRM (Unified)
# ─────────────────────────────────────────────────────────────

class LearningHRM:
    """
    Learning HRM - Unified learning interface.

    Manages:
    - Pattern storage and retrieval
    - Feedback processing
    - Pattern matching and recommendations
    """

    def __init__(
        self,
        memory_bus: Optional[MemoryBus] = None,
        trace: Optional[EpisodicTrace] = None
    ):
        self.trace = trace
        self.pattern_store = PatternStore(memory_bus, trace)
        self.feedback_loop = FeedbackLoop(self.pattern_store, trace)
        self.pattern_matcher = PatternMatcher(self.pattern_store, trace)

    def get_recommendations(
        self,
        classification: InputClassification,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get pattern-based recommendations."""
        return self.pattern_matcher.find_recommendations(classification, context)

    def record_outcome(
        self,
        feedback_type: FeedbackType,
        context: Dict[str, Any],
        action_taken: Dict[str, Any],
        outcome: str,
        patterns_used: List[str] = None
    ) -> Dict[str, Any]:
        """Record outcome and update patterns."""
        feedback = Feedback(
            feedback_type=feedback_type,
            context=context,
            action_taken=action_taken,
            outcome=outcome,
            patterns_used=patterns_used or []
        )
        return self.feedback_loop.process_feedback(feedback)

    def add_pattern(
        self,
        pattern_type: PatternType,
        description: str,
        trigger_conditions: Dict[str, Any],
        recommended_action: Dict[str, Any],
        confidence: float = 0.5
    ) -> Optional[str]:
        """Add a pattern manually."""
        return self.pattern_store.add_pattern(
            pattern_type=pattern_type,
            description=description,
            trigger_conditions=trigger_conditions,
            recommended_action=recommended_action,
            evidence_ids=["manual_addition"],
            confidence=confidence
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        return self.feedback_loop.get_learning_stats()


# ─────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────

def create_learning_hrm(
    memory_bus: Optional[MemoryBus] = None,
    trace: Optional[EpisodicTrace] = None
) -> LearningHRM:
    """Create a Learning HRM instance."""
    return LearningHRM(memory_bus, trace)
