# Verify Prompt

**Purpose:** Validate that an artifact matches its registry definition and is functioning correctly.

---

## Input Context

You receive a registry row with these fields:
- `id`: Item identifier
- `name`: Human-readable name
- `purpose`: What this item should do
- `artifact_path`: Where the artifact should be
- `status`: Expected status
- `dependencies`: Required dependencies

---

## Procedure

### Step 1: Check Existence
```
IF NOT EXISTS item.artifact_path:
  FAIL: "Artifact not found at {artifact_path}"
  RETURN verification_failed
```

### Step 2: Check Content
```
content = READ item.artifact_path

VERIFY content includes:
  - Reference to item.id or item.name
  - Content that matches item.purpose
  - No placeholder text like "TODO" or "TBD" (unless draft)
  - No broken references or dead links
```

### Step 3: Check Dependencies
```
FOR EACH dependency IN item.dependencies:
  FIND dependency in registries
  IF dependency.status != "active":
    WARN: "Dependency {dependency} is {status}, not active"
```

### Step 4: Check Registry Consistency
```
VERIFY registry row has:
  - Non-empty id
  - Non-empty name
  - Valid status value
  - artifact_path matches actual file location
```

### Step 5: Run Type-Specific Checks
```
Based on item.entity_type:

  script:
    - Check file is executable or has shebang
    - Check syntax (python -m py_compile, bash -n, etc.)

  prompt:
    - Check has Purpose/Procedure sections
    - Check no sensitive data

  framework/runbook:
    - Check has clear structure
    - Check references exist

  registry:
    - Run validate_registry.py on it
```

---

## Success Criteria

- [ ] Artifact exists at artifact_path
- [ ] Content is non-empty and meaningful
- [ ] No placeholder content (unless draft)
- [ ] Dependencies are satisfied
- [ ] Registry entry is consistent
- [ ] Type-specific checks pass

---

## Output Format

```
Verification Report: {item.id}
================================
Name: {item.name}
Path: {artifact_path}
Status: {status}

Checks:
  [PASS] Artifact exists
  [PASS] Content matches purpose
  [PASS] Dependencies satisfied
  [WARN] Contains TODO markers
  [PASS] Registry consistent

Result: PASS (with warnings)
```

---

## Error Handling

| Finding | Severity | Action |
|---------|----------|--------|
| Artifact missing | ERROR | Fail verification |
| Empty content | ERROR | Fail verification |
| TODO markers | WARN | Pass with warning |
| Missing dependency | WARN | Pass with warning |
| Broken reference | ERROR | Fail verification |

---

## Example

```
Input:
  id: FMWK-001
  name: Repo OS Spec
  artifact_path: /runbooks/governance/repo_os_spec.md
  status: active

Checks:
  1. File exists at /runbooks/governance/repo_os_spec.md ✓
  2. Content describes repo structure ✓
  3. No dependencies to check ✓
  4. Registry row is valid ✓
  5. Markdown structure is correct ✓

Output:
  Verification PASSED for FMWK-001 (Repo OS Spec)
```
