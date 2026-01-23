# Governance Mode Specification

**Part of:** `/init` sequence (Step 5, 10)
**Location:** `/Control_Plane/init/governance_mode_specification.md`

---

## Purpose

Initialize and activate governance mode, which enforces safety constraints, action logging, and path restrictions during Control Plane operation.

---

## Governance Mode Definition

**Governance Mode** is a constrained execution environment that:
1. Restricts operations to allowed paths
2. Validates action preconditions
3. Prevents destructive operations without confirmation
4. Enforces rule-based constraints from SYSTEM_CONSTITUTION.md
5. Logs significant actions

---

## Governance Mode Rules

### Rule 1: Path Boundary
```
ALLOW operations only within:
  - /Control_Plane/
  - /src/
  - /tests/
  - /docs/
  - /prompts/
  - /scripts/
  - /config/
  - /_archive/ (read-only, append new archives only)
  - Repository root files (README.md, VERSION, etc.)

DENY operations on:
  - System paths (/, /usr/, /etc/, /bin/, etc.)
  - Parent directories outside repo (../ beyond root)
  - Paths outside repository root
  - Other users' directories
```

### Rule 2: Registry Is Truth
```
BEFORE creating/modifying any artifact:
  1. Verify item exists in a registry
  2. If not in registry, add it first
  3. Update registry status after changes

NEVER create orphan files not tracked in registries
```

### Rule 3: Safe Mode Protection
```
DANGEROUS operations require confirmation:
  - Delete any file
  - Modify SYSTEM_CONSTITUTION.md
  - Modify registries directly
  - Execute shell commands with side effects
  - Archive or reset operations

BEFORE executing dangerous operation:
  PROMPT user: "This operation modifies [target]. Confirm? (yes/no)"
  IF user confirms:
    PROCEED with operation
    LOG: "Confirmed: {operation}"
  ELSE:
    ABORT operation
    LOG: "Denied: {operation}"
```

### Rule 4: Validation Before Commit
```
BEFORE committing any changes:
  1. Run: python Control_Plane/scripts/validate_registry.py
  2. Verify output shows "OK: All validations passed"
  3. If validation fails, DO NOT commit
  4. Fix issues first, then retry
```

### Rule 5: Dependency Ordering
```
WHEN executing plan.json:
  Items MUST be processed in the order listed
  Dependencies are already resolved by apply_selection.py

NEVER skip ahead in the plan
NEVER install an item before its dependencies
```

---

## Governance Mode Activation

### Activation Steps

```
Step 1: Initialize Governance State
  governance_config = {
    "mode": "active",
    "safe_mode": true,
    "path_restrictions": true,
    "validation_required": true,
    "dependency_enforcement": true,
    "confirmation_required": ["delete", "archive", "reset", "constitution_edit"]
  }

Step 2: Set Path Context
  allowed_paths = [
    "/Control_Plane/",
    "/src/",
    "/tests/",
    "/docs/",
    "/prompts/",
    "/scripts/",
    "/config/"
  ]
  LOG: "Path restrictions enabled"

Step 3: Load Constitution Rules
  LOAD /SYSTEM_CONSTITUTION.md
  PARSE Machine-Enforceable YAML block
  APPLY validation rules

Step 4: Load CLAUDE.md Rules
  LOAD /Control_Plane/CLAUDE.md
  APPLY behavioral rules and protected artifacts
  LOG: "CLAUDE.md rules applied"

Step 5: Enable Governance Checks
  FOR EACH operation:
    governance_enabled = true
    validation_required = true
  LOG: "Governance mode ACTIVE"
```

---

## Protected Artifacts

These files/directories have special protection:

| Path | Protection | Reason |
|------|------------|--------|
| `/_archive/` | no_delete, append_only | Historical record |
| `/SYSTEM_CONSTITUTION.md` | confirm_before_modify | Canonical rules |
| `/Control_Plane/registries/` | validate_after_modify | Source of truth |
| `/Control_Plane/init/` | no_delete | Bootstrap capability |

---

## Enforcement Points

### Before Operation:
```
1. Check path is within allowed boundaries
2. Check item is in registry (for artifacts)
3. Check dependencies satisfied
4. For protected files: request confirmation
```

### After Operation:
```
1. Run validator if registry modified
2. Update registry status if artifact changed
3. Log significant changes
```

---

## Governance Mode States

| State | Meaning | Operations Allowed |
|-------|---------|-------------------|
| `active` | Normal constrained execution | All (with checks) |
| `safe_mode` | Extra-restrictive | Read + validation only |
| `disabled` | No governance checks | NOT RECOMMENDED |

Default: `active`

---

## Temporarily Relaxing Governance

For advanced operations (e.g., bulk migrations):

```
REQUIRES: User explicit confirmation
REQUIRES: Specific reason stated

COMMAND: Set mode to safe_mode after operation
LOG WARNING: "Governance relaxed for: {reason}"

ALWAYS re-enable after operation completes
```

---

## Error Handling

If governance constraint violated:

```
1. ABORT current operation immediately
2. Report:
   - Constraint violated
   - Operation attempted
   - Suggested fix
3. Do NOT proceed
4. Wait for user to fix and retry
```

---

## Output

After successful activation:

```
Governance mode: ACTIVE
  - Path restrictions: ENABLED
  - Validation required: ENABLED
  - Safe mode: ENABLED (confirmation for destructive ops)
  - Dependency enforcement: ENABLED

Protected artifacts:
  - /_archive/ (no_delete)
  - /SYSTEM_CONSTITUTION.md (confirm_modify)
  - /Control_Plane/registries/ (validate_after)

Ready for safe operation.
```
