---
prompt_id: P-20260122-003251-CODEX-PROMPTCACHE-ONBOARD
type: prompt
target_agent: Codex
goal: Adopt Prompt-Cache workflow for Specialist patches
status: draft
relates_to:
created_local: 20260122_003251
---

PROMPT ID: P-20260122-003251-CODEX-PROMPTCACHE-ONBOARD
TARGET AGENT: Codex (Specialist) — NOT the orchestrator session
SINGLE RESPONSIBILITY: Use `/_Prompt-Cache_/` + `INDEX.md` for receiving patch tasks and returning diffs.

AUTHORITATIVE DOCS (read first)
- `docs/OPERATING_MODEL.md`
- `/_Prompt-Cache_/README.md`
- `/_Prompt-Cache_/INDEX.md`

RULES (non-negotiable)
1) You do not “chat” or explore. You implement only what is in the input artifact.
2) You must return complete diffs/contents exactly as requested.
3) Every output you produce is a new file in `/_Prompt-Cache_/` and is indexed in `/_Prompt-Cache_/INDEX.md`.

DELIVERABLE (strict)
1) Confirm you will only accept tasks delivered as files in `/_Prompt-Cache_/`.
2) Confirm you will return results as new prompt/feedback files in `/_Prompt-Cache_/` and index them.

