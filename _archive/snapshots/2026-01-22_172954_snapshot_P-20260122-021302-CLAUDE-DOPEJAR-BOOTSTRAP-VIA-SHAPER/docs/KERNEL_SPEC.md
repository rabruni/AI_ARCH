# Pluggable Cognitive Kernel (DoPeJar + Subagents) — Spec Input

## Purpose

Define a pluggable “cognitive kernel” that composes and governs **cognitive stacks** (persona + modules) for DoPeJar and task-specific subagents, while keeping the end-user UX consistent and auditable.

This document is intended to be used as **design input for Shaper** (L4).

## Core framing (non-negotiable)

- **DoPeJar** = conversational assistant (human continuity, long-horizon guidance, park/resume).
- **Shaper** = deterministic artifact shaping (WORK_ITEM/SPEC) with reveal/freeze gates.
- **Control Plane** = execution governance (G0 commit boundary + gates) for things that may run.

The kernel must not collapse these roles.

## Objectives

1) **Composable stacks**
- Allow selecting a released, versioned **StackProfile** (module set + policies) for a given task/session.
- Stacks may differ by persona (e.g., “ADHD anchor” vs “Writer”) and by task domain (learn/write/finance/family/build).

2) **Consistent UX**
- A persona defines the interaction surface and invariants so that switching stacks does not feel like switching products.

3) **Deterministic routing**
- Runtime selection must be deterministic (same inputs → same StackProfile).
- No mid-session “hot swaps” unless at an explicit boundary (park/resume/reset).

4) **Governance boundary**
- Modules propose; the kernel decides.
- The kernel produces auditable events/metrics for evaluation per sprint.

5) **Extensibility stubs**
- Provide stable “ports” for ingestion and memory so new capability can be added without redesigning the UX or authority boundary.

## Non-goals

- Implementing the kernel in code.
- Allowing the kernel or DoPeJar to execute commands.
- Allowing the kernel to create Control Plane commit artifacts (e.g., `08_commit.md`) or bypass Shaper/Control Plane gates.
- L5 autonomy (deferred).

## Key entities (deterministic shapes)

### PersonaProfile (versioned)

Defines UX invariants + defaults + constraints. Released on sprint boundaries.

```yaml
PersonaProfile:
  id: string
  version: string
  name: string
  ux_invariants:
    commands: [string]            # e.g., ["park", "resume", "status"]
    status_strip: string          # deterministic format contract
    memory_promises: [string]     # what is remembered + for how long
  defaults:
    stance: string
    meaning_altitude: string
    risk_posture: low|medium|high
  constraints:
    forbidden_behaviors: [string] # e.g., "no nagging task-manager behavior"
    escalation_rules: [string]    # when to push vs ask vs park
```

### StackProfile (released unit)

Concrete module composition + capability envelope + routing tags.

```yaml
StackProfile:
  id: string
  version: string
  persona_profile_id: string
  modules:
    attention: [string]      # module ids
    ingestion: [string]      # module ids
    memory: string           # module id
  capabilities:
    tools: none|read_only
    storage_allowlist: [string]   # what sources can be persisted
  risk_tier: low|medium|high
  routing_tags:
    domains: [string]
    task_types: [string]
```

## Kernel ports (interfaces)

### MemoryPort

Required operations:
- `get_state()` → structured state
- `set_state(state)` → replace authoritative state (versioned)
- `append_event(event)` → append-only audit
- `query_events(filter)` → retrieval for debugging/review

Invariants:
- Schema validation on write; no silent drops.
- Explicit retention policy.
- State is authoritative; transcripts are optional audit logs, not truth.

### IngestionPort

Required operations:
- `ingest(source_id, payload)` → list of `EvidenceItem`

```yaml
EvidenceItem:
  source_type: string        # email|doc|meeting_note|...
  source_id: string
  captured_at: string|null   # if present, must be provided externally
  content: string
  metadata: object
```

Invariants:
- Deterministic output for identical inputs.
- No action generation; evidence only.

### LLMPort (optional)

Required operations:
- `propose(prompt)` → proposals (non-authoritative)

Invariants:
- Kernel must remain deterministic even if LLM is absent (manual mode possible).
- LLM output is never authoritative state without explicit kernel acceptance.

## Routing policy (deterministic)

Two-layer routing:

1) **Persona selection (sprint-managed)**
- Select a released PersonaProfile version for the user.

2) **Task routing (runtime)**
- Choose StackProfile deterministically from released stacks based on:
  - declared task type/domain
  - risk tier signals
  - active persona

Boundary rule:
- Stack changes only at explicit boundaries: `park`, `resume`, `reset`, or an explicit transition event.

## Human continuity: park/resume as a first-class boundary

Kernel supports:
- `park(current_focus)` → stores a resumable pointer: what/why/next step.
- `resume(focus_id)` → asks “what changed?” only at resume time.

Invariant:
- Interruptions must never be treated as failure; parking is a normal path.

## Shaper / Control Plane handoff (no conflation)

Kernel may emit a **candidate brief** (text-only) to feed into Shaper conversation:
- objective (what)
- why (north-star link)
- suggested artifact altitude (L3 WORK_ITEM vs L4 SPEC)
- scope hints
- acceptance intent

Kernel must not:
- generate `08_commit.md`
- invoke Control Plane scripts
- claim “ready to execute”

## Acceptance criteria (for this spec)

- The above entities and ports are defined with deterministic shapes.
- Routing is deterministic and bounded by explicit boundaries.
- Authority boundary (“modules propose; kernel decides”) is explicit and testable.
- Handoff to Shaper/Control Plane is explicitly non-executing and non-committing.

