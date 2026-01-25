# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

AI_ARCH is a **governance meta-repo** that coordinates three decoupled systems:

| Repo | Location | Remote | Purpose |
|------|----------|--------|---------|
| control_plane | `Control_Plane/` | github.com/rabruni/control_plane | Registry-driven orchestration |
| locked_system | `_locked_system_flattened/` | github.com/rabruni/locked_system | Cognitive architecture |
| the_assist | `_assist_flattened/` | github.com/rabruni/the_assist | Cognitive anchor app |

These directories have their own git repos and are in `.gitignore`.

---

## What Remains in AI_ARCH

- **Governance docs**: `SYSTEM_CONSTITUTION.md`, `SPEC.md`
- **Registries**: `repo_registry.csv`, `project_registry.csv`
- **Product**: `the_assist/` (standalone cognitive anchor)
- **Archives**: `_archive/` (historical snapshots)

---

## Working with Decoupled Repos

Each decoupled repo runs independently:

```bash
# Control Plane
cd Control_Plane && python3 scripts/init.py

# Locked System
cd _locked_system_flattened && python main.py

# The Assist
cd _assist_flattened && python main.py
```

---

## Critical Rules

| Rule | Description |
|------|-------------|
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | ID is primary key; names for convenience |

---

## Commit Format

```
<type>: <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`
