# AI_ARCH Repo OS

This repository uses a **registry-driven control plane**.

## Control plane hierarchy
- **Root registries** live in `/registries/`
  - `frameworks_registry.csv` is the top-level control plane.
- Some selected rows expose their own control plane via `child_registry_path`.
  - Example: **Repo OS Module** (`FMWK-900`) points to `/modules/repo_os/registries/repo_os_registry.csv`.

## How selection works
1. Set `selected=yes` in the registries for what you want active.
2. Run validation (recurses into child registries):
   - `python scripts/validate_registry.py`
3. Generate an execution plan (recurses into child registries):
   - `python scripts/apply_selection.py`
4. Use `generated/plan.json` to drive an LLM/agent to execute install/update/verify actions.

## Key entry points
- Root: `/registries/frameworks_registry.csv`
- Repo OS module: `/modules/repo_os/registries/repo_os_registry.csv`
- Repo OS created-items (governed): `/modules/repo_os/registries/repo_os_created_items_registry.csv`

