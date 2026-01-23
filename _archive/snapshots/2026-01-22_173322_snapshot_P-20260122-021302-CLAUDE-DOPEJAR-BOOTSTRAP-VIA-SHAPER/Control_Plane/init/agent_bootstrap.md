# Agent Bootstrap

**Source of truth for all LLM agent governance.**

---

## Boot Sequence

```bash
python3 Control_Plane/scripts/init.py
```

Expected output:
```
LAYER 1: BOOTSTRAP     [PASS]
LAYER 2: VALIDATE      [PASS]
LAYER 3: INIT          [PASS]

✓ Ready to receive commands.
```

If any layer fails, fix before proceeding.

---

## The Registry

**One registry. One file. One source of truth.**

```
Control_Plane/registries/control_plane_registry.csv
```

| Column | Purpose |
|--------|---------|
| id | Primary key (FMWK-001, MOD-001, PRMPT-001, etc.) |
| name | Human readable name |
| entity_type | framework, module, component, prompt, cloud |
| category | Grouping (Governance, Memory, Harness, etc.) |
| purpose | One-line description |
| artifact_path | Where the artifact lives |
| status | missing, draft, active |
| selected | yes, no |
| priority | P0, P1, P2 |
| dependencies | Comma-separated IDs |
| version | Semantic version |
| config | JSON for entity-specific fields |

**Filter by entity_type to find what you need:**
```bash
# List all frameworks
python3 Control_Plane/scripts/registry.py list control_plane | grep framework

# Or use the specialized tools:
python3 Control_Plane/scripts/prompt.py list     # prompts only
python3 Control_Plane/scripts/module.py list     # modules only
```

---

## Critical Rules

| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | ID is primary key; names for convenience |

---

## Commands

| Task | Command |
|------|---------|
| Boot | `python3 Control_Plane/scripts/init.py` |
| List all | `python3 Control_Plane/scripts/registry.py list control_plane` |
| Show item | `python3 Control_Plane/scripts/registry.py show <ID>` |
| Install | `python3 Control_Plane/scripts/prompt.py execute install <ID>` |
| Verify | `python3 Control_Plane/scripts/prompt.py execute verify <ID>` |
| Check deps | `python3 Control_Plane/scripts/link.py check` |

---

## Install Flow

```bash
# 1. Select
python3 Control_Plane/scripts/registry.py modify <ID> selected=yes

# 2. Plan
python3 Control_Plane/scripts/apply_selection.py

# 3. Execute
python3 Control_Plane/scripts/prompt.py execute install <ID>

# 4. (Create artifact following prompt)

# 5. Update
python3 Control_Plane/scripts/registry.py modify <ID> status=active
```

---

## Verb Prompts (Standardized)

All items use the same 4 verb prompts:

| Verb | Path |
|------|------|
| install | Control_Plane/control_plane/prompts/install.md |
| update | Control_Plane/control_plane/prompts/update.md |
| verify | Control_Plane/control_plane/prompts/verify.md |
| uninstall | Control_Plane/control_plane/prompts/uninstall.md |

---

## Protected Paths

| Path | Rule |
|------|------|
| `/_archive/` | no_delete |
| `/SYSTEM_CONSTITUTION.md` | confirm_modify |
| `/Control_Plane/registries/` | validate_after |

---

## Commit Format

```
<type>: <description>

Co-Authored-By: <Agent> <email>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`
