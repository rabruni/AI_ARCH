# Claude Code PR Checklist

## Before Starting Work

- [ ] Read relevant spec files (`DECISIONS.md`, `BUILD_PROCESS.md`)
- [ ] Verify current milestone with user
- [ ] Create feature branch from `main`

## During Development

- [ ] Read existing code before modifying
- [ ] Follow existing patterns and conventions
- [ ] No application logic changes in scaffolding PRs
- [ ] Update todo list as work progresses

## Before Committing

- [ ] Run `scripts/verify.sh` - all checks pass
- [ ] No secrets or credentials in code
- [ ] No unnecessary files added
- [ ] Commit message is clear and descriptive

## Before PR

- [ ] All tests pass locally
- [ ] Documentation updated if needed
- [ ] Decision record added for architectural changes
- [ ] Session log created in `docs/sessions/`

## PR Description

- [ ] Summarizes what changed
- [ ] Links to relevant issues/decisions
- [ ] Includes test plan
