# Verify Selected Frameworks Meta-Prompt

**ID:** PRMPT-012
**Purpose:** Verify all selected frameworks and update their status/evidence.

---

## Overview

This meta-prompt runs verification checks on all installed frameworks. It validates artifacts exist, content matches purpose, dependencies are satisfied, and updates registry evidence.

---

## Prerequisites

Before running this prompt:
- [ ] Control Plane bootstrapped (`init.py` passes)
- [ ] Frameworks installed (`status=active` or `status=draft`)
- [ ] Verify prompt available (`Control_Plane/control_plane/prompts/verify.md`)

---

## Procedure

### Step 1: Load Registry

```python
import csv

registry_path = "Control_Plane/registries/frameworks_registry.csv"
with open(registry_path) as f:
    reader = csv.DictReader(f)
    frameworks = [r for r in reader if r.get("selected") == "yes"]
```

### Step 2: Verify Each Framework

```
FOR EACH framework IN frameworks:
    1. PRINT "Verifying {framework.id}: {framework.name}"

    2. CHECK artifact exists:
       IF NOT exists(framework.artifact_path):
           SET status=missing
           CONTINUE

    3. CHECK content:
       - Read artifact content
       - Verify matches framework.purpose
       - Check for required sections/structure

    4. CHECK dependencies:
       FOR EACH dep IN framework.dependencies:
           IF dep.status != "active":
               WARN "Dependency {dep} not active"

    5. RECORD evidence:
       - File exists: yes/no
       - Content valid: yes/no
       - Dependencies met: yes/no
       - Last verified: timestamp

    6. UPDATE status:
       IF all checks pass:
           SET status=active
           SET validation=ci  # or manual, none
       ELSE:
           SET status=draft
           RECORD failures in notes
```

### Step 3: Generate Report

```
Verification Summary
====================

[✓] FMWK-001: Repo OS Spec
    - Artifact: exists
    - Content: valid
    - Dependencies: met

[⚠] FMWK-002: Prompt Governance Framework
    - Artifact: exists
    - Content: incomplete (missing versioning section)
    - Dependencies: met

[✗] FMWK-003: Change Control & Release Process
    - Artifact: missing
    - Dependencies: N/A

--------------------------------------------------
Verified: 15/20
Active: 12
Draft: 3
Missing: 5
```

---

## Success Criteria

- [ ] All selected frameworks verified
- [ ] Artifacts validated for existence
- [ ] Content checked against purpose
- [ ] Dependencies validated
- [ ] Registry statuses updated
- [ ] Evidence recorded

---

## Verification Checks

### 1. Existence Check
```python
from pathlib import Path
artifact_path = Path(framework.get("artifact_path", ""))
exists = artifact_path.is_file()
```

### 2. Content Check
```python
content = artifact_path.read_text()
checks = [
    "# " in content,  # Has header
    len(content) > 100,  # Minimum content
    framework["name"].lower() in content.lower(),  # Name mentioned
]
valid = all(checks)
```

### 3. Dependency Check
```python
deps = framework.get("dependencies", "").split(",")
for dep_id in deps:
    dep = find_by_id(dep_id)
    if dep.get("status") != "active":
        return False
return True
```

---

## Error Handling

| Issue | Action |
|-------|--------|
| Artifact missing | Set status=missing |
| Content incomplete | Set status=draft, note issues |
| Dependency not active | Warn, mark as blocked |
| Permission denied | Report error, skip |

---

## Example Session

```bash
$ python prompt.py execute verify FMWK-001

Executing VERIFY for FMWK-001
======================================================================
Item:     Repo OS Spec
Registry: Control_Plane/registries/frameworks_registry.csv
Status:   active

--- Verification Checks ---

[✓] Artifact exists: /runbooks/governance/repo_os_spec.md
[✓] Content valid: 2,456 bytes, 3 sections
[✓] Dependencies: none required
[✓] Last modified: 2026-01-15T10:30:00Z

Result: PASS

$ python registry.py modify FMWK-001 validation=ci last_updated=2026-01-15
Modified: FMWK-001
```

---

## Batch Verification

```bash
# Verify all selected frameworks
for id in $(grep ",yes," Control_Plane/registries/frameworks_registry.csv | cut -d',' -f3); do
    echo "Verifying $id..."
    python Control_Plane/scripts/prompt.py execute verify $id
done

# Quick validation summary
python Control_Plane/scripts/registry.py list Control_Plane/registries/frameworks_registry.csv
```

---

## CI Integration

For automated verification in CI:

```yaml
- name: Verify Frameworks
  run: |
    python Control_Plane/scripts/init.py
    python Control_Plane/scripts/prompt.py validate
    # Add custom verification logic as needed
```

---

## Post-Verification

After verification:
1. Review items with `status=draft` - fix or document issues
2. Review items with `status=missing` - install or remove from selection
3. Update `validation` field: `none`, `manual`, `ci`
4. Commit registry updates
