# Install Prompt

**Purpose:** Create a new artifact defined by a registry row.

---

## Input Context

You receive a registry row with these fields:
- `id`: Item identifier (e.g., FMWK-001)
- `name`: Human-readable name
- `purpose`: What this item does
- `artifact_path`: Where to create the artifact
- `dependencies`: Comma-separated list of dependency IDs
- `status`: Current status (should be "missing" for install)

---

## Procedure

### Step 1: Check Dependencies
```
FOR EACH dependency IN item.dependencies:
  FIND dependency in registries
  IF dependency.status != "active":
    ABORT: "Dependency {dependency} not installed"
```

### Step 2: Verify Path Available
```
IF EXISTS item.artifact_path:
  WARN: "Artifact already exists at {artifact_path}"
  ASK: "Overwrite? (yes/no)"
  IF no:
    ABORT
```

### Step 3: Create Artifact
```
Based on item.entity_type:
  - framework → Create runbook/policy document
  - prompt → Create prompt markdown file
  - script → Create Python/shell script
  - pack → Create directory + child registry
  - module → Create module directory + README

Content should:
  - Match the item.purpose
  - Include standard header with ID and name
  - Be immediately usable
```

### Step 4: Update Registry
```
UPDATE registry row:
  status = "active"
  last_updated = NOW()
```

### Step 5: Verify Installation
```
RUN verify prompt for this item
IF verification fails:
  WARN: "Installation may be incomplete"
  KEEP status = "draft"
```

---

## Success Criteria

- [ ] Artifact exists at artifact_path
- [ ] Content matches purpose
- [ ] Registry status updated to "active"
- [ ] Validator passes
- [ ] Verify prompt succeeds

---

## Error Handling

| Error | Action |
|-------|--------|
| Dependency missing | Abort, report which dependency |
| Path exists | Ask to overwrite or abort |
| Creation fails | Keep status=missing, report error |
| Verification fails | Set status=draft, report issues |

---

## Example

```
Input:
  id: FMWK-001
  name: Repo OS Spec
  purpose: Defines repo operating system structure
  artifact_path: /runbooks/governance/repo_os_spec.md
  dependencies: (none)
  status: missing

Action:
  1. No dependencies - proceed
  2. Path doesn't exist - proceed
  3. Create /runbooks/governance/repo_os_spec.md with governance content
  4. Update registry: status=active
  5. Run verify - passes

Output:
  Installed FMWK-001 (Repo OS Spec) at /runbooks/governance/repo_os_spec.md
```
