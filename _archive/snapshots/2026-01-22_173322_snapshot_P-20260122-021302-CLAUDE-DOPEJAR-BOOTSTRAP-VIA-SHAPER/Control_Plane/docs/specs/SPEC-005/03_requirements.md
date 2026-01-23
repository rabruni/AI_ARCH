# Requirements — Attention Modules (SPEC-005)

## M1 — Module interface

Each module must define:
- Inputs (signals/events/state)
- Outputs (proposals; never direct actions)
- Invariants (what it must never do)
- Metrics (how to evaluate effectiveness)

## M2 — Determinism and auditability

- Module decisions must be explainable via stored signals/events.
- Any non-deterministic inputs (timestamps, external feeds) must be provided externally
  and recorded as evidence, not generated internally.

## M3 — Integration boundaries

- Modules may influence:
  - stance suggestions
  - park/resume decisions
  - verbosity limits
  - “need clarification” proposals
- Modules must not:
  - write Control Plane artifacts
  - set MODE=COMMIT
  - execute commands

## M4 — Profiles and extensibility

- Modules must be composable into StackProfiles and scoped per persona/subagent.
- Modules should be optional; stack profiles define which are active.
