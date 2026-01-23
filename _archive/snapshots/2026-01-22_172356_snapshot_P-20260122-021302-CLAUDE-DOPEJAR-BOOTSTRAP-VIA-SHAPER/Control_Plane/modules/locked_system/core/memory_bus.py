"""Memory Bus - Unified memory access with tier-based storage.

Four compartments unified under one interface:
- Working: Per-problem isolated, TTL-based
- Shared: Versioned, cross-problem facts
- Episodic: Append-only audit logs (via EpisodicTrace)
- Semantic: Evidence-linked patterns
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import uuid
import threading

from locked_system.core.types import (
    BlastRadius,
    ConflictLevel,
    HRMError,
    WriteSignals,
)
from locked_system.core.trace import EpisodicTrace, Event


# ─────────────────────────────────────────────────────────────
# Storage Tier Enum
# ─────────────────────────────────────────────────────────────

class Tier:
    """Memory tiers with different policies."""
    WORKING = "working"      # TTL, mutable, problem-scoped
    SHARED = "shared"        # Versioned, cross-problem
    EPISODIC = "episodic"    # Append-only, immutable
    SEMANTIC = "semantic"    # Versioned, evidence-linked


# ─────────────────────────────────────────────────────────────
# Data Types
# ─────────────────────────────────────────────────────────────

@dataclass
class WorkingEntry:
    """Entry in working set."""
    key: str
    value: Any
    problem_id: str
    created_at: datetime
    expires_at: datetime
    updated_at: datetime = None

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "problem_id": self.problem_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class SharedEntry:
    """Versioned entry in shared reference."""
    key: str
    value: Any
    version: int
    source: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "version": self.version,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SemanticEntry:
    """Evidence-linked pattern in semantic memory."""
    id: str
    pattern_type: str
    description: str
    input_signature: dict
    recommended_action: dict
    confidence: float
    evidence_ids: List[str]
    created_at: datetime
    last_strengthened_at: datetime

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "input_signature": self.input_signature,
            "recommended_action": self.recommended_action,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids,
            "created_at": self.created_at.isoformat(),
            "last_strengthened_at": self.last_strengthened_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────
# Write Gate
# ─────────────────────────────────────────────────────────────

class WriteGate:
    """Signal-based write policy decisions."""

    def __init__(
        self,
        blast_radius_threshold: float = 0.7,
        min_source_quality: float = 0.3,
        min_alignment: float = 0.4
    ):
        self.blast_radius_threshold = blast_radius_threshold
        self.min_source_quality = min_source_quality
        self.min_alignment = min_alignment

    def evaluate(self, tier: str, signals: WriteSignals) -> bool:
        """
        Evaluate whether write should proceed.

        Rules:
        1. Working: Always allowed (local scope)
        2. Episodic: Always allowed (append-only)
        3. Shared: Requires quality + alignment
        4. Semantic: Highest bar (quality + alignment + no conflict)
        """
        if tier == Tier.WORKING:
            return True  # No gate for local scope

        if tier == Tier.EPISODIC:
            return True  # Append-only always succeeds

        if tier == Tier.SHARED:
            # Check source quality and alignment
            if signals.source_quality < self.min_source_quality:
                return False
            if signals.alignment_score < self.min_alignment:
                return False
            # High blast radius requires higher thresholds
            if signals.blast_radius == BlastRadius.GLOBAL:
                return signals.source_quality > self.blast_radius_threshold
            return True

        if tier == Tier.SEMANTIC:
            # Highest bar: no conflicts, high quality
            if signals.conflict_level != ConflictLevel.NONE:
                return False
            if signals.source_quality < 0.5:
                return False
            if signals.alignment_score < 0.6:
                return False
            return True

        return False


# ─────────────────────────────────────────────────────────────
# Memory Bus
# ─────────────────────────────────────────────────────────────

class MemoryBus:
    """
    Unified memory access with file locking.

    All four compartments accessed through one interface.
    WriteGate controls writes to Shared and Semantic.
    """

    def __init__(
        self,
        storage_dir: Path = None,
        trace: EpisodicTrace = None,
        write_gate: WriteGate = None,
        default_ttl_hours: int = 2
    ):
        self.storage_dir = Path(storage_dir) if storage_dir else Path("./memory")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.trace = trace or EpisodicTrace(self.storage_dir / "trace.jsonl")
        self.write_gate = write_gate or WriteGate()
        self.default_ttl_hours = default_ttl_hours

        # In-memory caches
        self._working: Dict[str, Dict[str, WorkingEntry]] = {}  # problem_id -> key -> entry
        self._shared: Dict[str, SharedEntry] = {}
        self._shared_history: Dict[str, List[SharedEntry]] = {}  # For versioning
        self._semantic: Dict[str, SemanticEntry] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Load persistent data
        self._load()

    def _load(self):
        """Load persistent data from storage."""
        shared_file = self.storage_dir / "shared.json"
        if shared_file.exists():
            try:
                data = json.loads(shared_file.read_text())
                for key, entry_data in data.items():
                    entry_data["created_at"] = datetime.fromisoformat(entry_data["created_at"])
                    entry_data["updated_at"] = datetime.fromisoformat(entry_data["updated_at"])
                    self._shared[key] = SharedEntry(**entry_data)
            except Exception:
                pass

        semantic_file = self.storage_dir / "semantic.json"
        if semantic_file.exists():
            try:
                data = json.loads(semantic_file.read_text())
                for id_, entry_data in data.items():
                    entry_data["created_at"] = datetime.fromisoformat(entry_data["created_at"])
                    entry_data["last_strengthened_at"] = datetime.fromisoformat(entry_data["last_strengthened_at"])
                    self._semantic[id_] = SemanticEntry(**entry_data)
            except Exception:
                pass

    def _save_shared(self):
        """Persist shared memory."""
        shared_file = self.storage_dir / "shared.json"
        data = {k: v.to_dict() for k, v in self._shared.items()}
        shared_file.write_text(json.dumps(data, indent=2))

    def _save_semantic(self):
        """Persist semantic memory."""
        semantic_file = self.storage_dir / "semantic.json"
        data = {k: v.to_dict() for k, v in self._semantic.items()}
        semantic_file.write_text(json.dumps(data, indent=2))

    # ─────────────────────────────────────────────────────────
    # Working Set (problem-scoped, TTL)
    # ─────────────────────────────────────────────────────────

    def write_working(self, problem_id: str, key: str, value: Any) -> bool:
        """Write to problem-isolated Working Set. No gate required."""
        with self._lock:
            if problem_id not in self._working:
                self._working[problem_id] = {}

            now = datetime.now()
            self._working[problem_id][key] = WorkingEntry(
                key=key,
                value=value,
                problem_id=problem_id,
                created_at=now,
                expires_at=now + timedelta(hours=self.default_ttl_hours),
                updated_at=now
            )
            return True

    def read_working(self, problem_id: str, key: str) -> Optional[Any]:
        """Read from Working Set."""
        with self._lock:
            if problem_id in self._working and key in self._working[problem_id]:
                entry = self._working[problem_id][key]
                if not entry.is_expired():
                    return entry.value
                else:
                    del self._working[problem_id][key]
            return None

    def get_working_set(self, problem_id: str) -> Dict[str, Any]:
        """Get all entries for a problem."""
        with self._lock:
            if problem_id not in self._working:
                return {}
            return {
                k: v.value
                for k, v in self._working[problem_id].items()
                if not v.is_expired()
            }

    def expire_working(self) -> int:
        """Expire stale working set entries. Returns count removed."""
        with self._lock:
            count = 0
            for problem_id in list(self._working.keys()):
                for key in list(self._working[problem_id].keys()):
                    if self._working[problem_id][key].is_expired():
                        del self._working[problem_id][key]
                        count += 1
                if not self._working[problem_id]:
                    del self._working[problem_id]
            return count

    # ─────────────────────────────────────────────────────────
    # Shared Reference (versioned, cross-problem)
    # ─────────────────────────────────────────────────────────

    def write_shared(
        self,
        key: str,
        value: Any,
        source: str,
        signals: WriteSignals
    ) -> bool:
        """Write to Shared Reference. Requires WriteGate approval."""
        if not self.write_gate.evaluate(Tier.SHARED, signals):
            self.trace.log_write(
                target="shared",
                key=key,
                approved=False,
                problem_id=None
            )
            return False

        with self._lock:
            now = datetime.now()
            version = 1
            if key in self._shared:
                # Store history for versioning
                if key not in self._shared_history:
                    self._shared_history[key] = []
                self._shared_history[key].append(self._shared[key])
                version = self._shared[key].version + 1

            self._shared[key] = SharedEntry(
                key=key,
                value=value,
                version=version,
                source=source,
                created_at=now if version == 1 else self._shared_history[key][0].created_at,
                updated_at=now
            )
            self._save_shared()

        self.trace.log_write(target="shared", key=key, approved=True)
        return True

    def read_shared(self, key: str, version: int = None) -> Optional[Any]:
        """Read from Shared Reference."""
        with self._lock:
            if key in self._shared:
                entry = self._shared[key]
                if version is None or entry.version == version:
                    return entry.value
                # Check history for specific version
                if key in self._shared_history:
                    for hist in self._shared_history[key]:
                        if hist.version == version:
                            return hist.value
            return None

    def cite_shared(self, key: str) -> str:
        """Generate citation string for a shared reference."""
        if key in self._shared:
            entry = self._shared[key]
            return f"[shared:{key}@v{entry.version}]"
        return f"[shared:{key}:not_found]"

    # ─────────────────────────────────────────────────────────
    # Episodic Trace (append-only)
    # ─────────────────────────────────────────────────────────

    def log_episode(self, entry: Event) -> str:
        """Append to Episodic Trace. Always succeeds."""
        return self.trace.append(entry)

    def query_episodes(
        self,
        event_type: str = None,
        problem_id: str = None,
        start: datetime = None,
        limit: int = None
    ) -> List[Event]:
        """Query Episodic Trace."""
        return self.trace.query(
            event_type=event_type,
            problem_id=problem_id,
            start=start,
            limit=limit
        )

    # ─────────────────────────────────────────────────────────
    # Semantic Synthesis (evidence-linked patterns)
    # ─────────────────────────────────────────────────────────

    def add_pattern(
        self,
        pattern_type: str,
        description: str,
        input_signature: dict,
        recommended_action: dict,
        confidence: float,
        evidence_ids: List[str],
        signals: WriteSignals
    ) -> Optional[str]:
        """Add to Semantic Synthesis. Requires WriteGate approval."""
        if not self.write_gate.evaluate(Tier.SEMANTIC, signals):
            self.trace.log_write(target="semantic", key=pattern_type, approved=False)
            return None

        with self._lock:
            now = datetime.now()
            pattern_id = f"pat_{uuid.uuid4().hex[:12]}"

            self._semantic[pattern_id] = SemanticEntry(
                id=pattern_id,
                pattern_type=pattern_type,
                description=description,
                input_signature=input_signature,
                recommended_action=recommended_action,
                confidence=confidence,
                evidence_ids=evidence_ids,
                created_at=now,
                last_strengthened_at=now
            )
            self._save_semantic()

        self.trace.log_write(target="semantic", key=pattern_id, approved=True)
        return pattern_id

    def get_pattern(self, pattern_id: str) -> Optional[SemanticEntry]:
        """Get pattern by ID."""
        return self._semantic.get(pattern_id)

    def search_patterns(
        self,
        pattern_type: str = None,
        min_confidence: float = 0.0
    ) -> List[SemanticEntry]:
        """Search patterns with filters."""
        results = list(self._semantic.values())

        if pattern_type:
            results = [p for p in results if p.pattern_type == pattern_type]

        results = [p for p in results if p.confidence >= min_confidence]

        return sorted(results, key=lambda p: -p.confidence)

    def strengthen_pattern(self, pattern_id: str, evidence_id: str) -> bool:
        """Strengthen pattern with new evidence."""
        with self._lock:
            if pattern_id in self._semantic:
                entry = self._semantic[pattern_id]
                entry.evidence_ids.append(evidence_id)
                entry.confidence = min(1.0, entry.confidence + 0.05)
                entry.last_strengthened_at = datetime.now()
                self._save_semantic()
                return True
            return False

    def weaken_pattern(self, pattern_id: str, reason: str) -> bool:
        """Weaken pattern confidence."""
        with self._lock:
            if pattern_id in self._semantic:
                entry = self._semantic[pattern_id]
                entry.confidence = max(0.0, entry.confidence - 0.1)
                self.trace.log("pattern_weakened", {
                    "pattern_id": pattern_id,
                    "reason": reason,
                    "new_confidence": entry.confidence
                })
                self._save_semantic()
                return True
            return False

    def get_evidence_chain(self, pattern_id: str) -> List[Event]:
        """Get full evidence chain for a pattern."""
        if pattern_id not in self._semantic:
            return []

        pattern = self._semantic[pattern_id]
        return [
            self.trace.get(eid)
            for eid in pattern.evidence_ids
            if self.trace.get(eid) is not None
        ]
