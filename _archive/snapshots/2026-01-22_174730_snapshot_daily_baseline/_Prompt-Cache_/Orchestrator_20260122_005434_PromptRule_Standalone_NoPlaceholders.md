---
prompt_id: P-20260122-005434-PROMPTRULE-STANDALONE
type: prompt
target_agent: Human
goal: Adopt prompt rule: standalone, no placeholders, token-efficient
status: sent
relates_to:
created_local: 20260122_005434
---

RULE (effective immediately)

All prompts exchanged between agents MUST be:
1) Standalone: no placeholders, no “fill this in”, no reliance on chat history.
2) Self-contained: include all required repo paths, IDs, constraints, and exact deliverable format.
3) Token-efficient: minimum words necessary to execute correctly.
4) Deterministic: no timestamps/UUIDs/randomness inside prompt bodies unless required.

Enforcement:
- If a prompt contains placeholders or requires external filling, it is invalid and must be rewritten as a new prompt file.

