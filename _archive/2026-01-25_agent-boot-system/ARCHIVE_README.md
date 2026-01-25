# Agent Boot System Archive

**Archived:** 2026-01-25
**Reason:** System decoupling made multi-agent orchestration obsolete

## What This Was

A multi-agent coordination system designed for a monorepo architecture where:
- Claude (Primary Implementer), Codex (Spec Enforcer), and Gemini (Validator) worked together
- A single Orchestrator controlled task sequencing
- `_Prompt-Cache_/` served as shared task dispatch board
- `boot.py` provided unified agent entry point
- `auto_loop.py` automated continuous agent dispatch

## Why It Was Archived

On 2026-01-25, three major systems were decoupled into independent repositories:
- `control_plane` → github.com/rabruni/control_plane
- `locked_system` → github.com/rabruni/locked_system
- `the_assist` → github.com/rabruni/the_assist

With each repo now having its own:
- Git repository and history
- Init/startup sequence
- Independent operation

The multi-agent orchestration became orphaned infrastructure. Each system runs independently without needing cross-agent coordination via a shared prompt cache.

## Contents

| File | Purpose |
|------|---------|
| `boot.py` | Unified agent entry point (8KB) |
| `auto_loop.py` | Automated agent loop dispatcher (13KB) |
| `AGENTS.md` | Multi-agent protocol and role definitions |
| `CODEX.md` | Codex-specific constraints and mission |
| `GEMINI.md` | Gemini-specific constraints and mission |
| `_Prompt-Cache_/` | Task dispatch board (22 files) |

## Restoration

If multi-agent coordination is needed again:
1. Copy files back to repo root
2. Update CLAUDE.md to reference startup protocol
3. Ensure `scripts/init.py` exists and works
4. Re-establish `generated/active_orchestrator.json` tracking

Note: A redesigned coordination system using Control_Plane registries would likely be more appropriate for the decoupled architecture.

## Historical Value

These files document:
- Successful adherence tests (Jan 22, 2026) for Claude, Codex, Gemini
- Multi-agent task dispatch patterns
- Role segregation model (Orchestrator, Implementer, Enforcer, Validator)
- Prompt-based agent coordination approach
