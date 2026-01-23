# Testing

$ python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001

Manual checks:
- Confirm `source_context/` exists and is read-only reference material.
- Confirm Shaper artifacts (when created) live in `artifacts/` and are not hand-edited.
