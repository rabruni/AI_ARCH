# Agent System Prompt: Design Framework

**Purpose:** Guide AI agents through the spec pack creation and validation process.

---

## Context

You are working within a Control Plane governed repository. All features must be specified using spec packs before implementation.

**Core Principle:** No code without spec. No merge without validation.

---

## Spec Pack Structure

A spec pack consists of 8 files in `docs/specs/{{SPEC_ID}}/`:

| File | Purpose | Required |
|------|---------|----------|
| `00_overview.md` | Summary, scope, success criteria | Yes |
| `01_problem.md` | Problem statement and impact | Yes |
| `02_solution.md` | Proposed solution and alternatives | Yes |
| `03_requirements.md` | Functional and non-functional requirements | Yes |
| `04_design.md` | Technical architecture and design | Yes |
| `05_testing.md` | Test strategy and cases | Yes |
| `06_rollout.md` | Deployment and rollback plan | Yes |
| `07_registry.md` | Registry entries for artifacts | Yes |

---

## Creating a Spec Pack

### Step 1: Initialize

```bash
python3 Control_Plane/scripts/apply_spec_pack.py --target {{SPEC_ID}}
```

This creates the directory structure with templates.

### Step 2: Fill Templates

Replace all `{{PLACEHOLDER}}` values with actual content.

**Validation markers to remove:**
- `{{...}}` - Template placeholders
- `TBD` - To be determined
- `TODO` - Incomplete sections

### Step 3: Validate

```bash
python3 Control_Plane/scripts/validate_spec_pack.py --target {{SPEC_ID}}
```

**Exit codes:**
- 0 = Valid
- 1 = Invalid (missing files or placeholders)
- 2 = Target not found

### Step 4: Registry Entry

Add the spec pack to the registry:

```bash
python3 Control_Plane/scripts/registry.py add control_plane \
  id={{SPEC_ID}} \
  name="{{SPEC_NAME}}" \
  entity_type=framework \
  category=Spec \
  artifact_path=/docs/specs/{{SPEC_ID}}/ \
  status=draft \
  selected=yes
```

---

## Validating All Spec Packs

```bash
python3 Control_Plane/scripts/validate_spec_pack.py --all
```

This validates every spec pack in `docs/specs/`.

---

## Agent Workflow

When asked to implement a feature:

1. **Check for spec pack**
   ```bash
   ls docs/specs/
   ```

2. **If no spec pack exists:**
   - Create one using `apply_spec_pack.py`
   - Fill out all 8 templates
   - Get user approval before proceeding

3. **If spec pack exists:**
   - Validate it: `validate_spec_pack.py --target {{ID}}`
   - Fix any validation errors
   - Proceed with implementation

4. **Before implementation:**
   - Ensure spec pack status is `approved`
   - Verify all dependencies are active
   - Create registry entries from `07_registry.md`

5. **After implementation:**
   - Update spec pack status to `implemented`
   - Verify against acceptance criteria in `03_requirements.md`
   - Run tests from `05_testing.md`

---

## Validation Rules

A spec pack is valid when:

1. All 8 files exist
2. No `{{placeholder}}` markers remain
3. No empty required sections
4. Registry entry in `07_registry.md` is complete
5. Dependencies listed are active or have their own spec packs

---

## Force Mode

Use `--force` to skip validation errors (not recommended):

```bash
python3 Control_Plane/scripts/apply_spec_pack.py --target {{ID}} --force
```

This is only for exceptional cases where validation must be bypassed.

---

## Integration with Control Plane

Spec packs integrate with the Control Plane:

- **Registry:** Each spec pack has a registry entry
- **Dependencies:** Spec packs can depend on other items
- **Status:** draft → review → approved → implemented
- **Verification:** `cp verify` checks spec pack artifacts

---

## Example Session

```
User: "Add user authentication feature"

Agent:
1. Check: No spec pack exists for authentication
2. Create: apply_spec_pack.py --target AUTH-001
3. Fill: Complete all 8 templates
4. Present: "Here is the spec pack for authentication..."
5. Wait: User approval
6. Validate: validate_spec_pack.py --target AUTH-001
7. Implement: Follow design in 04_design.md
8. Test: Execute plan from 05_testing.md
9. Deploy: Follow 06_rollout.md
10. Update: Mark spec pack as implemented
```
