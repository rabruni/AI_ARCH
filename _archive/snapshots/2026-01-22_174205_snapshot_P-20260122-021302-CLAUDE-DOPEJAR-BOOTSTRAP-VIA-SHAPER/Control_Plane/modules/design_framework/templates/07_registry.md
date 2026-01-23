# Registry Entry

**Spec:** {{SPEC_NAME}} ({{SPEC_ID}})

---

## Primary Registry Entry

Add this row to `Control_Plane/registries/control_plane_registry.csv`:

| Field | Value |
|-------|-------|
| id | {{SPEC_ID}} |
| name | {{SPEC_NAME}} |
| entity_type | {{framework / module / prompt / script}} |
| category | {{Category}} |
| purpose | {{One-line purpose}} |
| artifact_path | {{/path/to/artifact}} |
| status | missing |
| selected | no |
| priority | {{P0 / P1 / P2 / P3}} |
| dependencies | {{comma-separated IDs}} |
| version | 1.0.0 |
| config | {{JSON config if needed}} |

---

## Dependent Registry Entries

### Entry 1: {{Name}}

| Field | Value |
|-------|-------|
| id | {{ID}} |
| name | {{Name}} |
| entity_type | {{Type}} |
| artifact_path | {{Path}} |
| status | missing |
| dependencies | {{SPEC_ID}} |

---

## Artifact Paths

| Artifact | Path | Description |
|----------|------|-------------|
| Main | `{{path}}` | Primary deliverable |
| Config | `{{path}}` | Configuration |
| Tests | `{{path}}` | Test files |

---

## Installation Sequence

Based on dependencies, install in this order:

1. {{Dependency 1}} (if not active)
2. {{Dependency 2}} (if not active)
3. **{{SPEC_ID}}** (this item)

---

## Verification Commands

```bash
# Verify registry entry
python3 Control_Plane/scripts/registry.py show {{SPEC_ID}}

# Verify dependencies
python3 Control_Plane/scripts/link.py deps {{SPEC_ID}}

# Verify artifact exists
ls -la {{artifact_path}}
```

---

## Post-Installation

After artifact is created:

```bash
# Mark as active
python3 Control_Plane/scripts/registry.py modify {{SPEC_ID}} status=active

# Regenerate plan
python3 Control_Plane/scripts/apply_selection.py

# Verify
python3 Control_Plane/cp.py verify {{SPEC_ID}}
```
