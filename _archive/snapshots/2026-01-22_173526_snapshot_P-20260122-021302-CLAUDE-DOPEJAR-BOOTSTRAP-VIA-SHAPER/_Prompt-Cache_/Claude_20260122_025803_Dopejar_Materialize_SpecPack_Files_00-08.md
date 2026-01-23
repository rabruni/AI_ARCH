---
prompt_id: P-20260122-025803-CLAUDE-DOPEJAR-MATERIALIZE-SPECPACK-00-08
type: prompt
target_agent: Claude
goal: Make SPEC-DOPEJAR-001 pass `cp validate-spec` by adding missing spec pack files 00_overview..08_commit (no overwrites, no placeholders)
status: draft
relates_to: P-20260122-021302-CLAUDE-DOPEJAR-BOOTSTRAP-VIA-SHAPER
created_local: 20260122_025803
---

You are Claude (The Builder).
Single responsibility: materialize the missing spec pack files required by `cp validate-spec` for SPEC-DOPEJAR-001. Do not implement Dopejar. Do not modify `_archive/`. Do not touch Shaper module code. Do not commit.

Repo root: `/Users/raymondbruni/AI_ARCH`

Preflight:
1) `python3 Control_Plane/scripts/init.py`
2) Confirm current failure (expected before the fix):
   - `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001 || true`

Target directory (write here only):
- `Control_Plane/docs/specs/SPEC-DOPEJAR-001/`

Create these 9 files (DO NOT overwrite if they already exist; if any exist, stop and ask the user):
- `00_overview.md`
- `01_problem.md`
- `02_solution.md`
- `03_requirements.md`
- `04_design.md`
- `05_testing.md` (must contain ONLY ONE line starting with `$`)
- `06_rollout.md`
- `07_registry.md`
- `08_commit.md` (must contain required sections)

Commands (copy/paste exact; each will fail if file already exists, by design):

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/00_overview.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/00_overview.md <<'EOF'
# SPEC-DOPEJAR-001 — Overview

This spec pack defines the artifact-first rebuild/migration of the archived `the_assist` system into a new resident named Dopejar under this repo’s Control Plane + Shaper workflow.

Primary intent artifacts live in:
- `artifacts/` (Shaper outputs, e.g., `SPEC.md`)
- `work_items/` (Shaper outputs, e.g., `WORK_ITEM.md`)
- `source_context/` (read-only archive-derived context snapshots)
EOF`
```

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/01_problem.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/01_problem.md <<'EOF'
# Problem

We have an archived system at `_archive/2026-01-14_repo-archive_v1/the_assist/` and need a controlled, repeatable path to reconstitute its structure and intent into the current repository’s governance model (Control Plane + Shaper), without direct execution or untracked edits.
EOF`
```

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/02_solution.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/02_solution.md <<'EOF'
# Solution

Use Shaper v2 to generate and freeze:
- an L4 spec (`artifacts/SPEC.md`) and
- L3 work items (`work_items/WORK_ITEM*.md`)

Implementation (code changes) occurs only after artifacts are validated and committed via the Control Plane’s normal gates.
EOF`
```

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/03_requirements.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/03_requirements.md <<'EOF'
# Requirements

- Artifact-first authority: frozen artifacts are the source of intent.
- No execution during shaping: shaping produces text artifacts only.
- Determinism: artifacts must not include timestamps/UUIDs/randomness.
- No silent overwrite of outputs: new outputs must be uniquely named.
- Phase confirmation gate (L4): phases are not accepted unless explicitly confirmed.
EOF`
```

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/04_design.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/04_design.md <<'EOF'
# Design

The authoritative design for this effort is captured in the Shaper-produced L4 artifact in `artifacts/` and the Shaper-produced L3 work items in `work_items/`.

This spec pack’s role is to provide the Control Plane’s standard required file set for validation and gating.
EOF`
```

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/05_testing.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/05_testing.md <<'EOF'
# Testing

$ python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001

Manual checks:
- Confirm `source_context/` exists and is read-only reference material.
- Confirm Shaper artifacts (when created) live in `artifacts/` and are not hand-edited.
EOF`
```

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/06_rollout.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/06_rollout.md <<'EOF'
# Rollout

- Establish spec pack validity (`cp validate-spec` passes).
- Freeze L4 spec via Shaper into `artifacts/`.
- Create and freeze L3 work items via Shaper into `work_items/`.
- Proceed to implementation only after validation feedback is PASS.
EOF`
```

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/07_registry.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/07_registry.md <<'EOF'
# Registry

This spec pack does not introduce registry changes yet.

If/when registry entries are required, they must be added via the Control Plane’s registry workflow and validated after changes.
EOF`
```

```bash
test -e Control_Plane/docs/specs/SPEC-DOPEJAR-001/08_commit.md && echo 'exists' && exit 1 || true
cat > Control_Plane/docs/specs/SPEC-DOPEJAR-001/08_commit.md <<'EOF'
# Commit Manifest

## MODE
EXPLORE

## ALTITUDE
L4

## REFERENCES
goal: Rebuild/migrate the archived `the_assist` system into Dopejar under Control Plane governance.
non-goals: Do not execute tasks or implement code during shaping; do not modify `_archive/`.
acceptance: `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001` returns VALID.

## STOP CONDITIONS
- Stop if any required spec pack files are missing or validation reports errors.
EOF`
```

Validation (must pass):
- `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001`

Write feedback artifact:
- Path: `/_Prompt-Cache_/Claude_20260122_025803_Dopejar_Materialize_SpecPack_Files_00-08_Feedback.md`
- Front matter: `type: feedback`, `target_agent: Human`, `status: passed|failed`, `relates_to: P-20260122-025803-CLAUDE-DOPEJAR-MATERIALIZE-SPECPACK-00-08`, `created_local: 20260122_025803`
- Include validation output summary and any files created.

Index update:
- Append your feedback file row to `/_Prompt-Cache_/INDEX.md`.

Deliverable (in chat):
- The full contents of the feedback artifact you wrote.
