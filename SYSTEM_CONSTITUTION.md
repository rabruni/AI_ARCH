# SYSTEM_CONSTITUTION.md

Version: 1.0.0
Status: Canonical

---

## TL;DR (Always Follow These)

1. **Registries are truth** — If it's not registered, it doesn't exist
2. **ID is primary key** — All lookups by ID; names are display only
3. **Everything versioned** — Code, prompts, policies, docs
4. **CI must pass** — No merge without green checks
5. **No secrets in git** — Ever
6. **Agents log everything** — Plans, diffs, tests, failures
7. **Safe resets** — Archive before restart, preserve lineage

---

## Truth Hierarchy

Resolve conflicts top-down:

1. This Constitution (`SYSTEM_CONSTITUTION.md`)
2. Control Plane registries (`Control_Plane/registries/`)
3. Governance policies (`Control_Plane/control_plane/`)
4. Runbooks (`Control_Plane/runbooks/`)
5. Docs and code

---

## Repository Structure

```
/
├── SYSTEM_CONSTITUTION.md   # This file (canonical rules)
├── Control_Plane/           # Registry-driven governance system
│   ├── registries/          # Source of truth (CSV)
│   ├── control_plane/       # Policies and contracts
│   ├── modules/             # Installable frameworks
│   ├── scripts/             # validate, apply, generate
│   ├── runbooks/            # Operational procedures
│   ├── generated/           # Output artifacts (plan.json, reports)
│   └── prompts/             # Verb templates (install/update/verify)
├── src/                     # Application code
├── prompts/                 # Prompt modules (governed)
├── tests/                   # All validation
├── docs/                    # Architecture and decisions
├── scripts/                 # Repo-level automation
├── config/                  # Configuration files
└── _archive/                # Historical snapshots (read-only)
```

---

## Registry Contract

All registries use **ID as primary key**.

| Field | Required | Purpose |
|-------|----------|---------|
| `*_id` | Yes | Primary key (e.g., `FMWK-001`, `ROS-P001`) |
| `name` | Yes | Human display name |
| `status` | Yes | `missing` / `draft` / `active` / `deprecated` |
| `selected` | Yes | `yes` / `no` |
| `artifact_path` | If selected | Path to implementation |

**Rule:** If not in a registry, it is not part of the system.

---

## Quality Gates

Merge requires:

- [ ] Registries valid (`python Control_Plane/scripts/validate_registry.py`)
- [ ] Structure valid (required dirs exist)
- [ ] Tests pass
- [ ] No secrets detected

---

## Agent Protocol

Agents MUST:

1. Read plan from `Control_Plane/generated/plan.json`
2. Execute items in dependency order
3. Log actions to `Control_Plane/generated/agent_runs/<timestamp>/`
4. Update registry status after completion

Output for each action:
- Files changed
- Commands run
- Tests executed
- Failures encountered

---

## Operational Modes

| Mode | When | Action |
|------|------|--------|
| **Build** | Adding features | Update registry, keep CI green |
| **Stabilize** | Drift detected | Freeze features, add tests |
| **Reset** | Clean restart | Archive first, re-bootstrap |

---

## Safe Reset Protocol

1. Move state to `/_archive/<YYYY-MM-DD>/`
2. Preserve registries and manifests
3. Write `ARCHIVE_README.md` with reason
4. Re-bootstrap from clean state
5. Validate baseline before adding modules

---

## Amendment

Changes require:
- ADR in `/docs/decisions/`
- Version bump in this file
- CI update if enforcement changes

---

## Machine-Enforceable

```yaml
version: 1.0.0
primary_key: id

required_directories:
  - Control_Plane
  - Control_Plane/registries
  - src
  - tests
  - docs
  - scripts
  - _archive

required_files:
  - SYSTEM_CONSTITUTION.md
  - README.md
  - VERSION
  - Control_Plane/registries/frameworks_registry.csv

registry_schema:
  required_columns:
    - "*_id"
    - name
    - status
    - selected
  status_values:
    - missing
    - draft
    - active
    - deprecated
  selected_values:
    - "yes"
    - "no"
```
