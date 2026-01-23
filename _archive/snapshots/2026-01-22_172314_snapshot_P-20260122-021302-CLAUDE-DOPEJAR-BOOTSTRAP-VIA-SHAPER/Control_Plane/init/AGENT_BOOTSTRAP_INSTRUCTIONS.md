# Agent Bootstrap Instructions

**Purpose:** Tell a fresh agent how to configure itself for this repository.

---

## What You Need To Do

1. **Identify your agent file** (one of these):
   - Claude Code → `CLAUDE.md`
   - Gemini → `GEMINI.md`
   - Codex → `AGENTS.md`
   - Other → `AGENTS.md`

2. **Append the boot instructions below** to your agent file.

3. **Run the boot sequence** immediately after.

---

## Content To Append

Copy this section and append it to your agent file:

```markdown
## On Startup: Boot the Control Plane

**Run this immediately when starting a session:**

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

Then read: `Control_Plane/CONTROL_PLANE_SPEC.md`

---

## Key Concepts

- **Registry is source of truth:** `Control_Plane/registries/control_plane_registry.csv`
- **Use NAMES for lookups, not IDs** (P003)
- **Four verbs:** install, update, verify, uninstall

---

## Commands

```bash
# List everything
python3 Control_Plane/scripts/registry.py list control_plane

# Show item by name
python3 Control_Plane/scripts/registry.py show "Definition of Done"

# Modify item
python3 Control_Plane/scripts/registry.py modify "Local Dev Harness" selected=yes
```

---

## Critical Rules

| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | ID is primary key; names for convenience |
```

---

## After Appending

1. Run: `python3 Control_Plane/scripts/init.py`
2. Confirm all 3 layers pass
3. Read: `Control_Plane/CONTROL_PLANE_SPEC.md`
4. You're ready to work

---

## Commit Suffix By Agent

When committing, use the appropriate suffix:

| Agent | Suffix |
|-------|--------|
| Claude | `Co-Authored-By: Claude <noreply@anthropic.com>` |
| Gemini | `Co-Authored-By: Gemini <noreply@google.com>` |
| Codex | `Co-Authored-By: Codex <noreply@openai.com>` |
| Other | `Co-Authored-By: <Agent Name> <noreply@agent.ai>` |
