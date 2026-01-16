# Design Framework Module

**ID:** MOD-DFW-001
**Status:** active
**Version:** 1.0.0

---

## Purpose

Enforce structured specification before implementation through 8-file spec packs.

**Core Principle:** No code without spec. No merge without validation.

---

## Structure

```
Control_Plane/modules/design_framework/
├── README.md                    # This file
├── templates/                   # 8-file spec pack templates
│   ├── 00_overview.md
│   ├── 01_problem.md
│   ├── 02_solution.md
│   ├── 03_requirements.md
│   ├── 04_design.md
│   ├── 05_testing.md
│   ├── 06_rollout.md
│   └── 07_registry.md
└── PROMPTS/
    └── agent_system.md          # Agent instructions
```

---

## Usage

### Create New Spec Pack

```bash
python3 Control_Plane/scripts/apply_spec_pack.py --target FEAT-001
```

Creates `docs/specs/FEAT-001/` with all 8 template files.

### Validate Spec Pack

```bash
# Single spec pack
python3 Control_Plane/scripts/validate_spec_pack.py --target FEAT-001

# All spec packs
python3 Control_Plane/scripts/validate_spec_pack.py --all
```

### Via Unified CLI

```bash
# Validate all
python3 Control_Plane/cp.py validate-spec --all

# Validate specific
python3 Control_Plane/cp.py validate-spec --target FEAT-001
```

---

## Spec Pack Files

| File | Purpose |
|------|---------|
| `00_overview.md` | Summary, scope, success criteria, timeline |
| `01_problem.md` | Problem statement, impact, root cause |
| `02_solution.md` | Proposed solution, alternatives, risks |
| `03_requirements.md` | Functional/non-functional requirements |
| `04_design.md` | Architecture, API, data model |
| `05_testing.md` | Test strategy, cases, coverage |
| `06_rollout.md` | Deployment plan, rollback, verification |
| `07_registry.md` | Registry entries for artifacts |

---

## Validation Rules

A spec pack is **valid** when:

1. All 8 required files exist
2. No `{{placeholder}}` markers remain
3. No standalone `TBD` or `TODO` markers
4. Files have meaningful content (>50 chars)

---

## Exit Codes

### apply_spec_pack.py

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Target already exists (use --force) |
| 2 | Template files not found |
| 3 | Invalid arguments |

### validate_spec_pack.py

| Code | Meaning |
|------|---------|
| 0 | Valid |
| 1 | Invalid (errors found) |
| 2 | Target not found |
| 3 | Invalid arguments |

---

## CI Integration

The CI workflow runs:

```yaml
- name: Validate Spec Packs
  run: python3 Control_Plane/scripts/validate_spec_pack.py --all
```

This ensures all spec packs are complete before merge.

---

## Workflow

1. **Propose:** Create spec pack with `apply_spec_pack.py`
2. **Document:** Fill out all 8 files
3. **Review:** Get approval on spec pack
4. **Validate:** Run `validate_spec_pack.py`
5. **Implement:** Follow the spec
6. **Verify:** Run tests from `05_testing.md`
7. **Deploy:** Follow `06_rollout.md`

---

## Metadata

```yaml
module_id: MOD-DFW-001
name: Design Framework Module
version: 1.0.0
status: active
artifact_path: /Control_Plane/modules/design_framework/README.md
```
