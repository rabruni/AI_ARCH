# Technical Design

**Spec:** {{SPEC_NAME}} ({{SPEC_ID}})

---

## Architecture

### Overview

{{Describe the overall architecture}}

### Component Diagram

```
┌─────────────┐     ┌─────────────┐
│ Component A │────▶│ Component B │
└─────────────┘     └─────────────┘
```

---

## Data Model

### Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| {{Entity}} | {{Description}} | {{Fields}} |

### Schema Changes

```sql
-- Example schema change
ALTER TABLE {{table}} ADD COLUMN {{column}} {{type}};
```

---

## API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/{{resource}}` | {{Description}} |
| POST | `/api/v1/{{resource}}` | {{Description}} |

### Request/Response Examples

```json
// POST /api/v1/{{resource}}
{
  "field": "value"
}
```

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `{{path}}` | Create | {{Why}} |
| `{{path}}` | Modify | {{What changes}} |

---

## Dependencies

### Internal
- {{Module/service}}

### External
- {{Library/API}}

---

## Security Considerations

- {{Consideration 1}}
- {{Consideration 2}}

---

## Performance Considerations

- {{Consideration 1}}
- {{Consideration 2}}

---

## Backwards Compatibility

{{Describe impact on existing functionality}}
