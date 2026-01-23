# Overview — Kernel (SPEC-004)

**ID:** SPEC-004  
**Title:** Pluggable Cognitive Kernel for DoPeJar + Subagents  
**Status:** draft  
**ALTITUDE:** L4  

## Summary

Define a kernel that enables governed, testable composition of “cognitive stacks” (persona + modules) across sprints, while keeping a consistent end-user experience. The kernel must support runtime routing to task-specific subagent stacks without enabling ad-hoc, mid-session reconfiguration.

## Goals

- Provide a stable kernel contract that supports:
  - Persona profiles versioned and shipped through a product lifecycle (sprint-managed).
  - Stack profiles (module sets + constraints) selected by routing policy.
  - Subagent specialization (learning, writing, finance, family coordination) behind a consistent UX.
- Define auditable risk and performance measurement primitives for stacks and modules.
- Preserve strict separation of authority: proposals vs decisions, and shaping vs execution.

## Non-Goals

- Implement the kernel or modules in this spec pack.
- Define L5 behavior or autonomous execution behavior.
- Replace the Control Plane governance model; this spec integrates with it.

## Success Criteria

- A versioned `PersonaProfile` + `StackProfile` spec is defined with deterministic routing semantics.
- Kernel interfaces (“ports”) are defined for ingestion and memory with explicit invariants.
- A test plan exists that can validate determinism, safety invariants, and routing correctness without relying on model “goodness”.
