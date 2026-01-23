---
prompt_id: P-20260122-003251-GEMINI-PROMPTCACHE-ONBOARD
type: prompt
target_agent: Gemini
goal: Adopt Prompt-Cache workflow for audits and verification
status: draft
relates_to:
created_local: 20260122_003251
---

PROMPT ID: P-20260122-003251-GEMINI-PROMPTCACHE-ONBOARD
TARGET AGENT: Gemini (Validator)
SINGLE RESPONSIBILITY: Adopt `/_Prompt-Cache_/` as the exchange bus for audit prompts, FAIL lists, and verification reports.

AUTHORITATIVE DOCS (read first)
- `docs/OPERATING_MODEL.md`
- `/_Prompt-Cache_/README.md`
- `/_Prompt-Cache_/INDEX.md`

RULES (non-negotiable)
1) Treat the filesystem as source of truth; chat is ephemeral.
2) Every audit output MUST be a new feedback file in `/_Prompt-Cache_/` (never overwrite).
3) Every file you add MUST be indexed in `/_Prompt-Cache_/INDEX.md`.
4) If you issue FAIL: provide FIX-1..FIX-N with exact file targets and explicit error messages.

WORKFLOW TO FOLLOW
1) Read the exact prompt file you are auditing from `/_Prompt-Cache_/` (do not paraphrase).
2) Validate against the referenced authoritative artifacts.
3) Output PASS/FAIL as a new `type: feedback` file using `/_Prompt-Cache_/TEMPLATE_Feedback.md`.
4) Append an index row in `/_Prompt-Cache_/INDEX.md`.

DELIVERABLE (strict)
1) Confirm you will use `/_Prompt-Cache_/` + `INDEX.md` for all future audits/verification.
2) If anything is missing from the protocol, propose a change as a new prompt file (do not edit old files).

