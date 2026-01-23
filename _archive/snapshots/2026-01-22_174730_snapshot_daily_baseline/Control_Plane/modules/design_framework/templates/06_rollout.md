# Rollout Plan

**Spec:** {{SPEC_NAME}} ({{SPEC_ID}})

---

## Rollout Strategy

**Type:** Big Bang | Phased | Feature Flag | Canary

{{Describe the chosen strategy and rationale}}

---

## Phases

### Phase 1: {{Name}}
**Target:** {{Date}}
**Scope:** {{What's included}}
**Success Criteria:**
- [ ] {{Criterion}}

### Phase 2: {{Name}}
**Target:** {{Date}}
**Scope:** {{What's included}}
**Success Criteria:**
- [ ] {{Criterion}}

---

## Pre-Rollout Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Registry entries created
- [ ] Monitoring in place
- [ ] Rollback plan tested
- [ ] Stakeholders notified

---

## Deployment Steps

1. {{Step 1}}
2. {{Step 2}}
3. {{Step 3}}

### Commands

```bash
# Deployment commands
{{commands}}
```

---

## Verification

### Smoke Tests

| Test | Command | Expected |
|------|---------|----------|
| {{Test}} | `{{command}}` | {{Expected}} |

### Health Checks

| Endpoint | Expected Status |
|----------|-----------------|
| `{{endpoint}}` | 200 OK |

---

## Rollback Plan

### Trigger Conditions
- {{Condition 1}}
- {{Condition 2}}

### Rollback Steps
1. {{Step 1}}
2. {{Step 2}}

### Rollback Commands
```bash
{{commands}}
```

---

## Communication Plan

| Audience | Channel | Message | When |
|----------|---------|---------|------|
| {{Audience}} | {{Channel}} | {{Message}} | {{Timing}} |

---

## Post-Rollout

### Monitoring
- {{What to monitor}}

### Success Metrics
| Metric | Target | Actual |
|--------|--------|--------|
| {{Metric}} | {{Target}} | {{TBD}} |

### Retrospective
- **Date:** {{Date}}
- **Attendees:** {{Names}}
