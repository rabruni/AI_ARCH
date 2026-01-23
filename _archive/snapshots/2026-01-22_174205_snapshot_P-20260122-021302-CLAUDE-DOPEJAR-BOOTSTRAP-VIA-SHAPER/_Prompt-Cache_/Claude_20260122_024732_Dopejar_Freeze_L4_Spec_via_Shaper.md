---
prompt_id: P-20260122-024732-CLAUDE-DOPEJAR-FREEZE-L4-SPEC
type: prompt
target_agent: Claude
goal: Create + freeze the L4 SPEC artifact for Dopejar rebuild/migration from the_assist archive (via Shaper)
status: draft
relates_to: P-20260122-021302-CLAUDE-DOPEJAR-BOOTSTRAP-VIA-SHAPER
created_local: 20260122_024732
---

You are Claude (The Builder).
Single responsibility: produce the L4 spec artifact for Dopejar using Shaper v2. Do not implement code. Do not edit artifacts by hand. Use Shaper only for `SPEC.md`.

Repo root (do not change): `/Users/raymondbruni/AI_ARCH`

Preflight (run exactly):
1) `python3 Control_Plane/scripts/init.py`
2) Verify spec pack exists:
   - `ls -la Control_Plane/docs/specs/SPEC-DOPEJAR-001`
   - `ls -la Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context`

Context sources (read-only; use as your grounding, no inference beyond what’s written):
- `_archive/2026-01-14_repo-archive_v1/the_assist/`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_TREE.txt`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_ENTRYPOINTS.txt`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_NOTES.md`

Task: run Shaper and create a SPEC (ALTITUDE L4), then freeze to:
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/artifacts/SPEC.md`
  - If the file already exists, Shaper’s output-safety must write a deterministic incremented filename (do not overwrite).

Run Shaper (output dir must be the artifacts folder):
- `./shaper.sh --output-dir Control_Plane/docs/specs/SPEC-DOPEJAR-001/artifacts`

In Shaper, do ALL of the following (in any order, but complete all required L4 fields):
- Set metadata explicitly:
  - `ID: SPEC-DOPEJAR-001`
  - `Title: Dopejar (rebuild the_assist)`
  - `ALTITUDE: L4`
- Fill L4 fields using Shaper prefixes:
  - `overview:` what Dopejar is, at a high level (artifact-first; no execution)
  - `problem:` what rebuilding/migrating solves (from context only)
  - `non-goal:` what is explicitly out of scope for this effort
  - `phase:` propose phases, but DO NOT confirm phases until the user explicitly confirms them (Shaper must enforce `phases_confirmed`)
  - `success:` objective pass/fail criteria that can be validated by another agent

Phase confirmation rule (must be enforced):
- If/when Shaper requests phase confirmation, ask the user for explicit confirmation and do not proceed without it.

Freeze rule:
- Before freezing, use Shaper “show me what you have” and ensure it is complete.
- Freeze using the exact phrase: `freeze it`

After freeze:
1) Validate the spec pack:
   - `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001`
2) Create a feedback artifact:
   - Write `/_Prompt-Cache_/Claude_20260122_024732_Dopejar_Freeze_L4_Spec_via_Shaper_Feedback.md`
   - Include: prompt_id, status (passed/failed), paths created/modified, and any blockers.
3) Append a row to `/_Prompt-Cache_/INDEX.md` for the feedback file (type=feedback).

Deliverable (in your chat response):
- The full contents of the feedback artifact you wrote.
