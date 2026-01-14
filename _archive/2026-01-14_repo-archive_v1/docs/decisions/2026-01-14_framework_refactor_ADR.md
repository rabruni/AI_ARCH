# ADR: Framework Refactor for AI_ARCH

**Date**: 2026-01-14
**Status**: Accepted
**Deciders**: Repository maintainers

## Context

The AI_ARCH repository has grown organically to include:
- HRM (Hierarchical Reasoning Model) implementation
- Locked System architecture
- Multiple documentation files
- Various support scripts and utilities

The current structure creates navigation difficulties, unclear boundaries between components, and maintenance challenges.

## Pain Points

1. **Documentation sprawl**: 17+ markdown files at root level
2. **Multiple code locations**: `the_assist/` and `locked_system/` without clear boundaries
3. **Problematic naming**: Directory with space (`GenAI Agent Asses/`)
4. **Tracked temporary files**: `Downloads/` should not be in version control
5. **No clear entry point**: Multiple run scripts without documentation
6. **Test fragmentation**: Tests scattered across multiple locations
7. **Missing standard layout**: No `src/`, `tests/`, or proper Python packaging at root
8. **Archive pollution**: Active tests mixed with archived code

## Decision

Adopt a **consolidated documentation + preserved source** layout that:
- Moves all documentation under `docs/`
- Preserves existing source code structure (minimal disruption)
- Establishes clear entry points and scripts
- Adds proper validation and CI

## Chosen Layout

```
AI_ARCH/
├── .claude/                    # Claude Code configuration
├── .github/workflows/          # CI/CD workflows
├── docs/                       # ALL documentation
│   ├── README.md               # Documentation index
│   ├── architecture/           # Architecture docs (moved from root)
│   ├── decisions/              # ADRs
│   ├── runbooks/               # Operational guides
│   ├── snapshots/              # Legacy snapshots
│   ├── sessions/               # Session logs
│   └── answers/                # Summary documents
├── scripts/                    # Shell scripts
│   ├── verify.sh               # Validation script
│   ├── capture.sh              # Context capture
│   └── validate_repo.sh        # Repository validation
├── configs/                    # Configuration files
├── locked_system/              # Locked System implementation (preserved)
├── the_assist/                 # The Assist / HRM implementation (preserved)
├── memory/                     # Memory system (preserved)
├── archive/                    # Historical code (preserved, excluded from tests)
├── CLAUDE.md                   # Claude Code instructions (kept at root)
├── README.md                   # Project README (kept at root)
├── requirements.txt            # Python dependencies
├── run.sh                      # Main entry point
└── .gitignore                  # Updated to exclude temp files
```

## Alternatives Considered

### Alternative 1: Full src/ Layout

```
AI_ARCH/
├── src/
│   ├── ai_arch/
│   │   ├── locked_system/
│   │   ├── the_assist/
│   │   └── memory/
├── tests/
├── docs/
└── pyproject.toml
```

**Pros**: Standard Python packaging, clear boundaries
**Cons**: Requires updating all imports, high disruption, breaks existing workflows

**Rejected because**: Too disruptive for the current stage; can be done incrementally later.

### Alternative 2: Monorepo with Packages

```
AI_ARCH/
├── packages/
│   ├── locked-system/
│   ├── the-assist/
│   └── memory-bus/
├── docs/
└── scripts/
```

**Pros**: Clear package separation, independent versioning
**Cons**: Requires build tooling, complex dependency management

**Rejected because**: Over-engineering for current needs; adds complexity without clear benefit.

### Alternative 3: Minimal Changes (Documentation Only)

Only move documentation, leave everything else unchanged.

**Pros**: Lowest risk, fastest to implement
**Cons**: Doesn't address test fragmentation, entry point confusion, or validation needs

**Rejected because**: Doesn't sufficiently address the pain points.

## Migration Strategy

### Phase 1: Documentation Consolidation (This PR)
1. Create `docs/` hierarchy
2. Move architecture docs from root to `docs/architecture/`
3. Preserve root README.md and CLAUDE.md
4. Add validation scripts
5. Update .gitignore

### Phase 2: Scripts and Entry Points (This PR)
1. Consolidate scripts in `scripts/`
2. Document entry points in `docs/runbooks/`
3. Add CI workflow

### Phase 3: Test Organization (Future)
1. Configure pytest to exclude archive/
2. Document test locations
3. Consider consolidating tests

### Phase 4: Source Restructuring (Future)
1. Optional move to src/ layout
2. Add pyproject.toml at root
3. Proper package publishing

## Consequences

### Positive
- Clear documentation hierarchy
- Easier navigation
- Validation catches issues early
- Preserved git history
- Easy rollback via tag

### Negative
- Some file moves create churn in git history
- Existing scripts may need path updates
- Team needs to learn new locations

### Neutral
- Source code structure unchanged
- Existing imports continue to work

## Validation

The refactor is considered successful when:
1. `bash scripts/validate_repo.sh` passes
2. All existing tests pass
3. Entry points documented and working
4. Legacy tag pushed and restorable
