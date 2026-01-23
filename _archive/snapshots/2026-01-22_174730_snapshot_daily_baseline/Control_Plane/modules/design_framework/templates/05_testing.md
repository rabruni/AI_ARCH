# Testing Strategy

**Spec:** {{SPEC_NAME}} ({{SPEC_ID}})

---

## Test Plan Overview

| Test Type | Coverage Goal | Owner |
|-----------|---------------|-------|
| Unit | {{%}} | {{Name}} |
| Integration | {{%}} | {{Name}} |
| E2E | {{Scenarios}} | {{Name}} |

---

## Unit Tests

### Test Cases

| ID | Description | Input | Expected Output |
|----|-------------|-------|-----------------|
| UT-001 | {{Description}} | {{Input}} | {{Output}} |
| UT-002 | {{Description}} | {{Input}} | {{Output}} |

### Test Files

| File | Purpose |
|------|---------|
| `tests/test_{{module}}.py` | {{Description}} |

---

## Integration Tests

### Scenarios

| ID | Description | Components | Expected Behavior |
|----|-------------|------------|-------------------|
| IT-001 | {{Description}} | {{A, B}} | {{Behavior}} |

---

## End-to-End Tests

### User Flows

| ID | Flow | Steps | Expected Result |
|----|------|-------|-----------------|
| E2E-001 | {{Flow name}} | {{Steps}} | {{Result}} |

---

## Edge Cases

| Case | Input | Expected Handling |
|------|-------|-------------------|
| Empty input | `""` | {{Behavior}} |
| Invalid input | `{{example}}` | {{Behavior}} |
| Boundary | `{{example}}` | {{Behavior}} |

---

## Performance Tests

| Metric | Target | Test Method |
|--------|--------|-------------|
| Response time | < {{N}}ms | {{Method}} |
| Throughput | > {{N}} rps | {{Method}} |

---

## Test Data

### Setup

```bash
# Commands to set up test data
{{commands}}
```

### Fixtures

| Fixture | Description | Location |
|---------|-------------|----------|
| {{Name}} | {{Description}} | `tests/fixtures/{{file}}` |

---

## Verification Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E scenarios verified
- [ ] Performance targets met
- [ ] Edge cases handled
- [ ] No regressions
