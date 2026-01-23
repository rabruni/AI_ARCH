# Problem — Kernel (SPEC-004)

DoPeJar (the conversational assistant) and the Control Plane/Shaper solve different problems:

- DoPeJar is a continuity + attention + coaching partner that benefits from long-horizon context, memory, and adaptive interaction.
- Shaper/Control Plane is deterministic governance for turning selected intent into audited work artifacts and validated execution.

Current gaps that prevent scaling DoPeJar into a robust “agentic system manager”:

1. **Stack drift and configuration ambiguity**
   - Without a kernel contract, “persona” and “behavior” changes become ad-hoc prompt edits that are hard to test, hard to revert, and hard to compare.

2. **Inconsistent UX across specialized behaviors**
   - Task-specific subagents can introduce different interaction patterns, which breaks trust and increases cognitive load.

3. **No unified measurement plane**
   - Risk, drift, and performance cannot be compared across stacks without shared metrics and event semantics.

4. **Hard to integrate ingestion without increasing chaos**
   - Email/docs/meeting notes ingestion can become a second inbox unless it is governed by contracts, retention, and a deterministic “attention” policy.

This spec defines a kernel that solves these gaps while preserving the purpose of DoPeJar and the Control Plane.
