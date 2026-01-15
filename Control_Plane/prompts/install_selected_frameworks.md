# Install Selected Frameworks Meta-Prompt

**ID:** PRMPT-011
**Purpose:** Install all frameworks marked as selected=yes in the registry plan.

---

## Overview

This meta-prompt iterates through the generated plan and installs each selected framework using the install verb prompt. It handles dependencies, validates installations, and updates registry status.

---

## Prerequisites

Before running this prompt:
- [ ] Control Plane bootstrapped (`init.py` passes)
- [ ] Frameworks selected (`selected=yes` in registry)
- [ ] Plan generated (`apply_selection.py` run)
- [ ] Plan file exists: `Control_Plane/generated/plan.json`

---

## Input

```bash
python Control_Plane/scripts/apply_selection.py
cat Control_Plane/generated/plan.json
```

The plan contains ordered items with their dependencies resolved.

---

## Procedure

### Step 1: Load Plan

```python
import json
plan = json.load(open("Control_Plane/generated/plan.json"))
items = plan.get("items", [])
```

### Step 2: Install Each Item

```
FOR EACH item IN items (in dependency order):
    1. PRINT "Installing {item.id}: {item.name}"

    2. CHECK dependencies:
       FOR EACH dep IN item.dependencies:
           IF dep.status != "active":
               SKIP item, WARN "Dependency {dep} not ready"

    3. EXECUTE install prompt:
       python prompt.py execute install {item.id}

    4. FOLLOW the install prompt procedure:
       - Check dependencies
       - Verify path available
       - Create artifact
       - Update registry
       - Verify installation

    5. UPDATE registry:
       python registry.py modify {item.id} status=active

    6. VERIFY:
       python prompt.py execute verify {item.id}
       IF verification fails:
           WARN "Installation incomplete"
           SET status=draft
```

### Step 3: Generate Report

```
PRINT "Installation Summary"
PRINT "===================="
FOR EACH item IN items:
    IF item.status == "active":
        PRINT "[✓] {item.id}: {item.name}"
    ELSE:
        PRINT "[✗] {item.id}: {item.name} - {item.error}"

PRINT ""
PRINT "Installed: {success_count}/{total_count}"
```

---

## Success Criteria

- [ ] All selected frameworks processed
- [ ] Dependencies installed before dependents
- [ ] Artifacts created at artifact_path
- [ ] Registry statuses updated
- [ ] Verify prompt passes for each item

---

## Error Handling

| Error | Action |
|-------|--------|
| Dependency not active | Skip item, continue with others |
| Artifact already exists | Ask to overwrite or skip |
| Creation fails | Set status=missing, report error |
| Verification fails | Set status=draft, continue |
| Circular dependency | Abort with error |

---

## Example Session

```bash
$ python prompt.py execute install FMWK-001

Executing INSTALL for FMWK-001
======================================================================
Item:     Repo OS Spec
Registry: Control_Plane/registries/frameworks_registry.csv
Prompt:   Control_Plane/control_plane/prompts/install.md
Status:   missing

--- Prompt Instructions ---
[install.md content shown]

--- Item Context ---
  framework_id: FMWK-001
  name: Repo OS Spec
  artifact_path: /runbooks/governance/repo_os_spec.md
  dependencies:

======================================================================
Execute this prompt with the item context above.
After completion, update the registry status accordingly.

# Agent creates the artifact...

$ python registry.py modify FMWK-001 status=active
Modified: FMWK-001
  status: 'missing' → 'active'

$ python prompt.py execute verify FMWK-001
[Verification output...]
```

---

## Batch Mode

For automated installation of all selected items:

```bash
# Generate plan
python Control_Plane/scripts/apply_selection.py

# View plan
cat Control_Plane/generated/plan.json | python -m json.tool

# Install each item (manual loop)
for id in $(jq -r '.items[].id' Control_Plane/generated/plan.json); do
    echo "Installing $id..."
    python Control_Plane/scripts/prompt.py execute install $id
done
```

---

## Post-Installation

After all frameworks installed:
1. Run `python prompt.py validate` to check all prompts
2. Run `python registry.py list` to verify statuses
3. Run `python nested.py tree` to see full registry tree
4. Commit changes to git
