# Solution — Attention Modules (SPEC-005)

Define a module library with:

1) **Park/Resume (Open Loops)**
- Normalize interruptions.
- Preserve a resumable pointer.

2) **Working Set Budget (Now/Next/Parked)**
- Maintain a small working set as an attention display, not a backlog.

3) **Stress/Threat Response (Over-explanation suppression)**
- When stress signals rise, reduce verbosity and reduce options.

4) **Recognition-Primed Next Move**
- Propose one best next move + one disconfirm check.

5) **Goal Shielding (North-star lens)**
- Use identity/strategy to filter what is worth acting on now.

Each module emits proposals and metrics; kernel decides whether to apply.
