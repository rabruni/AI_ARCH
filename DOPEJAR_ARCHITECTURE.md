# DoPeJar Architecture - Deep Design Document

**Version:** 2.0
**Date:** 2026-01-13
**Purpose:** Enable agent audit of design prior to implementation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Four HRM Layers](#2-four-hrm-layers)
3. [Memory Bus Architecture](#3-memory-bus-architecture)
4. [Agent Orchestration](#4-agent-orchestration)
5. [Attention & Priority System](#5-attention--priority-system)
6. [Signal System](#6-signal-system)
7. [Gate System](#7-gate-system)
8. [Execution Pipeline](#8-execution-pipeline)
9. [Data Flows](#9-data-flows)
10. [Dependencies & Integration Order](#10-dependencies--integration-order)
11. [Security Model](#11-security-model)
12. [Token Efficiency](#12-token-efficiency)
13. [Observability](#13-observability)
14. [Decisions Log](#14-decisions-log)
15. [File Inventory](#15-file-inventory)

---

## 1. System Overview

### 1.1 Purpose

DoPeJar is a cognitive partner system that provides:
- **Altitude-aware assistance**: Operates at appropriate abstraction level (identity→moment)
- **Governed execution**: All actions flow through explicit authorization gates
- **Adaptive reasoning**: Selects strategies based on input characteristics
- **Continuous learning**: Improves from feedback without manual tuning
- **Multi-problem support**: Handles multiple problems simultaneously with isolation

### 1.2 Core Principles

| Principle | Description |
|-----------|-------------|
| **Two-Tempo** | Slow loop (governance) + Fast loop (execution) |
| **Reasoning Proposes, Focus Approves** | Strategy selection separated from authorization |
| **Memory as Bus** | 4 compartments with write gate policy |
| **Agents Never Self-Authorize** | All agent actions require gate approval |
| **Default Deny** | All writes require explicit approval |

### 1.3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INPUT                                      │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. ALTITUDE HRM (Scope Governance)                                          │
│     Location: the_assist/hrm/                                                │
│     Purpose: Determine abstraction level (L4 Identity → L1 Moment)           │
│     Output: Altitude context, friction score                                 │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. REASONING HRM (Strategy Selection) ← PROPOSES AGENTS                     │
│     Location: the_assist/reasoning/                                          │
│     Purpose: Classify input, select strategy, propose agent bundles          │
│     Output: AgentBundleProposal (agents + orchestration mode)                │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ proposal
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. FOCUS HRM (Control Governance) ← APPROVES & EXECUTES                     │
│     Location: locked_system/                                                 │
│     Purpose: Validate proposals, manage stance/gates/commitments, execute    │
│     Output: Approved execution, agent results                                │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. LEARNING HRM (Pattern Memory)                                            │
│     Location: the_assist/learning/                                           │
│     Purpose: Record outcomes, learn patterns, inform future routing          │
│     Output: Pattern matches for Reasoning HRM                                │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RESPONSE                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Four HRM Layers

### 2.1 Altitude HRM (Scope Governance)

**Location:** `the_assist/hrm/`
**Status:** 95% implemented
**Role:** Determines WHAT level of abstraction to operate at

#### Altitude Levels

| Level | Name | Description | Examples |
|-------|------|-------------|----------|
| **L4** | Identity | Why we exist, values, north stars | "What matters to you?" |
| **L3** | Strategy | Priorities, projects, goals | "What are your priorities?" |
| **L2** | Operations | This week, today, tasks | "What's on your plate?" |
| **L1** | Moment | Right now, this conversation | "What's on your mind?" |

#### Key Rule: Cannot Descend Without Context

```
L4 (Identity) ← Can be discussed anytime
    │
    ▼ requires connection
L3 (Strategy) ← Must connect to L4 values
    │
    ▼ requires establishment
L2 (Operations) ← Must have L3 strategic context
    │
    ▼ requires grounding
L1 (Moment) ← Must have L2 operational grounding
```

#### Request Type Classification (L2 Fast Lane)

| Type | Description | Behavior |
|------|-------------|----------|
| **ATOMIC** | Safe, factual, no drift risk | Micro-anchor (not block) |
| **DERIVATIVE** | Risk of drift, needs grounding | Enforce altitude requirements |
| **HIGH_STAKES** | Requires verification | Slowdown + verification |

#### Key Files

| File | Purpose | Status |
|------|---------|--------|
| `altitude.py` | AltitudeGovernor, Level enum, RequestType | 95% |
| `loop.py` | HRM orchestration (plan→evaluate→execute) | 85% |
| `planner.py` | Plan generation at current altitude | 75% |
| `evaluator.py` | Plan and result assessment | 75% |
| `executor.py` | Approved action execution | 70% |
| `history.py` | Session history with search | 100% |

---

### 2.2 Reasoning HRM (Strategy Selection)

**Location:** `the_assist/reasoning/`
**Status:** TO BE BUILT
**Role:** Determines WHAT strategy and agents are needed (PROPOSES, does not execute)

#### Input Classification

| Dimension | Values | Purpose |
|-----------|--------|---------|
| **Complexity** | simple, moderate, complex | How much decomposition needed |
| **Uncertainty** | 0.0 - 1.0 | Confidence in understanding |
| **Conflict** | none, internal, external | Contradictory constraints |
| **Stakes** | low, medium, high | Impact of wrong answer |
| **Horizon** | immediate, near, far | Time scale of decision |

#### Strategy Selection

| Strategy | Trigger | Agent Mode |
|----------|---------|------------|
| **QUICK_ANSWER** | Low complexity, low stakes | None or single agent |
| **DECOMPOSITION** | High complexity | Hierarchical |
| **VERIFICATION** | High stakes | Voting |
| **EXPLORATION** | High uncertainty | Parallel |
| **DIALOGUE** | Conflict present | Pipeline |

#### Escalation Signals

| Signal | Threshold | Action |
|--------|-----------|--------|
| Uncertainty | confidence < 0.6 | Escalate to more thorough strategy |
| Conflict | medium or high | Route to dialogue/resolution |
| Stakes mismatch | high stakes + low verification | Force verification mode |

#### Agent Bundle Proposal

```python
@dataclass
class AgentBundleProposal:
    strategy: str                    # decomposition | verification | exploration | dialogue
    classification: InputClassification
    agents: list[str]                # Agent IDs to activate
    orchestration_mode: str          # pipeline | parallel | voting | hierarchical
    mode_config: dict                # Mode-specific configuration
    reason: str                      # Why these agents, why this mode
    confidence: float                # How confident in this proposal
    fallback: Optional[str]          # Alternative if denied
```

#### Key Files (TO BE CREATED)

| File | Purpose |
|------|---------|
| `router.py` | Main ReasoningRouter class |
| `classifier.py` | InputClassifier for signal detection |
| `strategies.py` | Strategy definitions and selection logic |
| `escalation.py` | Escalation/de-escalation management |
| `proposals.py` | AgentBundleProposal generation |

---

### 2.3 Focus HRM (Control Governance)

**Location:** `locked_system/`
**Status:** 85% implemented
**Role:** APPROVES proposals and EXECUTES agents (sole authority for state changes)

#### Stance Machine (2x2 Matrix)

```
                    Accuracy        Momentum
                    ────────        ────────
Exploration         SENSEMAKING     DISCOVERY
Exploitation        EVALUATION      EXECUTION
```

| Stance | Allowed Actions | Suppressed Actions |
|--------|-----------------|-------------------|
| **SENSEMAKING** | question, clarify, explore, reframe | execute, commit, optimize |
| **DISCOVERY** | brainstorm, prototype, experiment | commit, optimize, evaluate |
| **EXECUTION** | execute, deliver, implement | reframe, explore, question_frame |
| **EVALUATION** | assess, compare, measure, decide | execute, explore, commit |

#### Gate System

| Gate | Purpose | Transitions To |
|------|---------|----------------|
| **Framing** | Clarifying what matters | SENSEMAKING, DISCOVERY |
| **Commitment** | Deciding to move forward | EXECUTION |
| **Evaluation** | Assessing outcomes | EVALUATION, SENSEMAKING |
| **Emergency** | Escape hatch (costly) | SENSEMAKING |
| **AgentApproval** | Validate agent proposals | (validates, doesn't transition) |

#### Agent Approval Gate (NEW)

```python
class AgentApprovalGate:
    def evaluate(proposal: AgentBundleProposal, stance: Stance, commitment: Commitment) -> GateDecision:
        # Check stance compatibility
        # Check commitment alignment
        # Check agent authorization
        # Check orchestration mode constraints
        return GateDecision(approved=True/False, reason="...")
```

#### Key Files

| File | Purpose | Status |
|------|---------|--------|
| `slow_loop/stance.py` | StanceMachine class | 90% |
| `slow_loop/gates.py` | GateController class | 90% |
| `slow_loop/commitment.py` | CommitmentManager class | 85% |
| `front_door/agent.py` | HRM Router (signal detection) | 85% |
| `front_door/signals.py` | SignalDetector | 85% |
| `agents/runtime.py` | Agent execution runtime | 80% |
| `agents/orchestrator.py` | Multi-agent orchestration | 75% |
| `agents/firewall.py` | Output validation | 85% |
| `lanes/store.py` | LaneStore class | 85% |
| `executor/gates.py` | WriteApprovalGate | 85% |

---

### 2.4 Learning HRM (Pattern Memory)

**Location:** `the_assist/learning/`
**Status:** TO BE BUILT
**Role:** Records outcomes, learns patterns, informs future routing

#### Pattern Storage

```python
@dataclass
class SynthesizedPattern:
    id: str
    pattern_type: str            # signal | routing | outcome | behavioral | coaching
    content: dict
    evidence_ids: list[str]      # Links to episodic entries
    confidence: float
    created_at: datetime
    last_validated: datetime
    protected: bool = False      # Never auto-remove if True
```

#### Learning Cycle

1. **Capture**: Collect signal→routing→outcome tuples from session
2. **Analyze**: Group similar patterns, calculate hit rates
3. **Update**: Strengthen high-hit, weaken low-hit patterns
4. **Trim**: NO AUTOMATIC TRIM (per decision) - manual only
5. **Generalize**: Merge similar patterns into abstractions

#### Integration with Reasoning HRM

```
Reasoning HRM                          Learning HRM
     │                                      │
     │ "Classifying input..."               │
     │                                      │
     │──── query: similar signals? ────────>│
     │                                      │
     │<─── pattern matches (if any) ────────│
     │                                      │
     │ "Pattern match found, using          │
     │  cached strategy instead of          │
     │  full classification"                │
```

#### Key Files (TO BE CREATED)

| File | Purpose |
|------|---------|
| `patterns.py` | PatternStore class |
| `feedback_loop.py` | Session analysis and pattern updates |
| `generalizer.py` | Pattern merging and abstraction |

---

## 3. Memory Bus Architecture

### 3.1 Core Design: Memory as Bus with Compartments

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MEMORY BUS                                      │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  WORKING    │  │   SHARED    │  │  EPISODIC   │  │  SEMANTIC   │        │
│  │    SET      │  │  REFERENCE  │  │   TRACE     │  │  SYNTHESIS  │        │
│  │ (per-problem│  │ (cross-prob │  │ (append-only│  │ (distilled  │        │
│  │  isolated)  │  │  versioned) │  │  audit)     │  │  patterns)  │        │
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

### 3.2 Four Compartments

| Compartment | Scope | Lifetime | Key Property |
|-------------|-------|----------|--------------|
| **Working Set** | Per-problem | Minutes-hours | Isolated, expires aggressively |
| **Shared Reference** | Cross-problem | Long-lived | Versioned, citable |
| **Episodic Trace** | Append-only | Long-lived | Never overwritten, searchable |
| **Semantic Synthesis** | Distilled | Long-lived | Evidence-linked patterns |

#### Working Set (Per-Problem, Hot)

- **Purpose**: Hold what current problem needs RIGHT NOW
- **Isolation**: Problem A cannot read Problem B's working set
- **Contains**: Constraints, assumptions, open questions, drafts, local decisions
- **TTL**: Default 2 hours, max 24 hours

#### Shared Reference (Cross-Problem, Stable)

- **Purpose**: Reusable facts and canonical documents
- **Versioned**: Every update creates new version
- **Citable**: Every fact has source reference
- **Contains**: North stars, priorities, preferences, glossaries

#### Episodic Trace (Time-Indexed, Audit)

- **Purpose**: "What happened when" - complete audit trail
- **Append-only**: Never overwritten, only superseded
- **Searchable**: By time, tags, problem_id, HRM layer
- **Contains**: Turns, tool outputs, decisions, deltas

#### Semantic Synthesis (Distilled, Portable)

- **Purpose**: Extracted patterns and "what we believe"
- **Evidence-linked**: Every conclusion points to episodic evidence
- **Contains**: Conclusions, heuristics, policies, pattern codes

### 3.3 Write Gate (Policy Layer)

**The gate decides:**
- Is this local (Working Set) or global (Shared/Semantic)?
- Is it a draft or a fact?
- What confidence threshold to persist?
- What expiry/decay rule applies?
- Does this violate a trust boundary?

**Signal inputs to gate:**

| Signal | Source | Meaning |
|--------|--------|---------|
| Progress Delta | All HRMs | Did we learn something? |
| Conflict Level | Reasoning HRM | Is it contested? → stay local |
| Source Quality | All HRMs | Was it grounded? → log only if low |
| Alignment Score | Altitude HRM | Was it relevant? → don't synthesize if low |
| Blast Radius | Focus HRM | If wrong, how bad? → higher threshold |

**Gate rules:**
- High blast radius → higher confidence threshold required
- Conflict detected → Working Set only (don't pollute global)
- Low alignment → won't synthesize
- Low source quality → Episodic only (log, don't conclude)

### 3.4 Multi-Problem Support

**Current state:** Serial (one lane active, no isolation)
**Target state:** Parallel with isolation

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Problem A   │  │ Problem B   │  │ Problem C   │
│ (active)    │  │ (paused)    │  │ (background)│
│             │  │             │  │             │
│ Working Set │  │ Working Set │  │ Working Set │
│ (ISOLATED)  │  │ (ISOLATED)  │  │ (ISOLATED)  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┴────────────────┘
                        │
          ┌─────────────┴─────────────┐
          │    SHARED REFERENCE       │ ← All problems read
          │    EPISODIC TRACE         │ ← Tagged by problem_id
          │    SEMANTIC SYNTHESIS     │ ← Cross-problem patterns
          └───────────────────────────┘
```

### 3.5 Key Files (TO BE CREATED)

| File | Purpose |
|------|---------|
| `shared/memory/bus.py` | MemoryBus main class |
| `shared/memory/working_set.py` | WorkingSetStore |
| `shared/memory/shared_reference.py` | SharedReferenceStore |
| `shared/memory/episodic_trace.py` | EpisodicTraceStore |
| `shared/memory/semantic_synthesis.py` | SemanticSynthesisStore |
| `shared/memory/write_gate.py` | WriteGate policy |
| `shared/memory/problem_registry.py` | ProblemRegistry |

---

## 4. Agent Orchestration

### 4.1 Core Principle: Reasoning Proposes, Focus Approves

| Component | Can Propose Agents | Can Approve Agents | Can Execute Agents |
|-----------|-------------------|--------------------|--------------------|
| **Altitude HRM** | No | No | No |
| **Reasoning HRM** | YES | No | No |
| **Focus HRM** | No | YES | YES (via runtime) |
| **Learning HRM** | No | No | No |
| **Agents themselves** | Can request (hierarchical) | No | No |

### 4.2 Four Orchestration Modes

#### Mode 1: Pipeline (Serial)

```
Input → Agent A → Output A → Agent B → Output B → Agent C → Final
```

**Use Case:** Sequential refinement (draft → edit → review)

**Config:**
```python
{
    "sequence": ["draft_agent", "edit_agent", "review_agent"],
    "pass_output": True,
    "stop_on_failure": True
}
```

#### Mode 2: Parallel (Simultaneous)

```
         ┌─→ Agent A ──→ Output A ─┐
Input ───┼─→ Agent B ──→ Output B ─┼──→ Aggregator → Final
         └─→ Agent C ──→ Output C ─┘
```

**Use Case:** Multi-perspective analysis, speed-critical

**Config:**
```python
{
    "agents": ["analyst_a", "analyst_b", "analyst_c"],
    "aggregation": "merge" | "select_best" | "synthesize",
    "timeout_ms": 5000,
    "min_responses": 2
}
```

#### Mode 3: Voting (Consensus)

```
         ┌─→ Agent A ──→ Vote A ─┐
Input ───┼─→ Agent B ──→ Vote B ─┼──→ Tally → Decision
         └─→ Agent C ──→ Vote C ─┘
```

**Use Case:** High-stakes decisions requiring agreement

**Config:**
```python
{
    "voters": ["judge_a", "judge_b", "judge_c"],
    "threshold": 0.6,
    "tiebreaker": "first" | "abstain" | "escalate"
}
```

#### Mode 4: Hierarchical (Delegation)

```
                    ┌──────────────┐
                    │  Lead Agent  │
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Sub-Agent A│  │ Sub-Agent B│  │ Sub-Agent C│
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          └───────────────┴───────────────┘
                          │
                    ┌─────┴─────┐
                    │Lead Agent │
                    │(Synthesize)│
                    └───────────┘
```

**Use Case:** Complex problems requiring decomposition

**Config:**
```python
{
    "lead": "planner_agent",
    "delegates": ["research_agent", "analysis_agent"],
    "max_delegation_depth": 2,
    "require_synthesis": True
}
```

### 4.3 Agent Runtime

```python
class AgentRuntime:
    def execute_bundle(agents: list[str], context: AgentExecutionContext) -> AgentExecutionHandle:
        # 1. Load approved agents
        # 2. Execute per orchestration mode
        # 3. Validate all outputs through firewall
        # 4. Return results to Focus HRM
```

### 4.4 Agent Firewall

All agent outputs validated before returning:
- Agents cannot make decisions (only proposals)
- No unauthorized capability requests
- Valid output packet structure
- Prompt injection detection

---

## 5. Attention & Priority System

### 5.1 Four Layers of Attention

| Layer | Mechanism | Determines |
|-------|-----------|------------|
| **Altitude** | L4/L3/L2/L1 levels | WHAT abstraction level |
| **Stance** | 2x2 matrix | HOW to approach |
| **Commitment** | Lease with TTL | HOW LONG to focus |
| **Problem** | Working Set isolation | WHICH problem has attention |

### 5.2 Priority Resolution

| Priority | Signal | Behavior |
|----------|--------|----------|
| 1 | EMERGENCY | Immediately to sensemaking |
| 2 | URGENCY | Execute first, align after |
| 3 | EMOTIONAL_OVERLOAD | Trigger evaluation gate |
| 4 | HIGH_STAKES | Verification before action |
| 5 | LANE_SWITCH | Save context, switch |
| 6 | NORMAL | Follow current stance rules |

---

## 6. Signal System

### 6.1 Signal Types

| Signal | Detection Patterns | Proposed Gate |
|--------|-------------------|---------------|
| FORMAL_WORK | "let's work on", "help me write" | WorkDeclarationGate |
| INTERRUPT | "actually", "wait", "hold on" | LaneSwitchGate |
| URGENCY | "urgent", "asap", "emergency" | LaneSwitchGate (elevated) |
| COMPLETION | "done", "finished", "wrap up" | EvaluationGate |
| EMOTIONAL | frustration/overwhelm | EvaluationGate (check-in) |

### 6.2 Emotional Telemetry

Bounded states:
- **Energy**: depleted → low → neutral → high → elevated
- **Focus**: scattered → distracted → neutral → focused → locked
- **Stress**: calm → mild → moderate → high → overwhelmed

---

## 7. Gate System

### 7.1 Gate Types

| Gate | Purpose | Transitions To | Allowed Writes |
|------|---------|----------------|----------------|
| **Framing** | Clarifying what matters | SENSEMAKING, DISCOVERY | Draft commitment |
| **Commitment** | Deciding to move forward | EXECUTION | Activate commitment |
| **Evaluation** | Assessing outcomes | EVALUATION, SENSEMAKING | Update commitment |
| **Emergency** | Escape hatch (costly) | SENSEMAKING | Log emergency |
| **WriteApproval** | Filesystem writes | (no transition) | Approved writes |
| **AgentApproval** | Agent activation | (no transition) | (none) |

### 7.2 Gate Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FRAMING    │────>│ COMMITMENT  │────>│  EXECUTION  │
│   GATE      │     │    GATE     │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
      ▲                                        │
      │             ┌─────────────┐            │
      └─────────────│ EVALUATION  │<───────────┘
                    │    GATE     │
                    └─────────────┘
```

---

## 8. Execution Pipeline

### 8.1 Turn Execution Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│  1. INPUT PROCESSING                                                      │
│     • Altitude HRM: Detect level, check context requirements              │
│     • Signal detection: Identify intent signals                           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  2. REASONING (Strategy Selection)                                        │
│     • Classify input (complexity, uncertainty, stakes)                    │
│     • Query Learning HRM for pattern matches                              │
│     • Select strategy and propose agent bundle                            │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ AgentBundleProposal
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  3. FOCUS (Governance)                                                    │
│     • Validate proposal against stance/commitment                         │
│     • If approved: activate agents via runtime                            │
│     • Manage gate transitions                                             │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  4. AGENT EXECUTION                                                       │
│     • Execute per orchestration mode (pipeline/parallel/voting/hier)      │
│     • All outputs through firewall                                        │
│     • Results back to Focus HRM                                           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  5. POST-TURN                                                             │
│     • Memory extraction (compressed format)                               │
│     • Record (signal, routing, outcome) for Learning HRM                  │
│     • Trace logging                                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Flows

### 9.1 HRM Layer Communication

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Altitude   │     │  Reasoning  │     │   Focus     │     │  Learning   │
│    HRM      │     │    HRM      │     │    HRM      │     │    HRM      │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │ altitude_level    │                   │                   │
       │ friction_score    │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │ AgentBundleProposal                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │ pattern_matches   │                   │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │                   │                   │ (signal,routing,  │
       │                   │                   │  outcome)         │
       │                   │                   │──────────────────>│
```

### 9.2 Memory Bus Communication

```
All HRMs
    │
    ├──> Working Set (problem-scoped writes)
    │
    ├──> Shared Reference (gated global writes)
    │
    ├──> Episodic Trace (append-only logs)
    │
    └──> Semantic Synthesis (gated pattern writes)
              │
              ▼
         Write Gate (policy evaluation)
```

---

## 10. Dependencies & Integration Order

### 10.1 Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FOUNDATION                                     │
│  • shared/memory/ (Memory Bus)                                           │
│  • shared/tracing/ (Observability)                                       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FOCUS HRM                                      │
│  • stance.py, gates.py, commitment.py                                    │
│  • agents/runtime.py, agents/orchestrator.py                             │
│  Depends on: Foundation                                                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          ALTITUDE HRM                                    │
│  • altitude.py, loop.py                                                  │
│  Depends on: Focus HRM (for gate validation)                             │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         REASONING HRM                                    │
│  • router.py, classifier.py, strategies.py                               │
│  Depends on: Altitude (context), Focus (approval), Learning (patterns)  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          LEARNING HRM                                    │
│  • patterns.py, feedback_loop.py                                         │
│  Depends on: All HRMs (receives signals from all)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Milestones

| Milestone | Description | Components |
|-----------|-------------|------------|
| **M0.0** | Foundation | Memory Bus, Tracing |
| **M0.1** | Integration | Wire Altitude ↔ Focus |
| **M0.2** | Consolidation | Remove duplicates, UI module |
| **M0.3** | Reasoning HRM | router.py, strategies.py, escalation.py |
| **M0.4** | Learning HRM | patterns.py, feedback_loop.py |
| **M1.0** | Unified | Single entry point, all 4 HRMs working |

---

## 11. Security Model

### 11.1 Authority Hierarchy

```
CORE LAWS (Highest)
    │
    ▼
GATE CONTROLLER (Sole authority for state changes)
    │
    ▼
AGENTS (Proposal authority only)
```

### 11.2 Key Constraints

1. **Default Deny**: All writes require explicit approval
2. **Proposal-Only Agents**: Agents propose, core decides
3. **Sandboxed Context**: Agent context cannot override core laws
4. **Consent-Aware**: User consent checked before persist
5. **Agents Never Self-Authorize**: Even hierarchical delegation is pre-approved

---

## 12. Token Efficiency

### 12.1 Compression Strategy

All memory uses compressed format:

```python
# PROSE (wasteful):
"John is a work colleague who often blocks progress"

# COMPRESSED (efficient):
{"name": "john", "r": "wk", "t": ["bottleneck"]}

# Token savings: ~70%
```

### 12.2 Targets

| Data Type | Current | Target |
|-----------|---------|--------|
| Patterns | 60% savings | 70% |
| People | 50% savings | 75% |
| Signals | No compression | 60% |
| Routing | N/A | 70% |

**Overall target: 65% average token reduction**

---

## 13. Observability

### 13.1 Trace Event Structure

```python
@dataclass
class TraceEvent:
    trace_id: str
    parent_id: Optional[str]
    timestamp: datetime
    hrm_layer: str           # altitude|focus|reasoning|learning
    operation: str           # read|write|transition|route|execute
    component: str
    input_summary: str
    output_summary: str
    duration_ms: int
    status: str              # success|error|blocked
    metadata: dict
```

### 13.2 Enabling Tracing

```bash
export DOPEJAR_TRACE=1
python -m the_assist.main --trace
```

---

## 14. Decisions Log

| Decision | Choice | Date |
|----------|--------|------|
| Memory Locking | Implement from start | 2026-01-13 |
| Naming | Keep `locked_system`, `front_door` | 2026-01-13 |
| Trim Policy | No auto-trim (manual only) | 2026-01-13 |
| Escalation Threshold | 0.6 confidence | 2026-01-13 |
| Orchestration Modes | All 4 (pipeline, parallel, voting, hierarchical) | 2026-01-13 |
| Agent Authority | Reasoning proposes, Focus approves | 2026-01-13 |
| Memory Model | Bus with 4 compartments + write gate | 2026-01-13 |
| Multi-Problem | Supported via Working Set isolation | 2026-01-13 |

---

## 15. File Inventory

### 15.1 Altitude HRM (the_assist/hrm/)

| File | Status | Purpose |
|------|--------|---------|
| altitude.py | 95% | AltitudeGovernor, Level enum |
| loop.py | 85% | HRM orchestration |
| planner.py | 75% | Plan generation |
| evaluator.py | 75% | Plan evaluation |
| executor.py | 70% | Action execution |
| history.py | 100% | Session history |

### 15.2 Reasoning HRM (the_assist/reasoning/) - TO BUILD

| File | Status | Purpose |
|------|--------|---------|
| router.py | 0% | ReasoningRouter class |
| classifier.py | 0% | InputClassifier |
| strategies.py | 0% | Strategy definitions |
| escalation.py | 0% | Escalation management |
| proposals.py | 0% | AgentBundleProposal |

### 15.3 Focus HRM (locked_system/)

| File | Status | Purpose |
|------|--------|---------|
| slow_loop/stance.py | 90% | StanceMachine |
| slow_loop/gates.py | 90% | GateController |
| slow_loop/commitment.py | 85% | CommitmentManager |
| front_door/agent.py | 85% | HRM Router |
| front_door/signals.py | 85% | SignalDetector |
| agents/runtime.py | 80% | Agent execution |
| agents/orchestrator.py | 75% | Multi-agent orchestration |
| agents/firewall.py | 85% | Output validation |
| lanes/store.py | 85% | LaneStore |
| executor/gates.py | 85% | WriteApprovalGate |

### 15.4 Learning HRM (the_assist/learning/) - TO BUILD

| File | Status | Purpose |
|------|--------|---------|
| patterns.py | 0% | PatternStore |
| feedback_loop.py | 0% | Session analysis |
| generalizer.py | 0% | Pattern merging |

### 15.5 Memory Bus (shared/memory/) - TO BUILD

| File | Status | Purpose |
|------|--------|---------|
| bus.py | 0% | MemoryBus class |
| working_set.py | 0% | WorkingSetStore |
| shared_reference.py | 0% | SharedReferenceStore |
| episodic_trace.py | 0% | EpisodicTraceStore |
| semantic_synthesis.py | 0% | SemanticSynthesisStore |
| write_gate.py | 0% | WriteGate policy |
| problem_registry.py | 0% | ProblemRegistry |

### 15.6 Tracing (shared/tracing/) - TO BUILD

| File | Status | Purpose |
|------|--------|---------|
| tracer.py | 0% | Tracer singleton |
| viewer.py | 0% | Trace viewer CLI |
| stats.py | 0% | Performance stats |

---

## Appendix A: Pattern Code Reference

### Behavioral Patterns (from memory_v2.py)

```python
PATTERN_CODES = {
    "timeboxing": "Uses timeboxing to prevent analysis paralysis",
    "exit_criteria": "Sets clear exit criteria (time OR outcome)",
    "buffer_planning": "Builds buffers into schedules",
    "schedule_underest": "Underestimates schedule packed-ness",
    "struct_prefer": "Prefers structured breakdowns",
    "numbers_not_bullets": "Prefers numbers over bullets",
    "fast_context_switch": "Fast context switching, high ADHD",
}
```

### Coaching Patterns (from memory_v2.py)

```python
COACHING_CODES = {
    "ask_impact": "Ask how tasks connect to strategies",
    "surface_why": "Surface the 'why' behind tasks",
    "strategic_questions": "Ask bigger picture questions",
    "challenge_alignment": "Challenge when tasks don't align",
    "push_harder": "User wants more direct pushback",
    "more_concise": "Be more concise, less explanation",
}
```

### Reasoning Patterns (TO ADD)

```python
REASONING_PATTERN_CODES = {
    "needs_decomp": "Complex problems need decomposition",
    "quick_answer_ok": "Simple questions, fast response",
    "verify_high_stakes": "High-stakes need verification",
}
```

---

**End of Document**
