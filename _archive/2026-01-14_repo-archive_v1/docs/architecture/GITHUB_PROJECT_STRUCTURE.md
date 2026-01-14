# GitHub Project Structure: DoPeJar

## Project Board Columns

| Column | Purpose |
|--------|---------|
| Backlog | All work items not yet scheduled |
| Ready | Refined, ready to start |
| In Progress | Currently being worked on |
| Review | Awaiting code review |
| Done | Completed and merged |

## Milestones

### Milestone 0.1: Integration (Wire Altitude ↔ Focus)
**Goal:** Make the_assist use locked_system for all governance

| Issue | Priority | Depends On |
|-------|----------|------------|
| Wire executor.py (assist) to gates.py (locked) | P0 | - |
| Wire planner.py to Focus HRM validation | P0 | Above |
| Wire evaluator.py to continuous_eval | P1 | Above |
| Create integration tests | P0 | Above |
| Test full turn cycle | P0 | All above |

### Milestone 0.2: Consolidation (Cleanup + UI)
**Goal:** Remove duplicates, centralize UI

| Issue | Priority | Depends On |
|-------|----------|------------|
| Delete core/governance/ duplicates | P1 | M0.1 |
| Delete core/execution/ duplicates | P1 | M0.1 |
| Create the_assist/ui/ module | P2 | - |
| Move formatter.py to ui/ | P2 | Above |
| Move chat_ui.py to ui/ | P2 | Above |
| Move demo_front_door.py to the_assist/ | P2 | Above |
| Create llm.py adapter | P0 | - |
| Create llm_config.yaml | P1 | Above |

### Milestone 0.3: Reasoning HRM (Signal Router)
**Goal:** Add adaptive reasoning strategy selection

| Issue | Priority | Depends On |
|-------|----------|------------|
| Create the_assist/reasoning/ package | P1 | M0.2 |
| Implement router.py | P1 | Above |
| Implement strategies.py | P1 | Above |
| Implement classifier.py | P1 | Above |
| Implement escalation.py | P1 | Above |
| Create unit tests | P1 | All above |
| Create integration tests | P1 | All above |

### Milestone 0.4: Learning HRM (Pattern Memory)
**Goal:** Add learning memory that grows/trims/self-manages

| Issue | Priority | Depends On |
|-------|----------|------------|
| Create the_assist/learning/ package | P1 | M0.3 |
| Implement patterns.py (extend memory_v2 format) | P1 | Above |
| Implement trimmer.py | P2 | Above |
| Implement generalizer.py | P2 | Above |
| Implement feedback_loop.py | P1 | Above |
| Create unit tests | P1 | All above |
| Create integration tests | P1 | All above |

### Milestone 1.0: Unified Experience
**Goal:** Single entry point with all 4 HRM layers working

| Issue | Priority | Depends On |
|-------|----------|------------|
| Create unified main.py entry | P0 | M0.4 |
| Boot sequence uses all 4 HRMs | P0 | Above |
| End-to-end integration test | P0 | Above |
| Documentation | P2 | Above |
| Performance testing | P2 | Above |

## Labels

| Label | Color | Purpose |
|-------|-------|---------|
| `altitude-hrm` | Blue | Altitude HRM (scope governance) |
| `focus-hrm` | Green | Focus HRM (control governance) |
| `reasoning-hrm` | Purple | Reasoning HRM (signal router) |
| `learning-hrm` | Orange | Learning HRM (pattern memory) |
| `ui` | Gray | UI components |
| `integration` | Red | Integration work |
| `tests` | Yellow | Test coverage |
| `p0-blocking` | Dark Red | Must be done first |
| `p1-core` | Red | Core functionality |
| `p2-enhancement` | Orange | Nice to have |
| `p3-cleanup` | Gray | Cleanup/refactor |

## Issue Templates

### Feature Issue Template
```markdown
## Summary
Brief description of the feature

## HRM Layer
- [ ] Altitude HRM
- [ ] Focus HRM
- [ ] Reasoning HRM
- [ ] Learning HRM

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Test Requirements
- [ ] Unit tests
- [ ] Integration tests

## Dependencies
- Depends on: #issue_number
```

### Bug Issue Template
```markdown
## Description
What's happening

## Expected Behavior
What should happen

## Steps to Reproduce
1. Step 1
2. Step 2

## HRM Layer Affected
- [ ] Altitude HRM
- [ ] Focus HRM
- [ ] Reasoning HRM
- [ ] Learning HRM
```

## Branch Strategy

```
main
├── develop (integration branch)
│   ├── feature/altitude-focus-bridge
│   ├── feature/ui-consolidation
│   ├── feature/reasoning-hrm
│   └── feature/learning-hrm
```

## CI/CD Pipeline

```yaml
# .github/workflows/tests.yml (already exists)
on: [push, pull_request]
jobs:
  test:
    - Run pytest locked_system/tests/
    - Run pytest the_assist/tests/ (to be created)
    - Check test coverage
    - Fail if coverage < 80% for changed files
```

## Definition of Done

- [ ] Code complete
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] No security-critical code without tests
- [ ] Code reviewed
- [ ] Documentation updated (if applicable)
- [ ] Merged to develop

## Sprint Cadence (Suggested)

| Week | Focus |
|------|-------|
| 1 | M0.1 Integration |
| 2 | M0.2 Consolidation |
| 3-4 | M0.3 Reasoning HRM |
| 5-6 | M0.4 Learning HRM |
| 7 | M1.0 Unified Experience |
