# DoPeJar Build Process

**Created:** 2026-01-14
**Purpose:** Repeatable, verifiable build process that matches specifications

---

## 1. Pre-Build Checklist

Before ANY implementation work, the agent MUST:

### 1.1 Read Canonical Specs (IN THIS ORDER)

1. **`DECISIONS.md`** - All design decisions (READ FIRST)
2. **`DOPEJAR_ARCHITECTURE.md`** - System architecture
3. **`capabilities_v2.csv`** - Component inventory with locations
4. **`HRM_INTERFACE_SPECS.md`** - API contracts
5. **`IMPLEMENTATION_ORDER.md`** - Build sequence

### 1.2 Verify Understanding

Before writing ANY code, answer these questions:
- [ ] Which milestone am I working on? (M0.0, M0.1, etc.)
- [ ] Which specific files from capabilities_v2.csv am I building?
- [ ] What is the EXACT location for each file?
- [ ] What does the interface spec say about inputs/outputs?
- [ ] What tests must pass?

### 1.3 Check Context

- [ ] Has context been compacted? (Look for "This session is being continued")
- [ ] If yes, RE-READ all specs before proceeding
- [ ] Never rely on summary alone

---

## 2. File Locations (FROM capabilities_v2.csv)

### 2.1 DO NOT CREATE IN locked_system/core/

The `locked_system/core/` location was used incorrectly. The correct locations are:

| Component | CORRECT Location | WRONG Location |
|-----------|------------------|----------------|
| Reasoning HRM | `the_assist/reasoning/` | ~~locked_system/core/reasoning.py~~ |
| Learning HRM | `the_assist/learning/` | ~~locked_system/core/learning.py~~ |
| Memory Bus | `shared/memory/` | ~~locked_system/core/memory_bus.py~~ |
| Trace | `shared/tracing/` | ~~locked_system/core/trace.py~~ |

### 2.2 Correct Structure

```
AI_ARCH/
├── the_assist/
│   ├── hrm/                    # Altitude HRM (EXISTS)
│   │   ├── altitude.py         # 95% done
│   │   ├── loop.py             # 85% done
│   │   ├── planner.py          # 75% done
│   │   ├── evaluator.py        # 75% done
│   │   ├── executor.py         # 70% done
│   │   └── history.py          # 100% done
│   │
│   ├── reasoning/              # TO BUILD (M0.3)
│   │   ├── router.py           # ReasoningRouter class
│   │   ├── classifier.py       # InputClassifier
│   │   ├── strategies.py       # Strategy definitions
│   │   ├── escalation.py       # Escalation management
│   │   └── action_selector.py  # ActionSelector (final stage)
│   │
│   ├── learning/               # TO BUILD (M0.4)
│   │   ├── patterns.py         # PatternStore
│   │   ├── feedback_loop.py    # Session analysis
│   │   └── generalizer.py      # Pattern abstraction
│   │
│   └── ui/                     # TO BUILD (M0.2)
│       ├── chat.py             # From locked_system/cli/chat_ui.py
│       ├── signals.py          # From locked_system/signals/display.py
│       └── formatter.py        # From the_assist/core/formatter.py
│
├── shared/                     # TO BUILD (M0.0)
│   ├── memory/
│   │   ├── bus.py              # MemoryBus class
│   │   ├── working_set.py      # Per-problem storage
│   │   ├── shared_reference.py # Cross-problem versioned
│   │   ├── episodic_trace.py   # Append-only audit
│   │   ├── semantic_synthesis.py # Distilled patterns
│   │   └── write_gate.py       # Signal-based policy
│   │
│   └── tracing/
│       ├── tracer.py           # Tracer singleton
│       └── viewer.py           # Trace viewer CLI
│
└── locked_system/              # Focus HRM (EXISTS - mostly done)
    ├── slow_loop/              # Governance
    ├── fast_loop/              # Execution
    ├── front_door/             # Signal detection
    ├── agents/                 # Agent runtime
    └── memory/                 # Current memory (migrate to bus)
```

---

## 3. Build Sequence

### 3.1 Milestone M0.0: Foundation

**Files to create:**
```
shared/memory/bus.py
shared/memory/working_set.py
shared/memory/shared_reference.py
shared/memory/episodic_trace.py
shared/memory/semantic_synthesis.py
shared/memory/write_gate.py
shared/tracing/tracer.py
```

**Tests required:**
- Memory compartment isolation
- Write gate signal evaluation
- Trace append-only property

### 3.2 Milestone M0.1: Integration

**Work:**
- Wire Altitude HRM to Focus HRM
- Ensure gate validation works

### 3.3 Milestone M0.2: Consolidation

**Files to create:**
```
the_assist/ui/chat.py          # Move from locked_system/cli/chat_ui.py
the_assist/ui/signals.py       # Move from locked_system/signals/display.py
the_assist/ui/formatter.py     # Move from the_assist/core/formatter.py
```

**Work:**
- Remove duplicates
- Standardize UI

### 3.4 Milestone M0.3: Reasoning HRM

**Files to create:**
```
the_assist/reasoning/router.py
the_assist/reasoning/classifier.py
the_assist/reasoning/strategies.py
the_assist/reasoning/escalation.py
the_assist/reasoning/action_selector.py
```

### 3.5 Milestone M0.4: Learning HRM

**Files to create:**
```
the_assist/learning/patterns.py
the_assist/learning/feedback_loop.py
the_assist/learning/generalizer.py
```

### 3.6 Milestone M1.0: Unified

**Work:**
- Single entry point
- All 4 HRMs working together
- Full test suite passing

---

## 4. Verification Steps

### 4.1 After Each File

```bash
# 1. Run tests for that file
./venv/bin/python3 -m pytest path/to/test_file.py -v

# 2. Verify location matches CSV
grep "filename" capabilities_v2.csv

# 3. Commit with descriptive message
git add path/to/file.py
git commit -m "feat(milestone): Add component - description"
```

### 4.2 After Each Milestone

```bash
# 1. Run all tests
./venv/bin/python3 -m pytest -v

# 2. Update capabilities_v2.csv percentages
# 3. Tag release
git tag -a vM0.X -m "Milestone M0.X complete"
git push origin vM0.X
```

---

## 5. Git Workflow

### 5.1 Spec Changes

ALL spec changes MUST be committed immediately:

```bash
git add DECISIONS.md DOPEJAR_ARCHITECTURE.md HRM_INTERFACE_SPECS.md
git commit -m "spec: Description of what changed"
git push origin main
```

### 5.2 Implementation

```bash
git checkout -b milestone/M0.X-component-name
# ... do work ...
git add .
git commit -m "feat(M0.X): Add component"
git push origin milestone/M0.X-component-name
# Create PR, merge to main
```

---

## 6. Recovery from Context Compaction

If you see "This session is being continued from a previous conversation":

### 6.1 STOP

Do NOT proceed based on summary alone.

### 6.2 READ

1. Read `DECISIONS.md` completely
2. Read `BUILD_PROCESS.md` (this file)
3. Read `capabilities_v2.csv` to know where files go

### 6.3 VERIFY

Ask user:
- "What milestone are we on?"
- "What was the last completed work?"
- "Should I read any other files?"

### 6.4 PROCEED

Only after verification, continue work.

---

## 7. run.sh Convention

All entry points MUST be accessible via `run.sh`:

```bash
./run.sh              # Default (frontdoor demo)
./run.sh assist       # The Assist HRM
./run.sh locked       # Locked System CLI
./run.sh test         # Run all tests
./run.sh help         # Show options
```

When adding new entry points, ALWAYS update `run.sh`.

---

**CRITICAL:** This process exists because 12 hours of work was nearly lost due to context compaction. Follow it exactly.
