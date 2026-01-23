---
prompt_id: P-20260122-025803-GEMINI-VALIDATE-DOPEJAR-SPECPACK-00-08
type: prompt
target_agent: Gemini
goal: Validate SPEC-DOPEJAR-001 spec pack required files 00_overview..08_commit now exist and `cp validate-spec` passes
status: draft
relates_to: P-20260122-025803-CLAUDE-DOPEJAR-MATERIALIZE-SPECPACK-00-08
created_local: 20260122_025803
---

You are Gemini (Validator).
Single responsibility: validate that SPEC-DOPEJAR-001 now passes Control Plane spec pack validation. Do not implement code. You may write one feedback artifact to `/_Prompt-Cache_/`.

Repo root: `/Users/raymondbruni/AI_ARCH`

Run:
1) `python3 Control_Plane/scripts/init.py`
2) `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001`

Required file existence checks:
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/00_overview.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/01_problem.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/02_solution.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/03_requirements.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/04_design.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/05_testing.md` (must contain only one `$` line)
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/06_rollout.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/07_registry.md`
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/08_commit.md` (must include required sections and MODE/ALTITUDE values)

PASS criteria:
- `cp validate-spec --target SPEC-DOPEJAR-001` reports `Result: VALID` (warnings allowed).

If FAIL:
- Provide minimal ordered FIX list (FIX-1..FIX-N) with exact file targets.

Write feedback artifact:
- Path: `/_Prompt-Cache_/Gemini_20260122_025803_Validate_Dopejar_SpecPack_00-08_Feedback.md`
- Front matter:
  - prompt_id (F-...),
  - type: feedback,
  - target_agent: Human,
  - goal,
  - status: passed|failed,
  - relates_to: `P-20260122-025803-GEMINI-VALIDATE-DOPEJAR-SPECPACK-00-08`,
  - created_local: 20260122_025803
- Body begins with PASS or FAIL.

Index update:
- Append your feedback artifact row to `/_Prompt-Cache_/INDEX.md`.

Deliverable (in chat):
- The full contents of the feedback artifact you wrote.
