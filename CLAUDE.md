# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## On Startup: Boot the Control Plane

**Run this immediately when starting a session:**

```bash
python3 Control_Plane/scripts/init.py
```

Expected output shows three layers passing:
```
LAYER 1: BOOTSTRAP     [PASS]
LAYER 2: VALIDATE      [PASS]
LAYER 3: INIT          [PASS]
✓ Ready to receive commands.
```

**After init completes, report status to user:**
```
═══════════════════════════════════════════════════
CONTROL PLANE STATUS
═══════════════════════════════════════════════════
  Registries: X loaded
  Selected:   X items
  Active:     X items
  Missing:    X items (to install)
  Mode:       BUILD | STABILIZE
  Plan:       Control_Plane/generated/plan.json
═══════════════════════════════════════════════════
```

**Recommendations based on mode:**
- **BUILD mode** (missing > 0): Review `plan.json`, install missing items in dependency order
- **STABILIZE mode** (all selected = active): System ready, focus on verification and improvements

If any layer fails, fix before proceeding.

Then read: `Control_Plane/CONTROL_PLANE_SPEC.md`

## Architecture

This repository implements a **registry-driven control plane** for AI agent governance.

### Core Concepts

- **Registry is source of truth**: `Control_Plane/registries/control_plane_registry.csv`
- **ID is primary key** (P003): IDs are canonical references; names accepted for human convenience
- **Four verbs**: install, update, verify, uninstall

### Directory Structure

| Directory | Purpose |
|-----------|---------|
| `Control_Plane/` | Registry system, scripts, and agent governance |
| `Control_Plane/registries/` | CSV registries (source of truth) |
| `Control_Plane/scripts/` | Python tools for registry operations |
| `Control_Plane/modules/` | Slot-based component implementations |
| `/src/` | Application source code |
| `/tests/` | Test files |
| `/docs/` | Architecture docs and ADRs |
| `/prompts/` | LLM prompts and templates |
| `/_archive/` | Read-only historical reference |

## Commands

**Unified CLI (recommended):**
```bash
python3 Control_Plane/cp.py init              # Full init (bootstrap + validate + plan)
python3 Control_Plane/cp.py status            # Show system status
python3 Control_Plane/cp.py list              # List all registries
python3 Control_Plane/cp.py list control_plane # List items in registry
python3 Control_Plane/cp.py show FMWK-001     # Show item by ID
python3 Control_Plane/cp.py show "Repo OS"    # Show item by name
python3 Control_Plane/cp.py install "Item"    # Install flow
python3 Control_Plane/cp.py verify            # Verify all selected
python3 Control_Plane/cp.py deps FMWK-001     # Show dependencies
```

**Individual scripts (also available):**
```bash
python3 Control_Plane/scripts/registry.py list control_plane
python3 Control_Plane/scripts/registry.py show FMWK-001
python3 Control_Plane/scripts/registry.py modify "Item" selected=yes
python3 Control_Plane/scripts/link.py check
python3 Control_Plane/scripts/validate.py
python3 Control_Plane/scripts/apply_selection.py
```

## Install Flow

**Using unified CLI (recommended):**
```bash
python3 Control_Plane/cp.py install "Item Name"   # Handles selection + plan + prompt
# Create the artifact manually
python3 Control_Plane/cp.py verify "Item Name"    # Verify artifact exists
python3 Control_Plane/cp.py activate "Item Name"  # Mark status=active
```

**Manual flow (if needed):**
```bash
python3 Control_Plane/scripts/registry.py modify "Item Name" selected=yes
python3 Control_Plane/scripts/apply_selection.py
python3 Control_Plane/scripts/prompt.py execute install "Item Name"
# Create the artifact
python3 Control_Plane/scripts/registry.py modify "Item Name" status=active
```

## Critical Rules

| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | ID is primary key; names for convenience |

## Protected Paths

| Path | Protection |
|------|------------|
| `/_archive/` | no_delete |
| `/SYSTEM_CONSTITUTION.md` | confirm_modify |
| `/Control_Plane/registries/` | validate_after |

## Testing

```bash
# Run all tests (when available)
pytest tests/

# Run with coverage
pytest tests/ --cov=src
```

## Commit Format

```
<type>: <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`

## User Feedback Guidelines

**Always provide clear status feedback to the user:**

1. **On session start**: Run init.py and report the status summary shown above
2. **After registry changes**: Report what changed and current item status
3. **After validation**: Report pass/fail with specific errors if any
4. **After install/update**: Confirm completion and new status

**Recommended status format for operations:**
```
[OK] Operation completed: <item name>
     Status: <old> → <new>
     Next: <recommended action>
```

**Error format:**
```
[FAIL] Operation failed: <item name>
       Error: <specific error message>
       Fix: <recommended fix>
```

**Progress format for multi-step operations:**
```
[1/N] Installing <item>...
[2/N] Configuring <item>...
...
[N/N] Complete. All items installed.
```
