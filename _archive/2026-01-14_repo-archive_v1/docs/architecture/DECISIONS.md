# DoPeJar Design Decisions Log

**Created:** 2026-01-14
**Source:** Extracted from conversation history (267109d0-6589-44f8-bb9d-5ca227f8eda8.jsonl)
**Purpose:** Canonical record of all design decisions to prevent loss during context compaction

---

## 1. Architecture Decisions

### 1.1 Four HRM Layers (Decided 2026-01-13)

| Layer | Name | Location | Role |
|-------|------|----------|------|
| 1 | **Altitude HRM** | `the_assist/hrm/` | Scope governance (L4 Identity → L1 Moment) |
| 2 | **Reasoning HRM** | `the_assist/reasoning/` | Strategy selection, proposes agents |
| 3 | **Focus HRM** | `locked_system/` | Control governance, approves and executes |
| 4 | **Learning HRM** | `the_assist/learning/` | Pattern memory, informs future routing |

**Key principle:** Reasoning PROPOSES, Focus APPROVES

### 1.2 Memory Architecture (Decided 2026-01-14 01:22)

**Decision:** Use Memory Bus with 4 compartments (not 3-tier hot/warm/cold)

| Compartment | Scope | Lifetime | Key Property |
|-------------|-------|----------|--------------|
| Working Set | Per-problem | Minutes-hours | Isolated, expires aggressively |
| Shared Reference | Cross-problem | Long-lived | Versioned, citable |
| Episodic Trace | Append-only | Long-lived | Never overwritten, searchable |
| Semantic Synthesis | Distilled | Long-lived | Evidence-linked patterns |

**Write Gate:** Signal-based policy layer (blast radius, conflict, alignment)

### 1.3 Agent Orchestration (Decided 2026-01-14 01:30)

**Decision:** Four orchestration modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Pipeline | Serial, output feeds next | Sequential refinement |
| Parallel | All at once, then aggregate | Multi-perspective, speed |
| Voting | All at once, then consensus | High-stakes decisions |
| Hierarchical | Lead delegates to sub-agents | Complex decomposition |

### 1.4 ActionSelector (Decided 2026-01-14 02:08)

**Decision:** Implement inside Reasoning HRM (not as separate governor)

**Flow:**
```
Input → Classify → Strategy → [Generate Candidates] → ActionSelector → ONE action to Focus HRM
```

**Priority Signals:**
- `urgency` (0.0-1.0) - time-sensitive?
- `dependency` (0.0-1.0) - unblocks other work?
- `momentum` (0.0-1.0) - continues current flow?
- `energy_cost` (0.0-1.0) - cognitive load (lower=better)
- `alignment` (0.0-1.0) - matches commitment?

---

## 2. Policy Decisions

### 2.1 Arbitration Policy (Decided 2026-01-14 03:42)

**Decision:** Option C (Priority + TTL) with Option D as tie-breaker

- Default: Highest priority wins; ties broken by "staleness"
- Close calls (within 15% of each other): Ask user

### 2.2 Priority Scale (Decided 2026-01-14 03:43)

**Decision:** 1-10 scale (not 0-100)

- Forces clearer distinctions
- Maps to human intuition
- Simpler PreemptScore math

### 2.3 Memory Locking (Decided 2026-01-14 01:06)

**Decision:** Implement FileLock from start

### 2.4 Trim Policy (Decided 2026-01-14 01:06)

**Decision:** No automatic trimming - patterns persist until manual removal

### 2.5 Escalation Threshold (Decided 2026-01-14 01:06)

**Decision:** 0.6 confidence threshold for Reasoning HRM to escalate

### 2.6 Naming Convention (Decided 2026-01-14 01:06)

**Decision:** Keep existing names
- Keep `locked_system` (not rename)
- Keep `front_door` (not rename)

---

## 3. Simplification Decisions (Decided 2026-01-14 04:43-05:15)

**Context:** User approved 5 simplifications to reduce implementation complexity

### 3.1 Applied Simplifications

| # | Simplification | What Changed | Impact |
|---|----------------|--------------|--------|
| 9 | Remove Protocols | 15+ `Protocol` interfaces → plain classes | -500 lines |
| 12 | Inline Firewall | `IAgentFirewall` → `_validate_output()` in runtime | -100 lines |
| 14 | Callbacks → Events | `IHRMCallback` → Event appends to trace | Decoupled |
| 15 | Single HRMError | 12+ exception classes → `HRMError` with `ErrorCode` enum | Simpler |
| N/A | MapReduce Orchestrator | Unified orchestration pattern | Cleaner |

### 3.2 Simplifications NOT Applied (Preserved Complexity)

| # | Simplification | Why Kept |
|---|----------------|----------|
| 8 | Collapse Altitude+Stance | Preserves theoretical expressiveness |

---

## 4. UI Decisions (Decided 2026-01-13 20:56, 21:36)

### 4.1 UI Centralization

**Decision:** Centralize all UI in `the_assist/ui/`

| Source | Destination | Purpose |
|--------|-------------|---------|
| `locked_system/cli/chat_ui.py` | `the_assist/ui/chat.py` | Terminal chat interface |
| `locked_system/signals/display.py` | `the_assist/ui/signals.py` | Signal visualization |
| `the_assist/core/formatter.py` | `the_assist/ui/formatter.py` | Output formatting |

**Principle:** Locked System emits structured data, The Assist presents it.

### 4.2 Signal Display Features

**Decision:** Include real-time trust/learning indicators

- Status strip: `eval · L3▃ · ●↑ · ◉ · #63`
- Trust panel with visual bar
- Learning indicator (active/recent/idle)
- Altitude bar visualization

---

## 5. File Location Decisions

### 5.1 Canonical Spec Files

| File | Purpose | Status |
|------|---------|--------|
| `DOPEJAR_ARCHITECTURE.md` | V2 system architecture | CANONICAL |
| `HRM_INTERFACE_SPECS.md` | API contracts between HRMs | CANONICAL |
| `TEST_SPECIFICATIONS.md` | Test strategy and cases | CANONICAL |
| `IMPLEMENTATION_ORDER.md` | Build sequence (72 days) | CANONICAL |
| `capabilities_v2.csv` | Component inventory | CANONICAL |
| `MEMORY_BUS_ARCHITECTURE.md` | Memory bus design | CANONICAL |
| `AGENT_ORCHESTRATION.md` | 4 orchestration modes | CANONICAL |

### 5.2 Directory Structure (From capabilities_v2.csv)

```
the_assist/
├── hrm/                    # Altitude HRM (95% done)
├── reasoning/              # Reasoning HRM (TO BUILD)
│   ├── router.py
│   ├── classifier.py
│   ├── strategies.py
│   ├── escalation.py
│   └── action_selector.py
├── learning/               # Learning HRM (TO BUILD)
│   ├── patterns.py
│   ├── feedback_loop.py
│   └── generalizer.py
└── ui/                     # Centralized UI (TO BUILD)
    ├── chat.py
    ├── signals.py
    └── formatter.py

locked_system/
├── slow_loop/              # Focus HRM governance
├── fast_loop/              # Focus HRM execution
├── front_door/             # Signal detection
├── agents/                 # Agent runtime
├── memory/                 # Current memory (migrate to bus)
└── core/                   # NOTE: Current build is WRONG LOCATION
```

---

## 6. Governance Kernel (Decided 2026-01-14 03:52-03:57)

### 6.1 PolicySurface (Single canonical tunables)

```python
PRIORITY_SCALE = 1..10
ESCALATION_THRESHOLD = 0.6
VOTING_THRESHOLD = 0.6
PREEMPT_WEIGHTS = {
    "priority": 0.4,
    "staleness": 0.2,
    "urgency": 0.25,
    "user_signal": 0.15
}
AMBIGUITY_BAND = 0.15  # Scores within 15% trigger user ask
```

### 6.2 Signal Derivation

| Signal | Method |
|--------|--------|
| conflict_level | Deterministic (safety-critical) |
| blast_radius | Deterministic (safety-critical) |
| source_quality | LLM-assisted (judgment call) |
| alignment_score | LLM-assisted (judgment call) |

### 6.3 Preference Authority Model

| Tier | Update Rule |
|------|-------------|
| Explicit | User said directly → auto-canon |
| Inferred-confirmed | System asks, user says YES → promote |
| Inferred-silent | Working Set only, never auto-promote |
| Behavioral | Observed patterns, decay without reinforcement |

---

## 7. Build Process (TO BE ESTABLISHED)

### 7.1 Milestones (From IMPLEMENTATION_ORDER.md)

| Milestone | Focus |
|-----------|-------|
| M0.0 | Foundation - Memory Bus, Tracing |
| M0.1 | Integration - Wire Altitude ↔ Focus |
| M0.2 | Consolidation - Remove duplicates, UI |
| M0.3 | Reasoning HRM - Build new |
| M0.4 | Learning HRM - Build new |
| M1.0 | Unified experience |

### 7.2 Test Requirements

- Invariant tests (authority, memory, prompts)
- Unit tests per component
- Integration tests per HRM
- E2E tests for full system

---

## Change Log

| Date | Decision | Source |
|------|----------|--------|
| 2026-01-13 | 4 HRM layers named | Conversation |
| 2026-01-14 01:06 | Memory locking, trim policy, escalation threshold | Conversation |
| 2026-01-14 01:22 | Memory Bus architecture | Conversation |
| 2026-01-14 01:30 | 4 orchestration modes | Conversation |
| 2026-01-14 02:08 | ActionSelector inside Reasoning HRM | Conversation |
| 2026-01-14 03:42 | Arbitration policy C+D | Conversation |
| 2026-01-14 03:52 | Governance Kernel spec | Conversation |
| 2026-01-14 04:43 | 5 simplifications approved | Conversation |
| 2026-01-14 05:15 | Simplifications applied to specs | Conversation |

---

**CRITICAL:** This document must be read by any agent continuing work on DoPeJar.
