---
prompt_id: P-20260122-024732-CLAUDE-DOPEJAR-SHAPE-L3-WORKITEMS-ARCHIVE-MOVE
type: prompt
target_agent: Claude
goal: Create + freeze the first L3 WORK_ITEM(s) to move the_assist archive into the Control Plane as Dopejar (via Shaper)
status: draft
relates_to: P-20260122-024732-CLAUDE-DOPEJAR-FREEZE-L4-SPEC
created_local: 20260122_024732
---

You are Claude (The Builder).
Single responsibility: create L3 work item artifacts via Shaper v2 for the “move full archive → Dopejar” effort. Do not implement code. Do not hand-edit work item files. Use Shaper only.

Repo root: `/Users/raymondbruni/AI_ARCH`

Preflight:
1) `python3 Control_Plane/scripts/init.py`
2) Confirm spec pack + L4 spec exist:
   - `ls -la Control_Plane/docs/specs/SPEC-DOPEJAR-001`
   - `ls -la Control_Plane/docs/specs/SPEC-DOPEJAR-001/artifacts`

Grounding context (read-only):
- `_archive/2026-01-14_repo-archive_v1/the_assist/`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_TREE.txt`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_ENTRYPOINTS.txt`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_NOTES.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/artifacts/SPEC.md` (or incremented filename)

Task:
- Use Shaper (ALTITUDE L3) to create and freeze at least ONE work item that, when implemented later, will migrate the full archive into the current Control Plane structure.
- Output directory MUST be:
  - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items`

Run Shaper:
- `./shaper.sh --output-dir Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items`

In Shaper:
- Set metadata explicitly:
  - `ID: SPEC-DOPEJAR-001-WI-ARCHIVE-MOVE-001`
  - `Title: Move the_assist archive into Dopejar resident (scaffold + import)`
  - `ALTITUDE: L3`
- Fill required L3 fields using prefixes:
  - `objective:`
  - `scope:`
  - `plan:` (no-inference: do not invent steps that aren’t grounded; if uncertain, constrain scope and state assumptions explicitly)
  - `acceptance:` (clear, testable checks)
- “Show me what you have”, then freeze with `freeze it`.
- If Shaper writes an incremented filename, accept it (do not overwrite).

After freeze:
1) Validate spec pack (optional but preferred):
   - `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001`
2) Create a feedback artifact:
   - Write `/_Prompt-Cache_/Claude_20260122_024732_Dopejar_Shape_L3_WorkItems_ArchiveMove_Feedback.md`
   - Include: status (passed/failed), the created work item paths, and any blockers.
3) Append a row to `/_Prompt-Cache_/INDEX.md` for the feedback file (type=feedback).

Deliverable (in your chat response):
- The full contents of the feedback artifact you wrote.
