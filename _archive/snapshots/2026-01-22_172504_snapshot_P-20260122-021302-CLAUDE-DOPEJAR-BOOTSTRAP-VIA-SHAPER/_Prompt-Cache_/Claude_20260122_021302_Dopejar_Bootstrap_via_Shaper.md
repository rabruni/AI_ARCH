---
prompt_id: P-20260122-021302-CLAUDE-DOPEJAR-BOOTSTRAP-VIA-SHAPER
type: prompt
target_agent: Claude
goal: Bootstrap SPEC-DOPEJAR-001 via Shaper-created WORK_ITEM
status: draft
relates_to:
created_local: 20260122_021302
---

PROMPT ID: P-20260122-021302-CLAUDE-DOPEJAR-BOOTSTRAP-VIA-SHAPER
TARGET AGENT: Claude (Builder)
SINGLE RESPONSIBILITY: Use `./shaper.sh` to create a frozen L3 `WORK_ITEM.md` that specifies the bootstrap work, then execute that work to prepare `SPEC-DOPEJAR-001` for Dopejar shaping from `_archive/.../the_assist/`.

READ FIRST (authoritative)
- `docs/OPERATING_MODEL.md` (agent-run ethos; Prompt-Cache protocol; no placeholders)
- `/_Prompt-Cache_/README.md` and `/_Prompt-Cache_/INDEX.md`

SOURCE CONTEXT (read-only)
- `_archive/2026-01-14_repo-archive_v1/the_assist/`

TASK A — CREATE THE AUTHORITATIVE WORK ITEM VIA SHAPER (do not hand-write)
1) Run Shaper (interactive):
   - `./shaper.sh --output-dir Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items`
2) Enter these lines exactly (then use triggers). Do not add extra sections.
   - `ID: WI-DOPEJAR-BOOTSTRAP-001`
   - `Title: Bootstrap SPEC-DOPEJAR-001 for Dopejar`
   - `Status: Draft`
   - `ALTITUDE: L3`
   - `objective: Create SPEC-DOPEJAR-001 spec pack and archive context packet for shaping Dopejar from the_assist.`
   - `scope: Control_Plane/docs/specs/SPEC-DOPEJAR-001/`
   - `scope: _Prompt-Cache_/`
   - `plan: Create spec pack skeleton (apply-spec).`
   - `plan: Create source_context/ with deterministic tree + notes from _archive/.../the_assist/.`
   - `plan: Ensure work_items/ exists for Shaper output.`
   - `acceptance: python3 Control_Plane/cp.py apply-spec --target SPEC-DOPEJAR-001`
   - `acceptance: test -d Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items`
   - `acceptance: test -d Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context`
   - `acceptance: test -f Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_TREE.txt`
3) Trigger sequence:
   - type: `show me what you have`
   - type: `freeze it`
4) Confirm the file exists:
   - `Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items/WORK_ITEM.md` (or suffixed `_1` if already present)

TASK B — EXECUTE THE WORK ITEM (agent-run)
1) Create spec pack skeleton (do not overwrite if already exists):
   - `python3 Control_Plane/cp.py apply-spec --target SPEC-DOPEJAR-001`
2) Create context directory:
   - `mkdir -p Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context`
3) Write deterministic tree snapshot:
   - Output file: `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_TREE.txt`
   - Contents: one path per line, sorted, relative to `_archive/2026-01-14_repo-archive_v1/the_assist/`
4) Write entrypoints list:
   - Output file: `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_ENTRYPOINTS.txt`
   - Contents: short list of likely entry points/top-level modules (filenames only), derived from the tree
5) Write short notes (observations only; 15 lines max):
   - Output file: `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_NOTES.md`

TASK C — PROMPT-CACHE REPORTING (required)
1) Create feedback file:
   - `/_Prompt-Cache_/Claude_20260122_021302_Dopejar_Bootstrap_via_Shaper_Feedback.md`
   - YAML header: `type: feedback`, `status: sent`, `relates_to: P-20260122-021302-CLAUDE-DOPEJAR-BOOTSTRAP-VIA-SHAPER`
2) In the feedback body, include:
   - the exact WORK_ITEM path produced by Shaper
   - the list of created/updated paths under `Control_Plane/docs/specs/SPEC-DOPEJAR-001/`
3) Append rows to `/_Prompt-Cache_/INDEX.md` for:
   - the WORK_ITEM file (as `type: feedback`, `target_agent: Human`, status `sent`, relates_to this prompt_id)
   - the feedback file you created

DELIVERABLE (STRICT)
Return ONLY:
1) The WORK_ITEM path created by Shaper
2) The feedback file path you created

