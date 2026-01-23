# Design Framework Module

**ID:** MOD-DFW-001
**Status:** active
**Version:** 1.1.0

---

## Purpose

Enforce structured specification before implementation through 8-file spec packs with gate enforcement.

**Core Principle:** No code without spec. No merge without validation.

---

## Structure

```
Control_Plane/modules/design_framework/
├── README.md                    # This file
├── templates/                   # 8-file spec pack templates (CANONICAL)
│   ├── 00_overview.md
│   ├── 01_problem.md
│   ├── 02_solution.md
│   ├── 03_requirements.md
│   ├── 04_design.md
│   ├── 05_testing.md
│   ├── 06_rollout.md
│   └── 07_registry.md
├── PROMPTS/
│   └── agent_system.md          # Agent instructions
└── _archive/                    # Deprecated templates (do not use)
```

Spec packs are created at:
```
Control_Plane/docs/specs/<run_id>/
├── 00_overview.md
├── 01_problem.md
├── 02_solution.md
├── 03_requirements.md
├── 04_design.md
├── 05_testing.md
├── 06_rollout.md
├── 07_registry.md
└── artifacts/
    ├── gate_logs/               # Gate execution logs
    ├── outcomes.yaml            # Optional: workflow outputs
    ├── goals.yaml               # Optional: goal definitions
    └── plan.json                # Optional: execution plan
```

---

## End-to-End Control Plane Run (Vision → Validate)

This section proves the Control Plane can execute a complete workflow from Vision through Validation.

### Step 1: Create Spec Pack

```bash
python3 Control_Plane/cp.py apply-spec --target SPEC-001
# Or directly:
python3 Control_Plane/scripts/apply_spec_pack.py --target SPEC-001
```

Output: `Control_Plane/docs/specs/SPEC-001/` with all 8 template files and `artifacts/` directory.

### Step 2: Fill Out Spec Pack

Edit all 8 files to replace:
- All `{{placeholder}}` markers
- All `TBD` markers
- All `TODO` markers
- All `FILL IN` markers

The spec pack maps the workflow:
- **Vision → Goals**: `00_overview.md` (vision, success, scope) + `01_problem.md` (why, constraints)
- **Spec**: `02_solution.md`, `03_requirements.md`, `04_design.md`
- **Build → Validate**: `05_testing.md`, `06_rollout.md`, `07_registry.md`

### Step 3: Run G0 Gate (Goal Qualification)

```bash
python3 Control_Plane/cp.py gate G0 SPEC-001
```

G0 validates:
1. Directory exists at `Control_Plane/docs/specs/SPEC-001/`
2. All 8 canonical spec files exist
3. No file contains forbidden placeholders (TBD, TODO, FILL IN)

Exit codes: 0 = pass, 1 = fail, 2 = target missing

### Step 4: Run G1 Gate (Spec Validation)

```bash
python3 Control_Plane/cp.py gate G1 SPEC-001
```

G1 runs `validate_spec_pack.py` which checks:
- All 8 files exist
- No `{{placeholder}}` markers remain
- Files have meaningful content (>50 chars)

Exit codes: 0 = valid, 1 = invalid, 2 = not found

### Step 5: Run All Gates

```bash
python3 Control_Plane/cp.py gate --all SPEC-001
```

Runs G0 → G1 in sequence. Stops on first failure.

### Proof Statement

**If these commands pass, the Control Plane has proven Vision → Validate execution:**

```bash
python3 Control_Plane/scripts/apply_spec_pack.py --target SPEC-001
# [Fill out spec pack]
python3 Control_Plane/cp.py gate --all SPEC-001
# Exit code 0 = Proof complete
```

Gate logs are written to `Control_Plane/docs/specs/SPEC-001/artifacts/gate_logs/`.

---

## Spec Pack Files

| File | Purpose | Workflow Stage |
|------|---------|----------------|
| `00_overview.md` | Summary, scope, success criteria | Vision |
| `01_problem.md` | Problem statement, impact, constraints | Goals |
| `02_solution.md` | Proposed solution, alternatives, risks | Spec |
| `03_requirements.md` | Functional/non-functional requirements | Spec |
| `04_design.md` | Architecture, API, data model | Spec |
| `05_testing.md` | Test strategy, cases, coverage | Validate |
| `06_rollout.md` | Deployment plan, rollback, verification | Build |
| `07_registry.md` | Registry entries for artifacts | Build |

---

## Gates

### G0 — Goal Qualification

Structural validation gate. Ensures the spec pack exists and is complete.

**Validates:**
- Directory exists
- All 8 files present
- No forbidden placeholders (TBD, TODO, FILL IN)

**Does NOT validate:** Semantic quality, correctness, or completeness of content.

### G1 — Spec Validation

Content validation gate. Runs `validate_spec_pack.py`.

**Validates:**
- All 8 files exist
- No `{{placeholder}}` markers
- Files have meaningful content

### Gate Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Gate passed |
| 1 | Gate failed |
| 2 | Target missing or invalid |
| 3 | Invalid arguments |

---

## Usage

### Create New Spec Pack

```bash
python3 Control_Plane/scripts/apply_spec_pack.py --target FEAT-001
```

Creates `Control_Plane/docs/specs/FEAT-001/` with all 8 template files.

### Validate Spec Pack

```bash
# Single spec pack
python3 Control_Plane/scripts/validate_spec_pack.py --target FEAT-001

# All spec packs
python3 Control_Plane/scripts/validate_spec_pack.py --all
```

### Via Unified CLI

```bash
# Create spec pack
python3 Control_Plane/cp.py apply-spec --target FEAT-001

# Validate
python3 Control_Plane/cp.py validate-spec FEAT-001

# Run gates
python3 Control_Plane/cp.py gate G0 FEAT-001
python3 Control_Plane/cp.py gate G1 FEAT-001
python3 Control_Plane/cp.py gate --all FEAT-001
```

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

### gate.py

| Code | Meaning |
|------|---------|
| 0 | Gate passed |
| 1 | Gate failed |
| 2 | Target missing or invalid |
| 3 | Invalid arguments |

---

## CI Integration

The CI workflow should run:

```yaml
- name: Validate Spec Packs
  run: python3 Control_Plane/scripts/validate_spec_pack.py --all

- name: Run All Gates
  run: |
    for dir in Control_Plane/docs/specs/*/; do
      id=$(basename "$dir")
      python3 Control_Plane/cp.py gate --all "$id"
    done
```

---

## Metadata

```yaml
module_id: MOD-DFW-001
name: Design Framework Module
version: 1.1.0
status: active
artifact_path: /Control_Plane/modules/design_framework/README.md
```
