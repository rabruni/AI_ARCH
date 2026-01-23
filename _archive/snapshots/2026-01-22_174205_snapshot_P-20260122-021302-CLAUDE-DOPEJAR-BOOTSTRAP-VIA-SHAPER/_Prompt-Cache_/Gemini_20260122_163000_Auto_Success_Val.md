---
id: P-20260122-163000-GEMINI-AUTO-SUCCESS-VAL
target_agent: Gemini
exec_order: 14
status: sent
relates_to: P-20260122-163000-CLAUDE-AUTO-SUCCESS
---

# Goal: Validate Automation Test File

Part of the Automation Trial.

## Task
1. Check if `automation_test.txt` exists in the root.
2. Read the file and verify it contains exactly the word `READY`.

## Self-Healing
If it fails, follow the `GEMINI.md` protocol to issue a fix prompt.
