# Acceptance Tests

Run from repository root.

## G3 Test Command
$ python3 Control_Plane/scripts/validate_spec_pack.py --target SPEC-003 && python3 Control_Plane/scripts/validate_work_item.py Control_Plane/docs/specs/SPEC-003/work_items/WI-003-01.md

## Test 1: Validate a Correct Work Item (after implementation exists)
Command:
```bash
python3 Control_Plane/scripts/validate_work_item.py Control_Plane/docs/specs/SPEC-003/work_items/WI-003-01.md
```

Expected:
Exit code 0.

## Test 2: Reject an Invalid Work Item (after implementation exists)
Command:
```bash
python3 Control_Plane/scripts/validate_work_item.py Control_Plane/docs/specs/SPEC-003/work_items/WI-003-02-invalid.md
```

Expected:
Non-zero exit code.

## Test 3: Spec Pack Validation (now)
Command:
```bash
python3 Control_Plane/scripts/validate_spec_pack.py --target SPEC-003
```

Expected:
VALID (warnings acceptable).
