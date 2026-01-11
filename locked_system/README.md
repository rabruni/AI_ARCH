# Locked System

A two-loop cognitive architecture for AI agents that manages commitment over time, preventing agents from solving the wrong problem well, thinking forever without delivering, or behaving like task managers instead of partners.

## Quick Start

```python
from locked_system import LockedLoop, Config

# Create loop with default config
loop = LockedLoop(Config())

# Process user input
result = loop.process("Hello, I need help organizing my week")
print(result.response)
print(f"Stance: {result.stance}, Altitude: {result.altitude}")
```

Or via CLI:
```bash
# Interactive mode
python -m locked_system.main

# Single message
python -m locked_system.main -m "Hello" --json
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  SLOW LOOP (Authority)                                  │
│  Controls WHAT problem to solve and HOW to behave       │
│                                                         │
│  Perception ──→ Commitment ──→ Stance ──→ Gates         │
└───────────────────────────┬─────────────────────────────┘
                            │ bounds
                            ▼
┌─────────────────────────────────────────────────────────┐
│  FAST LOOP (Execution)                                  │
│  Controls HOW DEEPLY to reason within bounds            │
│                                                         │
│  HRM (depth) ──→ Execute ──→ Continuous Evaluation      │
└───────────────────────────┬─────────────────────────────┘
                            │ writes
                            ▼
┌─────────────────────────────────────────────────────────┐
│  MEMORY (Durable State)                                 │
│  Slow: gate-only | Fast: continuous | Bridge: artifacts │
└─────────────────────────────────────────────────────────┘
```

## Core Concepts

### Four Stances (Mutually Exclusive)

|                | Accuracy      | Momentum    |
|----------------|---------------|-------------|
| **Exploration**| Sensemaking   | Discovery   |
| **Exploitation**| Evaluation   | Execution   |

Only one stance is active at a time. Each defines acceptable behaviors.

### Three Gates (+ Emergency)

| Gate | Purpose | Transition |
|------|---------|------------|
| **Framing** | Clarify what matters | → Sensemaking or Discovery |
| **Commitment** | Decide to move forward | → Execution |
| **Evaluation** | Assess outcomes | → Sensemaking or Execution |
| **Emergency** | Escape hatch (costly) | Any → Sensemaking |

### Commitment Leases

Commitments expire unless renewed. This prevents stale goals from persisting.

```python
loop.create_commitment(
    frame="Help user organize their week",
    success_criteria=["Weekly plan created", "User confirms it works"],
    non_goals=["Long-term life planning", "Deep philosophical discussion"],
    turns=20  # Expires in 20 turns unless renewed
)
```

### HRM Altitudes (Response Depth)

| Altitude | Style | Use When |
|----------|-------|----------|
| L1 | Brief acknowledgment | Simple confirmations |
| L2 | Direct, efficient | Clear requests |
| L3 | Thoughtful, balanced | Normal conversation |
| L4 | Exploratory, nuanced | Complex topics |
| L5 | Synthesis, comprehensive | Deep exploration |

## Package Structure

```
locked_system/
├── __init__.py           # Exports: LockedLoop, Config
├── config.py             # Configuration with defaults
├── loop.py               # Main orchestration (LockedLoop class)
├── main.py               # CLI entry point
│
├── slow_loop/            # Authority layer
│   ├── stance.py         # StanceMachine - 4 exclusive stances
│   ├── commitment.py     # CommitmentManager - lease-based commitments
│   ├── gates.py          # GateController - transition authority
│   └── bootstrap.py      # Bootstrap - first-contact protocol
│
├── fast_loop/            # Execution layer
│   ├── hrm.py            # HRM - depth controller (L1-L5)
│   ├── executor.py       # Executor - response generation
│   └── continuous_eval.py # ContinuousEvaluator - quality (non-authoritative)
│
├── sensing/              # Perception layer
│   ├── perception.py     # PerceptionSensor - user state detection
│   └── contrast.py       # ContrastDetector - gap detection
│
├── memory/               # Durable state
│   ├── slow.py           # SlowMemory - authoritative, gate-only writes
│   ├── fast.py           # FastMemory - continuous, decays
│   ├── bridge.py         # BridgeMemory - artifact index
│   └── history.py        # History - audit trail
│
└── proposals/
    └── buffer.py         # ProposalBuffer - central routing
```

## Configuration Reference

```python
from locked_system import Config

config = Config(
    # Model settings
    model="claude-sonnet-4-20250514",          # Main response model
    perception_model="claude-sonnet-4-20250514", # Perception sensor model
    max_tokens=2000,                           # Max response tokens

    # Memory paths
    memory_dir="./memory",                     # Base directory for all memory files

    # Bootstrap settings
    bootstrap_soft_timeout_turns=10,           # Turns before re-offering handoff

    # Emergency gate settings
    emergency_cooldown_turns=3,                # Minimum turns between emergencies

    # Proposal processing priority (first = highest)
    proposal_priority_order=[
        "user_signal",      # Explicit user requests
        "decay_manager",    # Commitment expiry
        "perception",       # User state signals
        "continuous_eval",  # Quality concerns
        "task_agent"        # Child task proposals
    ],

    # Commitment defaults
    default_lease_turns=20,                    # Default commitment duration
)
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API key for Claude models |

## Integration Guide

### Connecting an LLM

The default executor uses a placeholder. To connect a real LLM:

```python
from anthropic import Anthropic
from locked_system import LockedLoop, Config

client = Anthropic()

def call_claude(prompt: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

loop = LockedLoop(Config(), llm_callable=call_claude)
```

### Creating Commitments

```python
# Must be in Sensemaking or Discovery stance
if loop.create_commitment(
    frame="Help user debug their Python script",
    success_criteria=["Bug identified", "Fix implemented", "User confirms working"],
    non_goals=["Rewriting entire codebase", "Adding new features"],
    turns=15
):
    print("Commitment created")
else:
    print("Cannot create commitment in current stance")
```

### Triggering Gates Manually

```python
# Request evaluation
loop.request_evaluation("User asked to review progress")

# Emergency (costly - use sparingly)
loop.trigger_emergency("User said 'stop, this is all wrong'")
```

### Inspecting State

```python
state = loop.get_state()
print(f"Turn: {state['turn']}")
print(f"Stance: {state['stance']}")
print(f"Commitment: {state['commitment']}")
print(f"Health: {state['health']}")
```

## File-by-File Reference

### slow_loop/stance.py

**Purpose:** Manages the 4-stance state machine.

**Key Classes:**
- `Stance` (Enum): SENSEMAKING, DISCOVERY, EXECUTION, EVALUATION
- `StanceMachine`: Enforces valid transitions, tracks history

**Key Methods:**
- `can_transition(to_stance, gate)` - Check if transition is valid
- `transition(to_stance, gate, reason)` - Attempt transition
- `get_behavioral_constraints()` - Get allowed/suppressed behaviors for current stance

### slow_loop/commitment.py

**Purpose:** Manages lease-based commitments with expiry.

**Key Classes:**
- `CommitmentManager`: Create, renew, expire commitments

**Key Methods:**
- `create(frame, success_criteria, non_goals, turns)` - Create new commitment
- `renew(turns)` - Extend commitment lease
- `check_expiry()` - Returns GateProposal if expired
- `decrement_turn()` - Called each turn to tick down lease

### slow_loop/gates.py

**Purpose:** Controls gate transitions with authority.

**Key Classes:**
- `GateController`: Process proposals, execute transitions
- `GateResult`: Success/failure with actions taken

**Key Methods:**
- `attempt_gate(gate, reason)` - Try framing/commitment/evaluation gate
- `attempt_emergency(reason)` - Try emergency gate (has cooldown)
- `process_proposals(buffer, priority_order)` - Batch process proposals

### slow_loop/bootstrap.py

**Purpose:** 4-stage first-contact protocol for new users.

**Stages:**
1. Ladder (state assessment)
2. Anchor (what's working)
3. Gap (one step up)
4. Microstep + Permission (handoff)

**Key Methods:**
- `process_input(user_input)` - Process bootstrap stage
- `is_active` - Check if still in bootstrap
- `complete_with_consent(consent)` - Exit bootstrap

### fast_loop/hrm.py

**Purpose:** Horizon/Risk/Moment depth controller.

**Key Classes:**
- `Altitude` (Enum): L1_ACKNOWLEDGE through L5_SYNTHESIS
- `HRM`: Assesses appropriate response depth
- `HRMAssessment`: Recommended altitude with rationale

**Assessment Dimensions:**
- Horizon: Time-based importance (0-1)
- Risk: Potential for harm/misalignment (0-1)
- Moment: Immediate user state needs (0-1)

### fast_loop/executor.py

**Purpose:** Generate responses within constraints.

**Key Classes:**
- `Executor`: Response generation
- `ExecutionContext`: Input bundle (stance, commitment, HRM assessment)
- `ExecutionResult`: Response with metadata

**Constraints Applied:**
- Altitude-based length/style
- Stance-based behavioral emphasis
- Commitment-based non-goals

### fast_loop/continuous_eval.py

**Purpose:** Non-authoritative quality assessment.

**Key Classes:**
- `ContinuousEvaluator`: Assess response quality
- `QualitySignal`: Individual quality dimension score
- `ContinuousEvalResult`: Overall health + proposals

**Dimensions Evaluated:**
- Response coherence
- Commitment alignment
- Progress trajectory
- User engagement

**Important:** Can only PROPOSE gate transitions, never execute them.

### sensing/perception.py

**Purpose:** Detect user state from input.

**Key Classes:**
- `PerceptionSensor`: User state detection
- `PerceptionContext`: Input bundle
- `PerceptionReport`: Structured observations

**Detects:**
- Emotional state (anxious, frustrated, calm, etc.)
- Urgency (low, medium, high)
- Intent (seeking_information, requesting_action, etc.)
- Context cues (verbose_input, repetition_detected, etc.)

### sensing/contrast.py

**Purpose:** Detect gaps between user need and assistant behavior.

**Key Classes:**
- `ContrastDetector`: Gap detection
- `ContrastContext`: Input bundle
- `ContrastReport`: Gap description with severity

**Gap Types:**
- Stance-intent alignment
- Emotional response appropriateness
- Urgency handling
- Commitment alignment

### memory/slow.py

**Purpose:** Authoritative memory, gate-written only.

**Key Classes:**
- `SlowMemory`: Persistence manager
- `CommitmentLease`: Active commitment with expiry
- `Decision`: Logged decision with rationale
- `BootstrapSnapshot`: Bootstrap state

**Invariant:** Only written at gates. Never continuous writes.

### memory/fast.py

**Purpose:** Non-authoritative memory, continuous writes, decays.

**Key Classes:**
- `FastMemory`: Progress and interaction tracking
- `ProgressState`: Current stage, next actions, blockers
- `InteractionSignals`: Preferences, friction, patterns

**Invariant:** Cannot override slow memory authority.

### memory/bridge.py

**Purpose:** Artifact index (pointers, not content).

**Key Classes:**
- `BridgeMemory`: Artifact registration
- `Artifact`: Name, type, pointer, status

**Status Lifecycle:** draft → review → final → deprecated

### memory/history.py

**Purpose:** Non-authoritative audit trail.

**Key Classes:**
- `History`: Session and gate transition logging
- `SessionRecord`: Session summary
- `GateTransition`: Transition record

**Important:** Audit only. Cannot become source of truth.

### proposals/buffer.py

**Purpose:** Central routing for all proposals.

**Key Classes:**
- `ProposalBuffer`: Append-only buffer
- `GateProposal`: Request gate transition
- `PerceptionReport`: Perception observations
- `ContrastReport`: Gap analysis

**Lifecycle:**
1. Components append proposals
2. Slow Loop reads at: gateway pass, end of turn, explicit request
3. Gate Controller accepts/rejects
4. Buffer cleared after read

## Key Invariants

1. **One stance at a time** - No modal confusion
2. **Commitments expire** - Prevents stale goals
3. **Evaluators propose only** - Authority stays with Gate Controller
4. **Slow memory = gates only** - No continuous authority writes
5. **Emergency is costly** - Cooldown prevents abuse
6. **HRM cannot override framing** - Depth control ≠ authority

## Canonical Design Document

For full architectural rationale, see: `the_assist/docs/LOCKED_SYSTEM.md`

This includes:
- Complete stance state machine diagram
- Gate write policies
- Memory decay rules
- Multi-agent model
- Bootstrap protocol details
- Perception & Contrast specification
