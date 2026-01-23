---
prompt_id: P-20260122-024732-GEMINI-VALIDATE-DOPEJAR-L3-WORKITEMS-ARCHIVE-MOVE
type: prompt
target_agent: Gemini
goal: Validate the L3 work item(s) for moving the_assist archive into Dopejar and report PASS/FAIL with minimal fixes
status: draft
relates_to: P-20260122-024732-CLAUDE-DOPEJAR-SHAPE-L3-WORKITEMS-ARCHIVE-MOVE
created_local: 20260122_024732
---

You are Gemini (Validator).
Single responsibility: validate the L3 work item(s) created for archive migration. Do not implement code. You may write a single feedback artifact to `/_Prompt-Cache_/`.

Repo root: `/Users/raymondbruni/AI_ARCH`

Run:
1) `python3 Control_Plane/scripts/init.py`
2) `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001`

Artifacts to inspect:
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items/` (expect `WORK_ITEM.md` and/or incremented filenames)
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/artifacts/` (L4 spec exists)

Validation checklist (PASS only if all true):
- Work item(s) exist on disk (frozen), not just described in chat.
- L3 fields present and complete (objective, scope, plan, acceptance).
- No-inference enforcement: plan does not fabricate unknown steps; uncertainties are handled by scoping down or explicitly calling out assumptions.
- Acceptance criteria are testable/verifiable.
- Deterministic formatting (no timestamps/UUIDs/randomness).

If FAIL:
- Provide a minimal ordered FIX list (FIX-1..FIX-N) that Claude can apply via Shaper without redesign.

Write feedback artifact:
- Path: `/_Prompt-Cache_/Gemini_20260122_024732_Validate_Dopejar_L3_WorkItems_ArchiveMove_Feedback.md`
- Front matter:
  - prompt_id (F-...),
  - type: feedback,
  - target_agent: Human,
  - goal,
  - status: passed|failed,
  - relates_to: `P-20260122-024732-GEMINI-VALIDATE-DOPEJAR-L3-WORKITEMS-ARCHIVE-MOVE`,
  - created_local: 20260122_024732
- Body starts with PASS or FAIL on its own line.

Index update:
- Append a row to `/_Prompt-Cache_/INDEX.md` for your feedback artifact.

Deliverable (in your chat response):
- The full contents of the feedback artifact you wrote.
