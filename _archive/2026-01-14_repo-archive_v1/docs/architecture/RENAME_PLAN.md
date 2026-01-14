# Rename Plan: locked_system → HRM Routing

## Summary

| Current | New |
|---------|-----|
| `locked_system/` | `hrm_routing/` |
| `front_door/` | `hrm_router/` |
| `from locked_system.xxx` | `from hrm_routing.xxx` |
| `demo_front_door.py` | `demo_hrm_router.py` |

---

## Impact Analysis

### Files Referencing `locked_system` (82 files)

**Core Module Files (will need import updates):**
- `locked_system/*.py` - All internal imports
- `the_assist/main_locked.py` - Integration point
- `the_assist/adapters/*.py` - Bridge to routing
- `.github/workflows/tests.yml` - CI paths

**Documentation Files (text updates only):**
- `capabilities_inventory.csv`
- `capabilities_master.csv`
- `MEMORY_ARCHITECTURE_PROPOSAL.md`
- `GITHUB_PROJECT_STRUCTURE.md`
- `test_coverage_summary.md`
- `code_derived_docs/*.md`
- `locked_system/README.md`
- `locked_system/CONTRIBUTING.md`

### Files Referencing `front_door` (19 files)

**Module Files:**
- `locked_system/front_door/` → `hrm_routing/hrm_router/`
- `locked_system/demo_front_door.py` → `hrm_routing/demo_hrm_router.py`
- `locked_system/tests/test_front_door.py` → `hrm_routing/tests/test_hrm_router.py`
- All imports from `locked_system.front_door`

**External References:**
- `Downloads/agents/defs/front_door.yaml`
- `capabilities_*.csv`
- `test_coverage_summary.md`

---

## Rename Strategy

### Phase 1: Create Aliases (Non-Breaking)

Add compatibility imports so both names work temporarily:

```python
# hrm_routing/__init__.py
# Alias for backwards compatibility
import sys
sys.modules['locked_system'] = sys.modules['hrm_routing']

# hrm_routing/hrm_router/__init__.py
# Alias for backwards compatibility
import sys
sys.modules['locked_system.front_door'] = sys.modules['hrm_routing.hrm_router']
```

### Phase 2: Rename Directory

```bash
# Rename main directory
git mv locked_system hrm_routing

# Rename front_door subdirectory
git mv hrm_routing/front_door hrm_routing/hrm_router

# Rename demo file
git mv hrm_routing/demo_front_door.py hrm_routing/demo_hrm_router.py

# Rename test file
git mv hrm_routing/tests/test_front_door.py hrm_routing/tests/test_hrm_router.py
```

### Phase 3: Update Imports (Automated)

```bash
# Update all Python imports
find . -name "*.py" -exec sed -i '' 's/from locked_system/from hrm_routing/g' {} \;
find . -name "*.py" -exec sed -i '' 's/import locked_system/import hrm_routing/g' {} \;
find . -name "*.py" -exec sed -i '' 's/locked_system\./hrm_routing./g' {} \;

# Update front_door references
find . -name "*.py" -exec sed -i '' 's/front_door/hrm_router/g' {} \;
```

### Phase 4: Update Documentation

```bash
# Update markdown and CSV files
find . -name "*.md" -exec sed -i '' 's/locked_system/hrm_routing/g' {} \;
find . -name "*.md" -exec sed -i '' 's/front_door/hrm_router/g' {} \;
find . -name "*.csv" -exec sed -i '' 's/locked_system/hrm_routing/g' {} \;
find . -name "*.csv" -exec sed -i '' 's/front_door/hrm_router/g' {} \;
```

### Phase 5: Update Config Files

- `.github/workflows/tests.yml`
- `run.sh`
- `pyproject.toml`
- `setup.py`

### Phase 6: Verify & Remove Aliases

```bash
# Run all tests
pytest hrm_routing/tests/
pytest the_assist/tests/  # If exists

# Remove compatibility aliases after verification
```

---

## Detailed File Changes

### Directory Structure (Before → After)

```
locked_system/                      →  hrm_routing/
├── front_door/                     →  ├── hrm_router/
│   ├── __init__.py                    │   ├── __init__.py
│   ├── agent.py                       │   ├── agent.py
│   ├── signals.py                     │   ├── signals.py
│   ├── bundles.py                     │   ├── bundles.py
│   └── emotional.py                   │   └── emotional.py
├── demo_front_door.py              →  ├── demo_hrm_router.py
├── tests/                             ├── tests/
│   ├── test_front_door.py          →  │   ├── test_hrm_router.py
│   └── ...                            │   └── ...
└── ...                                └── ...
```

### Import Changes

| Before | After |
|--------|-------|
| `from locked_system.front_door import agent` | `from hrm_routing.hrm_router import agent` |
| `from locked_system.slow_loop import gates` | `from hrm_routing.slow_loop import gates` |
| `from locked_system.fast_loop import executor` | `from hrm_routing.fast_loop import executor` |
| `from locked_system import config` | `from hrm_routing import config` |
| `import locked_system` | `import hrm_routing` |

### pyproject.toml Changes

```toml
# Before
[project]
name = "locked_system"

# After
[project]
name = "hrm_routing"
```

### run.sh Changes

```bash
# Before
cd locked_system && python -m locked_system.main

# After
cd hrm_routing && python -m hrm_routing.main
```

### CI Workflow Changes

```yaml
# Before
- name: Run tests
  run: |
    cd locked_system
    pytest tests/

# After
- name: Run tests
  run: |
    cd hrm_routing
    pytest tests/
```

---

## Risk Mitigation

1. **Create branch first**: `git checkout -b rename/locked-system-to-hrm-routing`
2. **Run full test suite before**: Ensure baseline passes
3. **Add compatibility aliases first**: Allows rollback
4. **Atomic commit for rename**: One commit for `git mv`
5. **Separate commits for imports**: Can revert independently
6. **Test after each phase**: Don't proceed if tests fail

---

## Verification Checklist

- [ ] All Python imports resolve
- [ ] All tests pass
- [ ] `run.sh` works
- [ ] CI pipeline passes
- [ ] No broken internal links
- [ ] Documentation updated
- [ ] CSV inventories updated
- [ ] No `locked_system` or `front_door` references remain (except historical docs)

---

## Estimated Scope

| Category | Count |
|----------|-------|
| Directory renames | 2 |
| File renames | 3 |
| Import updates | ~200 lines |
| Documentation updates | ~50 lines |
| Config updates | ~10 lines |

---

## Recommended Execution

This rename should be its own PR:
1. Branch: `rename/locked-system-to-hrm-routing`
2. Execute phases 1-6
3. Full test verification
4. PR review (check all imports work)
5. Merge with squash

**Do NOT mix with feature work** - keep the rename clean and isolated.
