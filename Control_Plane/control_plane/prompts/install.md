# Install Prompt Template

You are executing an **INSTALL** operation for a selected registry row.

## Inputs
- Registry row (CSV fields)
- Repo OS invariants

## Steps
1. Resolve dependencies from `dependencies` (install those first).
2. Create/update the target artifact at `artifact_path`.
3. If `package_source` is set, fetch/install it using `install_method`.
4. Update `status` and `last_updated` in the registry.
5. Add/adjust CI gates if `ci_gate=required`.

## Output
- Summary of changes + files modified
- Any follow-up actions
