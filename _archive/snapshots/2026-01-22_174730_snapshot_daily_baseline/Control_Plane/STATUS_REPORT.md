# STATUS_REPORT (v0.3)

## What was fixed vs v0.2
- Implemented true hierarchy: root `frameworks_registry.csv` selects Repo OS **module** (`FMWK-900`) which points to `/modules/repo_os/registries/repo_os_registry.csv`.
- Repo OS is now an inventory of packs, each pack points to a child registry (scripts, workflows, templates, docs, profiles, runbooks, prompts, created-items).
- `repo_os_items.csv` is **not** used as an operational registry. It is preserved as a source file only:
  - `/modules/repo_os/source/repo_os_items_original.csv`
  - Operational view is `/modules/repo_os/registries/repo_os_created_items_registry.csv` (governed, actionable).
- Validation and plan generation are now **recursive** (child registries are validated and planned automatically).

## What is still intentionally TODO (but now correctly represented)
- Non-interactive installer: `/modules/repo_os/scripts/repo_os_install.sh` (draft, not selected)
- Upgrade workflow: `/modules/repo_os/scripts/repo_os_upgrade.sh` (draft, not selected)
- Guardrails workflow content: `/.github/workflows/repo_guardrails.yml` (draft, not selected)
- CLAUDE.md rules content: `/CLAUDE.md` (placeholder; fill using v1 prompt ROS-P003)

## How to validate self-diagnosis
1. `python scripts/validate_registry.py`
   - fails if any selected item points to missing artifacts
   - fails if a row claims to expose a control plane but lacks `child_registry_path`
2. `python scripts/apply_selection.py`
   - produces `generated/plan.json` and `generated/selection_report.md` including module child registries
