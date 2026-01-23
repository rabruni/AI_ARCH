"""Tests for locked_system.core.memory_bus module.

Tests cover:
- Tier definitions
- WriteGate evaluation
- MemoryBus operations for all 4 tiers
- Persistence and loading
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from locked_system.core.types import (
    ConflictLevel, BlastRadius, WriteSignals,
)
from locked_system.core.memory_bus import (
    Tier, WorkingEntry, SharedEntry, SemanticEntry,
    WriteGate, MemoryBus,
)
from locked_system.core.trace import EpisodicTrace, Event


class TestTier:
    """Tests for Tier constants."""

    def test_tier_values(self):
        """Test tier constant values."""
        assert Tier.WORKING == "working"
        assert Tier.SHARED == "shared"
        assert Tier.EPISODIC == "episodic"
        assert Tier.SEMANTIC == "semantic"


class TestWorkingEntry:
    """Tests for WorkingEntry."""

    def test_is_expired(self):
        """Test expiry detection."""
        now = datetime.now()

        # Not expired
        entry = WorkingEntry(
            key="test",
            value="data",
            problem_id="p1",
            created_at=now,
            expires_at=now + timedelta(hours=2)
        )
        assert entry.is_expired() is False

        # Expired
        entry.expires_at = now - timedelta(hours=1)
        assert entry.is_expired() is True

    def test_to_dict(self):
        """Test serialization."""
        now = datetime.now()
        entry = WorkingEntry(
            key="test",
            value={"nested": "data"},
            problem_id="p1",
            created_at=now,
            expires_at=now + timedelta(hours=2)
        )

        data = entry.to_dict()
        assert data["key"] == "test"
        assert data["value"] == {"nested": "data"}
        assert data["problem_id"] == "p1"


class TestWriteGate:
    """Tests for WriteGate."""

    def test_working_tier_always_allowed(self):
        """Test working tier writes are always allowed."""
        gate = WriteGate()
        signals = WriteSignals(
            progress_delta=0.1,
            conflict_level=ConflictLevel.HIGH,  # Even with conflict
            source_quality=0.1,  # Even with low quality
            alignment_score=0.1,
            blast_radius=BlastRadius.GLOBAL
        )

        assert gate.evaluate(Tier.WORKING, signals) is True

    def test_episodic_tier_always_allowed(self):
        """Test episodic tier writes are always allowed."""
        gate = WriteGate()
        signals = WriteSignals(
            progress_delta=0.0,
            conflict_level=ConflictLevel.HIGH,
            source_quality=0.0,
            alignment_score=0.0,
            blast_radius=BlastRadius.GLOBAL
        )

        assert gate.evaluate(Tier.EPISODIC, signals) is True

    def test_shared_tier_requires_quality(self):
        """Test shared tier requires source quality."""
        gate = WriteGate()

        # Low quality - denied
        low_quality = WriteSignals(
            progress_delta=0.5,
            conflict_level=ConflictLevel.NONE,
            source_quality=0.1,  # Below threshold
            alignment_score=0.8,
            blast_radius=BlastRadius.LOCAL
        )
        assert gate.evaluate(Tier.SHARED, low_quality) is False

        # Good quality - allowed
        good_quality = WriteSignals(
            progress_delta=0.5,
            conflict_level=ConflictLevel.NONE,
            source_quality=0.5,
            alignment_score=0.5,
            blast_radius=BlastRadius.LOCAL
        )
        assert gate.evaluate(Tier.SHARED, good_quality) is True

    def test_shared_tier_global_blast_radius(self):
        """Test shared tier with global blast radius requires higher quality."""
        gate = WriteGate(blast_radius_threshold=0.7)

        # Global blast radius needs higher quality
        signals = WriteSignals(
            progress_delta=0.5,
            conflict_level=ConflictLevel.NONE,
            source_quality=0.5,  # Below blast threshold
            alignment_score=0.8,
            blast_radius=BlastRadius.GLOBAL
        )
        assert gate.evaluate(Tier.SHARED, signals) is False

        # Higher quality passes
        signals.source_quality = 0.8
        assert gate.evaluate(Tier.SHARED, signals) is True

    def test_semantic_tier_requires_no_conflict(self):
        """Test semantic tier requires no conflict."""
        gate = WriteGate()

        # With conflict - denied
        with_conflict = WriteSignals(
            progress_delta=0.5,
            conflict_level=ConflictLevel.LOW,
            source_quality=0.8,
            alignment_score=0.8,
            blast_radius=BlastRadius.LOCAL
        )
        assert gate.evaluate(Tier.SEMANTIC, with_conflict) is False

        # No conflict - allowed
        no_conflict = WriteSignals(
            progress_delta=0.5,
            conflict_level=ConflictLevel.NONE,
            source_quality=0.8,
            alignment_score=0.8,
            blast_radius=BlastRadius.LOCAL
        )
        assert gate.evaluate(Tier.SEMANTIC, no_conflict) is True

    def test_semantic_tier_requires_high_quality(self):
        """Test semantic tier requires high quality."""
        gate = WriteGate()

        # Low quality - denied
        low_quality = WriteSignals(
            progress_delta=0.5,
            conflict_level=ConflictLevel.NONE,
            source_quality=0.3,  # Too low
            alignment_score=0.8,
            blast_radius=BlastRadius.LOCAL
        )
        assert gate.evaluate(Tier.SEMANTIC, low_quality) is False


class TestMemoryBusWorking:
    """Tests for MemoryBus working set operations."""

    def test_write_and_read_working(self):
        """Test write and read from working set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            bus.write_working("prob_1", "key_1", {"data": "value"})
            result = bus.read_working("prob_1", "key_1")

            assert result == {"data": "value"}

    def test_working_set_isolated_by_problem(self):
        """Test working set is isolated by problem_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            bus.write_working("prob_1", "key", "data_1")
            bus.write_working("prob_2", "key", "data_2")

            assert bus.read_working("prob_1", "key") == "data_1"
            assert bus.read_working("prob_2", "key") == "data_2"

    def test_working_set_expiry(self):
        """Test working set entries expire."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir), default_ttl_hours=0)

            bus.write_working("prob_1", "key", "value")

            # Manually expire
            entry = bus._working["prob_1"]["key"]
            entry.expires_at = datetime.now() - timedelta(hours=1)

            result = bus.read_working("prob_1", "key")
            assert result is None

    def test_get_working_set(self):
        """Test getting all entries for a problem."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            bus.write_working("prob_1", "a", 1)
            bus.write_working("prob_1", "b", 2)
            bus.write_working("prob_1", "c", 3)

            working_set = bus.get_working_set("prob_1")
            assert len(working_set) == 3
            assert working_set["a"] == 1

    def test_expire_working(self):
        """Test expiring stale entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            bus.write_working("prob_1", "key", "value")

            # Manually expire
            bus._working["prob_1"]["key"].expires_at = datetime.now() - timedelta(hours=1)

            count = bus.expire_working()
            assert count == 1
            assert bus.read_working("prob_1", "key") is None


class TestMemoryBusShared:
    """Tests for MemoryBus shared reference operations."""

    def test_write_and_read_shared(self):
        """Test write and read from shared reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.7,
                alignment_score=0.7,
                blast_radius=BlastRadius.LOCAL
            )

            success = bus.write_shared("config", {"setting": True}, "system", signals)
            assert success is True

            result = bus.read_shared("config")
            assert result == {"setting": True}

    def test_shared_versioning(self):
        """Test shared reference versioning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.7,
                alignment_score=0.7,
                blast_radius=BlastRadius.LOCAL
            )

            bus.write_shared("key", "v1", "source", signals)
            bus.write_shared("key", "v2", "source", signals)
            bus.write_shared("key", "v3", "source", signals)

            # Latest version
            assert bus.read_shared("key") == "v3"

            # Specific version
            assert bus.read_shared("key", version=1) == "v1"
            assert bus.read_shared("key", version=2) == "v2"

    def test_shared_write_denied_by_gate(self):
        """Test shared write denied by gate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            # Low quality signals
            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.1,  # Too low
                alignment_score=0.1,
                blast_radius=BlastRadius.LOCAL
            )

            success = bus.write_shared("key", "value", "source", signals)
            assert success is False

    def test_cite_shared(self):
        """Test citation generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.7,
                alignment_score=0.7,
                blast_radius=BlastRadius.LOCAL
            )

            bus.write_shared("doc", "content", "source", signals)
            citation = bus.cite_shared("doc")

            assert "[shared:doc@v1]" == citation


class TestMemoryBusEpisodic:
    """Tests for MemoryBus episodic operations."""

    def test_log_episode(self):
        """Test logging to episodic trace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            event = Event.create("test_event", {"data": 1})
            event_id = bus.log_episode(event)

            assert event_id.startswith("evt_")

    def test_query_episodes(self):
        """Test querying episodic trace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            bus.trace.log("type_a", {"n": 1})
            bus.trace.log("type_b", {"n": 2})
            bus.trace.log("type_a", {"n": 3})

            results = bus.query_episodes(event_type="type_a")
            assert len(results) == 2


class TestMemoryBusSemantic:
    """Tests for MemoryBus semantic operations."""

    def test_add_pattern(self):
        """Test adding pattern to semantic memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.8,
                alignment_score=0.8,
                blast_radius=BlastRadius.LOCAL
            )

            pattern_id = bus.add_pattern(
                pattern_type="strategy",
                description="Test pattern",
                input_signature={"stakes": "high"},
                recommended_action={"action": "escalate"},
                confidence=0.7,
                evidence_ids=["evt_1"],
                signals=signals
            )

            assert pattern_id is not None
            assert pattern_id.startswith("pat_")

    def test_get_pattern(self):
        """Test getting pattern by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.8,
                alignment_score=0.8,
                blast_radius=BlastRadius.LOCAL
            )

            pattern_id = bus.add_pattern(
                pattern_type="test",
                description="Test",
                input_signature={},
                recommended_action={},
                confidence=0.5,
                evidence_ids=[],
                signals=signals
            )

            pattern = bus.get_pattern(pattern_id)
            assert pattern is not None
            assert pattern.description == "Test"

    def test_search_patterns(self):
        """Test searching patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.8,
                alignment_score=0.8,
                blast_radius=BlastRadius.LOCAL
            )

            bus.add_pattern("type_a", "A", {}, {}, 0.5, [], signals)
            bus.add_pattern("type_b", "B", {}, {}, 0.8, [], signals)
            bus.add_pattern("type_a", "A2", {}, {}, 0.3, [], signals)

            # By type
            results = bus.search_patterns(pattern_type="type_a")
            assert len(results) == 2

            # By confidence
            results = bus.search_patterns(min_confidence=0.6)
            assert len(results) == 1

    def test_strengthen_pattern(self):
        """Test pattern strengthening."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.8,
                alignment_score=0.8,
                blast_radius=BlastRadius.LOCAL
            )

            pattern_id = bus.add_pattern(
                "test", "Test", {}, {}, 0.5, ["evt_1"], signals
            )

            bus.strengthen_pattern(pattern_id, "evt_2")

            pattern = bus.get_pattern(pattern_id)
            assert pattern.confidence > 0.5
            assert len(pattern.evidence_ids) == 2

    def test_weaken_pattern(self):
        """Test pattern weakening."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.8,
                alignment_score=0.8,
                blast_radius=BlastRadius.LOCAL
            )

            pattern_id = bus.add_pattern(
                "test", "Test", {}, {}, 0.7, [], signals
            )

            bus.weaken_pattern(pattern_id, "Did not work")

            pattern = bus.get_pattern(pattern_id)
            assert pattern.confidence < 0.7

    def test_get_evidence_chain(self):
        """Test getting evidence chain for pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MemoryBus(storage_dir=Path(tmpdir))

            # Create some events
            evt1 = bus.trace.log("evidence", {"n": 1})
            evt2 = bus.trace.log("evidence", {"n": 2})

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.8,
                alignment_score=0.8,
                blast_radius=BlastRadius.LOCAL
            )

            pattern_id = bus.add_pattern(
                "test", "Test", {}, {}, 0.7, [evt1, evt2], signals
            )

            chain = bus.get_evidence_chain(pattern_id)
            assert len(chain) == 2


class TestMemoryBusPersistence:
    """Tests for MemoryBus persistence."""

    def test_shared_persists(self):
        """Test shared memory persists across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.7,
                alignment_score=0.7,
                blast_radius=BlastRadius.LOCAL
            )

            # Write with first instance
            bus1 = MemoryBus(storage_dir=path)
            bus1.write_shared("key", "persisted_value", "source", signals)

            # Read with second instance
            bus2 = MemoryBus(storage_dir=path)
            result = bus2.read_shared("key")

            assert result == "persisted_value"

    def test_semantic_persists(self):
        """Test semantic memory persists across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)

            signals = WriteSignals(
                progress_delta=0.5,
                conflict_level=ConflictLevel.NONE,
                source_quality=0.8,
                alignment_score=0.8,
                blast_radius=BlastRadius.LOCAL
            )

            # Write with first instance
            bus1 = MemoryBus(storage_dir=path)
            pattern_id = bus1.add_pattern(
                "test", "Persistent pattern", {}, {}, 0.7, [], signals
            )

            # Read with second instance
            bus2 = MemoryBus(storage_dir=path)
            pattern = bus2.get_pattern(pattern_id)

            assert pattern is not None
            assert pattern.description == "Persistent pattern"
