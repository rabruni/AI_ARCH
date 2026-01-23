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

## Shaping Artifacts

Use the `shape` command to interactively create structured artifacts:

```bash
python3 Control_Plane/cp.py shape
python3 Control_Plane/cp.py shape --output-dir ./specs
```

**How it works:**
1. Enter text describing your work item or spec
2. Shaper auto-detects altitude:
   - **L3 (Work Item)**: Keywords like "implement", "fix", "task", "steps"
   - **L4 (Spec)**: Keywords like "architecture", "vision", "non-goals", "success criteria"
3. Use triggers to control the flow:
   - `show me what you have` → reveal current state
   - `turn this into a work item` → converge to L3
   - `turn this into a spec` → converge to L4
   - `freeze it` → finalize and output artifact

**Output:**
- L3: `WORK_ITEM.md` (Objective, Scope, Plan, Acceptance)
- L4: `SPEC.md` (Overview, Problem, Non-Goals, Phases, Work Items, Success Criteria)

## Extending
- Add a child registry path in a framework row to enable nested control planes.
- Add component/module rows to `registries/components_registry.csv` for architecture swap-ability.
