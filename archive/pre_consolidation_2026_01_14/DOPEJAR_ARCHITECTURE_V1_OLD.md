# DoPeJar Architecture - Deep Design Document

**Version:** 1.0
**Date:** 2026-01-13
**Purpose:** Enable agent audit of design prior to implementation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Four HRM Layers](#2-four-hrm-layers)
3. [Attention & Priority System](#3-attention--priority-system)
4. [Signal System](#4-signal-system)
5. [Memory Architecture](#5-memory-architecture)
6. [Gate System](#6-gate-system)
7. [Execution Pipeline](#7-execution-pipeline)
8. [Data Flows](#8-data-flows)
9. [Dependencies & Integration Order](#9-dependencies--integration-order)
10. [New Systems Design](#10-new-systems-design)
11. [Security Model](#11-security-model)
12. [Token Efficiency](#12-token-efficiency)
13. [Observability](#13-observability)
14. [Open Questions](#14-open-questions)

---

## 1. System Overview

### 1.1 Purpose

DoPeJar is a cognitive partner system that provides:
- **Altitude-aware assistance**: Operates at appropriate abstraction level (identity→moment)
- **Governed execution**: All actions flow through explicit authorization gates
- **Adaptive reasoning**: Selects strategies based on input characteristics
- **Continuous learning**: Improves from feedback without manual tuning

### 1.2 Core Principle: Two-Tempo Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SLOW LOOP (Governance)                           │
│  • Runs every turn                                                       │
│  • Manages stance, gates, commitments                                    │
│  • Authorizes capabilities                                               │
│  • Cannot be bypassed                                                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ authorizes
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FAST LOOP (Execution)                            │
│  • Runs within authorized scope                                          │
│  • Executes approved actions                                             │
│  • Monitored by continuous evaluation                                    │
│  • Reports results back to slow loop                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 High-Level Component Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ALTITUDE HRM (Scope Governance)                                         │
│  the_assist/hrm/                                                         │
│  • Detects altitude level (L4→L1)                                        │
│  • Enforces "can't go tactical without strategic"                        │
│  • Manages friction (preachy detection)                                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FOCUS HRM (Control Governance) - currently "locked_system"              │
│  locked_system/                                                          │
│  • HRM Router: Signal detection → Bundle → Agent selection               │
│  • Stance Machine: SENSEMAKING/DISCOVERY/EXECUTION/EVALUATION            │
│  • Gate Controller: Framing/Commitment/Evaluation/Emergency              │
│  • Commitment Manager: Lease-based focus with TTL                        │
│  • Lanes: Parallel workstream scheduler                                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  REASONING HRM (Strategy Selection) - TO BE BUILT                        │
│  the_assist/reasoning/                                                   │
│  • Classifies input complexity/type                                      │
│  • Selects reasoning strategy                                            │
│  • Manages escalation/de-escalation                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  LEARNING HRM (Pattern Memory) - TO BE BUILT                             │
│  the_assist/learning/                                                    │
│  • Stores signal→routing→outcome tuples                                  │
│  • Grows from feedback                                                   │
│  • Trims stale patterns                                                  │
│  • Generalizes across similar patterns                                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        RESPONSE                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Four HRM Layers

### 2.1 Altitude HRM (Scope Governance)

**Location:** `the_assist/hrm/`
**Status:** 95% implemented

#### Purpose
Ensures conversations operate at appropriate abstraction levels and prevents tactical drift without strategic grounding.

#### Altitude Levels

| Level | Name | Description | Examples |
|-------|------|-------------|----------|
| **L4** | Identity | Why we exist, values, north stars | "What matters to you?", "Who do you want to be?" |
| **L3** | Strategy | Priorities, projects, goals | "What are your priorities?", "What's the goal?" |
| **L2** | Operations | This week, today, tasks | "What's on your plate?", "What's due?" |
| **L1** | Moment | Right now, this conversation | "What's on your mind?", "How are you feeling?" |

#### Key Rule: Cannot Descend Without Context

```python
# ENFORCED CONSTRAINT
L4 (Identity) can be discussed anytime
L3 (Strategy) requires connection to L4 values
L2 (Operations) requires L3 strategic context
L1 (Moment) requires L2 operational grounding
```

#### Request Type Classification (L2 Fast Lane)

| Type | Description | Behavior |
|------|-------------|----------|
| **ATOMIC** | Safe, factual, no drift risk | Micro-anchor (not block) |
| **DERIVATIVE** | Risk of drift, needs grounding | Enforce altitude requirements |
| **HIGH_STAKES** | Requires verification | Slowdown + verification |

**Pattern Keywords:**

```python
ATOMIC_PATTERNS = [
    "what's on my calendar", "what time", "when is",
    "list my", "show me", "status of"
]

DERIVATIVE_PATTERNS = [
    "what should i", "help me decide", "prioritize",
    "how should i", "analyze", "compare"
]

HIGH_STAKES_PATTERNS = [
    "invest", "transfer money", "send", "delete",
    "legal", "medical", "security"
]
```

#### Friction Tracking

Altitude HRM tracks when it blocks L2 requests, detecting when the system is being "preachy":

```python
def record_friction(requested_level, actual_level, was_blocked):
    if was_blocked and requested_level == "L2":
        friction_events.append({...})
        total_friction_score += 1

def is_friction_high(threshold=3):
    return total_friction_score >= threshold
```

**If friction is high:** System becomes more permissive, uses execute-first policy.

#### Key Files

| File | Purpose |
|------|---------|
| `altitude.py` | AltitudeGovernor, Level enum, RequestType classification |
| `loop.py` | HRM loop orchestration (plan→evaluate→execute) |
| `planner.py` | Generates plans at current altitude |
| `evaluator.py` | Assesses plans and results |
| `executor.py` | Runs approved actions |
| `history.py` | Session history with search |

#### Data Structures

```python
@dataclass
class AltitudeContext:
    l4_connected: bool = False      # Has identity been discussed?
    l3_established: bool = False    # Has strategy been established?
    l2_grounded: bool = False       # Has operations context been set?
    current_level: str = "L3"       # Starting level
    level_history: list = []        # Track transitions
    time_at_current: int = 0        # Exchanges at current level
    friction_events: list = []      # Blocked requests
    total_friction_score: int = 0   # Cumulative friction

@dataclass
class ValidationResult:
    allowed: bool
    reason: str
    suggested_level: Optional[str]
    required_action: Optional[str]
    request_type: str               # atomic | derivative | high_stakes
    use_micro_anchor: bool          # Light anchor instead of block
    micro_anchor_text: Optional[str]
    execute_first: bool             # Execute immediately, align after
    requires_verification: bool     # High-stakes slowdown
```

---

### 2.2 Focus HRM (Control Governance)

**Location:** `locked_system/` (to be renamed `hrm_routing/`)
**Status:** 85% implemented

#### Purpose
Controls attention through stance machine, gates, commitments, and lanes.

#### Stance Machine (2x2 Matrix)

```
                    Accuracy        Momentum
                    ────────        ────────
Exploration         SENSEMAKING     DISCOVERY
Exploitation        EVALUATION      EXECUTION
```

| Stance | Mode | Priority | Allowed Actions | Suppressed Actions |
|--------|------|----------|-----------------|-------------------|
| **SENSEMAKING** | Exploration | Accuracy | question, clarify, explore, reframe | execute, commit, optimize |
| **DISCOVERY** | Exploration | Momentum | brainstorm, prototype, experiment, diverge | commit, optimize, evaluate |
| **EXECUTION** | Exploitation | Momentum | execute, deliver, implement, progress | reframe, explore, question_frame |
| **EVALUATION** | Exploitation | Accuracy | assess, compare, measure, decide | execute, explore, commit |

#### Stance Transitions (Gate-Controlled Only)

```python
VALID_TRANSITIONS = {
    "framing": {
        SENSEMAKING: [SENSEMAKING, DISCOVERY],
        DISCOVERY: [SENSEMAKING, DISCOVERY],
        EXECUTION: [SENSEMAKING, DISCOVERY],  # Exit execution
        EVALUATION: [SENSEMAKING, DISCOVERY],
    },
    "commitment": {
        SENSEMAKING: [EXECUTION],
        DISCOVERY: [EXECUTION],
        EXECUTION: [EXECUTION],  # Stay
        EVALUATION: [EXECUTION],
    },
    "evaluation": {
        SENSEMAKING: [EVALUATION],
        DISCOVERY: [EVALUATION],
        EXECUTION: [EVALUATION],
        EVALUATION: [SENSEMAKING, EXECUTION],  # Renew or revise
    },
    "emergency": {
        ALL: [SENSEMAKING],  # Always to sensemaking
    },
}
```

#### Gate System

| Gate | Purpose | Allowed Writes |
|------|---------|----------------|
| **Framing** | Clarifying what matters | Draft/renew commitment lease, lock frame decision |
| **Commitment** | Deciding to move forward | Activate/renew commitment lease, log binding decisions |
| **Evaluation** | Assessing outcomes | Renew/revise/expire commitment, update artifact status |
| **Emergency** | Escape hatch (costly) | Log emergency decision, reset commitment clock |

#### Commitment Manager

```python
@dataclass
class Commitment:
    id: str
    goal: str
    mode: str                    # "deliver" | "explore" | "decide"
    created_at: datetime
    turns_remaining: int         # TTL
    lane_id: Optional[str]

class CommitmentManager:
    def create(goal, mode, turns=10) -> Commitment
    def renew(additional_turns) -> bool
    def expire() -> None
    def tick() -> None           # Decrement turns each exchange
    def has_active_commitment() -> bool
```

#### Lane System

Lanes = parallel workstream scheduler with explicit bookmarking.

```python
@dataclass
class Lane:
    lane_id: str
    status: str                  # "active" | "paused" | "completed"
    lease_goal: str
    lease_mode: str
    created_at: datetime
    paused_at: Optional[datetime]
    snapshot: Optional[dict]     # Frozen state when paused
    bookmark: Optional[str]      # Human-readable resume point

# Lane Operations
class LaneStore:
    def create(goal, mode) -> Lane
    def pause(snapshot, bookmark) -> bool
    def resume() -> Optional[Lane]
    def complete() -> bool
    def switch(to_lane_id) -> bool
```

#### HRM Router (currently `front_door/`)

Detects signals from user input and proposes gates/bundles.

```
User Input → Signal Detection → Gate Proposal → Bundle Selection → Agent(s)
```

**Signal Types:**

| Signal | Detection Pattern | Proposed Gate |
|--------|------------------|---------------|
| FORMAL_WORK | "let's work on", "help me write" | WorkDeclarationGate |
| INTERRUPT | "actually", "wait", "hold on" | LaneSwitchGate |
| URGENCY | "urgent", "asap", "emergency" | LaneSwitchGate (elevated) |
| COMPLETION | "done", "finished", "wrap up" | EvaluationGate |
| EMOTIONAL | frustration/overwhelm signals | EvaluationGate (check-in) |

**Agent Bundles:**

| Bundle | Agents | Use Case |
|--------|--------|----------|
| **writer** | DraftAgent, EditAgent, ReviewAgent | Writing tasks |
| **finance** | AnalysisAgent, ComparisonAgent | Financial analysis |
| **monitor** | StatusAgent, AlertAgent | Monitoring/tracking |

#### Key Files

| File | Purpose |
|------|---------|
| `slow_loop/stance.py` | StanceMachine class |
| `slow_loop/gates.py` | GateController class |
| `slow_loop/commitment.py` | CommitmentManager class |
| `lanes/store.py` | LaneStore class |
| `lanes/gates.py` | WorkDeclarationGate, LaneSwitchGate |
| `front_door/agent.py` | FrontDoorAgent (HRM Router) |
| `front_door/signals.py` | SignalDetector |
| `front_door/bundles.py` | BundleProposer |
| `executor/gates.py` | WriteApprovalGate |

---

### 2.3 Reasoning HRM (Strategy Selection)

**Location:** `the_assist/reasoning/` (TO BE BUILT)
**Status:** 0% implemented

#### Purpose
Selects appropriate reasoning strategy based on input characteristics and manages escalation/de-escalation.

#### Signal-Based Routing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INPUT CLASSIFIER                                 │
│                                                                         │
│  Detects:                                                               │
│  • Complexity: simple | moderate | complex                              │
│  • Uncertainty: low | medium | high                                     │
│  • Conflict: none | internal | external                                 │
│  • Stakes: low | medium | high                                          │
│  • Horizon: immediate | near | far                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         STRATEGY SELECTOR                                │
│                                                                         │
│  Routes to:                                                             │
│  • QUICK_ANSWER: Simple, low-stakes, low-uncertainty                    │
│  • DECOMPOSITION: Complex, needs breakdown                              │
│  • VERIFICATION: High-stakes, needs confirmation                        │
│  • EXPLORATION: High-uncertainty, needs options                         │
│  • DIALOGUE: Conflict present, needs resolution                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ESCALATION MANAGER                               │
│                                                                         │
│  Escalate when:                                                         │
│  • Uncertainty signal: confidence < threshold                           │
│  • Conflict signal: contradictory constraints                           │
│  • Cost-value mismatch: effort vs impact unclear                        │
│  • Horizon mismatch: tactical request in strategic context              │
│                                                                         │
│  De-escalate when:                                                      │
│  • Pattern match: seen this before, know the answer                     │
│  • User override: "just do it"                                          │
│  • Simplification: problem became simpler                               │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Reasoning Strategies

| Strategy | Trigger | Behavior | Example |
|----------|---------|----------|---------|
| **QUICK_ANSWER** | Low complexity, low stakes | Direct response, no elaboration | "What time is it?" |
| **DECOMPOSITION** | High complexity | Break into sub-problems, solve sequentially | "Plan my product launch" |
| **VERIFICATION** | High stakes | Confirm understanding before acting | "Transfer $10,000" |
| **EXPLORATION** | High uncertainty | Generate options, compare trade-offs | "Should I take this job?" |
| **DIALOGUE** | Conflict present | Surface conflict, seek resolution | "I want X but also Y" |

#### Escalation Signals

| Signal | Description | Detection |
|--------|-------------|-----------|
| **UNCERTAINTY** | Model not confident in answer | Confidence score < 0.6 |
| **CONFLICT** | Contradictory constraints | Multiple incompatible goals |
| **COST_VALUE_MISMATCH** | Effort vs impact unclear | Large request, unclear benefit |
| **HORIZON_MISMATCH** | Wrong abstraction level | Tactical request needs strategic context |

#### Proposed Data Structures

```python
@dataclass
class InputClassification:
    complexity: str          # simple | moderate | complex
    uncertainty: float       # 0.0 - 1.0
    conflict: str            # none | internal | external
    stakes: str              # low | medium | high
    horizon: str             # immediate | near | far
    confidence: float        # Classification confidence

@dataclass
class StrategySelection:
    strategy: str            # quick_answer | decomposition | verification | exploration | dialogue
    reason: str
    escalation_level: int    # 0 = no escalation, 1-3 = levels
    fallback_strategy: Optional[str]

class ReasoningRouter:
    def classify(input: str, context: dict) -> InputClassification
    def select_strategy(classification: InputClassification) -> StrategySelection
    def should_escalate(current: StrategySelection, result: dict) -> bool
    def should_deescalate(current: StrategySelection, pattern_match: bool) -> bool
```

#### Integration Points

- **From Altitude HRM:** Receives current altitude level, friction score
- **From Focus HRM:** Receives current stance, active commitment
- **To Learning HRM:** Sends (signal, strategy, outcome) tuples for learning
- **From Learning HRM:** Receives pattern matches for de-escalation

---

### 2.4 Learning HRM (Pattern Memory)

**Location:** `the_assist/learning/` (TO BE BUILT)
**Status:** 0% implemented

#### Purpose
Learns from experience, stores patterns, grows and trims automatically.

#### Pattern Storage

```python
@dataclass
class Pattern:
    id: str
    pattern_type: str           # signal | routing | outcome | general
    input_signature: dict       # What triggered this pattern
    action_taken: str           # What was done
    outcome: str                # success | partial | failure
    confidence: float           # 0.0 - 1.0
    hit_count: int              # Times pattern matched successfully
    miss_count: int             # Times pattern matched but failed
    last_hit: datetime
    created_at: datetime
    source: str                 # which HRM created it

@dataclass
class SignalRoutingOutcome:
    """The core learning tuple."""
    signal: dict                # Input classification from Reasoning HRM
    routing: dict               # Strategy selected
    outcome: dict               # Result (success, user feedback, corrections)
    timestamp: datetime
```

#### Learning Cycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. CAPTURE                                                              │
│     • Session ends                                                       │
│     • Collect all signal→routing→outcome tuples                          │
│     • Collect all feedback (worked/didn't work)                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. ANALYZE                                                              │
│     • Group similar patterns                                             │
│     • Calculate hit rates per pattern                                    │
│     • Identify new patterns (repeated success)                           │
│     • Identify stale patterns (low recent hits)                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. UPDATE                                                               │
│     • Strengthen high-hit patterns (confidence += 0.1)                   │
│     • Weaken low-hit patterns (confidence -= 0.1)                        │
│     • Add new patterns (if repeated 3+ times)                            │
│     • Mark stale patterns for trimming                                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. TRIM                                                                 │
│     • Remove patterns with confidence < 0.3                              │
│     • Remove patterns not hit in 30 days                                 │
│     • Keep "protected" patterns (manually marked)                        │
│     • Log trimmed patterns for regret detection                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  5. GENERALIZE                                                           │
│     • Find similar patterns (semantic similarity)                        │
│     • Merge into abstract patterns                                       │
│     • Example: "timeboxing_coding" + "timeboxing_writing" →             │
│                "timeboxing_creative_work"                                │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Pattern Types

| Type | Source | Example |
|------|--------|---------|
| **Signal Pattern** | Input classification | "ambiguous + high-stakes = verification strategy" |
| **Routing Pattern** | Strategy selection | "this user prefers decomposition for planning" |
| **Outcome Pattern** | Feedback | "quick_answer for calendar = success" |
| **Behavioral Pattern** | User corrections | "timeboxing", "numbers_not_bullets" |
| **Coaching Pattern** | How AI should behave | "ask_impact", "challenge_alignment" |

#### Integration with Existing Memory

Extends `memory_v2.py` pattern codes:

```python
# Existing codes (from memory_v2.py)
PATTERN_CODES = {
    "timeboxing": "Uses timeboxing...",
    "exit_criteria": "Sets clear exit criteria...",
    # ...
}

# NEW: Reasoning patterns
REASONING_PATTERN_CODES = {
    "needs_decomp": "Complex problems need decomposition",
    "quick_answer_ok": "Simple questions, fast response",
    "verify_high_stakes": "High-stakes need verification",
}

# NEW: Learning patterns
LEARNING_PATTERN_CODES = {
    "escalate_uncertain": "Escalate when uncertain",
    "deescalate_familiar": "De-escalate when pattern matches",
    "protect_pattern": "Pattern marked as protected",
}
```

#### Proposed Data Structures

```python
class PatternStore:
    def add_pattern(pattern: Pattern) -> str
    def get_pattern(id: str) -> Optional[Pattern]
    def search(input_signature: dict) -> list[Pattern]
    def strengthen(id: str) -> None
    def weaken(id: str) -> None
    def trim_stale(days: int = 30) -> list[Pattern]
    def protect(id: str) -> None

class Generalizer:
    def find_similar(patterns: list[Pattern]) -> list[tuple[Pattern, Pattern]]
    def merge(p1: Pattern, p2: Pattern) -> Pattern
    def generalize_batch(patterns: list[Pattern]) -> list[Pattern]

class FeedbackLoop:
    def record_outcome(signal: dict, routing: dict, outcome: dict) -> None
    def analyze_session(session_data: dict) -> dict
    def get_patterns_for_signal(signal: dict) -> list[Pattern]
```

#### Cross-HRM Signal Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Altitude   │     │   Focus     │     │  Reasoning  │     │  Learning   │
│    HRM      │     │    HRM      │     │    HRM      │     │    HRM      │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │  altitude_level   │                   │                   │
       │  friction_score   │                   │                   │
       │───────────────────┼───────────────────>                   │
       │                   │                   │                   │
       │                   │  current_stance   │                   │
       │                   │  active_commitment│                   │
       │                   │───────────────────>                   │
       │                   │                   │                   │
       │                   │                   │ signal_routing    │
       │                   │                   │ outcome_tuple     │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ pattern_matches   │
       │                   │                   │<──────────────────│
       │                   │                   │                   │
       │                   │  gate_accuracy    │                   │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │  correction_rate  │                   │                   │
       │───────────────────────────────────────────────────────────>
```

---

## 3. Attention & Priority System

### 3.1 How Attention Works

Attention in DoPeJar is managed through multiple mechanisms:

#### Layer 1: Altitude (Scope)
- Determines WHAT level of abstraction to focus on
- L4 (identity) vs L1 (moment)
- Enforces "context before tactics"

#### Layer 2: Stance (Mode)
- Determines HOW to approach the current level
- Exploration vs Exploitation
- Accuracy vs Momentum

#### Layer 3: Commitment (Duration)
- Determines HOW LONG to maintain focus
- Lease-based with TTL
- Explicit renewal required

#### Layer 4: Lanes (Parallelism)
- Determines WHICH workstream has attention
- One active lane at a time
- Bookmarking for context preservation

### 3.2 Attention Flow

```
User Input
    │
    ▼
┌─────────────────────────┐
│ 1. ALTITUDE CHECK       │
│    What level?          │
│    L4/L3/L2/L1          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. STANCE CHECK         │
│    What mode?           │
│    Allowed actions?     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. COMMITMENT CHECK     │
│    Active commitment?   │
│    Turns remaining?     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. LANE CHECK           │
│    Active lane?         │
│    Switch needed?       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 5. EXECUTE              │
│    Within authorized    │
│    scope only           │
└─────────────────────────┘
```

### 3.3 Priority Resolution

When multiple signals compete:

| Priority | Signal | Behavior |
|----------|--------|----------|
| 1 | EMERGENCY | Immediately to sensemaking, all else paused |
| 2 | URGENCY | Execute first, align after |
| 3 | EMOTIONAL_OVERLOAD | Trigger evaluation gate |
| 4 | HIGH_STAKES | Verification before action |
| 5 | LANE_SWITCH | Save context, switch |
| 6 | NORMAL | Follow current stance rules |

---

## 4. Signal System

### 4.1 Signal Types

```python
class SignalType(Enum):
    NONE = "none"
    FORMAL_WORK = "formal_work"
    INTERRUPT = "interrupt"
    URGENCY = "urgency"
    COMPLETION = "completion"
    EMOTIONAL = "emotional"
```

### 4.2 Signal Detection

```python
class SignalDetector:
    PATTERNS = {
        SignalType.FORMAL_WORK: [
            "let's work on", "help me write", "i need to",
            "can you help me", "let's focus on"
        ],
        SignalType.INTERRUPT: [
            "actually", "wait", "hold on", "before that",
            "one thing", "quick question"
        ],
        SignalType.URGENCY: [
            "urgent", "asap", "emergency", "right now",
            "immediately", "critical"
        ],
        SignalType.COMPLETION: [
            "done", "finished", "complete", "wrap up",
            "that's it", "all set"
        ],
    }

    def detect(input: str, emotional_signals: dict) -> DetectedSignal:
        # 1. Check emotional signals first
        if emotional_signals.get("overwhelm") == "high":
            return DetectedSignal(SignalType.EMOTIONAL, 0.9)

        # 2. Pattern match
        for signal_type, patterns in PATTERNS.items():
            for pattern in patterns:
                if pattern in input.lower():
                    return DetectedSignal(signal_type, 0.8)

        return DetectedSignal(SignalType.NONE, 0.0)
```

### 4.3 Emotional Telemetry

```python
class EmotionalTelemetry:
    """Bounded emotional state tracking."""

    STATES = {
        "energy": ["depleted", "low", "neutral", "high", "elevated"],
        "focus": ["scattered", "distracted", "neutral", "focused", "locked"],
        "stress": ["calm", "mild", "moderate", "high", "overwhelmed"],
    }

    def process(signals: dict) -> TelemetryResponse:
        # Aggregate signals
        overwhelm = signals.get("stress") in ["high", "overwhelmed"]
        flow_state = signals.get("focus") in ["focused", "locked"]

        return TelemetryResponse(
            trigger_evaluation=overwhelm,
            recommend_defer=flow_state,
            escalation_risk=overwhelm and not flow_state
        )
```

---

## 5. Memory Architecture

> **NOTE:** This section superseded by **MEMORY_BUS_ARCHITECTURE.md** which implements
> the bus model with 4 compartments + write gate. See that document for full design.

### 5.0 Bus Model (Adopted)

Memory is a bus with 5 compartments:

| Compartment | Scope | Lifetime | Key Property |
|-------------|-------|----------|--------------|
| **Working Set** | Per-problem | Minutes-hours | Isolated, expires aggressively |
| **Shared Reference** | Cross-problem | Long-lived | Versioned, citable |
| **Episodic Trace** | Append-only | Long-lived | Never overwritten |
| **Semantic Synthesis** | Distilled | Long-lived | Evidence-linked |
| **Write Gate** | Policy | N/A | Signal-based routing |

**Multi-Problem Support:** YES - Working Sets are isolated per `problem_id`, preventing cross-contamination.

### 5.1 Current State (Fragmented)

| System | Location | Purpose |
|--------|----------|---------|
| memory.py (v1) | the_assist/core/ | Prose-based, 80% token waste |
| memory_v2.py | the_assist/core/ | Compressed, 60% savings |
| fast.py | locked_system/memory/ | Fast loop state |
| slow.py | locked_system/memory/ | Slow loop state |
| bridge.py | locked_system/memory/ | Cross-loop signals |
| consent.py | locked_system/memory/ | User consent |
| history.py | the_assist/hrm/ | Session history |

### 5.2 Proposed: Unified Memory Manager

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MEMORY MANAGER                                   │
│                         shared/memory/                                   │
│                                                                         │
│  Single access point for all HRMs                                       │
│  Enforces compressed format everywhere                                  │
│  Built-in tracing (trace_id on every operation)                         │
│  Optional locking for multi-process                                     │
│  Consent-aware (checks before persist)                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Three-Tier Storage

| Tier | Storage | Access Pattern | TTL | Examples |
|------|---------|----------------|-----|----------|
| **HOT** | In-memory | Every turn | Session | Current state, signals, active threads |
| **WARM** | Fast JSON | On demand | Days | Patterns, history, people, coaching |
| **COLD** | Archive | Rare | Weeks+ | Old conversations, checkpoints |

### 5.4 Namespace Segregation

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

  reasoning:
    - strategies   # Which strategies worked
    - escalations  # Escalation patterns
    - routing      # Routing decisions

  learning:
    - patterns     # Learned patterns (signal→routing→outcome)
    - feedback     # What worked / didn't work
    - generalizations  # Abstracted patterns

  shared:
    - north_stars  # Identity (L4) - all HRMs read
    - priorities   # Strategy (L3) - all HRMs read
    - people       # Relationship data - shared
```

### 5.5 Token-Efficient Format

```python
# PROSE (WASTEFUL):
"John is a work colleague who often blocks progress and needs coordination"

# COMPRESSED (EFFICIENT):
{"name": "john", "r": "wk", "t": ["bottleneck", "coord"], "n": 5}

# Token savings: ~70%
```

### 5.6 Memory API

```python
class MemoryManager:
    def read(namespace: str, key: str) -> dict
    def write(namespace: str, key: str, data: dict) -> str  # Returns trace_id
    def query(namespace: str, pattern: str) -> list[dict]
    def subscribe(namespace: str, callback: Callable) -> None

    # Consent-aware
    def write(self, namespace, key, data, trace_id=None):
        if not self._consent.can_persist(namespace):
            return self._hot_tier.write(namespace, key, data)
        return self._persist(namespace, key, data, trace_id)
```

---

## 6. Gate System

### 6.1 Gate Types

| Gate | Purpose | Transitions To | Allowed Writes |
|------|---------|----------------|----------------|
| **Framing** | Clarifying what matters | SENSEMAKING, DISCOVERY | Draft commitment, lock frame |
| **Commitment** | Deciding to move forward | EXECUTION | Activate commitment, log decisions |
| **Evaluation** | Assessing outcomes | EVALUATION, SENSEMAKING, EXECUTION | Renew/revise/expire commitment |
| **Emergency** | Escape hatch | SENSEMAKING | Log emergency, reset clock |

### 6.2 Gate Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FRAMING    │────>│ COMMITMENT  │────>│  EXECUTION  │
│   GATE      │     │    GATE     │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
      ▲                                        │
      │                                        │
      │             ┌─────────────┐            │
      └─────────────│ EVALUATION  │<───────────┘
                    │    GATE     │
                    └─────────────┘
```

### 6.3 Write Approval Gate

Special gate for filesystem writes:

```python
class WriteApprovalGate:
    """
    Requires explicit approval before any file write.

    Default: DENY ALL
    User must approve each write request.
    Consent can be stored for future similar writes.
    """

    def check(self, request: WriteRequest) -> GateDecision:
        # Check stored consent
        if self._consent.has_approval(request.path_pattern):
            return GateDecision.APPROVE

        # Prompt user
        return GateDecision.PROMPT_USER
```

---

## 7. Execution Pipeline

> **NOTE:** Agent orchestration details in **AGENT_ORCHESTRATION.md**
> Implements 4 modes: pipeline, parallel, voting, hierarchical

### 7.0 Agent Orchestration Summary

**Who spins up agents?**
- **Reasoning HRM** proposes agents (AgentBundleProposal)
- **Focus HRM** approves and executes (via AgentRuntime)

**4 Orchestration Modes:**
| Mode | Pattern | Use Case |
|------|---------|----------|
| Pipeline | A → B → C | Sequential refinement |
| Parallel | A + B + C → Aggregate | Multi-perspective |
| Voting | A + B + C → Consensus | High-stakes decisions |
| Hierarchical | Lead → Delegates → Synthesize | Complex decomposition |

### 7.1 Turn Execution Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              TURN START                                   │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  1. SLOW LOOP TICK                                                        │
│     • Check stance, gates                                                 │
│     • Process proposals from buffer                                       │
│     • Update commitment clock                                             │
│     • Determine allowed actions                                           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  2. FAST LOOP EXECUTE                                                     │
│     • Execute within authorized scope                                     │
│     • Continuous evaluation monitors                                      │
│     • Tool calls through PDP→PEP pipeline                                 │
│     • Agent outputs through firewall                                      │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  3. POST-TURN                                                             │
│     • Memory extraction (compressed format)                               │
│     • Feedback collection                                                 │
│     • Signal→routing→outcome capture for Learning HRM                     │
│     • Trace logging                                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Tool Execution Pipeline

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Tool Request │────>│     PDP       │────>│     PEP       │
│               │     │  (Decision)   │     │  (Execution)  │
└───────────────┘     └───────────────┘     └───────────────┘

PDP (Policy Decision Point):
- Evaluates request against rules
- Returns ALLOW | DENY | PROMPT

PEP (Policy Enforcement Point):
- Executes allowed requests
- Sandboxed connector execution
- Logs all actions
```

### 7.3 Agent Execution Pipeline

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Agent Invoke  │────>│    Agent      │────>│   Firewall    │
│               │     │   Runtime     │     │   (Output)    │
└───────────────┘     └───────────────┘     └───────────────┘

Agent Runtime:
- Loads agent definition
- Injects sandboxed context
- Runs agent logic

Firewall:
- Validates output packet
- Blocks unauthorized proposals
- Ensures agents can only propose, not decide
```

---

## 8. Data Flows

### 8.1 Input Processing Flow

```
User Input
    │
    ├──> Signal Detector ──> Gate Proposals
    │
    ├──> Altitude Detector ──> Level Validation
    │
    ├──> Emotional Telemetry ──> Escalation Signals
    │
    └──> Context Builder ──> Memory Read
```

### 8.2 Response Generation Flow

```
Authorized Scope
    │
    ├──> Strategy Selection (Reasoning HRM)
    │
    ├──> Pattern Lookup (Learning HRM)
    │
    ├──> Agent Selection (Focus HRM)
    │
    └──> Response Generation
           │
           ├──> Firewall Validation
           │
           └──> Response
```

### 8.3 Learning Flow (Post-Session)

```
Session End
    │
    ├──> Collect signal→routing→outcome tuples
    │
    ├──> Run retrospective analyzers
    │         ├── Altitude: corrections, friction
    │         ├── Focus: gate accuracy, stance flow
    │         ├── Reasoning: strategy effectiveness
    │         └── Learning: pattern hit/miss rates
    │
    ├──> Cross-HRM correlation
    │
    ├──> Pattern updates
    │         ├── Strengthen high-hit
    │         ├── Weaken low-hit
    │         ├── Add new patterns
    │         └── Trim stale patterns
    │
    └──> Generalization
```

---

## 9. Dependencies & Integration Order

### 9.1 Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FOUNDATION                                     │
│  • shared/memory/manager.py                                              │
│  • shared/tracing/tracer.py                                              │
│  • shared/feedback/logger.py                                             │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FOCUS HRM                                      │
│  • stance.py                                                             │
│  • gates.py                                                              │
│  • commitment.py                                                         │
│  • Depends on: Foundation                                                │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          ALTITUDE HRM                                    │
│  • altitude.py                                                           │
│  • loop.py                                                               │
│  • Depends on: Focus HRM (for gate validation)                           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         REASONING HRM                                    │
│  • router.py                                                             │
│  • strategies.py                                                         │
│  • Depends on: Altitude HRM (altitude context), Focus HRM (stance)       │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          LEARNING HRM                                    │
│  • patterns.py                                                           │
│  • feedback_loop.py                                                      │
│  • Depends on: All other HRMs (receives signals from all)                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Integration Order (Milestones)

| Milestone | Description | Components |
|-----------|-------------|------------|
| **M0.1** | Wire Altitude ↔ Focus | executor.py → gates.py, planner.py → validation |
| **M0.2** | Consolidation | Remove duplicates, create UI module, LLM adapter |
| **M0.3** | Reasoning HRM | router.py, strategies.py, escalation.py |
| **M0.4** | Learning HRM | patterns.py, trimmer.py, generalizer.py |
| **M1.0** | Unified Experience | Single entry point, all 4 HRMs working |

### 9.3 File Dependencies

```
the_assist/hrm/altitude.py
└── (standalone, no external deps)

the_assist/hrm/loop.py
├── the_assist/hrm/altitude.py
├── the_assist/hrm/planner.py
├── the_assist/hrm/evaluator.py
├── the_assist/hrm/executor.py
└── locked_system/slow_loop/gates.py (INTEGRATION NEEDED)

locked_system/slow_loop/gates.py
├── locked_system/slow_loop/stance.py
├── locked_system/slow_loop/commitment.py
├── locked_system/memory/slow.py
├── locked_system/memory/history.py
└── locked_system/proposals/buffer.py

locked_system/front_door/agent.py
├── locked_system/front_door/signals.py
├── locked_system/front_door/bundles.py
├── locked_system/front_door/emotional.py
└── locked_system/agents/__init__.py

the_assist/reasoning/router.py (TO BUILD)
├── the_assist/hrm/altitude.py
├── locked_system/slow_loop/stance.py
└── the_assist/learning/patterns.py

the_assist/learning/patterns.py (TO BUILD)
├── the_assist/core/memory_v2.py
├── shared/memory/manager.py
└── shared/feedback/logger.py
```

---

## 10. New Systems Design

### 10.1 Reasoning HRM Implementation

```python
# the_assist/reasoning/router.py

class ReasoningRouter:
    def __init__(self):
        self.classifier = InputClassifier()
        self.strategy_selector = StrategySelector()
        self.escalation_manager = EscalationManager()

    def route(self, input: str, context: HRMContext) -> RoutingDecision:
        # 1. Classify input
        classification = self.classifier.classify(input, context)

        # 2. Check for pattern match (from Learning HRM)
        pattern_match = self._check_patterns(classification)
        if pattern_match and pattern_match.confidence > 0.8:
            return RoutingDecision(
                strategy=pattern_match.action_taken,
                confidence=pattern_match.confidence,
                source="pattern_match"
            )

        # 3. Select strategy
        strategy = self.strategy_selector.select(classification)

        # 4. Check escalation
        if self.escalation_manager.should_escalate(classification, strategy):
            strategy = self.escalation_manager.escalate(strategy)

        return RoutingDecision(
            strategy=strategy.strategy,
            confidence=strategy.confidence,
            source="classifier"
        )
```

### 10.2 Learning HRM Implementation

```python
# the_assist/learning/patterns.py

class PatternStore:
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.namespace = "learning.patterns"

    def add_pattern(self, pattern: Pattern) -> str:
        # Compress pattern for storage
        compressed = self._compress(pattern)
        return self.memory.write(self.namespace, pattern.id, compressed)

    def search(self, input_signature: dict) -> list[Pattern]:
        # Query patterns matching signature
        results = self.memory.query(self.namespace, input_signature)
        return [self._decompress(r) for r in results]

    def strengthen(self, pattern_id: str) -> None:
        pattern = self.get_pattern(pattern_id)
        pattern.confidence = min(1.0, pattern.confidence + 0.1)
        pattern.hit_count += 1
        pattern.last_hit = datetime.now()
        self.memory.write(self.namespace, pattern_id, self._compress(pattern))

    def trim_stale(self, days: int = 30) -> list[Pattern]:
        cutoff = datetime.now() - timedelta(days=days)
        patterns = self._get_all_patterns()
        stale = [p for p in patterns if p.last_hit < cutoff and not p.protected]
        for p in stale:
            self.memory.delete(self.namespace, p.id)
        return stale
```

### 10.3 Feedback Loop Implementation

```python
# the_assist/learning/feedback_loop.py

class FeedbackLoop:
    def __init__(self, pattern_store: PatternStore):
        self.patterns = pattern_store
        self.buffer = []  # Accumulate session data

    def record_outcome(self, signal: dict, routing: dict, outcome: dict) -> None:
        self.buffer.append(SignalRoutingOutcome(
            signal=signal,
            routing=routing,
            outcome=outcome,
            timestamp=datetime.now()
        ))

    def analyze_session(self) -> dict:
        # Group by strategy
        by_strategy = defaultdict(list)
        for item in self.buffer:
            by_strategy[item.routing["strategy"]].append(item)

        # Calculate success rates
        analysis = {}
        for strategy, items in by_strategy.items():
            successes = len([i for i in items if i.outcome["status"] == "success"])
            analysis[strategy] = {
                "total": len(items),
                "success_rate": successes / len(items) if items else 0,
                "items": items
            }

        # Identify new patterns
        for strategy, data in analysis.items():
            if data["total"] >= 3 and data["success_rate"] > 0.7:
                self._create_pattern_from_strategy(strategy, data["items"])

        self.buffer = []  # Clear for next session
        return analysis
```

---

## 11. Security Model

### 11.1 Core Principles

1. **Default Deny**: All writes require explicit approval
2. **Proposal-Only Agents**: Agents propose, core decides
3. **Sandboxed Context**: Agent context cannot override core laws
4. **Consent-Aware**: User consent checked before persist

### 11.2 Authority Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CORE LAWS (Highest Authority)                                           │
│  • Cannot be overridden by agents or users                               │
│  • Compiled LAST in prompt (highest precedence)                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  GATE CONTROLLER (Sole Authority for State Changes)                      │
│  • Only authority for stance transitions                                 │
│  • Only authority for commitment changes                                 │
│  • Only authority for lane switches                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  AGENTS (Proposal Authority Only)                                        │
│  • Can propose gates                                                     │
│  • Can propose actions                                                   │
│  • Cannot execute without approval                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Prompt Compilation Order

```python
def compile_prompt(agent_context, executor_constraints, core_laws):
    """
    Order (last wins for conflicts):
    1. Agent context (style, domain) - SANDBOXED, can be overridden
    2. Executor constraints (altitude, stance) - Behavioral limits
    3. Core laws - ABSOLUTE, cannot be overridden
    """
    parts = [
        sandbox(agent_context),      # First (lowest priority)
        executor_constraints,        # Middle
        f"## CORE LAWS\n{core_laws}" # LAST (highest priority)
    ]
    return "\n\n".join(parts)
```

### 11.4 Capability Gating

```python
CAPABILITIES = {
    "note_capture": {
        "requires_delegation": True,
        "default_granted": False,
        "side_effects": ["file_write"],
    },
    "memory_write": {
        "requires_delegation": True,
        "default_granted": False,
        "side_effects": ["slow_memory"],
    },
}

class DelegationLease:
    id: str
    grantee: str              # Agent or capability ID
    scope: list[str]          # What's allowed
    expires_turns: int        # Auto-expire after N turns
    can_extend: bool = False
```

---

## 12. Token Efficiency

### 12.1 Current Savings

| Data Type | V1 Tokens | V2 Tokens | Savings |
|-----------|-----------|-----------|---------|
| Patterns | ~500 | ~200 | 60% |
| People | ~300 | ~90 | 70% |
| Active threads | ~400 | ~150 | 63% |
| Commits | ~200 | ~80 | 60% |

### 12.2 Compression Strategies

#### Code Expansion
```python
# Stored:
{"patterns": {"timeboxing": 0.9}}

# AI expands at inference:
"User uses timeboxing to prevent analysis paralysis (confidence: 0.9)"
```

#### Structured Schemas
```python
# Instead of prose:
"John is a work colleague who often blocks progress"

# Use schema:
{"name": "john", "r": "wk", "t": ["bottleneck"]}
```

#### Rolling Windows
```python
# Active threads: max 15
# Commits: max 10
# Session history: max 20
# Patterns: no limit but trimmed by confidence
```

### 12.3 Target Efficiency

| Data Type | Current | Target | Method |
|-----------|---------|--------|--------|
| Patterns | 60% savings | 70% | Extended codes |
| History | 40% savings | 65% | Summary-only |
| People | 50% savings | 75% | Relationship codes |
| Signals | No compression | 60% | Enum codes |
| Routing | N/A | 70% | Strategy codes |

**Overall target: 65% average token reduction**

---

## 13. Observability

### 13.1 Trace Event Structure

```python
@dataclass
class TraceEvent:
    trace_id: str              # Primary correlation ID
    parent_id: Optional[str]   # Parent trace (nested ops)
    timestamp: datetime
    hrm_layer: str             # altitude|focus|reasoning|learning
    operation: str             # read|write|transition|route
    component: str             # File/class that emitted
    input_summary: str         # Truncated input
    output_summary: str        # Truncated output
    duration_ms: int
    status: str                # success|error|blocked
    metadata: dict
```

### 13.2 Trace Points Per HRM

| HRM | Trace Points |
|-----|--------------|
| **Altitude** | transition, evaluate, plan, execute |
| **Focus** | stance_change, gate_check, lane_switch, consent_check |
| **Reasoning** | classify, route, escalate, deescalate |
| **Learning** | pattern_match, pattern_add, pattern_trim, generalize |
| **Memory** | read, write, promote, demote |

### 13.3 UI Integration

```bash
# Enable tracing
export DOPEJAR_TRACE=1

# Or via CLI
python -m the_assist.main --trace
```

Console output when enabled:
```
[alt] transition: L3→L2 → success (5ms)
  └─[foc] gate_check: WriteApproval → allowed (2ms)
      └─[mem] write: altitude.session → written (3ms)
```

---

## 14. Open Questions

### 14.1 Architecture Questions (RESOLVED)

1. **Memory Locking**: ✅ DECIDED: Implement from start (future-proofing)
2. **Pattern Generalization**: How aggressive should merging be? (TBD)
3. **Escalation Thresholds**: ✅ DECIDED: 0.6 confidence threshold
4. **Trim Policy**: ✅ DECIDED: No auto-trim, manual only (patterns persist)
5. **Naming**: ✅ DECIDED: Keep `locked_system` and `front_door` (no rename)

### 14.2 Integration Questions

1. **Altitude ↔ Focus**: Should altitude block before or after stance check?
2. **Reasoning ↔ Learning**: Real-time pattern lookup or batch update?
3. **Emergency Priority**: Does emergency override all gates or just stance?

### 14.3 Performance Questions

1. **Pattern Search**: Linear scan or index? At what scale does it matter?
2. **Memory Tiers**: When to promote/demote between tiers?
3. **Trace Overhead**: Acceptable latency for tracing? (<1ms target)

### 14.4 UX Questions

1. **Friction Threshold**: How many blocks before switching to permissive?
2. **Consent Fatigue**: How to reduce approval prompts without reducing safety?
3. **Orientation Display**: What context to show on resume?

---

## Appendix A: File Inventory

### Altitude HRM (the_assist/hrm/)

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| altitude.py | 510 | 95% | AltitudeGovernor, Level enum |
| loop.py | ~200 | 85% | HRM orchestration |
| planner.py | ~150 | 75% | Plan generation |
| evaluator.py | ~150 | 75% | Plan evaluation |
| executor.py | ~150 | 70% | Action execution |
| history.py | ~200 | 100% | Session history |

### Focus HRM (locked_system/)

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| slow_loop/stance.py | 169 | 90% | StanceMachine |
| slow_loop/gates.py | 318 | 90% | GateController |
| slow_loop/commitment.py | ~150 | 85% | CommitmentManager |
| front_door/agent.py | 220 | 85% | FrontDoorAgent |
| front_door/signals.py | ~150 | 85% | SignalDetector |
| lanes/store.py | ~200 | 85% | LaneStore |
| executor/gates.py | ~150 | 85% | WriteApprovalGate |

### Memory (the_assist/core/, locked_system/memory/)

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| memory_v2.py | 411 | 70% | Compressed memory |
| slow.py | ~150 | 80% | Slow loop state |
| fast.py | ~100 | 75% | Fast loop state |
| bridge.py | ~100 | 70% | Cross-loop signals |

### To Be Built

| File | Location | Purpose |
|------|----------|---------|
| router.py | the_assist/reasoning/ | Strategy selection |
| strategies.py | the_assist/reasoning/ | Strategy implementations |
| escalation.py | the_assist/reasoning/ | Escalation management |
| patterns.py | the_assist/learning/ | Pattern storage |
| feedback_loop.py | the_assist/learning/ | Learning cycle |
| generalizer.py | the_assist/learning/ | Pattern generalization |
| manager.py | shared/memory/ | Unified memory manager |
| tracer.py | shared/tracing/ | Observability |

---

## Appendix B: Pattern Code Reference

### Behavioral Patterns (memory_v2.py)

```python
PATTERN_CODES = {
    "timeboxing": "Uses timeboxing to prevent analysis paralysis",
    "exit_criteria": "Sets clear exit criteria (time OR outcome)",
    "buffer_planning": "Builds buffers into schedules",
    "risk_id": "Proactively identifies risks/bottlenecks",
    "schedule_underest": "Underestimates how packed schedule is",
    "calendar_desync": "Mental and actual calendar often desync",
    "struct_prefer": "Prefers structured breakdowns",
    "numbers_not_bullets": "Prefers numbers over bullets",
    "proactive_ok": "Open to being pushed/managed proactively",
    "fast_context_switch": "Fast context switching, high ADHD",
    "multi_project": "Multiple concurrent projects",
}
```

### Coaching Patterns (memory_v2.py)

```python
COACHING_CODES = {
    "ask_impact": "Ask how tasks connect to strategies and north stars",
    "surface_why": "Surface the 'why' behind tasks, not just status",
    "strategic_questions": "Ask bigger picture questions",
    "connect_layers": "Connect L2 tasks to L3 strategy to L4 identity",
    "challenge_alignment": "Challenge when tasks don't align",
    "spot_overload": "Proactively spot schedule overload",
    "suggest_drops": "Recommend what to drop, not just what to add",
    "match_altitude": "Match user's altitude (strategic vs tactical)",
    "push_harder": "User wants more direct pushback",
    "more_concise": "Be more concise, less explanation",
}
```

### Reasoning Patterns (TO BE ADDED)

```python
REASONING_PATTERN_CODES = {
    "needs_decomp": "Complex problems need decomposition",
    "quick_answer_ok": "Simple questions, fast response",
    "verify_high_stakes": "High-stakes need verification",
    "explore_uncertain": "High uncertainty needs exploration",
    "dialogue_conflict": "Conflict present needs resolution",
}
```

### Learning Patterns (TO BE ADDED)

```python
LEARNING_PATTERN_CODES = {
    "escalate_uncertain": "Escalate when uncertain",
    "deescalate_familiar": "De-escalate when pattern matches",
    "protect_pattern": "Pattern marked as protected",
    "trim_stale": "Pattern stale, low recent hits",
    "generalize_similar": "Similar patterns merged",
}
```

---

## Appendix C: Integration Test Scenarios

### Scenario 1: Full Turn Cycle

```
Input: "Help me plan my week"
Expected:
1. Altitude: Detect L2 request
2. Altitude: Check L3 established → if not, micro-anchor
3. Focus: Detect FORMAL_WORK signal
4. Focus: Propose WorkDeclarationGate
5. Focus: Transition to SENSEMAKING
6. Reasoning: Classify as moderate complexity
7. Reasoning: Select DECOMPOSITION strategy
8. Execute: Generate week plan
9. Learning: Record (signal, routing, outcome)
```

### Scenario 2: Emergency Override

```
Input: "STOP! Wrong project!"
Expected:
1. Altitude: Detect urgency patterns
2. Focus: Detect EMERGENCY signal
3. Focus: Trigger emergency gate
4. Focus: Force to SENSEMAKING
5. Focus: Reset commitment clock
6. Focus: Log emergency decision
7. Response: Immediate acknowledgment
```

### Scenario 3: Pattern Learning

```
Session 1: User asks for decomposition, success
Session 2: User asks for decomposition, success
Session 3: User asks for decomposition, success
Session End Analysis:
1. Learning: Detect repeated success
2. Learning: Create pattern "user_prefers_decomposition"
3. Learning: Confidence = 0.7
Next Session:
1. Similar input → pattern match → skip classifier
```

---

**End of Document**
