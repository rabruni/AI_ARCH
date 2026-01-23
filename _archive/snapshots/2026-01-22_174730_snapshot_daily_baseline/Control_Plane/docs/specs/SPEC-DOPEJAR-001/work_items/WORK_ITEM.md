---
ID: WI-DOPEJAR-BOOTSTRAP-001
Title: Bootstrap SPEC-DOPEJAR-001 for Dopejar
Status: Draft
ALTITUDE: L3
---

## Objective
- Create SPEC-DOPEJAR-001 spec pack and archive context packet for shaping Dopejar from the_assist.

## Scope: File Permissions
- Control_Plane/docs/specs/SPEC-DOPEJAR-001/
- _Prompt-Cache_/

## Implementation Plan
1. Create spec pack skeleton (apply-spec).
2. Create source_context/ with deterministic tree + notes from _archive/.../the_assist/.
3. Ensure work_items/ exists for Shaper output.

## Acceptance Commands
- python3 Control_Plane/cp.py apply-spec --target SPEC-DOPEJAR-001
- test -d Control_Plane/docs/specs/SPEC-DOPEJAR-001/work_items
- test -d Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context
- test -f Control_Plane/docs/specs/SPEC-DOPEJAR-001/source_context/the_assist_TREE.txt
