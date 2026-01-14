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
│  Perception ──→ Commitment ──→ Stance ──→ Gates         │
│  (sensor)       (what)         (how)      (transitions) │
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

## Perception & Contrast (Sensing Layer)

Perception and Contrast are first-class, non-authoritative sensing mechanisms that preserve experiential adaptation while remaining fully compliant with Locked System principles.

### Perception (Sensor, Not Agent)

Perception is explicitly defined as a **sensor**, not an agent.

**Purpose:**
- Assess interaction state as data, not as participant
- Provide structured situation awareness to Slow Loop
- Preserve Chinese-wall separation between observation and execution

**Perception does:**
- Observe ✓
- Analyze ✓
- Recommend ✓

**Perception cannot:**
- Decide ✗
- Write slow memory ✗
- Alter commitments ✗
- Trigger gates directly ✗
- Act on the Fast Loop ✗

**Perception Report** (proposal-only, one fresh-context call):

| Field | Description |
|-------|-------------|
| `elevation_level` | L1-L4 current operating level |
| `elevation_mismatch` | Is conversation at wrong level for topic? |
| `trajectory` | converging / drifting / stuck |
| `topic_saturation` | Topics being over-discussed |
| `sentiment` | User state, frustration signals, trust signals |
| `north_star_connection` | Alignment with declared user values |
| `recommended_stance` | support / challenge / redirect / elevate / ground |

All fields are observational or advisory only.

### Contrast (Experience Alignment Signal)

Contrast is a first-class evaluative artifact derived from Perception output.

**Purpose:**
- Make explicit the gap between inferred user need and observed assistant behavior
- Prevent silent degradation of experience quality
- Provide stable control surface for delivery adjustment

**Contrast Report** (derived from Perception, same call):

| Field | Description |
|-------|-------------|
| `inferred_user_need` | What the user appears to need |
| `observed_assistant_mode` | What the assistant is doing |
| `gap_type` | altitude / pacing / stance / verbosity / tangentiality |
| `severity` | low / medium / high |
| `confidence` | low / medium / high |
| `recommended_correction` | Bounded, non-authoritative suggestion |

**Contrast does not act. Contrast does not decide. Contrast does not mutate system state.**

### Flow: Perception → Slow Loop

```
Fast Loop interaction
        ↓
Perception (fresh context, no authority)
        ↓
Perception Report + Contrast Report
        ↓
Proposal Buffer
        ↓
Slow Loop (commitment / stance / gates)
        ↓
Bounded Fast Loop execution
```

Perception and Contrast Reports are routed to the Slow Loop through the existing Proposal Buffer.

The Slow Loop may:
- Accept or ignore recommendations
- Use them to validate stance
- Use them to evaluate GateProposals
- Use them to detect commitment drift
- Use them to bound Fast Loop delivery

No automatic transitions. Authority remains singular.

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

This architecture **replaces** the current `the_assist/hrm/` and `the_assist/core/` implementation:

| Current | Becomes |
|---------|---------|
| `intent.py` | Commitment Manager (add leases, expiry) |
| `planner.py` | Split: Stance Machine + approach in Fast Loop |
| `executor.py` | Absorbed into Fast Loop execution |
| `evaluator.py` | Split: Continuous Eval (fast) + Evaluation Stance (slow) |
| `altitude.py` | HRM depth control (subordinate to Slow Loop) |
| `history.py` | Part of Memory (Progress State + History) |
| `loop.py` | Rewrite to enforce two-loop model |
| `perception_agent.py` | Perception sensor (input to Slow Loop, produces Perception + Contrast Reports) |
| `hrm_agent.py` | Absorbed into Slow Loop decision logic |

---

## Bootstrap (First-Contact Protocol)

Bootstrap is the system's first-contact protocol. It establishes a consent-based social contract before any commitment forms.

### Bootstrap Intent

Bootstrap is designed to:
- Elicit user state with low cognitive load
- Establish collaboration posture (listen vs structure vs propose)
- Enable a single, bounded next step toward support
- Produce minimal, safe artifacts for continuity
- Defer North Stars and configuration until relationship contract is formed

Bootstrap is **not**: planning, optimization, scheduling, therapy, or commitment formation.

### Bootstrap Mode Constraints

When in Bootstrap Mode, the system is constrained to:
- **Summarize, don't solve** (default)
- **Propose-only** (no actions, no commitments)
- **Ask only bounded questions** (no multi-step interrogations)
- **Defer North Star acquisition** unless user explicitly requests structured support
- **Avoid coercive reassurance** (no minimization, no forced optimism)

Bootstrap exits only when user explicitly consents to:
- Receiving structure/ideas, or
- Establishing a scoped commitment/work order, or
- Starting configuration

### Bootstrap Interaction Flow (4 Stages)

**Stage 1 — Ladder Anchor (State)**

Cantril-style ladder to elicit coarse state signal.

> "Imagine a ladder where the top is the best possible life for you and the bottom is the worst. Where do you feel you're standing right now?"

Representation: Top / Middle / Bottom (coarse). Numeric (1-10) only if user provides it.

**Stage 2 — Anchor (Stability)**

Identify what is already working.

> "What's currently happening that keeps you from slipping lower?"

**Stage 3 — Gap (One-step change)**

Identify what "one step up" means in lived experience.

> "If you moved up just one step, what would be different in your day-to-day?"

**Stage 4 — Microstep + Permission (Handoff)**

Transition from listening into support, explicitly requesting permission.

> "What's one small thing that would make you feel supported moving toward that next step?"

Then:

> "Would you like me to keep listening, or would it help if I started offering structure and ideas?"

This last prompt is the canonical handoff switch from Bootstrap into normal operation.

### Identity-Affirming Hook (Optional)

A single, short identity-affirming statement after user has expressed ladder position and at least one supporting detail.

**Hook constraints (all must be satisfied):**
- Non-coercive: no obligation, guilt, or performance demand
- Non-permanent: no "you're always..."
- Non-comparative: no ranking against others
- Non-solutioning: no pivot into advice
- State-accurate: reflects user's expressed reality

### Bootstrap Artifacts

**1. Bootstrap Snapshot** (Slow Memory Candidate)

```json
{
  "bootstrap_timestamp": "...",
  "ladder_position": "top | middle | bottom",
  "user_state_summary": "one sentence, user-aligned",
  "stabilizers": "what keeps them from slipping",
  "one_step_gap": "what one step up means",
  "microstep_candidate": "user-named",
  "consent_state": "listen_only | propose_structure | ready_for_commitment",
  "derived_north_star_candidates": ["inferred, not ratified"],
  "delivery_fit_notes": "brevity preference, pacing signals"
}
```

Derived North Stars are recorded only as **candidates** until explicitly ratified.

**2. Bootstrap Transition Proposal** (Proposal Buffer)

Proposal routed to Slow Loop indicating recommended next transition:
- "Remain in listen-only"
- "Offer structure (propose-only)"
- "Offer to create a scoped Work Order"
- "Offer to formalize North Stars"

### Bootstrap Edge Cases (Resolved)

**Re-entry:** Bootstrap is primarily first-contact. However, if Perception detects severe state degradation (ladder position "bottom" + trust eroding), system may propose "Bootstrap Re-entry" via GateProposal. This pauses commitment and returns to listening mode without invalidating existing commitment.

**Timeout:** Bootstrap has no hard expiry. After 10 turns without transition, system gently re-offers the permission prompt. Soft nudge, not forced exit.

**Multi-session:** If session ends during Bootstrap, next session resumes from Bootstrap Snapshot. If `consent_state` was "listen_only", resume in Bootstrap. If "propose_structure", resume in propose-only mode.

**Existing users:** For users with existing North Stars and configuration, Bootstrap is abbreviated. System offers light check-in: "I have context from before. How are things today - still on track, or has something shifted?"

**Stage flow:** Stages can be fast-exited on explicit intent. If user says "I need help planning my week", system confirms intent briefly ("Got it - you want help with planning. Want me to dive in, or would you prefer I understand where you're at first?") and proceeds based on response. 4-stage sequence is default, not mandatory.

### North Stars Deferral Rule

Bootstrap does not request North Stars unless:
- User explicitly asks for planning/prioritization
- User grants permission for "structure and ideas"
- System is transitioning into a scoped Work Order requiring North Star anchoring

North Stars are always: explicit, consented, ratified, versioned.

---

## Resolved Implementation Answers

1. **Bootstrap:** See Bootstrap section above. 4-stage consent-based protocol with explicit handoff.

2. **Emergency cost:** Emergency Gate requires: (a) logging emergency decision with rationale, (b) full commitment clock reset, (c) mandatory return to Sensemaking stance, (d) cooldown period before next Emergency (3 turns minimum). This makes it costly enough to prevent casual use.

3. **Proposal merge:** Multiple proposals same turn are processed in priority order: (1) Emergency severity first, (2) then by source priority: user_signal > decay_manager > perception > continuous_eval > task_agent, (3) ties broken by timestamp (earlier wins). Slow Loop may accept multiple non-conflicting proposals.

---

*Fail fast, learn fast.*
