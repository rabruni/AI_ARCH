# GitHub Project Setup

Execute these commands to set up the complete GitHub project structure.

---

## 1. Create Labels

```bash
# HRM Layers
gh label create "altitude-hrm" --color "0052CC" --description "Altitude HRM (scope governance)"
gh label create "reasoning-hrm" --color "5319E7" --description "Reasoning HRM (strategy selection)"
gh label create "focus-hrm" --color "0E8A16" --description "Focus HRM (control governance)"
gh label create "learning-hrm" --color "D93F0B" --description "Learning HRM (pattern memory)"

# Component Types
gh label create "memory" --color "FBCA04" --description "Memory bus components"
gh label create "agents" --color "C2E0C6" --description "Agent runtime/orchestration"
gh label create "gates" --color "F9D0C4" --description "Gate system"
gh label create "tracing" --color "D4C5F9" --description "Observability/tracing"
gh label create "tests" --color "BFD4F2" --description "Test coverage"

# Priority
gh label create "p0-blocking" --color "B60205" --description "Must be done first"
gh label create "p1-core" --color "D93F0B" --description "Core functionality"
gh label create "p2-enhancement" --color "FBCA04" --description "Enhancement"
gh label create "p3-cleanup" --color "C5DEF5" --description "Cleanup/refactor"

# Type
gh label create "feature" --color "A2EEEF" --description "New feature"
gh label create "bug" --color "D73A4A" --description "Bug fix"
gh label create "docs" --color "0075CA" --description "Documentation"
gh label create "integration" --color "7057FF" --description "Integration work"
gh label create "spec" --color "E4E669" --description "Specification"
```

---

## 2. Create Milestones

```bash
gh api repos/:owner/:repo/milestones -f title="M0.0 Foundation" -f description="Memory Bus + Tracing infrastructure" -f due_on="2026-02-01T00:00:00Z"
gh api repos/:owner/:repo/milestones -f title="M0.1 Integration" -f description="Wire Altitude ↔ Focus HRMs" -f due_on="2026-02-15T00:00:00Z"
gh api repos/:owner/:repo/milestones -f title="M0.2 Consolidation" -f description="Remove duplicates, create UI module" -f due_on="2026-03-01T00:00:00Z"
gh api repos/:owner/:repo/milestones -f title="M0.3 Reasoning HRM" -f description="Build strategy selection layer" -f due_on="2026-03-15T00:00:00Z"
gh api repos/:owner/:repo/milestones -f title="M0.4 Learning HRM" -f description="Build pattern memory layer" -f due_on="2026-04-01T00:00:00Z"
gh api repos/:owner/:repo/milestones -f title="M1.0 Unified" -f description="Single entry point, all 4 HRMs working" -f due_on="2026-04-15T00:00:00Z"
```

---

## 3. Create Issues by Milestone

### M0.0 Foundation (12 issues)

```bash
# Memory Bus Core
gh issue create --title "[M0.0] Create shared/memory/ package structure" \
  --body "$(cat <<'EOF'
## Summary
Create the foundational package structure for Memory Bus.

## Files to Create
- `shared/memory/__init__.py`
- `shared/memory/bus.py` - MemoryBus main class
- `shared/storage/` - Storage directories

## Acceptance Criteria
- [ ] Package imports work
- [ ] MemoryBus class instantiates
- [ ] Storage directories created on init

## Dependencies
None (first task)
EOF
)" --label "memory,p0-blocking,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Implement WorkingSetStore" \
  --body "$(cat <<'EOF'
## Summary
Per-problem isolated memory with TTL expiry.

## Interface
```python
class WorkingSetStore:
    def create(problem_id: str, ttl_hours: int = 2) -> WorkingSet
    def get(problem_id: str) -> Optional[WorkingSet]
    def update(problem_id: str, **kwargs) -> None
    def expire_stale() -> int
    def export_summary(problem_id: str) -> str
```

## Acceptance Criteria
- [ ] Working sets are isolated per problem_id
- [ ] TTL expiry works correctly
- [ ] No cross-problem reads possible
- [ ] Export creates valid summary

## Dependencies
- shared/memory/ package structure
EOF
)" --label "memory,p0-blocking,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Implement SharedReferenceStore" \
  --body "$(cat <<'EOF'
## Summary
Versioned, citable cross-problem facts storage.

## Interface
```python
class SharedReferenceStore:
    def get(key: str, version: int = None) -> SharedReference
    def set(key: str, value: Any, source: str) -> int  # Returns version
    def list_versions(key: str) -> list[int]
    def rollback(key: str, to_version: int) -> bool
    def cite(key: str) -> str
```

## Acceptance Criteria
- [ ] Every update creates new version
- [ ] Old versions retrievable
- [ ] Rollback works
- [ ] Citation format correct

## Dependencies
- shared/memory/ package structure
EOF
)" --label "memory,p0-blocking,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Implement EpisodicTraceStore" \
  --body "$(cat <<'EOF'
## Summary
Append-only audit logs with time-indexed search.

## Interface
```python
class EpisodicTraceStore:
    def append(entry: EpisodeEntry) -> str
    def query(start: datetime, end: datetime, problem_id: str, ...) -> list
    def supersede(old_id: str, new_entry: EpisodeEntry) -> str
    def get_chunk(date: date) -> list[EpisodeEntry]
```

## Acceptance Criteria
- [ ] Entries are append-only (never deleted)
- [ ] Supersede creates new entry, marks old
- [ ] Query by time range works
- [ ] Query by problem_id works
- [ ] Query by tags works

## Dependencies
- shared/memory/ package structure
EOF
)" --label "memory,p0-blocking,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Implement SemanticSynthesisStore" \
  --body "$(cat <<'EOF'
## Summary
Evidence-linked pattern storage.

## Interface
```python
class SemanticSynthesisStore:
    def add_pattern(pattern: SynthesizedPattern) -> str
    def get_pattern(id: str) -> SynthesizedPattern
    def search(pattern_type: str, min_confidence: float) -> list
    def strengthen(id: str, new_evidence_id: str) -> None
    def weaken(id: str, reason: str) -> None
    def get_evidence_chain(id: str) -> list[EpisodeEntry]
```

## Acceptance Criteria
- [ ] Patterns link to evidence IDs
- [ ] Evidence chain retrievable
- [ ] Strengthen/weaken adjust confidence
- [ ] Search by type and confidence works

## Dependencies
- shared/memory/ package structure
- EpisodicTraceStore (for evidence links)
EOF
)" --label "memory,p1-core,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Implement WriteGate policy" \
  --body "$(cat <<'EOF'
## Summary
Signal-based write policy decisions.

## Interface
```python
class WriteGate:
    def evaluate(request: WriteRequest) -> WriteDecision

@dataclass
class WriteSignals:
    progress_delta: float
    conflict_level: str
    source_quality: float
    alignment_score: float
    blast_radius: str
```

## Gate Rules
1. High blast radius → higher confidence threshold
2. Conflict detected → Working Set only
3. Low alignment → won't synthesize
4. Low source quality → Episodic only

## Acceptance Criteria
- [ ] All rules implemented
- [ ] Signals correctly influence decision
- [ ] WriteDecision includes reason

## Dependencies
- All 4 compartment stores
EOF
)" --label "memory,p0-blocking,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Implement ProblemRegistry" \
  --body "$(cat <<'EOF'
## Summary
Multi-problem management with state tracking.

## Interface
```python
class ProblemRegistry:
    def create(name: str, priority: int) -> Problem
    def get_active() -> Optional[Problem]
    def switch_to(problem_id: str) -> bool
    def pause(problem_id: str) -> bool
    def resume(problem_id: str) -> bool
    def complete(problem_id: str) -> bool
```

## Problem States
- active: Currently being worked on
- paused: Suspended, can resume
- background: Low-priority monitoring
- completed: Done, archived

## Acceptance Criteria
- [ ] Only one active problem at a time
- [ ] Pause exports summary to Episodic
- [ ] Resume restores Working Set
- [ ] State transitions logged

## Dependencies
- WorkingSetStore
- EpisodicTraceStore
EOF
)" --label "memory,p1-core,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Implement MemoryBus main class" \
  --body "$(cat <<'EOF'
## Summary
Unified memory access with file locking.

## Interface
```python
class MemoryBus:
    def write_to_working(problem_id: str, key: str, value: Any) -> bool
    def write_to_shared(key: str, value: Any, source: str, signals: WriteSignals) -> bool
    def log_episode(entry: EpisodeEntry) -> str
    def add_synthesis(pattern: SynthesizedPattern, signals: WriteSignals) -> str
    def get_evidence_chain(pattern_id: str) -> list[EpisodeEntry]
```

## Acceptance Criteria
- [ ] File locking prevents race conditions
- [ ] All writes go through appropriate store
- [ ] Global writes go through WriteGate
- [ ] Evidence chain queries work

## Dependencies
- All compartment stores
- WriteGate
- ProblemRegistry
EOF
)" --label "memory,p0-blocking,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Migrate compression.py from memory_v2" \
  --body "$(cat <<'EOF'
## Summary
Move token-efficient encoding to shared/memory/.

## Files
- Source: `the_assist/core/memory_v2.py` (PATTERN_CODES, COACHING_CODES)
- Target: `shared/memory/compression.py`

## Acceptance Criteria
- [ ] All PATTERN_CODES migrated
- [ ] All COACHING_CODES migrated
- [ ] Compression functions work
- [ ] Old file updated to import from new location

## Dependencies
- shared/memory/ package structure
EOF
)" --label "memory,p1-core,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Create shared/tracing/ package" \
  --body "$(cat <<'EOF'
## Summary
Observability infrastructure.

## Interface
```python
class Tracer:
    def span(hrm: str, operation: str, component: str, input_data: str)
    def event(hrm: str, operation: str, ...)
    def generate_id(hrm: str) -> str

# Enable via
export DOPEJAR_TRACE=1
```

## Acceptance Criteria
- [ ] Tracer singleton works
- [ ] Span context manager works
- [ ] Events logged to trace.jsonl
- [ ] Parent/child correlation works
- [ ] Disabled by default

## Dependencies
None
EOF
)" --label "tracing,p1-core,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Create trace viewer CLI" \
  --body "$(cat <<'EOF'
## Summary
CLI tool to view and filter traces.

## Commands
```bash
python -m shared.tracing.viewer --last 100
python -m shared.tracing.viewer --hrm altitude
python -m shared.tracing.viewer --status error
python -m shared.tracing.viewer --trace-id alt_123
```

## Acceptance Criteria
- [ ] Filter by HRM layer
- [ ] Filter by status
- [ ] Filter by time range
- [ ] Show trace tree for ID

## Dependencies
- Tracer implementation
EOF
)" --label "tracing,p2-enhancement,feature" --milestone "M0.0 Foundation"

gh issue create --title "[M0.0] Write M0.0 integration tests" \
  --body "$(cat <<'EOF'
## Summary
Integration tests for Memory Bus.

## Test Cases
1. Working Set isolation - Problem A cannot read Problem B
2. Version history - SharedReference versions accumulate
3. Append-only - EpisodicTrace never overwrites
4. Evidence chain - Synthesis links to episodes
5. Write Gate - Policy rules enforced
6. File locking - Concurrent writes safe

## Acceptance Criteria
- [ ] All test cases pass
- [ ] Coverage > 80%
- [ ] Tests run in CI

## Dependencies
- All M0.0 components
EOF
)" --label "tests,p0-blocking,feature" --milestone "M0.0 Foundation"
```

### M0.1 Integration (8 issues)

```bash
gh issue create --title "[M0.1] Wire executor.py to gates.py" \
  --body "$(cat <<'EOF'
## Summary
Connect Altitude HRM executor to Focus HRM gates.

## Changes
- `the_assist/hrm/executor.py` calls `locked_system/slow_loop/gates.py`
- All writes require WriteApprovalGate

## Acceptance Criteria
- [ ] Executor checks gate before any write
- [ ] Gate denials handled gracefully
- [ ] Trace events emitted

## Dependencies
- M0.0 complete
EOF
)" --label "integration,altitude-hrm,focus-hrm,p0-blocking" --milestone "M0.1 Integration"

gh issue create --title "[M0.1] Wire planner.py to Focus HRM validation" \
  --body "$(cat <<'EOF'
## Summary
Connect Altitude HRM planner to Focus HRM stance validation.

## Changes
- `the_assist/hrm/planner.py` checks current stance
- Plans respect stance-allowed actions

## Acceptance Criteria
- [ ] Planner queries current stance
- [ ] Plans only include allowed actions
- [ ] Invalid plans rejected with reason

## Dependencies
- executor.py wiring complete
EOF
)" --label "integration,altitude-hrm,focus-hrm,p0-blocking" --milestone "M0.1 Integration"

gh issue create --title "[M0.1] Wire evaluator.py to continuous_eval" \
  --body "$(cat <<'EOF'
## Summary
Connect Altitude HRM evaluator to Focus HRM continuous evaluation.

## Changes
- `the_assist/hrm/evaluator.py` uses `locked_system/fast_loop/continuous_eval.py`
- Evaluation results feed back to Focus

## Acceptance Criteria
- [ ] Evaluator calls continuous_eval
- [ ] Results influence stance transitions
- [ ] Trace events emitted

## Dependencies
- planner.py wiring complete
EOF
)" --label "integration,altitude-hrm,focus-hrm,p1-core" --milestone "M0.1 Integration"

gh issue create --title "[M0.1] Create AgentApprovalGate" \
  --body "$(cat <<'EOF'
## Summary
Gate for validating agent bundle proposals.

## Interface
```python
class AgentApprovalGate:
    def evaluate(
        proposal: AgentBundleProposal,
        stance: Stance,
        commitment: Commitment
    ) -> GateDecision
```

## Validation Rules
1. Check stance compatibility
2. Check commitment alignment
3. Check agent authorization
4. Check orchestration mode constraints

## Acceptance Criteria
- [ ] All rules implemented
- [ ] Denial includes reason
- [ ] Approval triggers agent activation

## Dependencies
- Focus HRM gates.py
EOF
)" --label "gates,focus-hrm,p0-blocking,feature" --milestone "M0.1 Integration"

gh issue create --title "[M0.1] Update AgentRuntime for 4 orchestration modes" \
  --body "$(cat <<'EOF'
## Summary
Implement all 4 orchestration modes in agent runtime.

## Modes
1. Pipeline - Serial execution
2. Parallel - Async with aggregation
3. Voting - Consensus with threshold
4. Hierarchical - Lead + delegates

## Acceptance Criteria
- [ ] Pipeline mode works
- [ ] Parallel mode with async
- [ ] Voting with threshold and tiebreaker
- [ ] Hierarchical with max depth
- [ ] All outputs through firewall

## Dependencies
- agents/runtime.py
- agents/orchestrator.py
EOF
)" --label "agents,focus-hrm,p0-blocking,feature" --milestone "M0.1 Integration"

gh issue create --title "[M0.1] Connect Memory Bus to existing memory" \
  --body "$(cat <<'EOF'
## Summary
Wire existing memory components to Memory Bus.

## Migration
- `locked_system/memory/fast.py` → WorkingSet adapter
- `locked_system/memory/slow.py` → SharedReference adapter
- `the_assist/core/memory_v2.py` → SemanticSynthesis adapter

## Acceptance Criteria
- [ ] Adapters preserve existing behavior
- [ ] New code uses Memory Bus
- [ ] Old code continues to work

## Dependencies
- M0.0 Memory Bus complete
EOF
)" --label "memory,integration,p0-blocking" --milestone "M0.1 Integration"

gh issue create --title "[M0.1] Create integration test suite" \
  --body "$(cat <<'EOF'
## Summary
End-to-end tests for Altitude ↔ Focus integration.

## Test Cases
1. Full turn cycle (input → altitude → focus → execute)
2. Write approval flow
3. Stance transition via gate
4. Agent activation via AgentApprovalGate
5. Memory persistence across turns

## Acceptance Criteria
- [ ] All test cases pass
- [ ] Coverage > 80% for integration points
- [ ] Tests run in CI

## Dependencies
- All M0.1 wiring complete
EOF
)" --label "tests,integration,p0-blocking" --milestone "M0.1 Integration"

gh issue create --title "[M0.1] Add tracing to Altitude and Focus HRMs" \
  --body "$(cat <<'EOF'
## Summary
Instrument HRM components with trace events.

## Trace Points
### Altitude HRM
- altitude.transition
- altitude.evaluate
- altitude.plan
- altitude.execute

### Focus HRM
- focus.stance_change
- focus.gate_check
- focus.lane_switch
- focus.agent_activate

## Acceptance Criteria
- [ ] All trace points emit events
- [ ] Parent/child correlation works
- [ ] Trace viewer shows HRM flow

## Dependencies
- shared/tracing/ complete
EOF
)" --label "tracing,altitude-hrm,focus-hrm,p1-core" --milestone "M0.1 Integration"
```

### M0.2 Consolidation (6 issues)

```bash
gh issue create --title "[M0.2] Remove duplicate governance files" \
  --body "$(cat <<'EOF'
## Summary
Merge duplicates in locked_system/core/governance/.

## Duplicates to Remove
- `core/governance/stance.py` → use `slow_loop/stance.py`
- `core/governance/commitment.py` → use `slow_loop/commitment.py`
- `core/governance/gates.py` → use `slow_loop/gates.py`

## Acceptance Criteria
- [ ] All imports updated
- [ ] Duplicate files deleted
- [ ] Tests pass

## Dependencies
- M0.1 complete
EOF
)" --label "p3-cleanup,focus-hrm" --milestone "M0.2 Consolidation"

gh issue create --title "[M0.2] Remove duplicate execution files" \
  --body "$(cat <<'EOF'
## Summary
Merge duplicates in locked_system/core/execution/.

## Duplicates to Remove
- `core/execution/executor.py` → use `fast_loop/executor.py`
- `core/execution/hrm.py` → use `fast_loop/hrm.py`
- `core/execution/continuous_eval.py` → use `fast_loop/continuous_eval.py`

## Acceptance Criteria
- [ ] All imports updated
- [ ] Duplicate files deleted
- [ ] Tests pass

## Dependencies
- M0.1 complete
EOF
)" --label "p3-cleanup,focus-hrm" --milestone "M0.2 Consolidation"

gh issue create --title "[M0.2] Create the_assist/ui/ module" \
  --body "$(cat <<'EOF'
## Summary
Centralize all UI/display components.

## Files to Move
- `the_assist/core/formatter.py` → `the_assist/ui/formatter.py`
- `locked_system/cli/chat_ui.py` → `the_assist/ui/chat_ui.py`
- `locked_system/signals/display.py` → `the_assist/ui/signal_display.py`

## Acceptance Criteria
- [ ] UI module created
- [ ] All display code consolidated
- [ ] Imports updated

## Dependencies
- None
EOF
)" --label "p2-enhancement,feature" --milestone "M0.2 Consolidation"

gh issue create --title "[M0.2] Create LLM adapter" \
  --body "$(cat <<'EOF'
## Summary
Abstract LLM provider for multiple backends.

## Interface
```python
class LLMAdapter:
    def chat(messages: list, system: str) -> str
    def stream(messages: list, system: str) -> Iterator[str]

class ClaudeAdapter(LLMAdapter): ...
class OpenAIAdapter(LLMAdapter): ...
```

## Config
```yaml
# llm_config.yaml
provider: anthropic
model: claude-sonnet-4-20250514
temperature: 0.7
max_tokens: 4096
```

## Acceptance Criteria
- [ ] Claude adapter works
- [ ] Config file loading works
- [ ] Easy to add new providers

## Dependencies
- None
EOF
)" --label "p0-blocking,feature" --milestone "M0.2 Consolidation"

gh issue create --title "[M0.2] Fix ungated notes.py" \
  --body "$(cat <<'EOF'
## Summary
Replace ungated notes.py with gated capability.

## Current Problem
`locked_system/notes.py` writes files without governance.

## Solution
1. Delete `notes.py`
2. Use `capabilities/note_capture/tool.py` (gated)
3. Require WriteApprovalGate for all note writes

## Acceptance Criteria
- [ ] Old notes.py removed
- [ ] New gated tool works
- [ ] All note writes require approval

## Dependencies
- WriteApprovalGate working
EOF
)" --label "p0-blocking,gates" --milestone "M0.2 Consolidation"

gh issue create --title "[M0.2] Merge entry points" \
  --body "$(cat <<'EOF'
## Summary
Consolidate entry points into single main.

## Current State
- `the_assist/main.py` - Legacy
- `the_assist/main_hrm.py` - HRM entry
- `the_assist/main_locked.py` - Locked integration

## Target
Single `the_assist/main.py` that:
1. Initializes all 4 HRMs
2. Connects to Memory Bus
3. Runs unified loop

## Acceptance Criteria
- [ ] Single entry point
- [ ] All HRMs initialized
- [ ] Old files removed

## Dependencies
- M0.1 integration complete
EOF
)" --label "p2-enhancement" --milestone "M0.2 Consolidation"
```

### M0.3 Reasoning HRM (7 issues)

```bash
gh issue create --title "[M0.3] Create the_assist/reasoning/ package" \
  --body "$(cat <<'EOF'
## Summary
Create Reasoning HRM package structure.

## Files
- `the_assist/reasoning/__init__.py`
- `the_assist/reasoning/router.py`
- `the_assist/reasoning/classifier.py`
- `the_assist/reasoning/strategies.py`
- `the_assist/reasoning/escalation.py`
- `the_assist/reasoning/proposals.py`

## Acceptance Criteria
- [ ] Package imports work
- [ ] All files created with stubs

## Dependencies
- M0.2 complete
EOF
)" --label "reasoning-hrm,p1-core,feature" --milestone "M0.3 Reasoning HRM"

gh issue create --title "[M0.3] Implement InputClassifier" \
  --body "$(cat <<'EOF'
## Summary
Classify input by complexity, uncertainty, stakes, etc.

## Interface
```python
@dataclass
class InputClassification:
    complexity: str      # simple | moderate | complex
    uncertainty: float   # 0.0 - 1.0
    conflict: str        # none | internal | external
    stakes: str          # low | medium | high
    horizon: str         # immediate | near | far
    confidence: float

class InputClassifier:
    def classify(input: str, context: HRMContext) -> InputClassification
```

## Acceptance Criteria
- [ ] All dimensions classified
- [ ] Confidence score reasonable
- [ ] Unit tests pass

## Dependencies
- reasoning/ package structure
EOF
)" --label "reasoning-hrm,p1-core,feature" --milestone "M0.3 Reasoning HRM"

gh issue create --title "[M0.3] Implement StrategySelector" \
  --body "$(cat <<'EOF'
## Summary
Select reasoning strategy based on classification.

## Strategies
- QUICK_ANSWER: Low complexity, low stakes
- DECOMPOSITION: High complexity
- VERIFICATION: High stakes
- EXPLORATION: High uncertainty
- DIALOGUE: Conflict present

## Interface
```python
class StrategySelector:
    def select(classification: InputClassification) -> StrategySelection
```

## Acceptance Criteria
- [ ] All strategies defined
- [ ] Selection logic correct
- [ ] Unit tests pass

## Dependencies
- InputClassifier
EOF
)" --label "reasoning-hrm,p1-core,feature" --milestone "M0.3 Reasoning HRM"

gh issue create --title "[M0.3] Implement EscalationManager" \
  --body "$(cat <<'EOF'
## Summary
Manage escalation/de-escalation decisions.

## Interface
```python
class EscalationManager:
    def should_escalate(classification: InputClassification, strategy: StrategySelection) -> bool
    def escalate(strategy: StrategySelection) -> StrategySelection
    def should_deescalate(strategy: StrategySelection, pattern_match: bool) -> bool
    def deescalate(strategy: StrategySelection) -> StrategySelection
```

## Rules
- Escalate when confidence < 0.6
- De-escalate when pattern match with high confidence

## Acceptance Criteria
- [ ] Escalation threshold = 0.6
- [ ] De-escalation on pattern match
- [ ] Unit tests pass

## Dependencies
- StrategySelector
EOF
)" --label "reasoning-hrm,p1-core,feature" --milestone "M0.3 Reasoning HRM"

gh issue create --title "[M0.3] Implement AgentBundleProposal generation" \
  --body "$(cat <<'EOF'
## Summary
Generate agent bundle proposals based on strategy.

## Interface
```python
@dataclass
class AgentBundleProposal:
    strategy: str
    classification: InputClassification
    agents: list[str]
    orchestration_mode: str  # pipeline | parallel | voting | hierarchical
    mode_config: dict
    reason: str
    confidence: float
    fallback: Optional[str]
```

## Mapping
- QUICK_ANSWER → No agents or single agent
- DECOMPOSITION → Hierarchical mode
- VERIFICATION → Voting mode
- EXPLORATION → Parallel mode
- DIALOGUE → Pipeline mode

## Acceptance Criteria
- [ ] All strategy→mode mappings work
- [ ] Config generated correctly
- [ ] Unit tests pass

## Dependencies
- StrategySelector
- EscalationManager
EOF
)" --label "reasoning-hrm,p1-core,feature" --milestone "M0.3 Reasoning HRM"

gh issue create --title "[M0.3] Implement ReasoningRouter main class" \
  --body "$(cat <<'EOF'
## Summary
Main router that coordinates classification, strategy, and proposals.

## Interface
```python
class ReasoningRouter:
    def route(input: str, context: HRMContext) -> RoutingDecision
    def propose_agents(input: str, context: HRMContext) -> Optional[AgentBundleProposal]
```

## Flow
1. Classify input
2. Query Learning HRM for pattern matches
3. If pattern match: use cached strategy
4. Else: select strategy
5. Check escalation
6. Generate proposal if agents needed

## Acceptance Criteria
- [ ] Full flow works
- [ ] Pattern queries Learning HRM
- [ ] Proposals sent to Focus HRM
- [ ] Integration tests pass

## Dependencies
- All reasoning/ components
- Learning HRM patterns (for queries)
EOF
)" --label "reasoning-hrm,p0-blocking,feature" --milestone "M0.3 Reasoning HRM"

gh issue create --title "[M0.3] Add tracing to Reasoning HRM" \
  --body "$(cat <<'EOF'
## Summary
Instrument Reasoning HRM with trace events.

## Trace Points
- reasoning.classify
- reasoning.strategy_select
- reasoning.escalate
- reasoning.deescalate
- reasoning.propose_agents

## Acceptance Criteria
- [ ] All trace points emit events
- [ ] Parent/child correlation works
- [ ] Trace viewer shows reasoning flow

## Dependencies
- ReasoningRouter complete
- shared/tracing/ complete
EOF
)" --label "reasoning-hrm,tracing,p1-core" --milestone "M0.3 Reasoning HRM"
```

### M0.4 Learning HRM (5 issues)

```bash
gh issue create --title "[M0.4] Create the_assist/learning/ package" \
  --body "$(cat <<'EOF'
## Summary
Create Learning HRM package structure.

## Files
- `the_assist/learning/__init__.py`
- `the_assist/learning/patterns.py`
- `the_assist/learning/feedback_loop.py`
- `the_assist/learning/generalizer.py`

## Acceptance Criteria
- [ ] Package imports work
- [ ] All files created with stubs

## Dependencies
- M0.3 complete
EOF
)" --label "learning-hrm,p1-core,feature" --milestone "M0.4 Learning HRM"

gh issue create --title "[M0.4] Implement PatternStore" \
  --body "$(cat <<'EOF'
## Summary
Store and query patterns with evidence links.

## Interface
```python
class PatternStore:
    def add_pattern(pattern: Pattern) -> str
    def get_pattern(id: str) -> Optional[Pattern]
    def search(input_signature: dict) -> list[Pattern]
    def strengthen(id: str) -> None
    def weaken(id: str) -> None
    def protect(id: str) -> None  # Prevent manual removal
```

## Acceptance Criteria
- [ ] CRUD operations work
- [ ] Evidence links preserved
- [ ] Search by signature works
- [ ] Confidence adjustments work
- [ ] NO automatic trimming (per decision)

## Dependencies
- learning/ package structure
- SemanticSynthesisStore (underlying storage)
EOF
)" --label "learning-hrm,p1-core,feature" --milestone "M0.4 Learning HRM"

gh issue create --title "[M0.4] Implement FeedbackLoop" \
  --body "$(cat <<'EOF'
## Summary
Session analysis and pattern learning.

## Interface
```python
class FeedbackLoop:
    def record_outcome(signal: dict, routing: dict, outcome: dict) -> None
    def analyze_session() -> dict
    def get_patterns_for_signal(signal: dict) -> list[Pattern]
```

## Learning Cycle
1. Capture signal→routing→outcome tuples
2. At session end: analyze patterns
3. Strengthen successful patterns
4. Weaken failed patterns
5. Create new patterns for repeated success (3+ times)

## Acceptance Criteria
- [ ] Outcome recording works
- [ ] Session analysis produces insights
- [ ] Pattern queries work for Reasoning HRM

## Dependencies
- PatternStore
EOF
)" --label "learning-hrm,p1-core,feature" --milestone "M0.4 Learning HRM"

gh issue create --title "[M0.4] Implement Generalizer" \
  --body "$(cat <<'EOF'
## Summary
Merge similar patterns into abstractions.

## Interface
```python
class Generalizer:
    def find_similar(patterns: list[Pattern]) -> list[tuple[Pattern, Pattern]]
    def merge(p1: Pattern, p2: Pattern) -> Pattern
    def generalize_batch(patterns: list[Pattern]) -> list[Pattern]
```

## Example
"timeboxing_coding" + "timeboxing_writing" → "timeboxing_creative_work"

## Acceptance Criteria
- [ ] Similarity detection works
- [ ] Merge preserves evidence from both
- [ ] Batch processing efficient

## Dependencies
- PatternStore
EOF
)" --label "learning-hrm,p2-enhancement,feature" --milestone "M0.4 Learning HRM"

gh issue create --title "[M0.4] Add tracing and cross-HRM integration" \
  --body "$(cat <<'EOF'
## Summary
Wire Learning HRM to other HRMs and add tracing.

## Integration Points
- FROM Reasoning HRM: Query patterns for signal
- FROM All HRMs: Receive outcome data
- TO Reasoning HRM: Return pattern matches

## Trace Points
- learning.pattern_match
- learning.pattern_add
- learning.strengthen
- learning.weaken
- learning.generalize

## Acceptance Criteria
- [ ] Reasoning HRM can query patterns
- [ ] Outcomes recorded from all HRMs
- [ ] Trace events emitted

## Dependencies
- All learning/ components
- Reasoning HRM complete
EOF
)" --label "learning-hrm,tracing,integration,p1-core" --milestone "M0.4 Learning HRM"
```

### M1.0 Unified (4 issues)

```bash
gh issue create --title "[M1.0] Create unified main.py entry" \
  --body "$(cat <<'EOF'
## Summary
Single entry point that initializes all 4 HRMs.

## Boot Sequence
1. Initialize Memory Bus
2. Initialize Focus HRM (stance, gates, commitments)
3. Initialize Altitude HRM (levels, validation)
4. Initialize Reasoning HRM (classifier, strategies)
5. Initialize Learning HRM (patterns, feedback)
6. Start main loop

## Acceptance Criteria
- [ ] All HRMs initialize correctly
- [ ] Memory Bus connected
- [ ] Single command to start: `python -m the_assist.main`

## Dependencies
- All M0.x milestones complete
EOF
)" --label "p0-blocking,feature" --milestone "M1.0 Unified"

gh issue create --title "[M1.0] End-to-end integration test" \
  --body "$(cat <<'EOF'
## Summary
Full system integration test.

## Test Scenario
1. User input: "Help me plan my week"
2. Altitude: Detect L2, check context
3. Reasoning: Classify, select DECOMPOSITION
4. Reasoning: Propose hierarchical agent bundle
5. Focus: Approve bundle, activate agents
6. Execute: Run planning agents
7. Learning: Record outcome
8. Response: Deliver plan

## Acceptance Criteria
- [ ] Full flow executes without error
- [ ] All HRMs participate
- [ ] Memory Bus records data
- [ ] Traces show complete flow

## Dependencies
- Unified main.py
EOF
)" --label "tests,integration,p0-blocking" --milestone "M1.0 Unified"

gh issue create --title "[M1.0] Performance testing" \
  --body "$(cat <<'EOF'
## Summary
Verify system meets performance targets.

## Targets
- Turn latency: < 2s (excluding LLM)
- Memory operation: < 10ms
- Trace overhead: < 1ms per event
- Pattern query: < 50ms

## Test Plan
1. Run 100 turns, measure latencies
2. Profile hot paths
3. Identify bottlenecks

## Acceptance Criteria
- [ ] All targets met
- [ ] No memory leaks
- [ ] Trace overhead acceptable

## Dependencies
- Unified system working
EOF
)" --label "tests,p2-enhancement" --milestone "M1.0 Unified"

gh issue create --title "[M1.0] Documentation" \
  --body "$(cat <<'EOF'
## Summary
Final documentation for release.

## Documents to Update
- README.md - Quick start
- DOPEJAR_ARCHITECTURE.md - Verify accuracy
- API docs for each HRM
- Configuration guide
- Troubleshooting guide

## Acceptance Criteria
- [ ] README has working quick start
- [ ] Architecture doc matches code
- [ ] API docs generated
- [ ] All config options documented

## Dependencies
- All code complete
EOF
)" --label "docs,p2-enhancement" --milestone "M1.0 Unified"
```

---

## 4. Project Board Setup

```bash
# Create project board
gh project create --title "DoPeJar Development" --body "4-HRM cognitive partner system"

# Add columns (done via web UI or API)
# - Backlog
# - Ready
# - In Progress
# - Review
# - Done
```

---

## 5. Verification

After running all commands, verify:

```bash
# Check labels
gh label list

# Check milestones
gh api repos/:owner/:repo/milestones

# Check issues by milestone
gh issue list --milestone "M0.0 Foundation"
gh issue list --milestone "M0.1 Integration"
gh issue list --milestone "M0.2 Consolidation"
gh issue list --milestone "M0.3 Reasoning HRM"
gh issue list --milestone "M0.4 Learning HRM"
gh issue list --milestone "M1.0 Unified"
```
