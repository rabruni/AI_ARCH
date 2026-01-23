---
id: P-20260122-163000-GEMINI-AUTO-FAIL-VAL
target_agent: Gemini
exec_order: 16
status: sent
relates_to: P-20260122-163000-CLAUDE-AUTO-FAIL
---

# Goal: Validate Retry Test File (FORCED FAILURE)

Part of the Automation Trial.

## Task
1. Check if `retry_test.txt` exists in the root.
2. Read the file and verify it contains exactly the word `WORLD`.

## Self-Healing Protocol (MANDATORY)
Since the previous agent wrote 'HELLO', this task **WILL FAIL**.
You MUST:
1.  Mark this task as `FAIL`.
2.  Create a new fix prompt `/_Prompt-Cache_/Claude_..._Fix_Retry.md` telling Claude to change the content to `WORLD`.
3.  Update `INDEX.md` and `STATUS.md` with the new prompt and increment the `retry_count`.
