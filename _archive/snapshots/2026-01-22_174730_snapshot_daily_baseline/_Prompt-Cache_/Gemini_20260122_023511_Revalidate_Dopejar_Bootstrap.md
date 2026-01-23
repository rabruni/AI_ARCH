---
prompt_id: P-20260122-023511-GEMINI-REVALIDATE-DOPEJAR-BOOTSTRAP
type: prompt
target_agent: Gemini
goal: Re-validate SPEC-DOPEJAR-001 bootstrap after fixes
status: draft
relates_to: P-20260122-021302-GEMINI-VALIDATE-DOPEJAR-BOOTSTRAP
created_local: 20260122_023511
---

PROMPT ID: P-20260122-023511-GEMINI-REVALIDATE-DOPEJAR-BOOTSTRAP
TARGET AGENT: Gemini (Validator)
SINGLE RESPONSIBILITY: Re-run the validation checks from `P-20260122-021302-GEMINI-VALIDATE-DOPEJAR-BOOTSTRAP` after Claude applies fixes, and produce a new PASS/FAIL feedback artifact.

READ FIRST (authoritative)
- `docs/OPERATING_MODEL.md`
- `/_Prompt-Cache_/README.md`
- `/_Prompt-Cache_/INDEX.md`

INPUTS (authoritative)
1) Original validation prompt (use as checklist):
   - `/_Prompt-Cache_/Gemini_20260122_021302_Validate_Dopejar_Bootstrap.md`
2) Claude fix report (must exist before acting):
   - `/_Prompt-Cache_/Claude_20260122_023511_Dopejar_Bootstrap_FixIfFail_Feedback.md`
3) Work item produced by Shaper (must exist):
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items/WORK_ITEM*.md`

TASK (no implementation)
1) Re-run all validation checks from `Gemini_20260122_021302_Validate_Dopejar_Bootstrap.md`.
2) Produce a new feedback file:
   - `/_Prompt-Cache_/Gemini_20260122_023511_Revalidate_Dopejar_Bootstrap_Feedback.md`
   - YAML header: `type: feedback`, `status: passed|failed`, `relates_to: P-20260122-023511-GEMINI-REVALIDATE-DOPEJAR-BOOTSTRAP`
3) Append ONE row to `/_Prompt-Cache_/INDEX.md` for your feedback file.

DELIVERABLE (STRICT)
Return ONLY:
1) The path to your feedback file
2) PASS or FAIL

