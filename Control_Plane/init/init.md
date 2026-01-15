# /init — Control Plane Bootstrap

**Version:** 1.0.0
**Purpose:** Bootstrap an LLM to manage the Control Plane (create, update, deploy, shutdown)

---

## Quick Start (For LLMs)

If you are an LLM reading this, execute these steps in order:

```
1. Read this file completely
2. Read SYSTEM_CONSTITUTION.md at repo root
3. Execute the 10-step boot sequence below
4. You are now ready to manage the Control Plane
```

---

## What This System Does

The Control Plane is a **registry-driven work management system**:

- **Registries (CSV)** define what exists and what's selected
- **Verb prompts** define how to install/update/verify/uninstall items
- **Validators** ensure registries match filesystem
- **Plans** are generated for execution

Your job as an LLM is to:
1. **Create** — Add new items to registries, create artifacts
2. **Update** — Modify existing items and their artifacts
3. **Deploy** — Execute plans, install selected items
4. **Shutdown** — Archive, uninstall, reset safely

---

## Boot Sequence (10 Steps)

### Step 1: Read Constitution
```
FILE: /SYSTEM_CONSTITUTION.md
ACTION: Parse and internalize the TL;DR rules and truth hierarchy
VERIFY: You understand that registries are truth and ID is primary key
```

### Step 2: Read Control Plane Contract
```
FILE: /Control_Plane/control_plane/CONTROL_PLANE_CONTRACT.md
ACTION: Understand registry structure and nested control planes
VERIFY: You understand child_registry_path and dependency ordering
```

### Step 3: Verify Structure
```
COMMAND: python Control_Plane/scripts/validate_registry.py
ACTION: Run validator to confirm structure is valid
VERIFY: Output shows "OK: All validations passed"
IF FAILS: Fix issues before proceeding
```

### Step 4: Load Registries
```
FILES:
  - /Control_Plane/registries/frameworks_registry.csv
  - /Control_Plane/registries/components_registry.csv
  - /Control_Plane/registries/prompts_registry.csv
ACTION: Parse all root registries, note selected items
VERIFY: You can list all selected items by ID
```

### Step 5: Load Verb Prompts
```
FILES:
  - /Control_Plane/control_plane/prompts/install.md
  - /Control_Plane/control_plane/prompts/update.md
  - /Control_Plane/control_plane/prompts/verify.md
  - /Control_Plane/control_plane/prompts/uninstall.md
ACTION: Understand how to execute each verb on registry items
VERIFY: You can describe what each verb does
```

### Step 6: Generate Plan
```
COMMAND: python Control_Plane/scripts/apply_selection.py
ACTION: Generate execution plan from selected items
OUTPUT: /Control_Plane/generated/plan.json
VERIFY: Plan contains all selected items in dependency order
```

### Step 7: Initialize Governance Mode
```
FILE: /Control_Plane/init/governance_mode_specification.md
ACTION: Enable constraints:
  - Path restrictions (stay within repo)
  - Audit logging (log all actions)
  - Safe mode (confirm destructive operations)
VERIFY: You will not modify files outside allowed paths
```

### Step 8: Load CLAUDE.md Rules
```
FILE: /Control_Plane/CLAUDE.md
ACTION: Apply behavioral rules specific to this repo
VERIFY: You understand protected artifacts and conventions
```

### Step 9: Verify Ready State
```
CHECKLIST:
  [ ] Constitution read and understood
  [ ] Registries loaded and validated
  [ ] Verb prompts loaded
  [ ] Plan generated
  [ ] Governance mode active
  [ ] CLAUDE.md rules applied
```

### Step 10: Report Ready
```
OUTPUT:
  Control Plane initialized.
  - Registries: [count] loaded, [count] selected items
  - Plan: /Control_Plane/generated/plan.json
  - Mode: [Build|Stabilize|Reset]

  Ready to receive commands.
```

---

## Commands You Can Execute

After initialization, you can:

### Create
```
ADD new item to registry:
  1. Edit CSV to add row with selected=no, status=missing
  2. Run validate_registry.py
  3. Create artifact at artifact_path
  4. Update status=draft, then status=active
  5. Set selected=yes when ready
```

### Update
```
MODIFY existing item:
  1. Find item by ID in registry
  2. Read current artifact
  3. Make changes following update.md prompt
  4. Run validate_registry.py
  5. Update last_updated timestamp
```

### Deploy (Install)
```
INSTALL selected items:
  1. Run apply_selection.py to generate plan
  2. For each item in plan.json (in order):
     a. Read install_prompt_path
     b. Execute installation
     c. Verify with verify_prompt_path
     d. Update registry status
  3. Commit changes
```

### Shutdown
```
ARCHIVE and reset:
  1. Run archive procedure (see constitution)
  2. Move current state to /_archive/<date>/
  3. Preserve registries and manifests
  4. Clean working directories
  5. Re-run /init from clean state
```

---

## File Locations Reference

| Purpose | Path |
|---------|------|
| Constitution | `/SYSTEM_CONSTITUTION.md` |
| Control Plane root | `/Control_Plane/` |
| Registries | `/Control_Plane/registries/*.csv` |
| Verb prompts | `/Control_Plane/control_plane/prompts/` |
| Init specs | `/Control_Plane/init/` |
| Generated plans | `/Control_Plane/generated/` |
| Modules | `/Control_Plane/modules/` |
| Runbooks | `/Control_Plane/runbooks/` |
| CLAUDE.md | `/Control_Plane/CLAUDE.md` |

---

## Error Recovery

If something goes wrong:

### Validation Fails
```
1. Read error message carefully
2. Fix the specific issue (missing file, invalid enum, etc.)
3. Re-run validate_registry.py
4. Do not proceed until green
```

### Plan Execution Fails
```
1. Note which item failed and why
2. Check artifact_path exists
3. Check dependencies are installed
4. Fix issue, update registry status if needed
5. Re-run from failed item
```

### Need Full Reset
```
1. Follow Safe Reset Protocol in constitution
2. Archive first, then reset
3. Never delete without archiving
```

---

## Governance Rules (Always Follow)

1. **Never modify files outside Control_Plane/ or repo root**
2. **Always run validator before committing**
3. **Always update registry when creating/modifying artifacts**
4. **Never skip dependencies**
5. **Log all significant actions**
6. **Ask for confirmation on destructive operations**

---

## Success Criteria

You have successfully initialized when:

1. ✅ `validate_registry.py` passes
2. ✅ `plan.json` is generated
3. ✅ You can list all selected items by ID
4. ✅ You understand the 4 verbs (install/update/verify/uninstall)
5. ✅ You know where all key files are located
6. ✅ You will not operate outside allowed paths

---

## Next Steps After Init

1. Review `plan.json` for pending work
2. Check registry for `status=missing` items that need creation
3. Execute install for selected items not yet active
4. Run verify on all active items to confirm integrity

**You are now ready to manage the Control Plane.**
