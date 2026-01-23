---
prompt_id: P-20260122-032208-CLAUDE-AGENTPULL-RUNPENDING
type: prompt
target_agent: Claude
goal: Self-serve runner: pull and execute next pending Claude prompt from Prompt-Cache
status: sent
relates_to:
created_local: 20260122_032208
---

You are Claude (The Builder).
Single responsibility: pull and execute the next pending prompt assigned to Claude from `/_Prompt-Cache_/STATUS.md`, then write a feedback artifact and index it. Do not commit unless the prompt explicitly says to.

Repo root: `/Users/raymondbruni/AI_ARCH`

Algorithm (repeatable):
1) Read `/_Prompt-Cache_/STATUS.md`.
2) Find the first line matching:
   - starts with `- Exec order`
   - contains `(Claude)`
   - ends with `— pending`
3) Extract the prompt file path in backticks on that line.
4) Read and execute that prompt exactly.
5) Write the required feedback artifact to `/_Prompt-Cache_/` (as specified by the prompt).
6) Append the feedback artifact row to `/_Prompt-Cache_/INDEX.md`.
7) Stop (do not proceed to the next prompt unless explicitly instructed).

Deliverable (in your chat response):
- Only the path to the feedback file you wrote.
