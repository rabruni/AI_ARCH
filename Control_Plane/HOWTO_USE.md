# How to Use Repo OS

## Daily loop
1. Update registries (CSV) in `registries/`.
2. Run validation locally:
   - `python scripts/validate_registry.py`
3. Generate an execution plan:
   - `python scripts/apply_selection.py`
4. Hand the plan + referenced prompts to your coding agent (Claude Code, etc.) to execute.

## What gets validated
- Required columns exist
- Unique IDs
- Status/priority enums
- Artifact paths exist for selected items
- Dependencies exist and are acyclic

## Extending
- Add a child registry path in a framework row to enable nested control planes.
- Add component/module rows to `registries/components_registry.csv` for architecture swap-ability.
