# AI_ARCH

A registry-driven repository operating system for building agentic software with repeatability, auditability, and CI-backed guarantees.

---

## Governance

This repository is governed by [`SYSTEM_CONSTITUTION.md`](./SYSTEM_CONSTITUTION.md).

Key principles:
- **Registries are truth** — All modules, prompts, and frameworks tracked in CSV registries
- **ID is primary key** — Lookups by ID; names are display only
- **Agents execute plans** — `Control_Plane/generated/plan.json` drives automation

---

## Structure

```
/
├── SYSTEM_CONSTITUTION.md   # Canonical rules
├── Control_Plane/           # Registry-driven governance
│   ├── registries/          # Source of truth (CSV)
│   ├── scripts/             # validate, apply, generate
│   └── generated/           # Execution plans and reports
├── src/                     # Application code
├── prompts/                 # Prompt modules
├── tests/                   # Validation
├── docs/                    # Architecture
└── _archive/                # Historical snapshots
```

---

## Quick Start

```bash
# Validate registries
python Control_Plane/scripts/validate_registry.py

# Generate execution plan
python Control_Plane/scripts/apply_selection.py

# View plan
cat Control_Plane/generated/plan.json
```

---

## Archive

Previous work preserved at [`/_archive/`](./_archive/).

---

## Version

See [`VERSION`](./VERSION) — currently `0.1.0`
