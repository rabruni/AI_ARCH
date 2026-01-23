# Definition of Done (Quality Bar)

**ID:** FMWK-005
**Category:** Governance
**Status:** Active

---

## Purpose

Uniform completion criteria across prompts, code, tests, docs, security.

---

## Definition of Done Checklist

An item is **done** when ALL applicable criteria are met:

### Code
- [ ] Code compiles/runs without errors
- [ ] No linting errors or warnings
- [ ] Follows project naming conventions
- [ ] No hardcoded secrets or credentials
- [ ] Edge cases handled

### Tests
- [ ] Unit tests written and passing
- [ ] Integration tests passing (if applicable)
- [ ] No regression in existing tests
- [ ] Test coverage maintained or improved

### Documentation
- [ ] Code comments for complex logic
- [ ] README updated (if new feature)
- [ ] API documentation updated (if applicable)
- [ ] Registry entry exists and is accurate

### Security
- [ ] No secrets in code or config
- [ ] Input validation in place
- [ ] OWASP top 10 considered
- [ ] Dependencies scanned for vulnerabilities

### Registry
- [ ] Item exists in appropriate registry
- [ ] Status updated to `active`
- [ ] Artifact path matches actual location
- [ ] Dependencies declared and satisfied

---

## Acceptance Criteria Format

Each work item should have acceptance criteria in this format:

```markdown
## Acceptance Criteria

**Given** [initial context]
**When** [action taken]
**Then** [expected outcome]

Verification:
- [ ] Criterion 1
- [ ] Criterion 2
```

---

## Quality Levels

| Level | Usage | Requirements |
|-------|-------|--------------|
| **Draft** | Work in progress | Compiles, basic structure |
| **Active** | Ready for use | Full DoD checklist passed |
| **Verified** | CI validated | Automated checks passing |

---

## Exemptions

Items may be marked `active` without full DoD if:
1. Explicitly approved by owner
2. Documented in registry `notes` field
3. Tracked for future completion

---

## Related

- FMWK-012: PR Workflow & Review Checklist
- FMWK-022: CI/CD Standard Pipeline
