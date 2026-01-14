# Unified Memory Architecture Proposal

## Current State: Fragmented

### Problem Summary
| Issue | Impact |
|-------|--------|
| 5 separate memory systems | No coordination, duplicate data |
| 50+ JSON files scattered | Hard to maintain, no consistency |
| No locking | Assumes single process (will break at scale) |
| Token optimization only in memory_v2 | Other systems waste tokens |
| No unified access | Each HRM accesses memory differently |
| No tracing | Can't debug memory operations |

### Current Memory Files (Audit Results)

**Altitude HRM (the_assist)**:
- `core/memory.py` - v1 prose-based (80% token waste)
- `core/memory_v2.py` - v2 compressed (60% savings)
- `hrm/history.py` - Session history
- `memory/store/` - 50+ JSON files
- `memory/state/` - 20+ checkpoint files

**Focus HRM (locked_system → HRM Routing)**:
- `memory/fast.py` - Fast loop state
- `memory/slow.py` - Slow loop state
- `memory/bridge.py` - Cross-loop signals
- `memory/history.py` - Gate transitions
- `memory/consent.py` - User consent

**Shared (AI_ARCH/memory/)**:
- Unclear ownership
- Duplicate of some locked_system files

---

## Proposed: Unified Memory Manager

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY MANAGER                           │
│                    (shared/memory/)                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  MemoryManager                                       │   │
│  │  • Single access point for all HRMs                  │   │
│  │  • Enforces compressed format everywhere             │   │
│  │  • Built-in tracing (trace_id on every operation)    │   │
│  │  • Optional locking for multi-process                │   │
│  │  • Consent-aware (checks before persist)             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Access Methods:                                            │
│  • manager.read(namespace, key) → compressed data           │
│  • manager.write(namespace, key, data) → trace_id           │
│  • manager.query(namespace, pattern) → results              │
│  • manager.subscribe(namespace, callback) → for signals     │
└─────────────────────────────────────────────────────────────┘
```

### Three-Tier Storage

| Tier | Storage | Access Pattern | TTL | Examples |
|------|---------|----------------|-----|----------|
| **HOT** | In-memory | Every turn | Session | Current state, signals, active threads |
| **WARM** | Fast JSON | On demand | Days | Patterns, history, people, coaching |
| **COLD** | Archive | Rare | Weeks+ | Old conversations, checkpoints, retrospectives |

### Namespace Segregation (Per HRM)

```yaml
namespaces:
  altitude:
    - session      # Current session state
    - history      # Session history (20 max)
    - patterns     # User behavior patterns
    - coaching     # AI behavior instructions

  focus:
    - fast         # Fast loop state
    - slow         # Slow loop state (commitment, decisions)
    - lanes        # Lane state
    - consent      # User consent preferences
    - gates        # Gate transition history

  reasoning:      # NEW
    - strategies   # Which strategies worked
    - escalations  # Escalation patterns
    - routing      # Routing decisions

  learning:       # NEW
    - patterns     # Learned patterns (signal→routing→outcome)
    - feedback     # What worked / didn't work
    - generalizations  # Abstracted patterns

  shared:
    - north_stars  # Identity (L4) - all HRMs read
    - priorities   # Strategy (L3) - all HRMs read
    - people       # Relationship data - shared
```

### Token Efficiency (Extended from memory_v2)

**Compressed Format (ALL data)**:
```python
# Instead of prose:
"John is a work colleague who often blocks progress and needs coordination"

# Use codes:
{"name": "john", "r": "wk", "t": ["bottleneck", "coord"], "n": 5}

# Token savings: ~70%
```

**Pattern Codes (Extended)**:
```python
PATTERN_CODES = {
    # Existing (from memory_v2)
    "timeboxing": "Uses timeboxing...",
    "exit_criteria": "Sets clear exit criteria...",

    # NEW: Reasoning patterns
    "needs_decomp": "Complex problems need decomposition",
    "quick_answer": "Simple questions, fast response",
    "verify_high_stakes": "High-stakes need verification",

    # NEW: Learning patterns
    "escalate_uncertain": "Escalate when uncertain",
    "deescalate_obvious": "De-escalate when obvious",
}
```

### Locking Strategy

```python
class MemoryManager:
    def __init__(self, enable_locking: bool = False):
        self._lock = FileLock("memory.lock") if enable_locking else None

    def write(self, namespace: str, key: str, data: dict, trace_id: str = None):
        if self._lock:
            with self._lock:
                return self._write_internal(namespace, key, data, trace_id)
        return self._write_internal(namespace, key, data, trace_id)
```

**When to lock**:
- Multi-process deployment: YES
- Single CLI session: NO (current state)
- Web server with multiple requests: YES

### Tracing Integration

Every memory operation returns/logs:
```python
{
    "trace_id": "mem_abc123",
    "operation": "write",
    "namespace": "altitude.patterns",
    "key": "timeboxing",
    "duration_ms": 2,
    "timestamp": "2026-01-13T...",
    "tokens_saved": 45  # vs prose equivalent
}
```

---

## Migration Plan

### Phase 1: Create MemoryManager
1. Create `shared/memory/manager.py`
2. Implement three-tier storage
3. Add tracing to every operation
4. Port memory_v2 compressed format

### Phase 2: Migrate Altitude HRM
1. Route `memory.py` calls through MemoryManager
2. Route `memory_v2.py` calls through MemoryManager
3. Keep files in place, add adapter layer
4. Delete `memory.py` (v1) after validation

### Phase 3: Migrate Focus HRM (HRM Routing)
1. Route `fast.py` through MemoryManager
2. Route `slow.py` through MemoryManager
3. Route `bridge.py` through MemoryManager
4. Consolidate consent handling

### Phase 4: Add Reasoning & Learning HRM
1. Create `reasoning` namespace
2. Create `learning` namespace
3. Extend pattern codes for new HRMs

### Phase 5: Cleanup
1. Remove duplicate files
2. Consolidate AI_ARCH/memory/ into shared/
3. Update all imports

---

## File Structure (After Migration)

```
shared/
├── memory/
│   ├── __init__.py
│   ├── manager.py          # MemoryManager class
│   ├── tiers.py            # Hot/Warm/Cold tier logic
│   ├── compression.py      # Token-efficient encoding
│   ├── tracing.py          # Trace logging
│   ├── locking.py          # Optional file locks
│   └── namespaces/
│       ├── altitude.py     # Altitude HRM namespace
│       ├── focus.py        # Focus HRM namespace
│       ├── reasoning.py    # Reasoning HRM namespace
│       ├── learning.py     # Learning HRM namespace
│       └── shared.py       # Cross-HRM data
├── storage/                # Actual data files
│   ├── hot/               # In-memory snapshots
│   ├── warm/              # Active JSON files
│   └── cold/              # Archives
└── integrity.py           # Boot/shutdown (moved from the_assist)
```

---

## Token Efficiency Targets

| Data Type | Current | Target | Method |
|-----------|---------|--------|--------|
| Patterns | 60% savings | 70% | Extended codes |
| History | 40% savings | 65% | Summary-only, rolling window |
| People | 50% savings | 75% | Relationship codes + tags |
| Signals | No compression | 60% | Enum codes |
| Routing decisions | N/A | 70% | Strategy codes |

**Overall target: 65% average token reduction**

---

## Consent Integration

```python
class MemoryManager:
    def write(self, namespace, key, data, trace_id=None):
        # Check consent before any persist
        if not self._consent.can_persist(namespace):
            # Store in HOT tier only (session-scoped)
            return self._hot_tier.write(namespace, key, data)

        # Full persist to appropriate tier
        return self._persist(namespace, key, data, trace_id)
```

---

## Success Criteria

1. ✅ Single access point for all memory operations
2. ✅ Token efficiency ≥65% across all data
3. ✅ Tracing on 100% of operations
4. ✅ No data loss during migration
5. ✅ Consent respected for all persists
6. ✅ Optional locking works correctly
7. ✅ All existing tests pass after migration
