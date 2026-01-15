# Repository Guidelines

## Boot Sequence (Do This First)

```
1. RUN:    python Control_Plane/scripts/init.py
2. VERIFY: All layers show [PASS]
3. READ:   Control_Plane/init/init.md
4. THEN:   Proceed with task
```

If any layer fails, fix before proceeding.

---

## Project Structure & Module Organization

- `Control_Plane/` holds the registry-driven governance layer. Source-of-truth CSV registries live in `Control_Plane/registries/`, with automation in `Control_Plane/scripts/` and generated artifacts in `Control_Plane/generated/`.
- `src/` contains application code and Python modules; keep business logic here.
- `tests/` mirrors `src/` for unit/integration/e2e coverage (e.g., `src/foo/bar.py` -> `tests/foo/test_bar.py`).
- `prompts/` stores prompt modules; `docs/` contains architecture and repo documentation; `_archive/` preserves historical snapshots.

## Build, Test, and Development Commands

- `python Control_Plane/scripts/validate_registry.py` — validate registry CSVs and schema assumptions.
- `python Control_Plane/scripts/apply_selection.py` — generate an execution plan into `Control_Plane/generated/plan.json`.
- `pytest` — run the test suite (uses `pytest` and `pytest-asyncio`).

## Coding Style & Naming Conventions

- Python-first codebase; use 4-space indentation and keep functions/variables in `snake_case`, classes in `PascalCase`.
- Test files should be named `test_*.py` and mirror module paths under `tests/`.
- No repository-wide formatter configuration is present; keep changes small and consistent with nearby code.

## Testing Guidelines

- Frameworks: `pytest` + `pytest-asyncio` (see `requirements.txt`).
- Prefer module-mirroring structure and focused tests per component.
- No explicit coverage target is documented; add tests for new behavior and edge cases.

## Commit & Pull Request Guidelines

- Recent history uses Conventional Commit-style prefixes (e.g., `feat:`) and often includes issue IDs like `BOOT-018`.
- PRs should explain the registry or module impact, include relevant command output (validation/tests), and link any associated issue/ticket.
- If changes touch registries, note which CSVs changed and whether `Control_Plane/generated/plan.json` was regenerated.

## Governance & References

- Follow `SYSTEM_CONSTITUTION.md` for repository-wide rules.
- Registries are the source of truth; IDs are primary keys and should remain stable.
