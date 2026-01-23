# Repo OS Spec

**ID:** FMWK-001
**Category:** Governance
**Status:** Active

---

## Purpose

Defines repo operating system: structure, invariants, naming, workflows.

---

## Repository Structure

```
/
├── Control_Plane/           # Registry-driven management system
│   ├── boot_os_registry.csv # Bootstrap system components
│   ├── registries/          # All registry files
│   ├── scripts/             # Automation scripts
│   ├── prompts/             # Custom prompts
│   ├── modules/             # Slot modules
│   └── generated/           # Auto-generated files
├── runbooks/                # Operational documentation
│   ├── governance/          # Governance frameworks
│   ├── delivery/            # Delivery processes
│   └── harness/             # Development harness
├── memory/                  # Persistent memory storage
├── docs/                    # Project documentation
└── _archive/                # Historical records
```

---

## Structural Invariants

1. **Registry as Source of Truth**
   - Every artifact MUST be tracked in a registry
   - If it's not in a registry, it doesn't officially exist
   - Status transitions: missing → draft → active

2. **No Hidden State**
   - All configuration in version-controlled files
   - No manual state outside registries
   - Deterministic regeneration must be possible

3. **Explicit Dependencies**
   - Dependencies declared in registry `depends_on` field
   - No circular dependencies allowed
   - Install order respects dependency graph

---

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Registry | `*_registry.csv` | `frameworks_registry.csv` |
| Script | `snake_case.py` | `apply_selection.py` |
| Prompt | `snake_case.md` | `install.md` |
| Runbook | `snake_case.md` | `repo_os_spec.md` |
| ID | `PREFIX-NNN` | `FMWK-001`, `BOOT-012` |

---

## Workflows

### Bootstrap Flow
```
1. python init.py           # Run 3-layer bootstrap
2. python apply_selection.py # Generate plan from selections
3. python prompt.py execute install <ID>  # Install items
4. python registry.py modify <ID> status=active  # Update status
```

### Change Flow
```
1. Modify registry (selected=yes, or field changes)
2. Run apply_selection.py to regenerate plan
3. Execute appropriate verb (install/update/verify/uninstall)
4. Commit changes
```

---

## Enforcement

- CI validation required before merge
- Registry validator must pass
- All artifacts must have registry entries

---

## Related

- FMWK-002: Prompt Governance Framework
- FMWK-052: Index/Registry System
- BOOT-001 to BOOT-019: Bootstrap system
