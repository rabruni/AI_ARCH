# Update Prompt

**Purpose:** Modify an existing artifact defined by a registry row.

---

## Input Context

You receive a registry row with these fields:
- `id`: Item identifier
- `name`: Human-readable name
- `purpose`: What this item does
- `artifact_path`: Where the artifact lives
- `status`: Current status (should be "active" or "draft")
- `version_current`: Current version
- `version_target`: Target version (if upgrade)

Plus:
- `update_reason`: Why the update is needed
- `changes_requested`: Specific changes to make

---

## Procedure

### Step 1: Verify Item Exists
```
IF NOT EXISTS item.artifact_path:
  ABORT: "Artifact not found at {artifact_path}"
  SUGGEST: "Run install prompt first"
```

### Step 2: Read Current Content
```
current_content = READ item.artifact_path
UNDERSTAND current structure and purpose
```

### Step 3: Plan Changes
```
Based on changes_requested:
  - Identify sections to modify
  - Preserve sections not being changed
  - Maintain consistent style
  - Keep header/metadata intact
```

### Step 4: Apply Changes
```
WRITE updated content to artifact_path
PRESERVE:
  - File structure
  - ID references
  - Dependency declarations
```

### Step 5: Update Registry
```
UPDATE registry row:
  last_updated = NOW()
  version_current = version_target (if version change)
  notes = append update reason
```

### Step 6: Verify Update
```
RUN verify prompt for this item
IF verification fails:
  WARN: "Update may have issues"
  CONSIDER rollback
```

---

## Success Criteria

- [ ] Changes applied correctly
- [ ] Original structure preserved
- [ ] Registry updated with timestamp
- [ ] Validator passes
- [ ] Verify prompt succeeds

---

## Error Handling

| Error | Action |
|-------|--------|
| Artifact not found | Abort, suggest install |
| Parse error | Abort, report issue |
| Verification fails | Warn, suggest review |
| Breaking change | Require confirmation |

---

## Example

```
Input:
  id: FMWK-001
  name: Repo OS Spec
  artifact_path: /runbooks/governance/repo_os_spec.md
  status: active
  update_reason: Add new directory requirement
  changes_requested: Add /Control_Plane/init/ to required directories

Action:
  1. Read current repo_os_spec.md
  2. Find "Required Directories" section
  3. Add /Control_Plane/init/ to list
  4. Write updated file
  5. Update registry: last_updated=now
  6. Run verify - passes

Output:
  Updated FMWK-001 (Repo OS Spec) - added init directory requirement
```
