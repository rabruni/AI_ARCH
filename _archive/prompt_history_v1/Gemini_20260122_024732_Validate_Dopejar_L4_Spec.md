---
prompt_id: P-20260122-024732-GEMINI-VALIDATE-DOPEJAR-L4-SPEC
type: prompt
target_agent: Gemini
goal: Validate the frozen L4 SPEC for Dopejar (SPEC-DOPEJAR-001) and report PASS/FAIL with fixes
status: draft
relates_to: P-20260122-024732-CLAUDE-DOPEJAR-FREEZE-L4-SPEC
created_local: 20260122_024732
---

You are Gemini (Validator).
Single responsibility: validate the Dopejar L4 spec artifact and the spec pack integrity. Do not implement or modify core repo files. You may write a single feedback artifact to `/_Prompt-Cache_/`.

Repo root: `/Users/raymondbruni/AI_ARCH`

Run (exact):
1) `python3 Control_Plane/scripts/init.py`
2) `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001`

Artifact(s) to inspect:
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/artifacts/` (expect `SPEC.md` or an incremented deterministic filename)
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items/WORK_ITEM.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/` (context grounding only)

Validation checklist (PASS only if all true):
- A frozen L4 spec file exists in `.../artifacts/` (not just draft state in chat).
- Spec includes all required L4 sections: overview, problem, non-goals, phases, success criteria.
- Determinism: no timestamps/UUIDs/randomness in the artifact text; stable ordering; ends with a single trailing newline.
- Phase confirmation gate: phases are not silently assumed; evidence that explicit confirmation happened (or else FAIL with required fix).
- No “plan inference” leakage: the spec does not fabricate details not grounded in the provided context.

If FAIL:
- Provide a minimal, ordered FIX list (FIX-1..FIX-N) that Claude can apply via Shaper without redesign.

Write feedback artifact:
- Path: `/_Prompt-Cache_/Gemini_20260122_024732_Validate_Dopejar_L4_Spec_Feedback.md`
- Must include front matter fields:
  - prompt_id (F-...),
  - type: feedback,
  - target_agent: Human,
  - goal,
  - status: passed|failed,
  - relates_to: `P-20260122-024732-GEMINI-VALIDATE-DOPEJAR-L4-SPEC`,
  - created_local: 20260122_024732
- Body must start with PASS or FAIL on its own line.

Index update:
- Append a row to `/_Prompt-Cache_/INDEX.md` for your feedback artifact (type=feedback, status=passed|failed).

Deliverable (in your chat response):
- The full contents of the feedback artifact you wrote.
