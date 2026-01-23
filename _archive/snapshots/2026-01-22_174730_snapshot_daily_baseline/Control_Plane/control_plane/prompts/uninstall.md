# Uninstall Prompt

**Purpose:** Remove or disable an artifact and update its registry status.

---

## Input Context

You receive a registry row with these fields:
- `id`: Item identifier
- `name`: Human-readable name
- `artifact_path`: Where the artifact lives
- `status`: Current status
- `selected`: Should be "no" to trigger uninstall

Plus:
- `uninstall_reason`: Why uninstalling
- `preserve_artifact`: Whether to keep file but mark deprecated

---

## Procedure

### Step 1: Check for Dependents
```
SEARCH all registries for items that depend on this item

IF dependents found:
  LIST dependents
  WARN: "These items depend on {item.id}:"
  FOR EACH dependent:
    PRINT "  - {dependent.id}: {dependent.name}"

  ASK: "Uninstall anyway? (yes/no)"
  IF no:
    ABORT
```

### Step 2: Confirm Uninstall
```
PROMPT: "Uninstalling {item.id} ({item.name})"
PROMPT: "Reason: {uninstall_reason}"
PROMPT: "Artifact: {artifact_path}"
PROMPT: "Confirm? (yes/no)"

IF no:
  ABORT
```

### Step 3: Handle Artifact
```
IF preserve_artifact:
  # Keep file but add deprecation notice
  ADD header to artifact:
    "# DEPRECATED
    # This item was uninstalled on {DATE}
    # Reason: {uninstall_reason}
    # Do not use - kept for reference only"

ELSE:
  # Move to archive instead of deleting
  MOVE artifact_path TO /_archive/uninstalled/{DATE}/{filename}
  CREATE /_archive/uninstalled/{DATE}/manifest.json with:
    - original_path
    - uninstall_reason
    - uninstall_date
    - item_id
```

### Step 4: Update Registry
```
UPDATE registry row:
  status = "deprecated"
  selected = "no"
  last_updated = NOW()
  notes = append "Uninstalled: {uninstall_reason}"
```

### Step 5: Update Dependents (if proceeding)
```
FOR EACH dependent that was warned:
  WARN: "Check {dependent.id} for broken references"
```

---

## Success Criteria

- [ ] Dependents warned or resolved
- [ ] User confirmed uninstall
- [ ] Artifact archived (not deleted) or marked deprecated
- [ ] Registry updated to deprecated status
- [ ] Validator passes

---

## Error Handling

| Error | Action |
|-------|--------|
| Has active dependents | Warn, require confirmation |
| Artifact not found | Update registry only |
| Archive fails | Abort, keep artifact in place |
| Protected artifact | Abort, explain protection |

---

## Protected Items

These items cannot be uninstalled:
- `/Control_Plane/init/init.md` (bootstrap entry point)
- `/SYSTEM_CONSTITUTION.md` (canonical rules)
- Core registries in `/Control_Plane/registries/`

```
IF item is protected:
  ABORT: "Cannot uninstall protected item: {item.id}"
  EXPLAIN: "{protection_reason}"
```

---

## Example

```
Input:
  id: FMWK-050
  name: Knowledge Base Pattern
  artifact_path: /runbooks/knowledge/kb_pattern.md
  status: active
  selected: no
  uninstall_reason: Replaced by new documentation system
  preserve_artifact: false

Action:
  1. Check dependents - none found
  2. Confirm with user - yes
  3. Move file to /_archive/uninstalled/2026-01-14/kb_pattern.md
  4. Create manifest.json with details
  5. Update registry: status=deprecated, selected=no

Output:
  Uninstalled FMWK-050 (Knowledge Base Pattern)
  Archived to: /_archive/uninstalled/2026-01-14/kb_pattern.md
```
