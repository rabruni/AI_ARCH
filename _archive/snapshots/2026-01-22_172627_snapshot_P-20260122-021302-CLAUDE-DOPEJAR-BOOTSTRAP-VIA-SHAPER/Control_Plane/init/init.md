# /init — Create First Meaningful State

**Version:** 2.0.0
**Layer:** 3 of 3 (Semantic)
**Assumes:** Bootstrap + Validate passed

---

## Prerequisites

Before running init, verify:

```bash
# Layer 1: Bootstrap (environmental)
python3 Control_Plane/scripts/bootstrap.py
# Must show: "BOOTSTRAP OK"

# Layer 2: Validate (integrity)
python3 Control_Plane/scripts/validate.py
# Must show: "VALIDATION OK"
```

If either fails, **do not proceed**. Fix issues first.

---

## What Init Does

Init creates the **first meaningful state** by answering:

| Question | Answer Comes From |
|----------|-------------------|
| What modules are enabled? | `selected=yes` in registries |
| What registries are populated? | CSV files in Control_Plane/registries/ |
| What configs are active? | SYSTEM_CONSTITUTION.md |
| What prompts are live? | control_plane/prompts/*.md |
| What mode are we in? | User intent or plan.json |

---

## Init Sequence (5 Steps)

### Step 1: Load Registries
```
READ all *.csv from Control_Plane/registries/
FOR EACH registry:
  COUNT items where selected=yes
  COUNT items where status=active
  NOTE child_registry_path for nested registries
```

### Step 2: Resolve Nested Registries
```
FOR EACH item with child_registry_path:
  IF selected=yes:
    LOAD child registry
    RECURSE until no more children
```

### Step 3: Determine Mode
```
Inspect registry state:

  BUILD mode (default):
    - selected items exist with status=missing
    - work to be done

  STABILIZE mode:
    - all selected items have status=active
    - maintenance only

  RESET mode:
    - user explicitly requested reset
    - archive then rebuild
```

### Step 4: Generate Plan
```
RUN: python3 Control_Plane/scripts/apply_selection.py
OUTPUT: Control_Plane/generated/plan.json

Plan contains:
  - Items to install (status=missing, selected=yes)
  - Items to verify (status=active, selected=yes)
  - Dependency order
```

### Step 5: Report State
```
OUTPUT:
  ════════════════════════════════════════
  INIT COMPLETE
  ════════════════════════════════════════
  Registries: [N] loaded
  Selected: [N] items
  Active: [N] items
  Missing: [N] items (to install)
  Mode: [BUILD|STABILIZE|RESET]
  Plan: Control_Plane/generated/plan.json
  ════════════════════════════════════════

  Ready to receive commands.
```

---

## Available Commands

After init completes, you can execute:

| Command | Verb Prompt | Action |
|---------|-------------|--------|
| `install <ID>` | install.md | Create artifact for registry item |
| `update <ID>` | update.md | Modify existing artifact |
| `verify <ID>` | verify.md | Check artifact matches registry |
| `uninstall <ID>` | uninstall.md | Archive and deprecate item |
| `plan` | — | Regenerate plan.json |
| `validate` | — | Re-run integrity checks |

### Command Pattern
```
1. Find item by ID in registries
2. Load appropriate verb prompt (Control_Plane/control_plane/prompts/*.md)
3. Execute procedure from prompt
4. Update registry
5. Run validate
```

---

## File Reference

| File | Purpose |
|------|---------|
| Control_Plane/scripts/bootstrap.py | Layer 1: Environmental |
| Control_Plane/scripts/validate.py | Layer 2: Integrity |
| Control_Plane/init/init.md | Layer 3: Semantic (this file) |
| Control_Plane/MANIFEST.json | Checksums for critical files |
| Control_Plane/generated/plan.json | Current execution plan |
| Control_Plane/CLAUDE.md | LLM behavioral rules |

---

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3: INIT (Semantic)                               │
│  "What does it mean?"                                   │
│  - Modules enabled                                      │
│  - Mode determined                                      │
│  - Plan generated                                       │
├─────────────────────────────────────────────────────────┤
│  Layer 2: VALIDATE (Integrity)                          │
│  "Is the data well-formed?"                             │
│  - Checksums match                                      │
│  - Schema valid                                         │
│  - References resolve                                   │
├─────────────────────────────────────────────────────────┤
│  Layer 1: BOOTSTRAP (Environmental)                     │
│  "Can the system exist?"                                │
│  - Directories present                                  │
│  - Tools installed                                      │
│  - CI runnable                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Error Recovery

### Init Fails
```
IF init fails after bootstrap+validate passed:
  - Registry content is semantically invalid
  - Check for circular dependencies
  - Check for invalid mode state
  - Re-run validate to confirm integrity
```

### Need Full Reset
```
1. Archive current state: _archive/YYYY-MM-DD/
2. Clear Control_Plane/generated/
3. Re-run bootstrap → validate → init
```

---

## Success Criteria

Init is complete when:

- [ ] Bootstrap passed (environment OK)
- [ ] Validate passed (integrity OK)
- [ ] Registries loaded with counts
- [ ] Mode determined (build/stabilize/reset)
- [ ] plan.json generated
- [ ] Ready to receive commands

---

## Quick Start (For LLMs)

```bash
# Run the three layers in order:
python3 Control_Plane/scripts/bootstrap.py && \
python3 Control_Plane/scripts/validate.py && \
python3 Control_Plane/scripts/apply_selection.py

# If all pass, you are initialized.
# Read plan.json to see pending work.
# Use verb prompts to execute work.
```
