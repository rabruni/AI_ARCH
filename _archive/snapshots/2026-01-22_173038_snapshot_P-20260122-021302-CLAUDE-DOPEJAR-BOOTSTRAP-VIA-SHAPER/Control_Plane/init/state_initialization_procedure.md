# State Initialization Procedure

**Part of:** `/init` sequence (Steps 1-3, 6-9)
**Location:** `/Control_Plane/init/state_initialization_procedure.md`

---

## Purpose

Create and initialize the Control Plane state, verify structure, and load context before the system becomes fully operational.

---

## Steps

### Step 1: Verify Repository Structure

```
READ /SYSTEM_CONSTITUTION.md
PARSE Machine-Enforceable YAML block
FOR EACH required_directory:
  IF NOT EXISTS:
    FAIL: "Required directory missing: {path}"
FOR EACH required_file:
  IF NOT EXISTS:
    FAIL: "Required file missing: {path}"
LOG: "Repository structure verified"
```

### Step 2: Create Generated Directory

```
IF NOT EXISTS /Control_Plane/generated/:
  CREATE DIRECTORY /Control_Plane/generated/
  LOG: "Generated directory created"
ELSE:
  LOG: "Generated directory exists"
```

### Step 3: Load Registry State

```
registries = []
FOR EACH file IN /Control_Plane/registries/*_registry.csv:
  PARSE CSV into rows
  registries.append({
    "path": file,
    "items": rows,
    "selected_count": count where selected=yes
  })
  LOG: "Loaded {file}: {selected_count} selected"

total_selected = sum(r.selected_count for r in registries)
LOG: "Total registries: {len(registries)}, Total selected: {total_selected}"
```

### Step 4: Load Child Registries (Recursive)

```
FOR EACH registry IN registries:
  FOR EACH row IN registry.items:
    IF row.selected == "yes" AND row.child_registry_path:
      child_path = /Control_Plane/ + row.child_registry_path
      IF EXISTS child_path:
        PARSE child registry
        ADD to registries queue
        LOG: "Loaded child registry: {child_path}"
      ELSE:
        FAIL: "Missing child registry: {child_path}"
```

### Step 5: Initialize Session Context

```
session_context = {
  "session_id": generate_uuid(),
  "started_at": ISO_8601_TIMESTAMP,
  "registries_loaded": len(registries),
  "items_selected": total_selected,
  "mode": "Build",  # or Stabilize, Reset
  "governance_enabled": false  # set true after Step 7
}
LOG: "Session context initialized: {session_id}"
```

### Step 6: Pre-Flight Verification

```
COMMAND: python /Control_Plane/scripts/validate_registry.py

VERIFY output shows "OK: All validations passed"

IF verification fails:
  LOG ERROR: "Pre-flight failed: {reason}"
  RETURN failure
ELSE:
  LOG: "Pre-flight verification passed"
```

### Step 7: Enable Governance Mode

```
LOAD /Control_Plane/init/governance_mode_specification.md
APPLY rules:
  - Path restrictions: enabled
  - Audit logging: enabled
  - Safe mode: enabled
session_context.governance_enabled = true
LOG: "Governance mode enabled"
```

### Step 8: Generate Execution Plan

```
COMMAND: python /Control_Plane/scripts/apply_selection.py
OUTPUT: /Control_Plane/generated/plan.json
OUTPUT: /Control_Plane/generated/selection_report.md

VERIFY plan.json exists and is valid JSON
LOG: "Execution plan generated"
```

### Step 9: Report Ready State

```
OUTPUT:
  ═══════════════════════════════════════
  Control Plane Initialized
  ═══════════════════════════════════════
  Session ID: {session_context.session_id}
  Started: {session_context.started_at}

  Registries: {registries_loaded}
  Selected Items: {items_selected}
  Mode: {mode}

  Governance: ENABLED
  Plan: /Control_Plane/generated/plan.json

  Ready for commands.
  ═══════════════════════════════════════
```

---

## Session Context Format

The session context is held in memory during operation:

```json
{
  "session_id": "uuid-here",
  "started_at": "2026-01-14T21:00:00Z",
  "registries_loaded": 12,
  "items_selected": 37,
  "mode": "Build",
  "governance_enabled": true,
  "last_command": null,
  "last_result": null,
  "error_state": false
}
```

---

## Error Handling

If any step fails:

1. Log error with step number and reason
2. Do NOT proceed to next steps
3. Report failure to user
4. Suggest remediation (e.g., "run validate_registry.py to see details")

---

## Output Artifacts

After successful initialization:

```
/Control_Plane/generated/
  ├── plan.json              # Execution plan
  └── selection_report.md    # Human-readable summary
```

Session context in memory, ready for command execution.
