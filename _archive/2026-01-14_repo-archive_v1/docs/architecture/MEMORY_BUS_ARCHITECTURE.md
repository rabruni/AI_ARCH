# Memory Bus Architecture

**Version:** 2.0
**Status:** Proposed (supersedes MEMORY_ARCHITECTURE_PROPOSAL.md)

---

## Core Design: Memory as a Bus with Compartments

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MEMORY BUS                                      │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  WORKING    │  │   SHARED    │  │  EPISODIC   │  │  SEMANTIC   │        │
│  │    SET      │  │  REFERENCE  │  │   TRACE     │  │  SYNTHESIS  │        │
│  │ (per-problem│  │ (cross-prob │  │ (time-index │  │ (distilled  │        │
│  │  hot, min)  │  │  stable)    │  │  append)    │  │  patterns)  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                    │                                        │
│                                    ▼                                        │
│                          ┌─────────────────┐                               │
│                          │   WRITE GATE    │                               │
│                          │  (policy layer) │                               │
│                          └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Compartment 1: Working Set (Per-Problem, Hot)

### Purpose
Hold what the current problem needs RIGHT NOW.

### Scope
Strictly namespaced to one "focus object" (problem_id).

### Lifetime
Minutes to hours. Expires aggressively.

### Contains

| Data | Description | Format |
|------|-------------|--------|
| **Constraints** | Current problem constraints | `{"must": [...], "must_not": [...]}` |
| **Assumptions** | Active assumptions | `[{"a": "...", "confidence": 0.8}]` |
| **Open Questions** | Unresolved questions | `["q1", "q2"]` |
| **Partial Artifacts** | Drafts, incomplete work | `{"draft": "...", "version": 1}` |
| **Local Decisions** | Decisions + rationale | `[{"d": "...", "why": "..."}]` |
| **Context Packet** | What model sees this turn | Compiled prompt context |

### Rules

1. **No cross-read**: Problem A cannot read Problem B's working set
2. **Export only summaries**: Raw data never leaves, only summaries
3. **Aggressive expiry**: Default TTL = 2 hours, max = 24 hours
4. **Problem ID required**: Every write must include `problem_id`

### Data Structure

```python
@dataclass
class WorkingSet:
    problem_id: str              # Unique problem identifier
    lane_id: Optional[str]       # If associated with a lane
    created_at: datetime
    expires_at: datetime
    constraints: dict
    assumptions: list[dict]
    open_questions: list[str]
    partial_artifacts: dict
    local_decisions: list[dict]
    context_packet: str          # Last compiled context

class WorkingSetStore:
    def create(problem_id: str, ttl_hours: int = 2) -> WorkingSet
    def get(problem_id: str) -> Optional[WorkingSet]
    def update(problem_id: str, **kwargs) -> None
    def expire_stale() -> int    # Returns count expired
    def export_summary(problem_id: str) -> str  # For promotion
    def isolate(problem_id: str) -> None  # Ensure no cross-read
```

### Why It Matters
This is what prevents "Problem A" from bleeding into "Problem B."

---

## Compartment 2: Shared Reference (Cross-Problem, Stable)

### Purpose
Reusable facts and canonical documents.

### Scope
Global, read-mostly.

### Lifetime
Long-lived. Updates are rare and deliberate.

### Contains

| Data | Description | Format |
|------|-------------|--------|
| **Canonical Definitions** | Glossaries, terms | `{"term": "definition"}` |
| **Standards/Specs** | Operating rules | Markdown or structured |
| **Preferences** | User preferences, constraints | `{"pref_key": value}` |
| **Trusted Tables** | Reference data | JSON tables |
| **North Stars** | Identity-level values | `["ns1", "ns2"]` |
| **Priorities** | Strategy-level goals | `["p1", "p2"]` |

### Rules

1. **Versioned**: Every update creates new version
2. **Citable**: Every fact has a source reference
3. **Gated updates**: Updates require Write Gate approval
4. **Read-mostly**: High read:write ratio expected

### Data Structure

```python
@dataclass
class SharedReference:
    key: str
    value: Any
    version: int
    source: str                  # Where this came from
    created_at: datetime
    updated_at: datetime
    updated_by: str              # Which HRM/agent updated

class SharedReferenceStore:
    def get(key: str, version: int = None) -> SharedReference
    def set(key: str, value: Any, source: str) -> int  # Returns new version
    def list_versions(key: str) -> list[int]
    def rollback(key: str, to_version: int) -> bool
    def cite(key: str) -> str    # Returns citation string
```

### Why It Matters
Multi-problem systems need a "common law" layer to stay coherent.

---

## Compartment 3: Episodic Trace (Time-Indexed, Audit)

### Purpose
"What happened when" - complete audit trail.

### Scope
Append-only logs.

### Lifetime
Long-lived, chunked by time period.

### Contains

| Data | Description | Format |
|------|-------------|--------|
| **Conversation Turns** | User/assistant exchanges | `{"role": "...", "content": "..."}` |
| **Tool Outputs** | Results from tool calls | `{"tool": "...", "result": "..."}` |
| **Retrieval Results** | What was retrieved | `{"query": "...", "results": [...]}` |
| **Decisions** | Decisions with timestamps | `{"decision": "...", "at": "..."}` |
| **Sources Used** | Which references cited | `["ref1", "ref2"]` |
| **Iteration Deltas** | What changed between iterations | `{"from": {...}, "to": {...}}` |

### Rules

1. **Never overwritten**: Only superseded, never deleted
2. **Searchable**: By time, tags, problem_id, HRM layer
3. **Feeds synthesis**: Raw data used to generate patterns
4. **Chunked storage**: New file per day/week

### Data Structure

```python
@dataclass
class EpisodeEntry:
    id: str                      # Unique entry ID
    timestamp: datetime
    problem_id: Optional[str]
    hrm_layer: str               # altitude|focus|reasoning|learning
    entry_type: str              # turn|tool|retrieval|decision|delta
    content: dict
    tags: list[str]
    supersedes: Optional[str]    # ID of entry this supersedes

class EpisodicTraceStore:
    def append(entry: EpisodeEntry) -> str  # Returns entry ID
    def query(
        start: datetime = None,
        end: datetime = None,
        problem_id: str = None,
        hrm_layer: str = None,
        entry_type: str = None,
        tags: list[str] = None
    ) -> list[EpisodeEntry]
    def supersede(old_id: str, new_entry: EpisodeEntry) -> str
    def get_chunk(date: date) -> list[EpisodeEntry]
    def export_for_synthesis(problem_id: str) -> list[EpisodeEntry]
```

### Why It Matters
This is the AI Accountability Framework expressed as memory.

---

## Compartment 4: Semantic Synthesis (Distilled, Portable)

### Purpose
Extracted patterns and "what we now believe."

### Scope
Global, structured by domain.

### Lifetime
Long-lived, rewritten periodically.

### Contains

| Data | Description | Format |
|------|-------------|--------|
| **Stable Conclusions** | What we've determined | `{"conclusion": "...", "evidence": [...]}` |
| **Compressed Heuristics** | Pattern codes | `{"code": "...", "meaning": "..."}` |
| **Policies** | "If X then Y" rules | `{"if": {...}, "then": {...}}` |
| **Episode Summaries** | Distilled episodes | `{"episode_ids": [...], "summary": "..."}` |
| **Behavioral Patterns** | User patterns | From memory_v2 PATTERN_CODES |
| **Coaching Patterns** | AI behavior | From memory_v2 COACHING_CODES |

### Rules

1. **Evidence linked**: Every conclusion points to episodic evidence
2. **Confidence + decay**: Confidence scores that decay over time
3. **Revalidation**: Periodically checked against new evidence
4. **No trim (per decision)**: Patterns persist until manual removal

### Data Structure

```python
@dataclass
class SynthesizedPattern:
    id: str
    pattern_type: str            # conclusion|heuristic|policy|summary
    content: dict
    evidence_ids: list[str]      # Links to EpisodeEntry IDs
    confidence: float
    created_at: datetime
    last_validated: datetime
    decay_rate: float            # How fast confidence decays
    protected: bool = False      # If true, never auto-remove

class SemanticSynthesisStore:
    def add_pattern(pattern: SynthesizedPattern) -> str
    def get_pattern(id: str) -> SynthesizedPattern
    def search(pattern_type: str = None, min_confidence: float = 0.0) -> list
    def strengthen(id: str, new_evidence_id: str) -> None
    def weaken(id: str, reason: str) -> None
    def decay_all() -> int       # Apply decay, return count affected
    def revalidate(id: str, still_valid: bool) -> None
    def get_evidence_chain(id: str) -> list[EpisodeEntry]
```

### Why It Matters
If you don't synthesize, episodic trace becomes a landfill.

---

## Compartment 5: Write Gate / Policy Layer

### Purpose
Decide what persists where, with what confidence.

### The Gate Decides

| Decision | Question |
|----------|----------|
| **Locality** | Is this local (Working Set) or global (Shared/Semantic)? |
| **Factuality** | Is it a draft or a fact? |
| **Confidence** | What threshold to persist? |
| **Expiry** | What decay/expiry rule applies? |
| **Safety** | Does this violate a trust boundary? |

### Signal Inputs (from HRM layers)

| Signal | Source | Meaning |
|--------|--------|---------|
| **Progress Delta** | All HRMs | Did we learn something new? |
| **Conflict Signal** | Reasoning HRM | Is it contested? |
| **Source Quality** | All HRMs | Was it grounded in evidence? |
| **Alignment Drift** | Altitude HRM | Was it relevant to goals? |
| **Blast Radius** | Focus HRM | If wrong, how damaging? |

### Data Structure

```python
@dataclass
class WriteRequest:
    source_hrm: str              # Which HRM is writing
    problem_id: Optional[str]    # If problem-scoped
    target_compartment: str      # working|shared|episodic|semantic
    data: dict
    signals: WriteSignals

@dataclass
class WriteSignals:
    progress_delta: float        # 0.0-1.0, how much learned
    conflict_level: str          # none|low|medium|high
    source_quality: float        # 0.0-1.0, groundedness
    alignment_score: float       # 0.0-1.0, relevance to goals
    blast_radius: str            # minimal|moderate|severe

@dataclass
class WriteDecision:
    approved: bool
    target_compartment: str      # May differ from request
    confidence_threshold: float
    expiry: Optional[datetime]
    reason: str

class WriteGate:
    def evaluate(request: WriteRequest) -> WriteDecision:
        # Rule 1: High blast radius → higher threshold
        if request.signals.blast_radius == "severe":
            min_confidence = 0.9
        elif request.signals.blast_radius == "moderate":
            min_confidence = 0.7
        else:
            min_confidence = 0.5

        # Rule 2: Conflict → Working Set only (don't pollute global)
        if request.signals.conflict_level in ["medium", "high"]:
            return WriteDecision(
                approved=True,
                target_compartment="working",
                confidence_threshold=min_confidence,
                expiry=datetime.now() + timedelta(hours=2),
                reason="Conflict detected, staying local"
            )

        # Rule 3: Low alignment → don't persist to Semantic
        if request.signals.alignment_score < 0.5:
            if request.target_compartment == "semantic":
                return WriteDecision(
                    approved=False,
                    target_compartment=None,
                    confidence_threshold=0,
                    expiry=None,
                    reason="Low alignment, won't synthesize"
                )

        # Rule 4: Low source quality → Episodic only (log, don't conclude)
        if request.signals.source_quality < 0.6:
            return WriteDecision(
                approved=True,
                target_compartment="episodic",
                confidence_threshold=0,
                expiry=None,
                reason="Low source quality, logging only"
            )

        # Default: approve as requested
        return WriteDecision(
            approved=True,
            target_compartment=request.target_compartment,
            confidence_threshold=min_confidence,
            expiry=self._calculate_expiry(request),
            reason="Approved"
        )
```

### Without This Gate, Memory Becomes

- Overwritten beliefs
- Stale facts treated as truths
- Cross-problem contamination
- "Confident nonsense" persistence

---

## Multi-Problem Support

### Current State: Serial (One Active Problem)

The current lane system provides context switching but:
- Only ONE lane active at a time
- No namespace isolation per problem
- Working memory bleeds across problems

### Target State: Parallel Problem Handling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROBLEM REGISTRY                                   │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Problem A   │  │ Problem B   │  │ Problem C   │  │ Problem D   │        │
│  │ (active)    │  │ (paused)    │  │ (paused)    │  │ (background)│        │
│  │             │  │             │  │             │  │             │        │
│  │ Working Set │  │ Working Set │  │ Working Set │  │ Working Set │        │
│  │ (isolated)  │  │ (isolated)  │  │ (isolated)  │  │ (isolated)  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                       │
│                    │      SHARED REFERENCE         │                       │
│                    │   (all problems can read)     │                       │
│                    └───────────────┬───────────────┘                       │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                       │
│                    │      EPISODIC TRACE           │                       │
│                    │   (tagged by problem_id)      │                       │
│                    └───────────────┬───────────────┘                       │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                       │
│                    │     SEMANTIC SYNTHESIS        │                       │
│                    │   (cross-problem patterns)    │                       │
│                    └───────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Problem States

| State | Description | Working Set | Can Execute |
|-------|-------------|-------------|-------------|
| **Active** | Currently being worked on | Hot, in-memory | Yes |
| **Paused** | Suspended, can resume | Warm, persisted | No |
| **Background** | Low-priority, monitoring | Cold, archived | No |
| **Completed** | Done, archived | Expired | No |

### Problem Isolation Rules

1. **Working Set**: Strictly namespaced to `problem_id`
2. **Cross-Read**: Only through Shared Reference or export
3. **Context Packet**: Built from ONE problem's Working Set only
4. **Switching**: Export summary to Episodic before switch

### Data Structure

```python
@dataclass
class Problem:
    problem_id: str
    name: str
    state: str                   # active|paused|background|completed
    lane_id: Optional[str]       # If associated with lane
    created_at: datetime
    last_active: datetime
    working_set: WorkingSet
    priority: int                # For scheduling

class ProblemRegistry:
    def create(name: str, priority: int = 5) -> Problem
    def get_active() -> Optional[Problem]
    def switch_to(problem_id: str) -> bool
    def pause(problem_id: str) -> bool
    def resume(problem_id: str) -> bool
    def complete(problem_id: str) -> bool
    def list_by_state(state: str) -> list[Problem]
    def get_working_set(problem_id: str) -> WorkingSet  # Isolated access
```

---

## Integration with Existing Systems

### Mapping to Current Components

| Bus Compartment | Current Component | Change Needed |
|-----------------|-------------------|---------------|
| Working Set | Hot tier + lanes | Add problem_id isolation |
| Shared Reference | memory_v2 (north_stars, priorities) | Add versioning, citation |
| Episodic Trace | history.py | Make append-only, add search |
| Semantic Synthesis | memory_v2 patterns + Learning HRM | Add evidence linking |
| Write Gate | consent.py | Add signal-based policy |

### Memory Manager API (Revised)

```python
class MemoryBus:
    def __init__(self):
        self.working_sets = WorkingSetStore()
        self.shared = SharedReferenceStore()
        self.episodic = EpisodicTraceStore()
        self.semantic = SemanticSynthesisStore()
        self.gate = WriteGate()
        self.problems = ProblemRegistry()
        self._lock = FileLock("memory.lock")  # Per decision: locking from start

    # Problem-scoped operations
    def write_to_working(self, problem_id: str, key: str, value: Any) -> bool:
        with self._lock:
            ws = self.working_sets.get(problem_id)
            if not ws:
                raise ValueError(f"No working set for problem {problem_id}")
            # Direct write to working set (no gate for local)
            ws.update(**{key: value})
            return True

    # Global operations (gated)
    def write_to_shared(self, key: str, value: Any, source: str, signals: WriteSignals) -> bool:
        request = WriteRequest(
            source_hrm=source,
            problem_id=None,
            target_compartment="shared",
            data={"key": key, "value": value},
            signals=signals
        )
        decision = self.gate.evaluate(request)
        if not decision.approved:
            return False
        with self._lock:
            self.shared.set(key, value, source)
            return True

    # Append-only operations
    def log_episode(self, entry: EpisodeEntry) -> str:
        with self._lock:
            return self.episodic.append(entry)

    # Synthesis operations (gated)
    def add_synthesis(self, pattern: SynthesizedPattern, signals: WriteSignals) -> Optional[str]:
        request = WriteRequest(
            source_hrm="learning",
            problem_id=None,
            target_compartment="semantic",
            data=pattern.__dict__,
            signals=signals
        )
        decision = self.gate.evaluate(request)
        if not decision.approved:
            return None
        with self._lock:
            return self.semantic.add_pattern(pattern)

    # Cross-compartment queries
    def get_evidence_chain(self, pattern_id: str) -> list[EpisodeEntry]:
        pattern = self.semantic.get_pattern(pattern_id)
        return [self.episodic.get(eid) for eid in pattern.evidence_ids]
```

---

## Token Efficiency (Preserved)

All compartments use compressed format from memory_v2:

```python
# Working Set constraint (compressed)
{"must": ["deadline:fri", "budget:<10k"], "must_not": ["vendor:acme"]}

# Shared Reference (compressed)
{"north_stars": ["family", "financial_ind", "impact"]}

# Episodic Entry (compressed)
{"t": "turn", "r": "user", "c": "help with patent", "tags": ["patent", "legal"]}

# Semantic Pattern (compressed)
{"code": "timeboxing", "conf": 0.9, "ev": ["ep_123", "ep_456"]}
```

---

## Migration Path

### Phase 1: Add Problem Registry
1. Create `ProblemRegistry` class
2. Wire to existing lane system
3. Add `problem_id` to all memory operations

### Phase 2: Split Working Set
1. Create `WorkingSetStore` with isolation
2. Migrate hot tier data to per-problem namespaces
3. Add TTL expiry

### Phase 3: Make Episodic Append-Only
1. Create `EpisodicTraceStore`
2. Migrate history.py to append-only
3. Add time-indexed search

### Phase 4: Add Versioning to Shared
1. Create `SharedReferenceStore`
2. Add version tracking to north_stars, priorities
3. Add citation capability

### Phase 5: Link Synthesis to Evidence
1. Update pattern storage to include `evidence_ids`
2. Migrate existing patterns
3. Add evidence chain queries

### Phase 6: Implement Write Gate
1. Create `WriteGate` with signal-based policy
2. Wire all writes through gate
3. Add blast radius estimation

---

## Success Criteria

- [ ] Working Sets are strictly isolated per problem_id
- [ ] No cross-problem contamination possible
- [ ] Episodic trace is append-only, never overwritten
- [ ] All Semantic patterns link to evidence
- [ ] Write Gate evaluates every global write
- [ ] Multi-problem support works (parallel problems)
- [ ] Token efficiency maintained (65%+ reduction)
- [ ] Locking prevents race conditions

---

## File Structure

```
shared/
├── memory/
│   ├── __init__.py
│   ├── bus.py                 # MemoryBus class
│   ├── working_set.py         # WorkingSetStore
│   ├── shared_reference.py    # SharedReferenceStore
│   ├── episodic_trace.py      # EpisodicTraceStore
│   ├── semantic_synthesis.py  # SemanticSynthesisStore
│   ├── write_gate.py          # WriteGate policy
│   ├── problem_registry.py    # ProblemRegistry
│   └── compression.py         # Token-efficient encoding (from memory_v2)
├── storage/
│   ├── working/               # Per-problem working sets
│   │   ├── problem_a.json
│   │   └── problem_b.json
│   ├── shared/                # Versioned shared reference
│   │   └── v{n}/
│   ├── episodic/              # Time-chunked logs
│   │   ├── 2026-01-13.jsonl
│   │   └── 2026-01-14.jsonl
│   └── semantic/              # Synthesized patterns
│       └── patterns.json
```
