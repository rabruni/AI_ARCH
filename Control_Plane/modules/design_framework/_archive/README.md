# Archived / Deprecated Items

**Status:** Deprecated
**Archived:** 2026-01-16

---

## Contents

### spec_pack/

The inner `spec_pack/` templates have been deprecated in favor of the canonical 8-file template set.

**Canonical templates:** `Control_Plane/modules/design_framework/templates/`

The canonical set includes:
- `00_overview.md`
- `01_problem.md`
- `02_solution.md`
- `03_requirements.md`
- `04_design.md`
- `05_testing.md`
- `06_rollout.md`
- `07_registry.md`

### apply_spec_pack_deprecated.py

The module-local apply script has been deprecated. It pointed to the old `spec_pack/` templates which no longer exist.

**Canonical script:** `Control_Plane/scripts/apply_spec_pack.py`

---

## Why Archived

1. **spec_pack/ templates:** Used a different file structure (ARCHITECTURE.md, BEHAVIOR.md, etc.) that was inconsistent with the 8-file canonical set.

2. **apply_spec_pack.py:** Pointed to non-existent `../templates/spec_pack/` directory and did not enforce the `Control_Plane/docs/specs/` landing zone.

To eliminate confusion and ensure deterministic behavior, only the canonical scripts at `Control_Plane/scripts/` are now supported.

---

## Do Not Use

Do not use any items from this archive directory. Use the canonical paths:
- Templates: `Control_Plane/modules/design_framework/templates/`
- Apply script: `Control_Plane/scripts/apply_spec_pack.py`
- Validate script: `Control_Plane/scripts/validate_spec_pack.py`
- Gate script: `Control_Plane/scripts/gate.py`
