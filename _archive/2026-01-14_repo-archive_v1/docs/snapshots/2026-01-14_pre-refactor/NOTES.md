# Pre-Refactor Inventory and Pain Points

## File Inventory

### Top-Level Structure (Pre-Refactor)

```
AI_ARCH/
├── .claude/                    # Claude Code settings
├── .github/                    # GitHub workflows
├── CANON/                      # Fundamental principles (2 files)
├── Downloads/                  # Temporary downloads (should not be tracked)
├── GenAI Agent Asses/          # Assessment docs (space in name - problematic)
├── archive/                    # Archived code/docs
├── code_derived_docs/          # Generated documentation
├── dev/                        # Development utilities
├── docs/                       # Documentation (minimal use)
├── locked_system/              # Locked System implementation (main code)
├── logs/                       # Log files
├── memory/                     # Memory system data
├── the_assist/                 # The Assist / HRM implementation (main code)
├── venv/                       # Python virtual environment
├── 17 markdown files at root   # Architecture/spec documentation
├── 4 Python files at root      # Scripts and tests
├── 3 shell scripts at root     # Setup and run scripts
├── requirements.txt            # Python dependencies
└── capabilities_v2.csv         # Component inventory
```

### File Count by Type

| Category | Count | Location |
|----------|-------|----------|
| Python source | ~50 | locked_system/, the_assist/ |
| Python tests | ~20 | locked_system/tests/, archive/ |
| Markdown docs | ~30 | Root, various subdirs |
| Shell scripts | ~5 | Root |
| Config files | ~5 | Root, .github/ |
| Data/logs | ~50+ | memory/, logs/ |

## Pain Points

### 1. Documentation Sprawl at Root

**Problem**: 17+ markdown files at root level create clutter and make navigation difficult.

**Files affected**:
- AGENT_ORCHESTRATION.md
- BUILD_PROCESS.md
- CLAUDE.md
- DECISIONS.md
- DOPEJAR_ARCHITECTURE.md
- HRM_INTERFACE_SPECS.md
- IMPLEMENTATION_ORDER.md
- MEMORY_BUS_ARCHITECTURE.md
- MORNING.md
- README.md
- RETROSPECTIVE_FEEDBACK_EXTENSION.md
- SESSION_HANDOFF.md
- SPEC.md
- TEST_SPECIFICATIONS.md
- TRACING_DESIGN.md
- WHAT_WENT_WRONG.md

**Impact**: Hard to find relevant docs, unclear what's current vs historical.

### 2. Multiple Code Locations

**Problem**: Core implementation split between `the_assist/` and `locked_system/` without clear boundaries.

**Confusion points**:
- Both contain HRM-related code
- Unclear which is "current" vs "legacy"
- Imports and dependencies cross between them

### 3. Problematic Directory Names

**Problem**: `GenAI Agent Asses/` contains a space, causing issues with shell commands and imports.

### 4. Tracked Temporary Files

**Problem**: `Downloads/` directory tracked in git, should be in .gitignore.

### 5. No Clear Entry Point

**Problem**: Multiple run scripts and entry points without clear documentation:
- `run.sh`
- `setup_assist.sh`
- `setup_hrm.sh`
- `the_assist/main.py`
- `the_assist/main_hrm.py`
- `locked_system/cli.py`

### 6. Test Fragmentation

**Problem**: Tests scattered across multiple locations:
- `locked_system/tests/`
- `archive/pre_consolidation_*/`
- `test_l2_fastlane.py` at root

### 7. Missing Standard Project Structure

**Problem**: No standard Python project layout:
- No `src/` directory
- No `tests/` at top level
- No `pyproject.toml` at root (only in locked_system/)
- Scripts mixed with source code

### 8. Archive Contains Active Code

**Problem**: `archive/` contains test files that are still being run by pytest, creating confusion about what's active vs archived.

## Recommendations for Refactor

1. Consolidate documentation under `docs/`
2. Establish clear `src/` structure for Python code
3. Move all tests to `tests/`
4. Create single entry point with clear CLI
5. Remove or gitignore temporary directories
6. Rename problematic directories
7. Add proper Python packaging at root level
