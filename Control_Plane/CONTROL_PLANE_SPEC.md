# Control Plane Specification

**Version:** 0.1.0
**Status:** Draft - Needs Review

---

## Definition

The Control Plane is a **registry-driven management layer** for declaratively controlling:
- LLM agents working on the codebase
- Services and infrastructure
- Application components and configuration
- Operational state and dependencies

It provides a single source of truth for **what should exist**, **what does exist**, and **what actions to take**.

---

## Core Principles

| Principle | Description |
|-----------|-------------|
| **Declarative** | Registry defines desired state; tools reconcile actual state |
| **Registry-Driven** | All state lives in CSV registries, versioned in git |
| **Names Primary** | Humans use names; IDs are for machine reference (P003) |
| **Verb-Based Operations** | Four standard verbs: install, update, verify, uninstall |
| **Agent-Agnostic** | Any LLM (Claude, Codex, Gemini, etc.) boots the same way |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Registry   │  │    Verbs    │  │   Scripts   │         │
│  │  (State)    │──│  (Actions)  │──│  (Tools)    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Artifacts                         │   │
│  │  frameworks · modules · services · configs · code    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## The Registry

**Location:** `Control_Plane/registries/control_plane_registry.csv`

**One registry. One file. One source of truth.**

### Schema

| Column | Type | Description |
|--------|------|-------------|
| id | string | Primary key (FMWK-001, MOD-001, etc.) |
| name | string | Human-readable name (primary for lookup) |
| entity_type | enum | framework, module, component, prompt, cloud |
| category | string | Grouping (Governance, Harness, Memory, etc.) |
| purpose | string | One-line description |
| artifact_path | path | Where the artifact lives |
| status | enum | missing, draft, active, deprecated |
| selected | enum | yes, no |
| priority | enum | P0, P1, P2 |
| dependencies | list | Comma-separated IDs |
| version | semver | Current version |
| config | json | Entity-specific configuration |

### Status Lifecycle

```
missing → draft → active → deprecated
   │                          │
   └──────────────────────────┘
         (can revert)
```

| Status | Meaning |
|--------|---------|
| missing | Should exist, doesn't yet |
| draft | Exists but incomplete/unvalidated |
| active | Exists and validated |
| deprecated | Scheduled for removal |

### Selection

`selected=yes` means "include in current plan/operation"

Used for:
- Batch installs (install all selected items)
- Profiles (select a curated set)
- Planning (generate plan.json from selected items)

---

## Entity Types

| Type | Purpose | Examples |
|------|---------|----------|
| framework | Governance docs, runbooks, standards | Repo OS Spec, Definition of Done |
| module | Swappable runtime components | File Memory Bus, Anthropic Provider |
| component | Architectural building blocks | HRM Controller, Vector Store |
| prompt | Meta-prompts and templates | Bootstrap prompt, Install prompt |
| cloud | External services | Redis, PostgreSQL |

---

## Verbs (Operations)

Four standard operations, each with a prompt template:

| Verb | Prompt | Purpose |
|------|--------|---------|
| install | install.md | Create artifact from scratch |
| update | update.md | Modify existing artifact |
| verify | verify.md | Validate artifact matches spec |
| uninstall | uninstall.md | Remove or deprecate artifact |

**Location:** `Control_Plane/control_plane/prompts/`

Verbs are generic - the same install.md works for any entity type.

---

## Scripts (Tools)

| Script | Purpose |
|--------|---------|
| init.py | Boot: bootstrap → validate → plan |
| registry.py | CRUD on registry (list, show, modify, delete) |
| prompt.py | Execute verb prompts |
| module.py | Manage swappable modules |
| link.py | Dependency graph, check for issues |
| validate.py | Integrity checks (checksums, schema) |

---

## Use Cases

### 1. LLM Agent Boot
```bash
python3 Control_Plane/scripts/init.py
# Agent reads registry, understands system state
```

### 2. Install a Framework
```bash
registry.py modify "Local Dev Harness" selected=yes
prompt.py execute install "Local Dev Harness"
# Create artifact following prompt
registry.py modify "Local Dev Harness" status=active
```

### 3. Reconfigure a Service
```bash
registry.py modify "Redis Cache" selected=yes
# Triggers downstream reconciliation
```

### 4. Troubleshoot Dependencies
```bash
link.py check          # Find broken deps
link.py deps "PR Workflow"  # What does it depend on?
link.py dependents "Definition of Done"  # What depends on it?
```

### 5. Swap a Module
```bash
module.py swap memory_bus "Redis Memory Bus"
# Hot-swap from File to Redis implementation
```

---

## Nested Control Planes

Modules can expose their own control plane via `child_registry_path`.

Example: FMWK-900 (Repo OS Module) has:
```
child_registry_path: /modules/repo_os/registries/repo_os_registry.csv
```

This creates a hierarchy:
```
control_plane_registry.csv
  └── FMWK-900 (Repo OS Module)
        └── repo_os_registry.csv
              ├── ROS-M001 (Prompts pack)
              ├── ROS-M002 (Scripts pack)
              └── ...
```

---

## Integrity

### Checksums
Critical files are checksummed in `MANIFEST.json`. Validation fails if files are modified unexpectedly.

### Schema Validation
Registries must have required columns (id, name, status, selected) and valid enum values.

### Referential Integrity
- `artifact_path` must exist if `status=active`
- `dependencies` must reference valid IDs
- `child_registry_path` must exist if specified

---

## Agent Governance

All LLM agents boot via the same sequence:

1. Read agent front door (AGENTS.md, CLAUDE.md, etc.)
2. Run `init.py`
3. Read `agent_bootstrap.md`
4. Use scripts (not cat/grep)
5. Reference items by NAME
6. Commit with agent suffix

---

## Open Questions

- [ ] Should `service` be a separate entity_type from `cloud`?
- [ ] How does deployment state integrate (what's running vs what's configured)?
- [ ] Should config changes trigger automatic reconciliation?
- [ ] How do secrets/credentials integrate?

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01-15 | Initial draft |
