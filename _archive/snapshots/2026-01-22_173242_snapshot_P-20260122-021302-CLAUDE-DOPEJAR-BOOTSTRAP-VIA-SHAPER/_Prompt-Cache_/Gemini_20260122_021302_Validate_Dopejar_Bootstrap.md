---
prompt_id: P-20260122-021302-GEMINI-VALIDATE-DOPEJAR-BOOTSTRAP
type: prompt
target_agent: Gemini
goal: Validate SPEC-DOPEJAR-001 bootstrap and Shaper output
status: draft
relates_to: P-20260122-021302-CLAUDE-DOPEJAR-BOOTSTRAP-VIA-SHAPER
created_local: 20260122_021302
---

PROMPT ID: P-20260122-021302-GEMINI-VALIDATE-DOPEJAR-BOOTSTRAP
TARGET AGENT: Gemini (Validator)
SINGLE RESPONSIBILITY: Validate that Claude’s bootstrap work matches the frozen Shaper work item and that the produced artifacts are deterministic and complete.

READ FIRST (authoritative)
- `docs/OPERATING_MODEL.md`
- `/_Prompt-Cache_/README.md`
- `/_Prompt-Cache_/INDEX.md`

INPUTS (authoritative)
1) Claude feedback file:
   - `/_Prompt-Cache_/Claude_20260122_021302_Dopejar_Bootstrap_via_Shaper_Feedback.md`
2) Work item produced by Shaper (path is inside the Claude feedback file):
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items/WORK_ITEM*.md`

VALIDATION TASKS (no implementation)
1) Confirm the work item is Shaper-produced (schema/format):
   - YAML front matter includes non-empty `ID`, `Title`, `Status`, `ALTITUDE`
   - Section headings exist in this exact order:
     - `## Objective`
     - `## Scope: File Permissions`
     - `## Implementation Plan`
     - `## Acceptance Commands`
   - File is UTF-8, LF, and has a single trailing newline.
2) Confirm repo state exists:
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/` exists
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/` exists
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_TREE.txt` exists and is sorted
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_ENTRYPOINTS.txt` exists
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_NOTES.md` exists and is <= 15 lines
3) Confirm Prompt-Cache protocol:
   - `/_Prompt-Cache_/INDEX.md` includes rows for:
     - `P-20260122-021302-CLAUDE-DOPEJAR-BOOTSTRAP-VIA-SHAPER`
     - Claude feedback file
     - the work item file (as a tracked exchange artifact)

OUTPUT (required)
1) Write a feedback file:
   - `/_Prompt-Cache_/Gemini_20260122_021302_Validate_Dopejar_Bootstrap_Feedback.md`
   - YAML header: `type: feedback`, `status: passed|failed`, `relates_to: P-20260122-021302-GEMINI-VALIDATE-DOPEJAR-BOOTSTRAP`
2) If FAIL: list FIX-1..FIX-N with exact file targets and exact error strings.
3) Append your feedback file row to `/_Prompt-Cache_/INDEX.md`.

DELIVERABLE (STRICT)
Return ONLY:
1) The path to your feedback file
2) PASS or FAIL

