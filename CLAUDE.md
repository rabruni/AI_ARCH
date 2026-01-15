# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## First: Boot the Control Plane

```bash
python3 Control_Plane/scripts/init.py
```

This validates the system and shows current state. Run this before any other work.

## What This Repo Is

A **Control Plane** - a registry-driven management layer for:
- LLM agents working on the codebase
- Services and infrastructure
- Application components and configuration

**One registry. One file. One source of truth:**
```
Control_Plane/registries/control_plane_registry.csv
```

## Architecture

```
Control_Plane/
├── registries/
│   └── control_plane_registry.csv   # THE source of truth (46 items)
├── scripts/
│   ├── init.py          # Boot: bootstrap → validate → plan
│   ├── registry.py      # CRUD: list, show, modify, delete
│   ├── prompt.py        # Execute verb prompts (install/update/verify/uninstall)
│   ├── module.py        # Swap runtime modules
│   ├── link.py          # Dependency graph operations
│   └── validate.py      # Integrity checks
├── control_plane/prompts/
│   ├── install.md       # Standard verb prompts (generic, work for any item)
│   ├── update.md
│   ├── verify.md
│   └── uninstall.md
└── CONTROL_PLANE_SPEC.md   # Full specification
```

## Commands

### Registry Operations (by NAME, not ID)
```bash
# List everything
python3 Control_Plane/scripts/registry.py list control_plane

# Show item by name
python3 Control_Plane/scripts/registry.py show "Definition of Done"

# Modify item by name
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

### Module Swapping
```bash
python3 Control_Plane/scripts/module.py list
python3 Control_Plane/scripts/module.py swap memory_bus "Redis Memory Bus"
```

## Critical Rules

| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | **Names are primary, IDs are reference** |

## Registry Schema

| Column | Purpose |
|--------|---------|
| id | Machine key (FMWK-001, MOD-001) |
| name | Human key - **use this for lookups** |
| entity_type | framework, module, component, prompt, cloud |
| status | missing → draft → active → deprecated |
| selected | yes/no - included in current plan |

## Commit Format

```
<type>: <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`

## Protected Paths

- `/_archive/` - no delete (historical record)
- `/SYSTEM_CONSTITUTION.md` - confirm before modify
- `/Control_Plane/registries/` - validate after changes
