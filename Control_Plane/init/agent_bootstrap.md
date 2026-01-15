# Agent Bootstrap

**Source of truth for all LLM agent governance.**

---

## Boot Sequence

```bash
python Control_Plane/scripts/init.py
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

## Critical Rules

| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registries are source of truth |
| P002 | Validate before commit |
| P003 | Names are primary, IDs are reference |

---

## Commands

| Task | Command |
|------|---------|
| Boot | `python Control_Plane/scripts/init.py` |
| List items | `python Control_Plane/scripts/registry.py list <registry>` |
| Show item | `python Control_Plane/scripts/registry.py show <ID>` |
| Install | `python Control_Plane/scripts/prompt.py execute install <ID>` |
| Verify | `python Control_Plane/scripts/prompt.py execute verify <ID>` |
| Check deps | `python Control_Plane/scripts/link.py check` |

---

## Install Flow

```bash
# 1. Select
python Control_Plane/scripts/registry.py modify <ID> selected=yes

# 2. Plan
python Control_Plane/scripts/apply_selection.py

# 3. Execute
python Control_Plane/scripts/prompt.py execute install <ID>

# 4. (Create artifact following prompt)

# 5. Update
python Control_Plane/scripts/registry.py modify <ID> status=active
```

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
