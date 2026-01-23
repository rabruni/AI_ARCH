# HRM Stacking Guide (DoPeJar + locked_system + Shaper)

## Purpose

This document defines how to **stack** (not merge) three distinct constructs:

1. **DoPeJar HRM Altitude** (meaning/abstraction: Identity → Strategy → Operations → Moment)
2. **locked_system Two-Loop Governance** (attention authority: Commitment + Stance + Gates)
3. **Shaper / Control Plane** (artifact-first shaping + deterministic validation and execution)

The goal is to preserve the purpose of each system while enabling a clean handoff from
conversation → contract → audited execution.

---

## Definitions (Non-Overlapping)

### A) Meaning Altitude (DoPeJar)

**What it controls:** *Level of abstraction of the conversation.*

- L4: Identity (north stars, values, “why”)
- L3: Strategy (projects, priorities, “what matters”)
- L2: Operations (commitments, plans, “what this week”)
- L1: Moment (current exchange, “right now”)

**Primary function:** Prevent tactical drift by requiring connection to higher context.

### B) Attention Authority (locked_system)

**What it controls:** *Whether to keep working on the current focus and how to behave.*

- Slow loop: Commitment lease + stance + gate transitions (authority)
- Fast loop: execution delivery (bounded)

**Primary function:** Prevent rabbit holes and stale goals through leases and gated stance.

### C) Artifact Commitment (Shaper / Control Plane)

**What it controls:** *What becomes executable and auditable.*

- Shaper produces artifacts (L3 `WORK_ITEM.md`, L4 `SPEC.md`)
- Control Plane gates validate artifacts and route failures deterministically
- `08_commit.md` (G0) defines EXPLORE vs COMMIT at the execution boundary

**Primary function:** Convert intent into deterministic contracts and stop accidental execution.

---

## Key Rule: Do Not Conflate “Altitude”

Two different “altitudes” exist in prior systems:

- DoPeJar meaning altitude (Identity/Strategy/Operations/Moment)
- locked_system HRM response depth (Acknowledgement → Synthesis)

For Control Plane integration, only the DoPeJar meaning altitude is relevant for routing
into Shaper L3 vs L4. Avoid naming collisions by using:

- `meaning_altitude` (DoPeJar)
- `response_depth` (locked_system HRM, optional)
- `artifact_altitude` (Shaper: L3=WORK_ITEM, L4=SPEC)

---

## Stacking Model (Who Owns What)

### 1) DoPeJar owns: Orientation and meaning

Responsibilities:
- Maintain north stars, long-horizon initiatives, and context continuity
- Detect drift and misalignment against identity/strategy
- Normalize interruptions: park/resume without demanding closure

Outputs:
- Proposals and notes, not executable plans

### 2) locked_system owns: Attention control and pacing

Responsibilities:
- Enforce stance and commitment leases (pause/renew/expire)
- Gate transitions (sensemaking/discovery/execution/evaluation) as authority controls
- Provide visibility signals (alignment drift, trust, progress) as diagnostics

Outputs:
- “Continue / pause / reframe” guidance
- Constraints for how to behave, not artifacts

### 3) Shaper/Control Plane owns: Contract formation and execution governance

Responsibilities:
- Convert a chosen slice into a bounded artifact (WORK_ITEM or SPEC)
- Require explicit reveal/confirm/freeze gates in shaping
- Require explicit commit boundary (G0 / `08_commit.md`) before execution

Outputs:
- Deterministic artifacts + deterministic gate results + auditable logs

---

## Canonical Flow (Conversation → Contract → Execution)

### Step 0: Conversational work (DoPeJar + locked_system)

Outcome: Identify a candidate that is worth turning into work.

### Step 1: Candidate selection (Human)

Human chooses one candidate to formalize (prevents “assistant decides what to ship”).

### Step 2: Shaping (Shaper, untrusted zone)

Shaper turns the candidate into one artifact:
- L3 → `WORK_ITEM.md` (implementation contract)
- L4 → `SPEC.md` (design/spec contract)

Shaper must require reveal-before-freeze and must not execute.

### Step 3: Commit boundary (Control Plane G0)

Human authorizes execution by creating/updating `08_commit.md` (MODE=COMMIT).

### Step 4: Flow runner + gates (Control Plane, trusted zone)

Deterministic validation and routing based on gate categories.

---

## How Stacking Works in Practice (Control Signals)

### A) From DoPeJar → Shaper (handoff content)

DoPeJar should emit a **candidate brief** (text-only) that Shaper can ingest:

- Objective (1–2 lines)
- Why it matters (north star link)
- Suggested `artifact_altitude` (L3 vs L4)
- Scope hints (optional)
- Acceptance intent (what “done” looks like)

DoPeJar must not create `08_commit.md` or mark MODE=COMMIT.

### B) From locked_system → DoPeJar (attention governance)

locked_system outputs should influence:
- Whether to park/resume
- Whether to reframe (sensemaking) or proceed (execution)
- Whether to slow down (risk) or keep it short (moment)

It should not directly author Shaper artifacts.

### C) From Control Plane → DoPeJar (feedback loop)

Control Plane outputs are evidence for DoPeJar:
- Gate failures and categories become “why it didn’t ship”
- Logs become “what happened” and “what to do next”

DoPeJar can then help decide whether to revise spec, revise implementation, or defer.

---

## Anti-Patterns (Do Not Do These)

1. **DoPeJar writes `08_commit.md`** → collapses untrusted shaping into trusted commitment.
2. **locked_system stance blocks all context switches** → feels robotic; should support park/resume.
3. **Single overloaded “altitude” variable** → mixes meaning level with response depth and causes misrouting.
4. **Shaper treats transcript as truth** → invites drift; artifact state must be authoritative.

---

## Minimal “Stacked” Vocabulary for Shaper Documents

When Shaper emits artifacts, keep the vocabulary consistent:

- WORK_ITEM (L3) focuses on implementation scope and acceptance commands.
- SPEC (L4) focuses on system design, phases, and success criteria.
- DoPeJar context (north stars / strategy) belongs in the conversational layer, referenced
  as rationale, not embedded as executable instructions.

