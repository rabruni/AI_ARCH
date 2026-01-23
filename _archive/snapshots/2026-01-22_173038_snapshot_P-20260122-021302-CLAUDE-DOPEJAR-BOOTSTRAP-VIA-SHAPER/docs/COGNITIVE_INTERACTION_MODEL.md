# Cognitive Interaction Model (CIM v1) + Mapping

## Purpose

Provide a single, science-aligned interaction model for how cognition “should work” in an assistant system, then map it onto the current framework:

- DoPeJar (conversational assistant UX)
- Kernel (pluggable composition/governance)
- Attention Modules (proposal generators)
- HRM (two-loop + response-depth control)
- Shaper + Control Plane (artifact shaping + execution governance)

This document is intended to be usable as Shaper L4 input.

## CIM v1 — The interaction model

Institutional framing: cognition behaves like a **bounded workspace** governed by **executive control**, continuously modulated by **salience/arousal/value**, stabilized by **metacognitive monitoring**, and supported by **memory systems**.

### A) The core loop (every turn)

1) **Input buffer (Perception)**
- Receive incoming data: user utterance, environment signals, new evidence.

2) **Fast appraisal (Salience + Value + Arousal/Threat)**
- Compute “what matters now” and “how constrained we are”:
  - salience (novelty/urgency)
  - value alignment (north stars)
  - arousal/threat (stress/load)

3) **Executive control selects focus and policy**
- Decide:
  - what the current focus is
  - what to defer/park
  - what clarification is required
- Enforce constraints (no execution, no implicit commitment, etc.).

4) **Workspace update (Working memory / active set)**
- Maintain a bounded working set:
  - now/next/parked (or equivalent)
  - current artifact/state-of-work
  - minimal recent conversational context

5) **Proposal generation (Action selection)**
- Produce a proposal:
  - a response
  - a single clarification question
  - park/resume action
  - one recommended next move + one disconfirm question

6) **Write-back (Memory)**
- Persist only what policy allows:
  - episodic audit events (what happened)
  - semantic updates (facts/goals)
  - procedural updates (routines), if allowed

7) **Metacognitive monitoring**
- Monitor confidence, drift/looping, overload.
- Trigger interventions (reduce verbosity/options; ask disconfirm; park).

### B) Three modulators (always on)

- **Arousal/Threat modulator:** under stress, shrink workspace and reduce options.
- **Value/North-star modulator:** bias attention toward aligned work; surface misalignment.
- **Habit/Routine modulator:** offer fast defaults; executive control can override.

### C) Two-speed hierarchy (where “two-loop HRM” fits)

- **Fast inner loop:** handles turn-by-turn appraisal → workspace → next move.
- **Slow outer loop:** periodically re-evaluates priorities, commitments, and strategy; consolidates memory; updates policies and profiles (sprint-managed in this system).

### D) Stability / anti-spiral mechanisms

- **Bounded workspace** prevents context rot and overload.
- **Explicit commitment boundaries** prevent accidental execution/over-commitment.
- **Park/resume** treats interruption as a first-class action, not failure.
- **Metacognitive interrupts** detect drift and reduce cognitive load.

## Mapping CIM v1 → our architecture (what owns what)

### Ownership boundaries (non-negotiable)

- **DoPeJar** owns the human-facing conversation experience and continuity.
- **Kernel** owns deterministic governance: accepting proposals, routing stacks, writing audit events, enforcing “memory promises”.
- **Modules** emit proposals/metrics only; they do not commit state directly.
- **Shaper** owns artifact generation (WORK_ITEM/SPEC) with reveal/freeze gates.
- **Control Plane** owns commit boundary (G0) + gates for any “could run” work.

### CIM component mapping table

| CIM component | In our system | Primary artifacts/state | Notes |
|---|---|---|---|
| Input buffer | DoPeJar + Kernel | event_window, evidence items | Kernel normalizes ingestion inputs |
| Salience/value/arousal | Attention Modules + Kernel policy | signals object | Deterministic signals computed by kernel |
| Executive control | Kernel | governance policy, constraints | “modules propose; kernel decides” |
| Workspace update | Kernel + MemoryPort | working set state | bounded now/next/parked |
| Proposal generation | Attention Modules + LLMPort (optional) | Proposal objects | proposals are non-authoritative |
| Write-back | MemoryPort | state + append-only events | retention policy enforced |
| Metacognitive monitoring | Modules + Kernel | drift/overload metrics | triggers interventions |

## Where HRM fits (without conflation)

HRM is best treated as two separable controls:

1) **Two-loop hierarchy**
- Inner loop: fast turn-level control (appraisal → workspace → next move)
- Outer loop: slower review and consolidation (alignment + profile evaluation per sprint)

2) **Response depth controller**
- A policy that sets response “depth/verbosity” (ack → clarify → synthesize), influenced by:
  - arousal/threat (stress suppression)
  - ambiguity (clarification required)
  - task risk tier

This avoids conflating:
- meaning altitude (identity/strategy/ops/moment)
- response depth (how much to say)
- artifact altitude (L3 vs L4 shaping)

## Mapping CIM → attention modules (SPEC-005 set)

| Module | CIM role | Primary effect | When it should fire |
|---|---|---|---|
| Park/Resume | Executive control aid + stability | creates a resumable pointer | explicit context switch or repeated drift |
| Working Set Budget | Workspace update | keeps “now/next/parked” bounded | working set > threshold or too many threads |
| Stress/Threat Response | Arousal modulator | reduces verbosity/options | rising frustration/urgency/load |
| RPD Next Move | Proposal generation | one best move + disconfirm | uncertainty with need for momentum |
| Goal Shielding | Value modulator | alignment lens, tradeoffs | misalignment detected or drift from north stars |

## Mapping CIM → kernel responsibilities (SPEC-004)

Kernel should explicitly implement:

- **Signals computation:** deterministic, recorded inputs → signals for modules.
- **Proposal arbitration:** accept/reject proposals; require confirmation when needed.
- **Routing:** deterministic selection of StackProfile based on persona + task type + risk tier.
- **Workspace policy:** enforce bounded working set and park/resume boundaries.
- **Memory promises:** retention policy + what is remembered vs not remembered.
- **Auditability:** append-only events + minimal metrics for sprint evaluation.

## Mapping CIM → Shaper + Control Plane handoff

Shaper is not the “cognitive stack”; it is the artifact compiler.

Recommended handoff structure (candidate brief, text-only):
- objective (what)
- why (north star link)
- suggested artifact altitude (L3 WORK_ITEM vs L4 SPEC)
- scope hints
- acceptance intent

Shaper then enforces:
- reveal-before-freeze gating
- completeness checks
- deterministic rendering

Control Plane then enforces:
- G0 commit boundary (MODE=EXPLORE vs COMMIT)
- subsequent gates for execution readiness

## Acceptance criteria for this document

- CIM v1 is a single coherent model (core loop + modulators + two-loop hierarchy).
- Ownership boundaries are explicit (DoPeJar vs Kernel vs Modules vs Shaper vs Control Plane).
- HRM is positioned as loop/depth control (not another “altitude”).
- Mapping tables are sufficient to guide Shaper to generate formal specs without conflation.

