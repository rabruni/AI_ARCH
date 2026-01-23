# Overview — Attention Modules (SPEC-005)

**ID:** SPEC-005  
**Title:** Attention Modules Library (for DoPeJar + Subagents)  
**Status:** draft  
**ALTITUDE:** L4  

## Summary

Define a small set of “attention modules” (behavioral control primitives) that can be
assembled into stack profiles. These modules are simple, measurable, and auditable,
and they support DoPeJar’s human-centric attention management without turning the
system into a task manager.

## Goals

- Define module contracts that are:
  - simple to understand and reason about
  - testable via deterministic signals and event semantics
  - composable under the kernel’s governance model
- Provide modules that reduce rabbit holes, reduce stress amplification, and improve
  continuity for ADHD-style context switching.

## Non-Goals

- Implement modules in this spec pack.
- Introduce autonomous execution.
- Replace DoPeJar personality and coaching layer.

## Success Criteria

- Each module has a clear contract: inputs, outputs, invariants, metrics.
- Modules map cleanly to kernel stack profiles and can be evaluated per sprint.
