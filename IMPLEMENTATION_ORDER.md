# Implementation Order

**Version:** 1.0
**Status:** Approved

This document specifies the exact order of implementation for DoPeJar components. Follow this order to minimize rework and ensure dependencies are satisfied.

---

## Guiding Principles

1. **Foundation First** - Shared infrastructure before HRM-specific code
2. **Interfaces Before Implementation** - Define contracts, then build
3. **Tests With Code** - Write tests alongside implementation
4. **Horizontal Before Vertical** - Core of each layer before depth
5. **No Orphans** - Don't build components that can't be used yet

---

## Phase 0: Setup (Day 0)

### 0.1 Create Directory Structure

```bash
# Execute in order
mkdir -p shared/memory
mkdir -p shared/tracing
mkdir -p shared/storage/{working,shared,episodic,synthesis}
mkdir -p the_assist/reasoning
mkdir -p the_assist/learning
mkdir -p the_assist/ui
mkdir -p the_assist/adapters
mkdir -p tests/{unit,integration,e2e,invariants,performance}
mkdir -p tests/unit/{altitude,reasoning,focus,learning,memory}
mkdir -p tests/integration

# Create __init__.py files
touch shared/__init__.py
touch shared/memory/__init__.py
touch shared/tracing/__init__.py
touch the_assist/reasoning/__init__.py
touch the_assist/learning/__init__.py
touch the_assist/ui/__init__.py
```

### 0.2 Create Base Files

```
shared/
├── __init__.py
├── types.py          # Shared enums and dataclasses
└── exceptions.py     # Base exception hierarchy
```

**File: shared/types.py**
- All enums from HRM_INTERFACE_SPECS.md Section 1.1
- HRMContext dataclass
- TurnInput dataclass

**File: shared/exceptions.py**
- HRMError base class
- All specific error classes from HRM_INTERFACE_SPECS.md Section 9.1

### 0.3 Set Up Test Infrastructure

```
tests/
├── conftest.py       # Fixtures from TEST_SPECIFICATIONS.md Section 7.1
├── helpers.py        # Helper functions from Section 7.2
└── pytest.ini        # Configuration from Section 8.2
```

---

## Phase 1: Memory Bus (M0.0) - Foundation

### Week 1: Core Memory Infrastructure

#### Step 1.1: Memory Bus Shell (Day 1)

**Create:** `shared/memory/bus.py`

```python
# Stub implementation
class MemoryBus:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "shared/storage"
        self._lock = threading.RLock()

    def write_to_working(self, problem_id, key, value) -> bool:
        raise NotImplementedError

    def write_to_shared(self, key, value, source, signals) -> WriteDecision:
        raise NotImplementedError

    def log_episode(self, entry) -> str:
        raise NotImplementedError

    def add_synthesis(self, pattern, signals) -> WriteDecision:
        raise NotImplementedError
```

**Test:** `tests/unit/memory/test_bus.py`
- Test instantiation works
- Test storage path creation

#### Step 1.2: Working Set Store (Days 2-3)

**Create:** `shared/memory/working_set.py`

```python
class WorkingSetStore:
    def create(self, problem_id: str, ttl_hours: int = 2) -> WorkingSet
    def get(self, problem_id: str) -> Optional[WorkingSet]
    def update(self, problem_id: str, **kwargs) -> None
    def expire_stale(self) -> int
    def export_summary(self, problem_id: str) -> str
```

**Implementation Order:**
1. WorkingSet dataclass
2. `create()` method with file storage
3. `get()` method
4. `update()` method
5. `expire_stale()` method
6. `export_summary()` method

**Tests:**
- test_create_working_set
- test_get_working_set
- test_update_working_set
- test_isolation_between_problems (INVARIANT)
- test_ttl_expiry
- test_export_summary

#### Step 1.3: Shared Reference Store (Days 4-5)

**Create:** `shared/memory/shared_reference.py`

```python
class SharedReferenceStore:
    def get(self, key: str, version: int = None) -> SharedReference
    def set(self, key: str, value: Any, source: str) -> int
    def list_versions(self, key: str) -> list[int]
    def rollback(self, key: str, to_version: int) -> bool
    def cite(self, key: str) -> str
```

**Implementation Order:**
1. SharedReference dataclass
2. Version storage structure (JSON with version array)
3. `set()` with auto-versioning
4. `get()` with version parameter
5. `list_versions()`
6. `rollback()`
7. `cite()`

**Tests:**
- test_set_creates_version
- test_versioning_increments (INVARIANT)
- test_get_specific_version
- test_rollback_works
- test_cite_format

#### Step 1.4: Episodic Trace Store (Days 6-7)

**Create:** `shared/memory/episodic_trace.py`

```python
class EpisodicTraceStore:
    def append(self, entry: EpisodeEntry) -> str
    def query(self, start, end, problem_id, tags, entry_type) -> list
    def supersede(self, old_id: str, new_entry: EpisodeEntry) -> str
    def get_chunk(self, date: date) -> list[EpisodeEntry]
```

**Implementation Order:**
1. EpisodeEntry dataclass
2. Date-based file storage (one file per day)
3. `append()` - always succeeds
4. `query()` with filters
5. `supersede()` - links old and new
6. `get_chunk()` for date ranges

**Tests:**
- test_append_always_succeeds
- test_append_only_no_delete (INVARIANT)
- test_query_by_time_range
- test_query_by_problem_id
- test_query_by_tags
- test_supersede_links_entries

### Week 2: Advanced Memory + WriteGate

#### Step 1.5: Semantic Synthesis Store (Days 8-9)

**Create:** `shared/memory/semantic_synthesis.py`

```python
class SemanticSynthesisStore:
    def add_pattern(self, pattern: SynthesizedPattern) -> str
    def get_pattern(self, id: str) -> SynthesizedPattern
    def search(self, pattern_type, min_confidence) -> list
    def strengthen(self, id: str, new_evidence_id: str) -> None
    def weaken(self, id: str, reason: str) -> None
    def get_evidence_chain(self, id: str) -> list[EpisodeEntry]
```

**Depends on:** EpisodicTraceStore (for evidence links)

**Implementation Order:**
1. SynthesizedPattern dataclass
2. `add_pattern()` with evidence validation
3. `get_pattern()`
4. `search()` with filters
5. `strengthen()` / `weaken()`
6. `get_evidence_chain()` - queries EpisodicTraceStore

**Tests:**
- test_add_pattern_requires_evidence (INVARIANT)
- test_get_pattern
- test_search_by_type
- test_strengthen_increases_confidence
- test_weaken_decreases_confidence
- test_evidence_chain_retrieval

#### Step 1.6: Write Gate (Days 10-11)

**Create:** `shared/memory/write_gate.py`

```python
class WriteGate:
    def evaluate(self, request: WriteRequest) -> WriteDecision
```

**Implementation Order:**
1. WriteSignals dataclass
2. WriteRequest dataclass
3. WriteDecision dataclass
4. Rule: High blast radius → deny without high confidence
5. Rule: Conflict → redirect to Working Set
6. Rule: Low alignment → block synthesis
7. Rule: Low source quality → Episodic only

**Tests:**
- test_high_blast_radius_denied
- test_conflict_redirects_to_working
- test_low_alignment_blocks_synthesis
- test_low_quality_episodic_only
- test_all_conditions_pass

#### Step 1.7: Problem Registry (Day 12)

**Create:** `shared/memory/problem_registry.py`

```python
class ProblemRegistry:
    def create(self, name: str, priority: int) -> Problem
    def get_active(self) -> Optional[Problem]
    def switch_to(self, problem_id: str) -> bool
    def pause(self, problem_id: str) -> bool
    def resume(self, problem_id: str) -> bool
    def complete(self, problem_id: str) -> bool
```

**Depends on:** WorkingSetStore, EpisodicTraceStore

**Tests:**
- test_create_problem
- test_only_one_active
- test_pause_exports_summary
- test_resume_restores_working_set
- test_complete_archives

#### Step 1.8: Complete Memory Bus (Day 13)

**Update:** `shared/memory/bus.py`

Wire all stores together:
- WorkingSetStore
- SharedReferenceStore
- EpisodicTraceStore
- SemanticSynthesisStore
- WriteGate
- ProblemRegistry

Add file locking (per user decision).

**Tests:**
- test_full_write_flow
- test_file_locking_prevents_corruption
- test_evidence_chain_works

#### Step 1.9: Migrate Compression (Day 14)

**Create:** `shared/memory/compression.py`

Migrate from `the_assist/core/memory_v2.py`:
- PATTERN_CODES
- COACHING_CODES
- Compression functions

**Update:** `the_assist/core/memory_v2.py` to import from new location.

### Week 3: Tracing Infrastructure

#### Step 1.10: Tracer (Days 15-16)

**Create:** `shared/tracing/tracer.py`

```python
class Tracer:
    _instance = None

    @classmethod
    def get(cls) -> 'Tracer':
        if cls._instance is None:
            cls._instance = Tracer()
        return cls._instance

    def span(self, hrm, operation, component, input_data) -> SpanContext
    def event(self, hrm, operation, status, data) -> None
    def generate_id(self, hrm) -> str
```

**Implementation Order:**
1. TraceEvent dataclass
2. SpanContext context manager
3. Singleton pattern
4. File output (trace.jsonl)
5. Enable/disable via DOPEJAR_TRACE env var

**Tests:**
- test_singleton_pattern
- test_span_context_manager
- test_event_logging
- test_parent_child_correlation
- test_disabled_by_default

#### Step 1.11: Trace Viewer (Day 17)

**Create:** `shared/tracing/viewer.py`

CLI tool for viewing traces:
```bash
python -m shared.tracing.viewer --last 100
python -m shared.tracing.viewer --hrm altitude
python -m shared.tracing.viewer --trace-id alt_123
```

**Tests:**
- test_filter_by_hrm
- test_filter_by_time
- test_show_trace_tree

#### Step 1.12: M0.0 Integration Tests (Day 18)

**Create:** `tests/integration/test_m0_0.py`

All memory bus integration tests from TEST_SPECIFICATIONS.md Section 4.4.

**Milestone Gate:** All M0.0 tests pass before proceeding.

---

## Phase 2: Integration (M0.1)

### Week 4: Wire Altitude ↔ Focus

#### Step 2.1: Study Existing Code (Day 19)

Read and understand:
- `the_assist/hrm/executor.py`
- `the_assist/hrm/planner.py`
- `the_assist/hrm/evaluator.py`
- `locked_system/slow_loop/gates.py`
- `locked_system/slow_loop/stance.py`

Document current interfaces and identify gaps.

#### Step 2.2: Wire Executor to Gates (Days 20-21)

**Update:** `the_assist/hrm/executor.py`

Add calls to:
- `locked_system/slow_loop/gates.py` WriteApprovalGate
- Memory Bus for writes

**Changes:**
```python
# Before any write
decision = self.gate_controller.attempt_gate(
    GateType.WRITE_APPROVAL,
    context={"signals": write_signals}
)
if decision.approved:
    self.memory_bus.write_to_*(...)
```

**Tests:**
- test_executor_checks_gate
- test_gate_denial_handled

#### Step 2.3: Wire Planner to Stance (Days 22-23)

**Update:** `the_assist/hrm/planner.py`

Add stance validation:
```python
# Check stance allows planned actions
current_stance = self.focus.stance_machine.get_current()
allowed_actions = self.focus.stance_machine.get_allowed_actions()
for step in plan.steps:
    if step.action_type not in allowed_actions:
        # Modify or reject plan
```

**Tests:**
- test_planner_queries_stance
- test_plans_respect_stance

#### Step 2.4: Wire Evaluator to Continuous Eval (Day 24)

**Update:** `the_assist/hrm/evaluator.py`

Connect to `locked_system/fast_loop/continuous_eval.py`.

**Tests:**
- test_evaluator_uses_continuous_eval
- test_results_influence_stance

#### Step 2.5: Create AgentApprovalGate (Days 25-26)

**Create:** `locked_system/slow_loop/agent_approval.py`

```python
class AgentApprovalGate:
    def evaluate(
        self,
        proposal: AgentBundleProposal,
        stance: Stance,
        commitment: Optional[Commitment]
    ) -> GateDecision
```

**Implementation Order:**
1. Stance compatibility check
2. Commitment alignment check
3. Agent authorization check
4. Orchestration mode constraints

**Tests:**
- test_stance_allows_matching_proposals
- test_stance_denies_mismatched
- test_commitment_alignment
- test_hierarchical_requires_delegation

#### Step 2.6: Update Agent Runtime (Days 27-28)

**Update:** `locked_system/agents/runtime.py`

Implement all 4 orchestration modes:
1. Pipeline - serial execution
2. Parallel - async with aggregation
3. Voting - consensus with threshold
4. Hierarchical - lead + delegates

**Tests:**
- test_pipeline_mode
- test_parallel_mode
- test_voting_mode
- test_hierarchical_mode
- test_all_through_firewall

#### Step 2.7: Memory Bus Adapters (Days 29-30)

**Create:** `shared/memory/adapters.py`

Adapters for existing memory:
- `locked_system/memory/fast.py` → WorkingSet
- `locked_system/memory/slow.py` → SharedReference

**Tests:**
- test_adapters_preserve_behavior

#### Step 2.8: Add Tracing (Day 31)

**Update:** All Altitude and Focus HRM files

Add trace events at key points:
```python
with tracer.span("altitude", "classify", "governor", input.text):
    result = self._do_classify(input)
    tracer.event("altitude", "classified", "completed",
                 {"level": result.level.value})
```

#### Step 2.9: M0.1 Integration Tests (Day 32)

**Create:** `tests/integration/test_m0_1.py`

All integration tests from TEST_SPECIFICATIONS.md Section 4.1-4.3.

**Milestone Gate:** All M0.1 tests pass.

---

## Phase 3: Consolidation (M0.2)

### Week 5: Clean Up

#### Step 3.1: Remove Duplicate Governance (Day 33)

**Delete:**
- `locked_system/core/governance/stance.py`
- `locked_system/core/governance/commitment.py`
- `locked_system/core/governance/gates.py`

**Update:** All imports to use `locked_system/slow_loop/` versions.

**Verify:** All tests still pass.

#### Step 3.2: Remove Duplicate Execution (Day 34)

**Delete:**
- `locked_system/core/execution/executor.py`
- `locked_system/core/execution/hrm.py`
- `locked_system/core/execution/continuous_eval.py`

**Update:** All imports to use `locked_system/fast_loop/` versions.

**Verify:** All tests still pass.

#### Step 3.3: Create UI Module (Day 35)

**Create:** `the_assist/ui/`

**Move:**
- `the_assist/core/formatter.py` → `the_assist/ui/formatter.py`
- `locked_system/cli/chat_ui.py` → `the_assist/ui/chat_ui.py`
- `locked_system/signals/display.py` → `the_assist/ui/signal_display.py`

**Update:** All imports.

#### Step 3.4: Create LLM Adapter (Days 36-37)

**Create:** `the_assist/adapters/llm.py`

```python
class LLMAdapter(Protocol):
    def chat(self, messages: list, system: str) -> str
    def stream(self, messages: list, system: str) -> Iterator[str]

class ClaudeAdapter(LLMAdapter): ...
class OpenAIAdapter(LLMAdapter): ...
```

**Create:** `the_assist/config/llm_config.yaml`

**Tests:**
- test_claude_adapter
- test_config_loading

#### Step 3.5: Fix Ungated Notes (Day 38)

**Delete:** `locked_system/notes.py`

**Update:** `locked_system/capabilities/note_capture/tool.py`
- Add WriteApprovalGate requirement
- Wire through governance

**Update:** Any code that called `notes.py` to use new gated tool.

**Tests:**
- test_note_capture_requires_approval (INVARIANT)

#### Step 3.6: Merge Entry Points (Day 39)

**Update:** `the_assist/main.py`

Single entry point that:
1. Loads configuration
2. Initializes Memory Bus
3. Initializes all HRMs (currently Altitude + Focus)
4. Runs main loop

**Delete:** (after verification)
- `the_assist/main_locked.py`

**Keep:** `the_assist/main_hrm.py` as alias for backwards compatibility.

#### Step 3.7: M0.2 Verification (Day 40)

Run all tests:
```bash
pytest tests/
```

Verify no broken imports, all functionality preserved.

---

## Phase 4: Reasoning HRM (M0.3)

### Week 6: Build Reasoning HRM

#### Step 4.1: Package Structure (Day 41)

**Create:**
```
the_assist/reasoning/
├── __init__.py
├── router.py         # Main router (stub)
├── classifier.py     # Input classifier
├── strategies.py     # Strategy definitions
├── escalation.py     # Escalation manager
└── proposals.py      # Agent bundle proposals
```

#### Step 4.2: Input Classifier (Days 42-43)

**Implement:** `the_assist/reasoning/classifier.py`

```python
class InputClassifier:
    def classify(self, input: TurnInput) -> InputClassification
```

**Implementation Order:**
1. InputClassification dataclass
2. Complexity detection
3. Uncertainty estimation
4. Conflict detection
5. Stakes assessment
6. Domain classification

**Tests:**
- test_classify_simple_input
- test_classify_complex_input
- test_classify_conflicting_input
- test_should_escalate

#### Step 4.3: Strategy Selector (Days 44-45)

**Implement:** `the_assist/reasoning/strategies.py`

```python
class StrategySelector:
    def select(
        self,
        classification: InputClassification,
        pattern_matches: list[PatternMatch]
    ) -> StrategySelection
```

**Strategies:**
- QUICK_ANSWER
- DECOMPOSITION
- VERIFICATION
- EXPLORATION
- DIALOGUE

**Tests:**
- test_quick_answer_for_simple
- test_decomposition_for_complex
- test_verification_for_high_stakes
- test_pattern_match_overrides

#### Step 4.4: Escalation Manager (Day 46)

**Implement:** `the_assist/reasoning/escalation.py`

```python
class EscalationManager:
    THRESHOLD = 0.6  # Per user decision

    def should_escalate(self, classification, strategy) -> bool
    def escalate(self, strategy) -> StrategySelection
    def should_deescalate(self, strategy, pattern_confidence) -> bool
    def deescalate(self, strategy) -> StrategySelection
```

**Tests:**
- test_escalate_below_threshold
- test_no_escalate_above_threshold
- test_deescalate_on_pattern_match

#### Step 4.5: Agent Bundle Proposals (Day 47)

**Implement:** `the_assist/reasoning/proposals.py`

```python
def generate_proposal(
    strategy: StrategySelection,
    classification: InputClassification
) -> Optional[AgentBundleProposal]
```

**Mapping:**
- QUICK_ANSWER → No agents or single
- DECOMPOSITION → Hierarchical
- VERIFICATION → Voting
- EXPLORATION → Parallel
- DIALOGUE → Pipeline

**Tests:**
- test_quick_answer_no_agents
- test_decomposition_hierarchical
- test_verification_voting
- test_exploration_parallel

#### Step 4.6: Reasoning Router (Days 48-49)

**Implement:** `the_assist/reasoning/router.py`

```python
class ReasoningRouter:
    def __init__(
        self,
        classifier: InputClassifier,
        selector: StrategySelector,
        escalation: EscalationManager,
        learning_hrm: Optional[LearningHRM] = None
    ):
        ...

    def route(self, input: TurnInput) -> RoutingDecision
    def propose_agents(self, input: TurnInput) -> Optional[AgentBundleProposal]
```

**Flow:**
1. Classify input
2. Query Learning HRM for patterns (if available)
3. Select strategy
4. Check escalation
5. Generate proposal if needed

**Tests:**
- test_full_routing_flow
- test_pattern_queries_learning
- test_proposals_generated

#### Step 4.7: Add Tracing (Day 50)

**Update:** All Reasoning HRM files

Add trace events:
- reasoning.classify
- reasoning.strategy_select
- reasoning.escalate
- reasoning.propose_agents

#### Step 4.8: M0.3 Integration (Days 51-52)

**Update:** `the_assist/main.py`

Wire Reasoning HRM into boot sequence and main loop.

**Create:** `tests/integration/test_m0_3.py`

Integration tests for Reasoning ↔ Focus flow.

---

## Phase 5: Learning HRM (M0.4)

### Week 7: Build Learning HRM

#### Step 5.1: Package Structure (Day 53)

**Create:**
```
the_assist/learning/
├── __init__.py
├── patterns.py       # Pattern store
├── feedback_loop.py  # Feedback and analysis
└── generalizer.py    # Pattern generalization
```

#### Step 5.2: Pattern Store (Days 54-55)

**Implement:** `the_assist/learning/patterns.py`

```python
class PatternStore:
    def __init__(self, synthesis_store: SemanticSynthesisStore):
        ...

    def add_pattern(self, pattern: Pattern) -> str
    def get_pattern(self, id: str) -> Optional[Pattern]
    def search(self, input_signature: dict) -> list[PatternMatch]
    def strengthen(self, id: str) -> None
    def weaken(self, id: str) -> None
    def protect(self, id: str) -> None  # No auto-trim per decision
```

**Note:** Uses SemanticSynthesisStore as underlying storage.

**Tests:**
- test_add_pattern
- test_search_by_signature
- test_strengthen_increases_confidence
- test_weaken_decreases_confidence
- test_no_auto_trim (INVARIANT)

#### Step 5.3: Feedback Loop (Days 56-57)

**Implement:** `the_assist/learning/feedback_loop.py`

```python
class FeedbackLoop:
    def __init__(self, pattern_store: PatternStore, episodic_store: EpisodicTraceStore):
        ...

    def record_outcome(self, signal, routing, outcome) -> str
    def analyze_session(self) -> SessionAnalysis
    def get_patterns_for_signal(self, signal: dict) -> list[PatternMatch]
```

**Learning Cycle:**
1. Record signal→routing→outcome
2. At session end: analyze
3. Strengthen successful patterns
4. Weaken failed patterns
5. Create new patterns (3+ successes)

**Tests:**
- test_record_outcome
- test_analyze_session
- test_pattern_creation_after_3_successes
- test_patterns_queryable

#### Step 5.4: Generalizer (Days 58-59)

**Implement:** `the_assist/learning/generalizer.py`

```python
class Generalizer:
    def find_similar(self, patterns: list[Pattern]) -> list[tuple]
    def merge(self, p1: Pattern, p2: Pattern) -> Pattern
    def generalize_batch(self, patterns: list[Pattern]) -> list[Pattern]
```

**Tests:**
- test_find_similar_patterns
- test_merge_preserves_evidence
- test_batch_processing

#### Step 5.5: Learning HRM Main Class (Day 60)

**Create:** `the_assist/learning/__init__.py`

```python
class LearningHRM:
    def __init__(self, memory_bus: MemoryBus):
        self.pattern_store = PatternStore(memory_bus.synthesis_store)
        self.feedback_loop = FeedbackLoop(
            self.pattern_store,
            memory_bus.episodic_store
        )
        self.generalizer = Generalizer()

    # Public interface
    def record_outcome(self, signal, routing, outcome) -> str
    def get_patterns_for_signal(self, signal: dict) -> list[PatternMatch]
    def analyze_session(self) -> SessionAnalysis
```

#### Step 5.6: Wire to Reasoning HRM (Day 61)

**Update:** `the_assist/reasoning/router.py`

```python
class ReasoningRouter:
    def __init__(self, ..., learning_hrm: LearningHRM):
        self.learning_hrm = learning_hrm

    def route(self, input):
        # Query patterns
        patterns = self.learning_hrm.get_patterns_for_signal(
            self._extract_signature(input)
        )
        ...
```

#### Step 5.7: Add Tracing (Day 62)

**Update:** All Learning HRM files

Trace events:
- learning.pattern_match
- learning.pattern_add
- learning.strengthen
- learning.weaken
- learning.generalize

#### Step 5.8: M0.4 Integration Tests (Day 63)

**Create:** `tests/integration/test_m0_4.py`

Tests from TEST_SPECIFICATIONS.md Section 4.3.

---

## Phase 6: Unified System (M1.0)

### Week 8: Final Integration

#### Step 6.1: Unified Main Entry (Days 64-65)

**Update:** `the_assist/main.py`

Complete boot sequence:
```python
def boot():
    # 1. Load configuration
    config = load_config()

    # 2. Initialize Memory Bus
    memory_bus = MemoryBus(config.storage_path)

    # 3. Initialize Focus HRM
    focus = FocusHRM()

    # 4. Initialize Altitude HRM
    altitude = AltitudeGovernor()

    # 5. Initialize Reasoning HRM
    reasoning = ReasoningRouter(
        classifier=InputClassifier(),
        selector=StrategySelector(),
        escalation=EscalationManager(),
        learning_hrm=None  # Will be set after Learning init
    )

    # 6. Initialize Learning HRM
    learning = LearningHRM(memory_bus)
    reasoning.learning_hrm = learning

    # 7. Wire callbacks
    wire_callbacks(altitude, reasoning, focus, learning)

    # 8. Start main loop
    return MainLoop(altitude, reasoning, focus, learning, memory_bus)
```

#### Step 6.2: End-to-End Tests (Days 66-67)

**Create:** `tests/e2e/test_full_cycle.py`

All E2E tests from TEST_SPECIFICATIONS.md Section 5.

#### Step 6.3: Performance Tests (Day 68)

**Create:** `tests/performance/test_latency.py`

Verify targets:
- Turn latency < 2s (excluding LLM)
- Memory operation < 10ms
- Trace overhead < 1ms
- Pattern query < 50ms

#### Step 6.4: Error Recovery Tests (Day 69)

**Create:** `tests/e2e/test_error_recovery.py`

Test graceful handling of:
- Gate denials
- Agent timeouts
- Memory write failures

#### Step 6.5: Documentation (Days 70-71)

**Update:**
- README.md with quick start
- DOPEJAR_ARCHITECTURE.md - verify accuracy
- Configuration guide
- Troubleshooting guide

#### Step 6.6: Final Verification (Day 72)

Run complete test suite:
```bash
pytest tests/ --cov --cov-report=html
```

Verify:
- All tests pass
- Coverage targets met
- No performance regressions

---

## Implementation Checklist

### M0.0 Foundation

- [ ] shared/types.py
- [ ] shared/exceptions.py
- [ ] shared/memory/bus.py (shell)
- [ ] shared/memory/working_set.py
- [ ] shared/memory/shared_reference.py
- [ ] shared/memory/episodic_trace.py
- [ ] shared/memory/semantic_synthesis.py
- [ ] shared/memory/write_gate.py
- [ ] shared/memory/problem_registry.py
- [ ] shared/memory/bus.py (complete)
- [ ] shared/memory/compression.py
- [ ] shared/tracing/tracer.py
- [ ] shared/tracing/viewer.py
- [ ] tests/integration/test_m0_0.py

### M0.1 Integration

- [ ] Wire executor.py to gates.py
- [ ] Wire planner.py to stance
- [ ] Wire evaluator.py to continuous_eval
- [ ] locked_system/slow_loop/agent_approval.py
- [ ] Update agents/runtime.py (4 modes)
- [ ] shared/memory/adapters.py
- [ ] Add tracing to Altitude/Focus
- [ ] tests/integration/test_m0_1.py

### M0.2 Consolidation

- [ ] Remove duplicate governance files
- [ ] Remove duplicate execution files
- [ ] Create the_assist/ui/ module
- [ ] the_assist/adapters/llm.py
- [ ] Fix ungated notes.py
- [ ] Merge entry points

### M0.3 Reasoning HRM

- [ ] the_assist/reasoning/__init__.py
- [ ] the_assist/reasoning/classifier.py
- [ ] the_assist/reasoning/strategies.py
- [ ] the_assist/reasoning/escalation.py
- [ ] the_assist/reasoning/proposals.py
- [ ] the_assist/reasoning/router.py
- [ ] Add tracing
- [ ] tests/integration/test_m0_3.py

### M0.4 Learning HRM

- [ ] the_assist/learning/__init__.py
- [ ] the_assist/learning/patterns.py
- [ ] the_assist/learning/feedback_loop.py
- [ ] the_assist/learning/generalizer.py
- [ ] Wire to Reasoning HRM
- [ ] Add tracing
- [ ] tests/integration/test_m0_4.py

### M1.0 Unified

- [ ] Unified main.py entry
- [ ] tests/e2e/test_full_cycle.py
- [ ] tests/performance/test_latency.py
- [ ] tests/e2e/test_error_recovery.py
- [ ] Documentation updates
- [ ] Final verification

---

## Critical Path Dependencies

```
shared/types.py
    ↓
shared/memory/bus.py (shell)
    ↓
┌───────────────────────────────────────┐
│  WorkingSet  SharedRef  Episodic      │  (parallel)
└───────────────────────────────────────┘
    ↓
SemanticSynthesis (needs Episodic)
    ↓
WriteGate
    ↓
MemoryBus (complete)
    ↓
┌───────────────────────────────────────┐
│  Altitude↔Focus wiring               │
│  AgentApprovalGate                   │
│  AgentRuntime (4 modes)              │
└───────────────────────────────────────┘
    ↓
Reasoning HRM
    ↓
Learning HRM
    ↓
Unified System
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Memory corruption | File locking from Day 1 |
| Broken imports after refactor | Update imports immediately after each move |
| Performance regression | Run perf tests after each phase |
| Integration failures | Integration tests gate each milestone |
| Authority leaks | Invariant tests run on every build |

---

## Success Metrics Per Milestone

| Milestone | Success Criteria |
|-----------|------------------|
| M0.0 | All memory invariants pass, file locking works |
| M0.1 | Altitude ↔ Focus fully wired, 4 orchestration modes work |
| M0.2 | No duplicate files, all imports work, LLM adapter works |
| M0.3 | Reasoning routes correctly, patterns influence routing |
| M0.4 | Learning records outcomes, patterns created from success |
| M1.0 | Full cycle works, latency targets met, no memory leaks |
