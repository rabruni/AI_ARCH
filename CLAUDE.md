# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## First: Registration

**Ask the user:**

> "This repository uses a Control Plane for managing state and configuration. Would you like to register this CLI session with the project?"

If **yes**, run the registration flow below.
If **no**, proceed with caution - you may not have full context.

---

## Registration Flow

### Step 1: Boot
```bash
python3 Control_Plane/scripts/init.py
```

Confirm all 3 layers pass:
```
LAYER 1: BOOTSTRAP     [PASS]
LAYER 2: VALIDATE      [PASS]
LAYER 3: INIT          [PASS]
✓ Ready to receive commands.
```

### Step 2: Read the Spec
```bash
Read: Control_Plane/CONTROL_PLANE_SPEC.md
```

Understand:
- Registry is source of truth
- One registry: `Control_Plane/registries/control_plane_registry.csv`
- Use NAMES for lookups, not IDs (P003)
- Four verbs: install, update, verify, uninstall

### Step 3: Confirm
Tell the user:
> "Registration complete. I've booted the Control Plane and understand the registry-driven workflow. Ready to receive commands."

---

## Quick Reference (Post-Registration)

### Commands
```bash
# List everything
python3 Control_Plane/scripts/registry.py list control_plane

# Show item by name
python3 Control_Plane/scripts/registry.py show "Definition of Done"

# Modify item
python3 Control_Plane/scripts/registry.py modify "Local Dev Harness" selected=yes

# Check dependencies
python3 Control_Plane/scripts/link.py check
```

### Install Flow
```bash
# 1. Select
python3 Control_Plane/scripts/registry.py modify "Local Dev Harness" selected=yes

# 2. Execute install prompt
python3 Control_Plane/scripts/prompt.py execute install "Local Dev Harness"

# 3. Create the artifact (follow the prompt)

# 4. Mark active
python3 Control_Plane/scripts/registry.py modify "Local Dev Harness" status=active
```

### Critical Rules
| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | Names are primary, IDs are reference |

### Commit Format
```
<type>: <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`

### Protected Paths
- `/_archive/` - no delete
- `/SYSTEM_CONSTITUTION.md` - confirm before modify
- `/Control_Plane/registries/` - validate after changes
