# Acceptance Tests

Run from repository root.

## G3 Test Command
$ python3 Control_Plane/scripts/validate_spec_pack.py --target SPEC-003 && python3 Control_Plane/scripts/validate_work_item.py Control_Plane/docs/specs/SPEC-003/work_items/WI-003-01.md

## Automated Smoke Tests

All tests are executed by `bash Control_Plane/scripts/flow_smoke_check.sh --spec=SPEC-003`

### Test 1: Valid Work Item Passes G0
**Automated in:** Step 8 of flow_smoke_check.sh

Verifies:
- G0 passes with MODE=COMMIT and valid WORK_ITEM_PATH
- Evidence includes: work_item_path, work_item_id, work_item_hash
- work_item_validated = true

### Test 2: Invalid Work Item Fails G0
**Automated in:** Step 9 of flow_smoke_check.sh

Verifies:
- G0 fails when WORK_ITEM_PATH points to an invalid work item
- Failure message contains "validation failed"

### Test 3: Tampered Work Item Fails G0 (Hash Mismatch)
**Automated in:** Step 10 of flow_smoke_check.sh

Verifies:
- G0 fails when work item content has been modified
- Failure message contains "hash mismatch"
- Evidence includes expected_hash and actual_hash

## Manual Validation Commands

### Validate Work Item Schema
```bash
python3 Control_Plane/scripts/validate_work_item.py Control_Plane/docs/specs/SPEC-003/work_items/WI-003-01.md
```
Expected: Exit code 0.

### Reject Invalid Work Item
```bash
python3 Control_Plane/scripts/validate_work_item.py Control_Plane/docs/specs/SPEC-003/work_items/WI-003-02-invalid.md
```
Expected: Non-zero exit code.

### Validate Spec Pack
```bash
python3 Control_Plane/scripts/validate_spec_pack.py --target SPEC-003
```
Expected: VALID (warnings acceptable).
