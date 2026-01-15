# GEMINI.md

**Purpose:** Governance rules for Google Gemini Code Assist.

---

## Boot Sequence (Do This First)

```
1. RUN:    python Control_Plane/scripts/init.py
2. VERIFY: All layers show [PASS]
3. READ:   Control_Plane/init/init.md
4. THEN:   Proceed with task
```

If any layer fails, fix before proceeding.

---

## Critical Rules

### P000: Always Bootstrap First
Before taking any action in this repository, run the init script and verify all checks pass.

### P001: Registries Are Truth
- Every artifact MUST be tracked in a registry
- If it's not in a registry, it doesn't officially exist
- Update registries BEFORE or AFTER modifying artifacts, never skip

### P002: Validate Before Commit
- ALWAYS run `python Control_Plane/scripts/init.py` before committing
- If validation fails, fix issues first
- Never commit with validation errors

### P003: ID Is Reference, Name Is Primary
- Names are for human display (primary)
- IDs are for lookups (shown in parentheses)
- Use IDs in commands: `registry.py show FMWK-001`

---

## Standard Operations

### To Install an Item
```bash
python Control_Plane/scripts/registry.py modify <ID> selected=yes
python Control_Plane/scripts/apply_selection.py
python Control_Plane/scripts/prompt.py execute install <ID>
# Create the artifact following the prompt
python Control_Plane/scripts/registry.py modify <ID> status=active
```

### To View Status
```bash
python Control_Plane/scripts/registry.py list frameworks
python Control_Plane/scripts/prompt.py list
python Control_Plane/scripts/module.py status
```

### To Check Dependencies
```bash
python Control_Plane/scripts/link.py check
python Control_Plane/scripts/link.py deps <ID>
```

---

## Commit Convention

```
feat: Add new feature
fix: Fix a bug
docs: Documentation changes
chore: Maintenance tasks

Always end with:
Co-Authored-By: Gemini <noreply@google.com>
```

---

## Protected Artifacts

| Path | Protection |
|------|------------|
| `/_archive/` | no_delete |
| `/SYSTEM_CONSTITUTION.md` | confirm_modify |
| `/Control_Plane/registries/` | validate_after |

---

## Quick Reference

| Task | Command |
|------|---------|
| Boot system | `python Control_Plane/scripts/init.py` |
| List registries | `python Control_Plane/scripts/registry.py list` |
| Show item | `python Control_Plane/scripts/registry.py show <ID>` |
| Install item | `python Control_Plane/scripts/prompt.py execute install <ID>` |
| Check deps | `python Control_Plane/scripts/link.py check` |
