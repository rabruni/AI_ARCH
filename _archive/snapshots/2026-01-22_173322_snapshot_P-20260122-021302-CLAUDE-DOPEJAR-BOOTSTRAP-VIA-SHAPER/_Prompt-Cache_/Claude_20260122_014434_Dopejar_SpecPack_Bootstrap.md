---
prompt_id: P-20260122-014434-CLAUDE-DOPEJAR-SPECPACK-BOOTSTRAP
type: prompt
target_agent: Claude
goal: Create Dopejar spec pack + archive context files for Shaper
status: draft
relates_to:
created_local: 20260122_014434
---

PROMPT ID: P-20260122-014434-CLAUDE-DOPEJAR-SPECPACK-BOOTSTRAP
TARGET AGENT: Claude (Builder)
SINGLE RESPONSIBILITY: Create the Control Plane spec pack and context files needed so the human can run Shaper against the archived `the_assist/` codebase to shape Dopejar.

READ FIRST (authoritative)
- `docs/OPERATING_MODEL.md` (roles, SoD, Prompt-Cache protocol)
- `/_Prompt-Cache_/README.md` and `/_Prompt-Cache_/INDEX.md`

INPUT (authoritative source code to read)
- Archive root: `_archive/2026-01-14_repo-archive_v1/the_assist/`

OUTPUT TARGET (create if missing)
- Spec pack ID: `SPEC-DOPEJAR-001`
- Spec pack path: `Control_Plane/docs/specs/SPEC-DOPEJAR-001/`
- Context dir: `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/`

TASK (do not redesign; do not commit)
1) Create spec pack skeleton:
   - Run: `python3 Control_Plane/cp.py apply-spec --target SPEC-DOPEJAR-001`
   - If the spec pack already exists, do NOT overwrite; proceed to step 2.
2) Create `source_context/` and write these deterministic context artifacts:
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_TREE.txt`
     - A stable file tree of `_archive/2026-01-14_repo-archive_v1/the_assist/`
     - One path per line, sorted, relative to `_archive/2026-01-14_repo-archive_v1/the_assist/`
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_ENTRYPOINTS.txt`
     - A short list of likely entry points and top-level modules (filenames only), derived from the tree
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_NOTES.md`
     - 15 lines max: what this archive appears to be (namespaces, rough components)
     - No implementation proposals; only observations
3) Confirm Shaper is runnable for the human:
   - Command (do not execute interactive): `python3 Control_Plane/cp.py shape --output-dir Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items`
   - Ensure `Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items/` exists.

PROMPT-CACHE PROTOCOL (required)
1) Create a feedback file:
   - `/_Prompt-Cache_/Claude_20260122_014434_Dopejar_SpecPack_Bootstrap_Feedback.md`
   - Use YAML header `type: feedback`, `status: sent`, `relates_to: P-20260122-014434-CLAUDE-DOPEJAR-SPECPACK-BOOTSTRAP`
2) Append both this prompt and your feedback file to `/_Prompt-Cache_/INDEX.md` if missing.

DELIVERABLE (STRICT)
Return ONLY:
1) A list of created/updated paths under `Control_Plane/docs/specs/SPEC-DOPEJAR-001/`
2) The path to your feedback file in `/_Prompt-Cache_/`

