# Archive README

## Archive Information

- **Date Archived:** 2026-01-14
- **Archive Version:** v1
- **Git Commit at Archive:** ae6b7cd3b4e8cd2d0ddd5e9d029f2071f1231c6a

## Reason for Archival

This repository ("The Assist" / AI_ARCH) is being archived to enable a clean re-initialization of the project structure. The existing codebase contains valuable work but requires a fresh architectural approach. Key factors driving the restart:

1. **Accumulated complexity** - Multiple experimental directions coexisted without clear separation
2. **Documentation-implementation drift** - Specs and code diverged over iterations
3. **Architecture evolution** - The project shifted from multi-agent orchestration to HRM (Hierarchical Reasoning Model), leaving legacy code intermingled
4. **Context compaction incidents** - Previous work sessions experienced continuity issues requiring more robust recovery mechanisms

## What This Archive Contains

**The Assist** was a cognitive anchor system implementing HRM (Hierarchical Reasoning Model) - a framework for AI agents that separates intent, planning, execution, and evaluation into distinct layers with stable interfaces.

### Key Components

- `the_assist/` - Main application code including HRM implementation
- `locked_system/` - New architecture (Slow Loop + Fast Loop design)
- `docs/` - Architecture documentation, specs, and decision records
- `memory/` - Session persistence and conversation history
- `CLAUDE.md` - Claude Code guidance and project conventions
- Various setup scripts and configuration files

### Architecture Highlights

- **HRM Layers:** Intent (L1) -> Planner (L2) -> Executor (L3) -> Evaluator (L4)
- **Key Principle:** "State flows UP, meaning flows DOWN"
- **Two Entry Points:** `main_hrm.py` (current), `main.py` (legacy)

## Known Limitations

1. Inconsistent file locations for new modules
2. Mixed legacy and new architecture code
3. Some tests incomplete or failing
4. Memory system needed redesign

## Important Notice

**This archive is READ-ONLY.**

Do not modify files in this archive. If you need to reference or restore code, copy it to the active repository structure. The archive exists for historical reference and traceability.

## Related Files

- See `MANIFEST.json` for structured metadata
- Original remote: https://github.com/rabruni/AI_ARCH.git
