# Commit Manifest

## MODE
EXPLORE

## ALTITUDE
L4

## REFERENCES
goal: Rebuild/migrate the archived `the_assist` system into Dopejar under Control Plane governance.
non-goals: Do not execute tasks or implement code during shaping; do not modify `_archive/`.
acceptance: `python3 Control_Plane/cp.py validate-spec --target SPEC-DOPEJAR-001` returns VALID.

## STOP CONDITIONS
- Stop if any required spec pack files are missing or validation reports errors.
