# Locked System Architecture (Canon)

> **Purpose:** Manage commitment over time so the agent doesn't solve the wrong problem well, doesn't think forever and never deliver, maintains coherence across horizons, and behaves like a trusted partner.

---

## Core Insight

Reasoning depth, problem framing, and time horizon are distinct control problems and should not be governed by a single loop.

- **HRM** governs how deeply to reason
- **Commitment** governs whether and how long to execute
- **Stance** governs what "good behavior" means right now

Failure happens when execution continues after framing should have changed.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  SLOW LOOP (Authority)                                  │
│                                                         │
│  Commitment Lease ──→ Stance ──→ Gate Evaluation        │
│  (one active)        (exclusive)   (authority changes)  │
│                                                         │
│  Emergency Evaluation Gate (escape hatch - costly)      │
└───────────────────────────┬─────────────────────────────┘
                            │ bounds
                            ▼
┌─────────────────────────────────────────────────────────┐
│  FAST LOOP (Execution)                                  │
│                                                         │
│  HRM (depth) ──→ Execute ──→ Continuous Evaluation      │
│                              (quality only, no authority)│
└───────────────────────────┬─────────────────────────────┘
                            │ writes (gate-triggered for slow,
                            │         continuous for fast)
                            ▼
┌─────────────────────────────────────────────────────────┐
│  MEMORY (Durable State)                                 │
│                                                         │
│  Slow: Commitment Lease, Decision Log, Principles       │
│  Fast: Progress State, Interaction Signals              │
│  Bridge: Artifact Index (index only, not content)       │
│                                                         │
│  Never initiates. Decays. Slow is gate-written only.    │
└─────────────────────────────────────────────────────────┘
```

---

## Four Components

### 1. Commitment Loop (Slow Loop / Authority)

- Decides what problem is legitimate to solve
- Sets time-horizon authority (short / mid / long)
- Uses leases (commitments expire unless renewed)
- Changes rarely and intentionally
- Governs **whether** we should be solving something

### 2. Normative Stance (Exclusive, Gated)

Exactly one stance is active at a time:

|                | Accuracy      | Momentum    |
|----------------|---------------|-------------|
| **Exploration**| Sensemaking   | Discovery   |
| **Exploitation**| Evaluation   | Execution   |

Stance defines:
- What "good behavior" means
- Acceptable tradeoffs
- What is suppressed vs allowed

Governs **how** we should behave right now.

### 3. HRM (Fast Loop / Procedural Control)

- Controls reasoning depth (ascent/descent)
- Operates within commitment + stance
- Cannot override either
- Governs **how deeply** we reason before acting

### 4. Memory (Durable State, Not Decision-Maker)

Stores only gated, durable facts:
- Commitment leases
- Decision rationale ("why")
- Artifact index
- Progress state

Memory:
- Stabilizes past choices
- Prevents relitigation
- Never initiates change
- Preserves coherence across time

---

## Invariant Flow

```
1. Check commitment (valid? expired? horizon?)
2. Select stance (one only)
3. Run HRM (within bounds)
4. Execute
5. Evaluate → renew / revise / release
```

No step can be skipped.
No component can override upstream authority.

---

## The Hard Lines (Non-Negotiable)

1. One active commitment at a time
2. One dominant stance at a time
3. Commitment must expire unless renewed
4. Inference before inquiry
5. Slow memory writes only at gates
6. HRM never decides framing or horizons
7. **Evaluators and classifiers propose only. Never decide.**

---

## Stance State Machine

```
                    ┌──────────────┐
        ┌──────────▶│ Sensemaking  │◀─────────────────┐
        │           └──────┬───────┘                  │
        │                  │                          │
        │                  ▼                          │
        │           ┌──────────────┐                  │
        │           │  Discovery   │                  │
        │           └──────┬───────┘                  │
        │                  │                          │
        │    Framing Gate  │  Commitment Gate         │
        │                  ▼                          │
        │           ┌──────────────┐                  │
        │           │  Execution   │                  │
        │           └──────┬───────┘                  │
        │                  │                          │
        │                  │ Evaluation Gate          │
        │                  ▼                          │
        │           ┌──────────────┐                  │
        └───────────│  Evaluation  │──────────────────┘
         Framing    └──────────────┘    Framing Gate
          Gate             │            (renew/revise)
                           │
                           │ Emergency Gate
                           ▼
                    (any state → Sensemaking)

CONSTRAINT: Execution → Discovery requires Framing Gate (or Emergency).
            No direct transition. Prevents churn.
```

---

## Three Gates

### Gate 1 — Framing Gate
**When:** Clarifying "what matters" or "what problem is real"

**Allowed writes:**
- Draft/renew Commitment Lease
- Add Decision only if it locks frame

**Disallowed:**
- Detailed progress tracking
- Artifact finalization

### Gate 2 — Commitment Gate
**When:** Deciding to move forward under chosen frame

**Allowed writes:**
- Activate/renew Commitment Lease
- Log binding decisions
- Initialize Progress State

**Disallowed:**
- Frame churn (unless lease invalid/expired)
- Endless exploration

### Gate 3 — Evaluation Gate
**When:** Assessing outcomes, deciding renew/revise/release

**Allowed writes:**
- Renew/revise/expire Commitment Lease
- Append Decision supersessions
- Update artifact status
- Reset progress state

**This gate is the only clean place to change direction without thrash.**

### Emergency Evaluation Gate
**Triggers:**
- Explicit user override ("stop / wrong / abort / reset")
- Confidence collapse + high stakes indication
- Repeated drift (2-3 turns) + user frustration

**Effects:**
- Bypasses cadence
- Invalidates current lease
- Forces stance → Sensemaking
- Logs emergency decision
- Resets commitment clock

**Cannot be used silently or repeatedly.**

---

## GateProposal (Formalized)

```python
@dataclass
class GateProposal:
    reason: str              # Why this gate is proposed
    severity: str            # low / medium / high / emergency
    suggested_gate: str      # framing / commitment / evaluation
    source: str              # continuous_eval / task_agent / decay_manager / user_signal
    timestamp: datetime
```

**Lifecycle:**
1. Continuous Evaluator (or task agent, or decay manager) creates GateProposal
2. Appended to Proposal Buffer
3. Slow Loop reads buffer at: gateway pass, end of turn, explicit request
4. Gate Controller accepts or rejects
5. Buffer cleared after read
6. **Only Gate Controller has authority to act**

---

## Memory Objects

### Slow Memory (Authoritative, Gate-Written Only)

**Commitment Lease**
```json
{
  "frame": "problem definition we are committed to",
  "horizon_authority": "short | mid | long",
  "success_criteria": ["1-3 bullets"],
  "non_goals": ["1-3 bullets"],
  "lease_expiry": "time | milestone | signal",
  "renewal_prompt": "one sentence to re-confirm"
}
```

**Decision Log** (append-only)
```json
{
  "decision": "what we chose",
  "rationale": ["1-3 bullets"],
  "tradeoffs": "what we knowingly gave up",
  "confidence": "low | med | high",
  "revisit_triggers": ["what would cause re-evaluation"],
  "timestamp": "when decided",
  "supersedes": "previous decision id if any"
}
```

**Principles** (rare changes, Evaluation Gate only)
- Non-negotiables
- Review cadence norms
- Global constraints

### Fast Memory (Non-Authoritative, Continuous, Decays)

**Progress State**
```json
{
  "current_stage": "where we are",
  "next_actions": ["1-5 items max"],
  "blockers": ["0-3 items"],
  "recent_wins": ["last 1-3 completed"],
  "staleness_clock": "when to reconsider"
}
```

**Interaction Signals**
```json
{
  "user_preferences": ["brevity", "structure", "no code"],
  "friction_signals": ["overwhelm", "impatience"],
  "effective_patterns": ["what worked"],
  "avoidances": ["what harms flow"]
}
```

### Bridge Memory (Registered Agents, Index Only)

**Artifact Index** (index only, not content)
```json
{
  "name": "artifact name",
  "type": "doc | spec | code | deck",
  "pointer": "path | link | id",
  "status": "draft | review | final | deprecated",
  "version": "latest",
  "owner": "agent or human",
  "dependencies": ["optional"]
}
```

### History (Non-Authoritative, Audit Only)

- `sessions.json` - session summaries
- `gates.json` - gate transition log

**Non-authoritative. Used for summarization/audit only. Cannot become source of truth.**

---

## Write Policy

| Memory Tier | Write Authority | When | Constraint |
|-------------|-----------------|------|------------|
| Slow | Gate Controller only | At gates | Authoritative. No continuous writes. |
| Fast | Fast Loop | Continuous | Non-authoritative. Decays. Cannot override slow. |
| Bridge | Registered agents | On artifact create/update | Index only, not content. Status-based decay. |
| History | System | Session end, gate transition | Non-authoritative. Audit only. |

---

## Read Policy (Inference Before Inquiry)

Before asking user for context, agent must consult in order:
1. Commitment Lease
2. Relevant Decisions
3. Artifact Index
4. Progress State
5. Interaction Signals (to shape delivery only)

Then respond with:
- Provisional understanding
- Confirmation question (not brain-dump request)

---

## Decay Rules (Anti-Creep)

| Object | Decay Mechanism |
|--------|-----------------|
| Commitment Lease | Expires unless renewed. Expiry emits `GateProposal(evaluation, high)` |
| Progress State | Staleness clock. Marked stale, not deleted. |
| Artifact Index | Status decay: current → stale → review-needed |
| Decisions | Never deleted. Superseded by new decisions. |
| Principles | Rare. Only at Evaluation Gate. |

---

## Multi-Agent Model

```
┌─────────────────────────────────────────┐
│           PRIMARY AGENT                  │
│                                          │
│  Owns: Commitment, Stance, Gates         │
│  Runs: Slow Loop + Fast Loop             │
│  Reads: Proposal Buffer                  │
└──────────────────┬──────────────────────┘
                   │ spawns / delegates
                   ▼
┌─────────────────────────────────────────┐
│      SCOPED WORK ORDERS (child tasks)    │
│                                          │
│  Inherit: Scope from active commitment   │
│  Can: Execute within scope               │
│  Can: Write artifacts (registered)       │
│  Can: Emit GateProposal (async)          │
│  Cannot: Alter commitment                │
│  Cannot: Change stance                   │
│  Cannot: Write slow memory               │
└─────────────────────────────────────────┘

Proposals append to Proposal Buffer.
Primary reads at: gateway pass, end of turn, explicit request.

Pattern name: "Scoped Work Order"
Do not invent "multiple commitments" - use this pattern instead.
```

---

## Continuous Evaluation Boundaries

**CAN do:**
- Detect plan drift
- Detect user friction
- Detect confusion
- Flag execution quality issues
- Emit GateProposal

**CANNOT do:**
- Change commitment
- Change stance
- Write slow memory
- Accept/reject proposals
- Trigger gates (only propose)

---

## What This System Is Good At

- Strategy
- Architecture
- Long-horizon work
- High-trust partnership
- Avoiding drift, thrash, and over-asking

## What It Is Not

- A throughput engine
- A microtask bot
- A reactive chatbot

---

## Relationship to Current HRM

This architecture **replaces** the current `the_assist/hrm/` implementation:

| Current | Becomes |
|---------|---------|
| `intent.py` | Commitment Manager (add leases, expiry) |
| `planner.py` | Split: Stance Machine + approach in Fast Loop |
| `executor.py` | Absorbed into Fast Loop execution |
| `evaluator.py` | Split: Continuous Eval (fast) + Evaluation Stance (slow) |
| `altitude.py` | HRM depth control (subordinate to Slow Loop) |
| `history.py` | Part of Memory (Progress State + History) |
| `loop.py` | Rewrite to enforce two-loop model |

---

## Open Implementation Questions

1. **Bootstrap:** First message, no commitment exists. Sequence?
2. **Emergency cost:** What specifically makes it costly beyond clock reset?
3. **Proposal merge:** Two proposals same turn. Resolution order?

These are implementation-time decisions. Invariants are the guardrails.

---

*Fail fast, learn fast.*
