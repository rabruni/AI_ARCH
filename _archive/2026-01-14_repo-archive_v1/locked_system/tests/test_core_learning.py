"""Tests for locked_system.core.learning module.

Tests cover:
- Pattern creation and matching
- PatternStore operations
- FeedbackLoop processing
- PatternMatcher recommendations
- LearningHRM unified operations
"""

import pytest
from datetime import datetime

from locked_system.core.types import (
    Complexity, Stakes, ConflictLevel, BlastRadius, WriteSignals, InputClassification,
)
from locked_system.core.learning import (
    Pattern, PatternMatch, PatternType,
    PatternStore, FeedbackLoop, PatternMatcher, LearningHRM,
    Feedback, FeedbackType,
    create_learning_hrm,
)
from locked_system.core.trace import EpisodicTrace
from locked_system.core.memory_bus import MemoryBus


class TestPattern:
    """Tests for Pattern data class."""

    def test_pattern_creation(self):
        """Test Pattern creation."""
        pattern = Pattern(
            id="pat_test",
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test pattern",
            trigger_conditions={"domain": "technical"},
            recommended_action={"action": "delegate"},
            confidence=0.7,
            evidence_count=3,
            created_at=datetime.now()
        )

        assert pattern.id == "pat_test"
        assert pattern.pattern_type == PatternType.INPUT_RESPONSE
        assert pattern.confidence == 0.7

    def test_pattern_matches_exact(self):
        """Test exact pattern matching."""
        pattern = Pattern(
            id="pat_1",
            pattern_type=PatternType.STRATEGY,
            description="Test",
            trigger_conditions={"complexity": "complex", "stakes": "high"},
            recommended_action={"action": "escalate"},
            confidence=0.8,
            evidence_count=5,
            created_at=datetime.now()
        )

        # Exact match
        score = pattern.matches({"complexity": "complex", "stakes": "high"})
        assert score > 0.7

        # Partial match
        score = pattern.matches({"complexity": "complex", "stakes": "low"})
        assert 0 < score < 0.8

        # No match
        score = pattern.matches({"complexity": "simple", "stakes": "low"})
        assert score < 0.5

    def test_pattern_matches_list_values(self):
        """Test matching with list values in conditions."""
        pattern = Pattern(
            id="pat_1",
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test",
            trigger_conditions={"domain": ["technical", "productivity"]},
            recommended_action={},
            confidence=0.8,
            evidence_count=2,
            created_at=datetime.now()
        )

        # Match in list
        score = pattern.matches({"domain": "technical"})
        assert score > 0

        # Not in list
        score = pattern.matches({"domain": "emotional"})
        assert score == 0

    def test_pattern_matches_empty_conditions(self):
        """Test matching with empty conditions."""
        pattern = Pattern(
            id="pat_1",
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test",
            trigger_conditions={},
            recommended_action={},
            confidence=0.5,
            evidence_count=1,
            created_at=datetime.now()
        )

        score = pattern.matches({"any": "context"})
        assert score == 0.0


class TestPatternStore:
    """Tests for PatternStore."""

    def test_add_pattern(self):
        """Test adding pattern to store."""
        store = PatternStore()

        pattern_id = store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test pattern",
            trigger_conditions={"domain": "technical"},
            recommended_action={"action": "respond"},
            evidence_ids=["evt_1", "evt_2"],
            confidence=0.6
        )

        assert pattern_id is not None
        assert pattern_id.startswith("pat_")

    def test_get_pattern(self):
        """Test retrieving pattern by ID."""
        store = PatternStore()

        pattern_id = store.add_pattern(
            pattern_type=PatternType.STRATEGY,
            description="Strategy pattern",
            trigger_conditions={"stakes": "high"},
            recommended_action={"action": "escalate"},
            evidence_ids=["evt_1"],
            confidence=0.7
        )

        retrieved = store.get_pattern(pattern_id)
        assert retrieved is not None
        assert retrieved.description == "Strategy pattern"

    def test_search_patterns_by_type(self):
        """Test searching patterns by type."""
        store = PatternStore()

        store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Response pattern",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=[],
            confidence=0.5
        )
        store.add_pattern(
            pattern_type=PatternType.STRATEGY,
            description="Strategy pattern",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=[],
            confidence=0.6
        )

        results = store.search_patterns(pattern_type=PatternType.STRATEGY)
        assert len(results) == 1
        assert results[0].description == "Strategy pattern"

    def test_search_patterns_by_confidence(self):
        """Test searching patterns by minimum confidence."""
        store = PatternStore()

        store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Low confidence",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=[],
            confidence=0.3
        )
        store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="High confidence",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=[],
            confidence=0.8
        )

        results = store.search_patterns(min_confidence=0.5)
        assert len(results) == 1
        assert results[0].description == "High confidence"

    def test_match_patterns(self):
        """Test pattern matching against context."""
        store = PatternStore()

        store.add_pattern(
            pattern_type=PatternType.STRATEGY,
            description="Technical high stakes",
            trigger_conditions={"domain": "technical", "stakes": "high"},
            recommended_action={"action": "verify"},
            evidence_ids=[],
            confidence=0.8
        )
        store.add_pattern(
            pattern_type=PatternType.STRATEGY,
            description="General pattern",
            trigger_conditions={"domain": "general"},
            recommended_action={"action": "respond"},
            evidence_ids=[],
            confidence=0.5
        )

        matches = store.match_patterns({"domain": "technical", "stakes": "high"})
        assert len(matches) >= 1
        assert matches[0].pattern.description == "Technical high stakes"

    def test_strengthen_pattern(self):
        """Test pattern strengthening."""
        store = PatternStore()

        pattern_id = store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=["evt_1"],
            confidence=0.5
        )

        original = store.get_pattern(pattern_id)
        original_confidence = original.confidence

        store.strengthen_pattern(pattern_id, "evt_2")

        updated = store.get_pattern(pattern_id)
        assert updated.confidence > original_confidence
        assert updated.evidence_count == 2

    def test_weaken_pattern(self):
        """Test pattern weakening."""
        store = PatternStore()

        pattern_id = store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=[],
            confidence=0.7
        )

        store.weaken_pattern(pattern_id, "Did not work")

        updated = store.get_pattern(pattern_id)
        assert updated.confidence < 0.7


class TestFeedback:
    """Tests for Feedback data class."""

    def test_is_positive(self):
        """Test positive feedback detection."""
        positive = Feedback(
            feedback_type=FeedbackType.SUCCESS,
            context={},
            action_taken={},
            outcome="Worked well",
            patterns_used=[]
        )
        assert positive.is_positive is True
        assert positive.is_negative is False

        user_positive = Feedback(
            feedback_type=FeedbackType.USER_POSITIVE,
            context={},
            action_taken={},
            outcome="User liked it",
            patterns_used=[]
        )
        assert user_positive.is_positive is True

    def test_is_negative(self):
        """Test negative feedback detection."""
        negative = Feedback(
            feedback_type=FeedbackType.FAILURE,
            context={},
            action_taken={},
            outcome="Failed",
            patterns_used=[]
        )
        assert negative.is_negative is True
        assert negative.is_positive is False


class TestFeedbackLoop:
    """Tests for FeedbackLoop."""

    def test_process_positive_feedback(self):
        """Test positive feedback strengthens patterns."""
        store = PatternStore()
        loop = FeedbackLoop(store)

        pattern_id = store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=[],
            confidence=0.5
        )

        feedback = Feedback(
            feedback_type=FeedbackType.SUCCESS,
            context={"test": True},
            action_taken={"action": "respond"},
            outcome="Success",
            patterns_used=[pattern_id]
        )

        result = loop.process_feedback(feedback)

        assert pattern_id in result["strengthened"]
        pattern = store.get_pattern(pattern_id)
        assert pattern.confidence > 0.5

    def test_process_negative_feedback(self):
        """Test negative feedback weakens patterns."""
        store = PatternStore()
        loop = FeedbackLoop(store)

        pattern_id = store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=[],
            confidence=0.7
        )

        feedback = Feedback(
            feedback_type=FeedbackType.FAILURE,
            context={},
            action_taken={},
            outcome="Failed miserably",
            patterns_used=[pattern_id]
        )

        result = loop.process_feedback(feedback)

        assert pattern_id in result["weakened"]
        pattern = store.get_pattern(pattern_id)
        assert pattern.confidence < 0.7

    def test_auto_create_pattern_on_novel_success(self):
        """Test auto-creation of pattern on novel success."""
        store = PatternStore()
        loop = FeedbackLoop(store, auto_create_patterns=True)

        feedback = Feedback(
            feedback_type=FeedbackType.SUCCESS,
            context={"complexity": "simple", "domain": "technical"},
            action_taken={"action": "respond", "style": "direct"},
            outcome="User was happy",
            patterns_used=[]  # Novel - no patterns used
        )

        result = loop.process_feedback(feedback)

        assert len(result["created"]) == 1

    def test_no_auto_create_when_patterns_used(self):
        """Test no auto-creation when existing patterns were used."""
        store = PatternStore()
        loop = FeedbackLoop(store, auto_create_patterns=True)

        pattern_id = store.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Existing",
            trigger_conditions={},
            recommended_action={},
            evidence_ids=[],
            confidence=0.5
        )

        feedback = Feedback(
            feedback_type=FeedbackType.SUCCESS,
            context={"test": True},
            action_taken={},
            outcome="Good",
            patterns_used=[pattern_id]  # Used existing pattern
        )

        result = loop.process_feedback(feedback)

        assert len(result["created"]) == 0

    def test_get_learning_stats(self):
        """Test learning statistics."""
        store = PatternStore()
        loop = FeedbackLoop(store)

        # Add some feedback
        for i in range(5):
            loop.process_feedback(Feedback(
                feedback_type=FeedbackType.SUCCESS,
                context={}, action_taken={}, outcome="OK", patterns_used=[]
            ))
        for i in range(2):
            loop.process_feedback(Feedback(
                feedback_type=FeedbackType.FAILURE,
                context={}, action_taken={}, outcome="Bad", patterns_used=[]
            ))

        stats = loop.get_learning_stats()

        assert stats["total_feedback"] == 7
        assert stats["positive_rate"] > 0.5


class TestPatternMatcher:
    """Tests for PatternMatcher."""

    def test_find_recommendations(self):
        """Test finding recommendations for classification."""
        store = PatternStore()
        matcher = PatternMatcher(store)

        store.add_pattern(
            pattern_type=PatternType.STRATEGY,
            description="High stakes pattern",
            trigger_conditions={"stakes": "high", "complexity": "complex"},
            recommended_action={"action": "escalate", "reason": "High risk"},
            evidence_ids=[],
            confidence=0.8
        )

        classification = InputClassification(
            complexity=Complexity.COMPLEX,
            uncertainty=0.5,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.HIGH,
            horizon="near"
        )

        recommendations = matcher.find_recommendations(classification)

        assert len(recommendations) >= 1
        assert recommendations[0]["recommended_action"]["action"] == "escalate"

    def test_recommendations_sorted_by_score(self):
        """Test recommendations are sorted by combined score."""
        store = PatternStore()
        matcher = PatternMatcher(store)

        store.add_pattern(
            pattern_type=PatternType.STRATEGY,
            description="Low confidence",
            trigger_conditions={"stakes": "high"},
            recommended_action={"action": "a"},
            evidence_ids=[],
            confidence=0.3
        )
        store.add_pattern(
            pattern_type=PatternType.STRATEGY,
            description="High confidence",
            trigger_conditions={"stakes": "high"},
            recommended_action={"action": "b"},
            evidence_ids=[],
            confidence=0.9
        )

        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.5,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.HIGH,
            horizon="near"
        )

        recommendations = matcher.find_recommendations(classification)

        # Higher confidence pattern should be first
        assert recommendations[0]["pattern_confidence"] == 0.9


class TestLearningHRM:
    """Tests for LearningHRM unified class."""

    def test_get_recommendations(self):
        """Test getting recommendations."""
        hrm = LearningHRM()

        # Add a pattern manually with matching conditions
        hrm.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test pattern",
            trigger_conditions={"stakes": "low", "complexity": "simple"},
            recommended_action={"action": "delegate"},
            confidence=0.7
        )

        classification = InputClassification(
            complexity=Complexity.SIMPLE,
            uncertainty=0.3,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.LOW,
            horizon="near",
            domain=["productivity"]
        )

        recs = hrm.get_recommendations(classification)
        # Pattern should match based on stakes and complexity
        assert len(recs) >= 1

    def test_record_outcome(self):
        """Test recording outcomes."""
        hrm = LearningHRM()

        pattern_id = hrm.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test",
            trigger_conditions={},
            recommended_action={},
            confidence=0.5
        )

        result = hrm.record_outcome(
            feedback_type=FeedbackType.SUCCESS,
            context={"test": True},
            action_taken={"action": "respond"},
            outcome="User was satisfied",
            patterns_used=[pattern_id]
        )

        assert pattern_id in result["strengthened"]

    def test_get_stats(self):
        """Test getting learning stats."""
        hrm = LearningHRM()

        hrm.record_outcome(
            feedback_type=FeedbackType.SUCCESS,
            context={}, action_taken={}, outcome="OK"
        )

        stats = hrm.get_stats()
        assert stats["total_feedback"] == 1


class TestCreateLearningHRM:
    """Tests for create_learning_hrm factory."""

    def test_create_with_defaults(self):
        """Test creating LearningHRM with defaults."""
        hrm = create_learning_hrm()
        assert isinstance(hrm, LearningHRM)

    def test_create_with_trace(self):
        """Test creating LearningHRM with trace."""
        trace = EpisodicTrace()
        hrm = create_learning_hrm(trace=trace)

        # The pattern_added event is only logged when the pattern
        # is successfully stored (via PatternStore with trace)
        hrm.add_pattern(
            pattern_type=PatternType.INPUT_RESPONSE,
            description="Test",
            trigger_conditions={},
            recommended_action={},
            confidence=0.5
        )

        # Check that the pattern was added to the store
        patterns = hrm.pattern_store.search_patterns()
        assert len(patterns) == 1


class TestLearningIntegration:
    """Integration tests for learning module."""

    def test_full_learning_cycle(self):
        """Test complete learning cycle."""
        trace = EpisodicTrace()
        hrm = create_learning_hrm(trace=trace)

        # 1. Initially no patterns
        classification = InputClassification(
            complexity=Complexity.MODERATE,
            uncertainty=0.5,
            conflict=ConflictLevel.NONE,
            stakes=Stakes.MEDIUM,
            horizon="near",
            domain=["productivity"]
        )
        recs = hrm.get_recommendations(classification)
        assert len(recs) == 0

        # 2. Record successful outcome (creates pattern)
        hrm.record_outcome(
            feedback_type=FeedbackType.SUCCESS,
            context={"complexity": "moderate", "domain": "productivity"},
            action_taken={"action": "delegate", "agents": ["task_manager"]},
            outcome="Task completed successfully"
        )

        # 3. Now should have recommendations
        # Note: auto-created patterns have low confidence initially
        patterns = hrm.pattern_store.search_patterns()
        assert len(patterns) >= 1

    def test_pattern_decay_on_failure(self):
        """Test patterns decay on repeated failure."""
        hrm = create_learning_hrm()

        pattern_id = hrm.add_pattern(
            pattern_type=PatternType.STRATEGY,
            description="Risky strategy",
            trigger_conditions={"stakes": "high"},
            recommended_action={"action": "aggressive"},
            confidence=0.8
        )

        # Multiple failures
        for _ in range(5):
            hrm.record_outcome(
                feedback_type=FeedbackType.FAILURE,
                context={},
                action_taken={},
                outcome="Failed",
                patterns_used=[pattern_id]
            )

        pattern = hrm.pattern_store.get_pattern(pattern_id)
        assert pattern.confidence < 0.5  # Should have decayed significantly
