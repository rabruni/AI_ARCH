# Technical Design

**Spec:** Design Framework Integration (PROOF-001)

---

## Architecture

### Overview

The gate system consists of two Python scripts (gate.py and validate_spec_pack.py) that validate spec packs. The unified CLI (cp.py) provides the user interface. All scripts use Control_Plane.lib for path resolution.

### Component Diagram

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│   cp.py     │────▶│   gate.py   │────▶│validate_spec_pack│
│  (CLI)      │     │ (G0/G1)     │     │    .py (G1)      │
└─────────────┘     └─────────────┘     └──────────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       └───────────▶│apply_spec   │
                    │  _pack.py   │
                    └─────────────┘
```

---

## Data Model

### Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| Spec Pack | Directory with 8 spec files | id, path, status |
| Gate Log | Timestamped gate result | gate, target, status, timestamp |

### Directory Structure

```
Control_Plane/docs/specs/<run_id>/
├── 00_overview.md       # Vision, scope
├── 01_problem.md        # Goals, constraints
├── 02_solution.md       # Approach, decisions
├── 03_requirements.md   # Functional/non-functional
├── 04_design.md         # Architecture, API
├── 05_testing.md        # Test strategy
├── 06_rollout.md        # Deployment plan
├── 07_registry.md       # Registry entries
└── artifacts/
    └── gate_logs/       # G0/G1 execution logs
```

---

## API Design

### CLI Commands

| Command | Description |
|---------|-------------|
| `cp apply-spec --target ID` | Create spec pack |
| `cp gate G0 ID` | Run G0 gate |
| `cp gate G1 ID` | Run G1 gate |
| `cp gate --all ID` | Run all gates |
| `cp validate-spec ID` | Validate spec pack |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success / Pass |
| 1 | Failure / Fail |
| 2 | Target not found |
| 3 | Invalid arguments |

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `Control_Plane/scripts/gate.py` | Create | G0/G1 gate implementation |
| `Control_Plane/scripts/apply_spec_pack.py` | Modify | Update SPECS_DIR path |
| `Control_Plane/scripts/validate_spec_pack.py` | Modify | Update SPECS_DIR path |
| `Control_Plane/cp.py` | Modify | Add gate and apply-spec commands |
| `Control_Plane/modules/design_framework/README.md` | Modify | Add end-to-end documentation |
| `Control_Plane/modules/design_framework/_archive/` | Create | Archive deprecated templates |

---

## Dependencies

### Internal
- Control_Plane.lib (REPO_ROOT, CONTROL_PLANE paths)
- validate_spec_pack.py (G1 delegates to this)

### External
- Python 3.x standard library only (pathlib, subprocess, re, argparse)

---

## Security Considerations

- Scripts only read/write within Control_Plane/docs/specs/
- No external network calls
- No execution of user-provided code

---

## Performance Considerations

- Gate execution is file-based, O(n) on file count
- Log writes are append-only
- No caching required

---

## Backwards Compatibility

- Old spec packs at docs/specs/ will not be found (must migrate to Control_Plane/docs/specs/)
- Inner spec_pack/ templates archived; existing references may need update
