# CLAUDE.md

**Purpose:** Pin LLM behavior to Control Plane standards across sessions.
**Version:** 1.0.0
**Audience:** Claude, GPT-4, and other LLM agents

---

## Bootstrap (Do This First)

```
1. READ /Control_Plane/init/init.md
2. FOLLOW the 10-step boot sequence
3. ONLY THEN proceed with commands
```

---

## Critical Rules

### P000: Always Bootstrap First
Before taking any action in this repository, read and execute `/Control_Plane/init/init.md`. This ensures you understand the system structure and governance rules.

### P001: Registries Are Truth
- Every artifact MUST be tracked in a registry
- If it's not in a registry, it doesn't officially exist
- Update registries BEFORE or AFTER modifying artifacts, never skip

### P002: Validate Before Commit
- ALWAYS run `python Control_Plane/scripts/validate_registry.py` before committing
- If validation fails, fix issues first
- Never commit with validation errors

### P003: ID Is Primary Key
- All lookups by ID (e.g., FMWK-001, ROS-P001)
- Names are for human display only
- Never use names as identifiers in code

---

## Protected Artifacts

| Path | Protection | Reason |
|------|------------|--------|
| `/_archive/` | no_delete | Historical record and rollback |
| `/SYSTEM_CONSTITUTION.md` | confirm_modify | Canonical governance rules |
| `/Control_Plane/registries/` | validate_after | Source of truth |
| `/Control_Plane/init/` | no_delete | Bootstrap capability |
| `/Control_Plane/modules/repo_os/prompts/v1/` | no_modify | Immutable v1 prompts |

---

## Required First Reads

Before taking significant actions, read:
1. `/SYSTEM_CONSTITUTION.md` — Canonical rules
2. `/Control_Plane/init/init.md` — Bootstrap procedure
3. `/Control_Plane/control_plane/CONTROL_PLANE_CONTRACT.md` — Registry contract

---

## Standard Operations

### To Create a New Item
```
1. Add row to appropriate registry (selected=no, status=missing)
2. Run validate_registry.py
3. Create artifact at artifact_path
4. Update registry: status=draft or status=active
5. Set selected=yes when ready for use
6. Run validate_registry.py again
7. Commit
```

### To Update an Existing Item
```
1. Find item by ID in registry
2. Read current artifact
3. Make changes
4. Update last_updated in registry
5. Run validate_registry.py
6. Commit
```

### To Execute the Plan
```
1. Run: python Control_Plane/scripts/apply_selection.py
2. Read: Control_Plane/generated/plan.json
3. For each item in order:
   a. Read the item's install_prompt_path (if exists)
   b. Execute the installation/update
   c. Run verify_prompt_path to confirm
   d. Update registry status
4. Commit when complete
```

### To Archive and Reset
```
1. Follow Safe Reset Protocol in SYSTEM_CONSTITUTION.md
2. Archive to /_archive/<YYYY-MM-DD>/
3. Write ARCHIVE_README.md
4. Re-run /init from clean state
```

---

## Conventions

### Commit Messages
```
feat: Add new feature
fix: Fix a bug
docs: Documentation changes
chore: Maintenance tasks
refactor: Code restructuring

Always end with:
Co-Authored-By: Claude <noreply@anthropic.com>
```

### File Naming
- Registries: `*_registry.csv`
- Prompts: `snake_case.md`
- Scripts: `snake_case.py`

### Registry Updates
- Always update `last_updated` when modifying items
- Use ISO 8601 timestamps
- Keep `registry_version` current

---

## Guardrails

### Before Any Modification
```
[ ] Item exists in registry (or will be added)
[ ] Dependencies are satisfied
[ ] Path is within allowed boundaries
[ ] Not modifying protected artifact without confirmation
```

### Before Committing
```
[ ] validate_registry.py passes
[ ] No secrets in files
[ ] Registry updated for any new/modified artifacts
[ ] Commit message follows convention
```

---

## Error Recovery

### If Validation Fails
1. Read the error message carefully
2. Fix the specific issue
3. Re-run validator
4. Do not proceed until green

### If Lost or Confused
1. Re-read `/Control_Plane/init/init.md`
2. Run validator to check current state
3. Generate fresh plan with apply_selection.py
4. Ask user for clarification if needed

---

## Determinism Anchors

To ensure consistent behavior across sessions:
- Always use absolute paths from repo root
- Always reference items by ID, not name
- Always validate before committing
- Always follow the plan order
- Always update registries when changing artifacts

---

## Metadata

```yaml
version: 1.0.0
created: 2026-01-14
regeneration_prompt: /Control_Plane/modules/repo_os/prompts/v1/03_claude_reliability_anchor.md
schema: /Control_Plane/init/CLAUDE_md_schema.json
```
