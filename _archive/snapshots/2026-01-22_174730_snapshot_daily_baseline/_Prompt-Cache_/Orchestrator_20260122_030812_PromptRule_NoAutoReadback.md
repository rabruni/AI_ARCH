---
prompt_id: P-20260122-030812-PROMPTRULE-NO-AUTO-READBACK
type: prompt
target_agent: Human
goal: Update prompt protocol: do not automatically read prompt contents back in chat
status: sent
relates_to: P-20260122-013942-PROMPTRULE-WRITE-THEN-READ
created_local: 20260122_030812
---

Rule update (effective immediately):
- Prompts are always written to `/_Prompt-Cache_/` and indexed.
- Do NOT automatically read prompt contents back to the screen.
- Readback happens only if explicitly requested (e.g., “show me the prompt contents”).

Rationale:
- User has adopted the workflow; screen readbacks are now unnecessary noise.
