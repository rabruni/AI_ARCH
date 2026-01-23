# Requirements — Kernel (SPEC-004)

## R1 — Profiles are versioned and testable

- Define `PersonaProfile` and `StackProfile` as versioned configuration artifacts.
- Profiles must be comparable across versions via deterministic diff of config fields.
- Profiles must define:
  - UX invariants (commands, status format, “memory promises”)
  - Allowed modules and capability envelope (e.g., read-only tools allowed or not)
  - Risk tier classification and gating policy

## R2 — Kernel owns governance; modules produce proposals

- Kernel is the authority boundary that:
  - decides stance/commitment transitions (or delegates to an authority module)
  - applies policy to accept/reject proposals
- Modules may not directly mutate authoritative state except via Kernel APIs.

## R3 — Routing is deterministic and bounded

- Kernel routes tasks to a released `StackProfile` using deterministic inputs:
  - declared task type and domain
  - risk tier signals
  - user-selected persona (active profile)
- Runtime routing must not depend on environment variables or timestamps.
- Mid-session stack changes require a reset/transition.

## R4 — Memory and ingestion are ports with explicit invariants

- `MemoryPort` must support:
  - get/set of authoritative state (structured, versioned)
  - append-only event log for audit
  - explicit retention policy and deletion semantics
- `IngestionPort` must:
  - normalize sources into `EvidenceItem` structures
  - be idempotent (same source id + payload yields same evidence items)
  - never create executable actions directly

## R5 — Measurement primitives exist

Define an event and metrics schema sufficient to measure:
- drift/looping
- interruption handling success (park/resume)
- user friction events
- risk posture changes (high-stakes slowdowns)
- performance proxies (time-to-decision, iterations-to-commit)

## R6 — Compatibility with Control Plane

- Kernel must be able to hand off a chosen slice of work to Shaper/Control Plane as a candidate brief.
- Kernel must not bypass Shaper reveal/confirm/freeze or Control Plane commit boundary.
