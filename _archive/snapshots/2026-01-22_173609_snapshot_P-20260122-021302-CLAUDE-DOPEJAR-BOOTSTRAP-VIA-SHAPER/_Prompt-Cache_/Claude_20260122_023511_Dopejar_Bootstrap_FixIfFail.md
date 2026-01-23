---
prompt_id: P-20260122-023511-CLAUDE-DOPEJAR-BOOTSTRAP-FIXIFFAIL
type: prompt
target_agent: Claude
goal: Apply Gemini FIX list if bootstrap validation fails
status: draft
relates_to: P-20260122-021302-GEMINI-VALIDATE-DOPEJAR-BOOTSTRAP
created_local: 20260122_023511
---

PROMPT ID: P-20260122-023511-CLAUDE-DOPEJAR-BOOTSTRAP-FIXIFFAIL
TARGET AGENT: Claude (Builder)
SINGLE RESPONSIBILITY: If Gemini validation FAILs, apply the explicit FIX list and prepare the repo for re-validation. If PASS, record “no changes required”.

READ FIRST (authoritative)
- `docs/OPERATING_MODEL.md` (agent-run ethos; Shaper-required for authoritative artifacts)
- `/_Prompt-Cache_/README.md` and `/_Prompt-Cache_/INDEX.md`

INPUT (authoritative)
- Gemini validation output (must exist before acting):
  - `/_Prompt-Cache_/Gemini_20260122_021302_Validate_Dopejar_Bootstrap_Feedback.md`

BEHAVIOR
1) If the Gemini feedback file does not exist: do not guess; stop and wait.
2) If Gemini status is PASS:
   - Do not change repo files.
   - Write a feedback file and index it (see Reporting).
3) If Gemini status is FAIL:
   - Implement FIX-1..FIX-N exactly as written (no extra scope, no redesign).
   - If any FIX requires changing the authoritative `WORK_ITEM` in:
     - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items/WORK_ITEM*.md`
     then regenerate it via Shaper (`./shaper.sh`) — do not hand-edit the work item.
   - After fixes, do not run interactive commands unless required; keep changes minimal.

REPORTING (required)
1) Create feedback file:
   - `/_Prompt-Cache_/Claude_20260122_023511_Dopejar_Bootstrap_FixIfFail_Feedback.md`
   - YAML header: `type: feedback`, `status: sent`, `relates_to: P-20260122-023511-CLAUDE-DOPEJAR-BOOTSTRAP-FIXIFFAIL`
2) Body must include:
   - `STATUS: PASS-NOOP` or `STATUS: FIXED`
   - If FIXED: list each FIX applied and the exact files changed
3) Append ONE row to `/_Prompt-Cache_/INDEX.md` for your feedback file.

DELIVERABLE (STRICT)
Return ONLY:
1) `/_Prompt-Cache_/Claude_20260122_023511_Dopejar_Bootstrap_FixIfFail_Feedback.md`

