---
prompt_id: P-20260122-013942-PROMPTRULE-WRITE-THEN-READ
type: prompt
target_agent: Human
goal: Adopt prompt rule: write prompt to file then read it in-chat
status: sent
relates_to: P-20260122-005434-PROMPTRULE-STANDALONE
created_local: 20260122_013942
---

RULE (effective immediately)

When the orchestrator is asked to write a prompt:
1) Write the prompt to `/_Prompt-Cache_/` first (new file; no overwrite).
2) Append the prompt to `/_Prompt-Cache_/INDEX.md`.
3) Then read the exact prompt content back in-chat.
4) Exception: if explicitly requested “file-only”, do not read it back.

