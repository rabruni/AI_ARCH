# Rollout — Kernel (SPEC-004)

## Phase 0: Spec locked

- Approve kernel requirements and invariants.
- Treat this spec pack as the baseline contract.

## Phase 1: Prototype (non-integrated)

- Implement kernel interfaces with stubs:
  - in-memory MemoryPort
  - file-backed event log
  - no ingestion (or a sample ingestion adapter)

## Phase 2: Integration with DoPeJar and Shaper (bounded)

- Integrate DoPeJar front-end to emit candidate briefs.
- Integrate Shaper as the contract generator (WORK_ITEM/SPEC).
- Add measurement signals.

## Phase 3: Iteration by sprint

- Introduce new StackProfiles via versioned releases.
- Evaluate profiles with the test plan.
