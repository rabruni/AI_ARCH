---
prompt_id: P-20260122-020742-PROMPTRULE-AGENT-RUN-ONLY
type: prompt
target_agent: Human
goal: Adopt rule: all repo work is executed by agents (no manual edits)
status: sent
relates_to: P-20260122-013942-PROMPTRULE-WRITE-THEN-READ
created_local: 20260122_020742
---

RULE (effective immediately)

Execution ethos:
- All repository work is executed by the assigned agent roles (Claude Builder / Gemini Validator / Codex Specialist / Orchestrator within allowed write-scope).
- The Human Operator approves and directs, but does not manually edit repo files as part of the workflow.
- Authoritative intent artifacts (L3 `WORK_ITEM`, L4 `SPEC`) are produced via Shaper (`./shaper.sh` / `cp.py shape`) by an agent session.

