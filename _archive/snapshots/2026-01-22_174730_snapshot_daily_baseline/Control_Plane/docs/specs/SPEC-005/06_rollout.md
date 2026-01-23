# Rollout — Attention Modules (SPEC-005)

## Phase 0: Spec locked

- Approve module contracts and invariants.

## Phase 1: Prototype modules (pure functions)

- Implement modules with deterministic inputs/outputs and metrics counters.
- Add test harness to feed synthetic event windows and verify proposals.

## Phase 2: Stack profiles

- Assemble a small number of StackProfiles:
  - “ADHD anchor” (park/resume + working set + stress suppression)
  - “Writer” (working set + RPD)
  - “Finance” (stress suppression + explicit disconfirm)

## Phase 3: Evaluate and iterate

- Use event logs and metrics to compare profiles per sprint.
