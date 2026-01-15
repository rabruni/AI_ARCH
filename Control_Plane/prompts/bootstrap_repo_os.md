# Bootstrap Repo OS Meta-Prompt

**ID:** PRMPT-010
**Purpose:** One-shot prompt to scaffold a repository operating system into an empty repo.

---

## Overview

This meta-prompt bootstraps a complete Control Plane into a new or existing repository. It creates the foundational structure that enables registry-driven management of all artifacts.

---

## Prerequisites

Before running this prompt:
- [ ] Git repository initialized
- [ ] Python 3.9+ available
- [ ] Write access to repository root

---

## Procedure

### Phase 1: Create Directory Structure

```
/Control_Plane/
├── init/
│   └── init.md              # Bootstrap documentation
├── scripts/
│   ├── bootstrap.py         # Environmental checks
│   ├── validate.py          # Integrity checks
│   ├── init.py              # Full initialization
│   └── ...                   # Other automation scripts
├── registries/
│   ├── frameworks_registry.csv
│   ├── prompts_registry.csv
│   ├── components_registry.csv
│   └── modules_registry.csv
├── control_plane/
│   └── prompts/
│       ├── install.md
│       ├── update.md
│       ├── verify.md
│       └── uninstall.md
├── generated/               # Auto-generated files
├── prompts/                 # Custom prompts
└── boot_os_registry.csv     # Bootstrap system registry
```

### Phase 2: Create Core Registries

1. **boot_os_registry.csv** - Bootstrap system components
2. **frameworks_registry.csv** - Governance and harness frameworks
3. **prompts_registry.csv** - Prompt templates
4. **components_registry.csv** - Reusable components

### Phase 3: Create Agent Front Doors

Create governance files for LLM agents:
- `/CLAUDE.md` - Claude Code governance
- `/.github/copilot-instructions.md` - GitHub Copilot
- `/.cursorrules` - Cursor
- `/.clinerules` - Cline

Each file should reference `/Control_Plane/init/init.md` as the bootstrap entry point.

### Phase 4: Create Boot Scripts

Create the three-layer bootstrap system:

1. **Layer 1 (bootstrap.py)**: Environmental checks
   - Directories exist
   - Required tools available
   - Version constraints met

2. **Layer 2 (validate.py)**: Integrity checks
   - Checksums match MANIFEST.json
   - Registry schemas valid
   - References resolve

3. **Layer 3 (init.py)**: Semantic layer
   - Load registries
   - Detect mode (BUILD/STABILIZE/RESET)
   - Generate plan

### Phase 5: Verify Installation

```bash
python Control_Plane/scripts/init.py
```

Expected output:
```
Layer 1: Bootstrap
  [PASS] Directories exist
  [PASS] Required tools available
  ...

Layer 2: Validate
  [PASS] Checksums match
  ...

Layer 3: Init
  [INFO] Mode: BUILD
  [INFO] Selected: N items
  ...

Boot sequence complete.
```

---

## Success Criteria

- [ ] All directories created
- [ ] Core registries populated with schema
- [ ] Agent front doors reference init.md
- [ ] `python init.py` returns success
- [ ] `.gitignore` updated for generated files

---

## Post-Bootstrap

After successful bootstrap:
1. Run `python prompt.py list` to see available prompts
2. Run `python registry.py list` to see registries
3. Select frameworks with `registry.py modify FMWK-xxx selected=yes`
4. Generate plan with `apply_selection.py`
5. Execute plan using verb prompts

---

## Rollback

If bootstrap fails:
```bash
rm -rf Control_Plane/
rm CLAUDE.md .cursorrules .clinerules .github/copilot-instructions.md
```

Then investigate the error and retry.
