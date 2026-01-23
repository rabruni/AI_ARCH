# Requirements

1. **REQ-001:** The system MUST define a formal schema for a `WORK_ITEM.md` artifact.
2. **REQ-002:** The `WORK_ITEM.md` schema MUST include mandatory sections for: unique ID, title, status, objective, file scope, step-by-step implementation plan, and programmatic acceptance commands.
3. **REQ-003:** The system MUST provide a deterministic validation script, `Control_Plane/scripts/validate_work_item.py`, that exits with code 0 if a `WORK_ITEM.md` is valid and a non-zero code otherwise.
4. **REQ-004:** The commit process MUST reference a single `WORK_ITEM.md` file for execution.
5. **REQ-005:** Gate logic MUST be able to find and validate the referenced `WORK_ITEM.md` before worker execution (implementation deferred; spec-only here).
