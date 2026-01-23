---
ID: SPEC-DOPEJAR-001-WI-ARCHIVE-MOVE-001
Title: Move the_assist archive into Dopejar resident (scaffold + import)
Status: draft
ALTITUDE: L3
---

## Objective
- Migrate the_assist source code from the read-only archive into a governed location under Control Plane as the Dopejar module.
- This work item covers SPEC-DOPEJAR-001 Phase 1 (Analysis) and Phase 2 (Migration).

## Scope: File Permissions
- READ: `_archive/2026-01-14_repo-archive_v1/the_assist/` (entire directory tree)
- READ: `Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/` (context files)
- WRITE: `Control_Plane/modules/dopejar/` (new directory to create)
- WRITE: `Control_Plane/registries/control_plane_registry.csv` (for Phase 3, separate work item)

## Implementation Plan
1. Create scaffold directory: `Control_Plane/modules/dopejar/`
2. Copy core module: `_archive/.../the_assist/core/` → `Control_Plane/modules/dopejar/core/`
3. Copy HRM module: `_archive/.../the_assist/hrm/` → `Control_Plane/modules/dopejar/hrm/`
4. Copy adapters module: `_archive/.../the_assist/adapters/` → `Control_Plane/modules/dopejar/adapters/`
5. Copy config module: `_archive/.../the_assist/config/` → `Control_Plane/modules/dopejar/config/`
6. Copy personality module: `_archive/.../the_assist/personality/` → `Control_Plane/modules/dopejar/personality/`
7. Copy prompts directory: `_archive/.../the_assist/prompts/` → `Control_Plane/modules/dopejar/prompts/`
8. Copy entry points: `main.py`, `main_hrm.py`, `main_locked.py` → `Control_Plane/modules/dopejar/`
9. Copy `__init__.py` → `Control_Plane/modules/dopejar/`
10. Do NOT copy: `__pycache__/`, `memory/`, `feedback/`, `docs/` (runtime artifacts and docs excluded)

## Acceptance Commands
- `ls -la Control_Plane/modules/dopejar/` shows scaffold exists with expected subdirectories
- `ls Control_Plane/modules/dopejar/core/` shows orchestrator.py, hrm_agent.py, perception_agent.py, memory_v2.py
- `ls Control_Plane/modules/dopejar/hrm/` shows loop.py, executor.py, planner.py, evaluator.py
- `ls Control_Plane/modules/dopejar/` shows main.py, main_hrm.py, main_locked.py
- `python3 -c "import sys; sys.path.insert(0, 'Control_Plane/modules'); from dopejar import main_locked"` returns exit 0
