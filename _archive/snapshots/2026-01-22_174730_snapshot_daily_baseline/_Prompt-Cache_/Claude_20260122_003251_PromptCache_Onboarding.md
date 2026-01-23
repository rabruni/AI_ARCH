---
prompt_id: P-20260122-003251-CLAUDE-PROMPTCACHE-ONBOARD
type: prompt
target_agent: Claude
goal: Adopt Prompt-Cache workflow for handoffs
status: draft
relates_to:
created_local: 20260122_003251
---

PROMPT ID: P-20260122-003251-CLAUDE-PROMPTCACHE-ONBOARD
TARGET AGENT: Claude (Builder)
SINGLE RESPONSIBILITY: Adopt `/_Prompt-Cache_/` as the handoff bus and use it consistently for prompts and feedback.

AUTHORITATIVE DOCS (read first)
- `docs/OPERATING_MODEL.md`
- `/_Prompt-Cache_/README.md`
- `/_Prompt-Cache_/INDEX.md`

RULES (non-negotiable)
1) Use `/_Prompt-Cache_/` for handoffs; `/prompts/` is curated long-term templates.
2) Every new prompt/feedback file MUST:
   - be a new file (no overwrite)
   - start with the required YAML header
   - be appended as a new row in `/_Prompt-Cache_/INDEX.md`
3) Follow-up work is a new file linked via `relates_to`.

WORKFLOW TO FOLLOW
1) When you receive a task from the Orchestrator, the input is a specific file in `/_Prompt-Cache_/` (do not rely on chat history).
2) After you complete implementation work, write a short feedback file (or completion report) to `/_Prompt-Cache_/` using:
   - `/_Prompt-Cache_/TEMPLATE_Feedback.md`
3) Update `/_Prompt-Cache_/INDEX.md` for every file you add.

DELIVERABLE (strict)
1) Confirm you will use `/_Prompt-Cache_/` + `INDEX.md` for all future handoffs.
2) If any part is unclear, write a clarifying question as a new prompt file in `/_Prompt-Cache_/` and index it.

