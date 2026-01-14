# Claude Code Reliability Rules

## Core Principles

1. **Verify Before Acting**: Always run `scripts/verify.sh` before committing changes
2. **Document Decisions**: Log significant decisions in `docs/decisions/`
3. **Follow Checklists**: Complete the checklist in `CHECKLIST.md` for each PR
4. **Capture Context**: Use `scripts/capture.sh` to save session context

## Git Workflow

- Create feature branches from `main`
- Branch naming: `feat/`, `fix/`, `docs/`, `refactor/`
- Run verification before pushing
- Include decision records for architectural changes

## Code Changes

- Read existing code before modifying
- Preserve existing patterns and conventions
- Do not over-engineer or add unnecessary features
- Test changes locally before committing

## Session Continuity

- Read `DECISIONS.md` and `BUILD_PROCESS.md` after context compaction
- Check `capabilities_v2.csv` for exact file locations
- Verify with user on current milestone before proceeding

## File Locations (This Project)

- HRM implementation: `the_assist/hrm/`
- Locked System: `locked_system/`
- Reasoning HRM: `the_assist/reasoning/`
- Learning HRM: `the_assist/learning/`
- Memory Bus: `shared/memory/`
