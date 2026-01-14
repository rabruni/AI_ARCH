# ADR-0001: Reliability Workflow for Claude Code Sessions

## Status

Accepted

## Date

2026-01-14

## Context

Working with Claude Code on complex, multi-session projects requires:
- Consistent verification before commits
- Documentation of decisions and session work
- CI/CD integration to catch issues early
- Reproducible development workflows

Without these, issues can arise from:
- Context compaction losing important state
- Inconsistent code quality
- Missing documentation of architectural decisions
- Failed builds on main branch

## Decision

Implement a reliability workflow consisting of:

1. **Verification Script** (`scripts/verify.sh`)
   - Checks Python syntax
   - Runs tests if available
   - Validates project structure
   - Runs on every PR via CI

2. **Capture Script** (`scripts/capture.sh`)
   - Saves session context for continuity
   - Captures git state, environment info
   - Creates timestamped session logs

3. **Claude Rules** (`.claude/RULES.md`)
   - Documents Claude-specific workflows
   - Links to canonical spec files
   - Defines file location conventions

4. **Checklist** (`.claude/CHECKLIST.md`)
   - PR review checklist
   - Pre-commit verification steps
   - Documentation requirements

5. **GitHub Actions CI** (`.github/workflows/ci.yml`)
   - Runs verify.sh on push to main and PRs
   - Provides consistent verification environment

6. **Runbooks** (`docs/runbooks/`)
   - BUILD.md: Setup and build instructions
   - TEST.md: Test execution guide

## Consequences

### Positive

- Consistent verification across sessions
- Automated CI catches issues before merge
- Clear documentation for future sessions
- Reduced risk of regressions

### Negative

- Additional files to maintain
- CI runs add latency to PRs
- Must remember to run verify.sh locally

## Implementation

See session log: `docs/sessions/2026-01-14_claude-reliability.md`
