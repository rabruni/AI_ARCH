# Testing Strategy

**Spec:** Design Framework Integration (PROOF-001)

---

## Test Plan Overview

| Test Type | Coverage Goal | Owner |
|-----------|---------------|-------|
| Unit | N/A (scripts) | Claude |
| Integration | Key paths | Claude |
| E2E | Full workflow | Claude |

---

## Integration Tests

### Test Cases

| ID | Description | Input | Expected Output |
|----|-------------|-------|-----------------|
| IT-001 | Create spec pack | --target TEST-001 | Exit 0, 8 files created |
| IT-002 | G0 on incomplete pack | Spec with placeholders | Exit 1 |
| IT-003 | G0 on complete pack | Spec without placeholders | Exit 0 |
| IT-004 | G1 on valid pack | Complete spec pack | Exit 0 |
| IT-005 | G1 on missing pack | Non-existent target | Exit 2 |
| IT-006 | All gates pass | Complete spec pack | Exit 0 |

### Test Commands

```bash
# IT-001: Create spec pack
python3 Control_Plane/scripts/apply_spec_pack.py --target TEST-001
# Expected: Exit 0

# IT-002: G0 on incomplete pack (has placeholders)
python3 Control_Plane/cp.py gate G0 TEST-001
# Expected: Exit 1 (placeholders detected)

# IT-003 through IT-006: Use PROOF-001 after completion
python3 Control_Plane/cp.py gate --all PROOF-001
# Expected: Exit 0
```

---

## End-to-End Tests

### User Flows

| ID | Flow | Steps | Expected Result |
|----|------|-------|-----------------|
| E2E-001 | Complete workflow | apply, fill, gate --all | Exit 0, logs created |

### E2E-001 Commands

```bash
# 1. Create spec pack
python3 Control_Plane/scripts/apply_spec_pack.py --target E2E-001

# 2. Fill out all files (remove placeholders)
# ... manual or scripted ...

# 3. Run all gates
python3 Control_Plane/cp.py gate --all E2E-001
# Expected: Exit 0

# 4. Verify logs exist
ls Control_Plane/docs/specs/E2E-001/artifacts/gate_logs/
# Expected: G0_*.log, G1_*.log
```

---

## Edge Cases

| Case | Input | Expected Handling |
|------|-------|-------------------|
| Empty directory | No files | G0 fails (missing files) |
| Partial files | 5 of 8 files | G0 fails (missing files) |
| Uppercase placeholder | "todo" | G0 passes (case-sensitive word boundary) |
| Inline placeholder | "This is not a placeholder" | G0 passes (word boundary) |
| Missing target | Non-existent ID | Exit 2 |

---

## Verification Commands

```bash
# Verify gate.py exists and runs
python3 Control_Plane/scripts/gate.py --help

# Verify cp.py gate command works
python3 Control_Plane/cp.py gate G0 PROOF-001

# Verify apply-spec command works
python3 Control_Plane/cp.py apply-spec --target VERIFY-001 --force

# Cleanup
rm -rf Control_Plane/docs/specs/VERIFY-001
```

---

## Verification Checklist

- [x] apply_spec_pack.py creates correct structure
- [x] G0 detects missing files
- [x] G0 detects forbidden placeholders
- [x] G1 calls validate_spec_pack.py
- [x] Gate logs are written
- [x] cp.py commands work
- [x] Exit codes are correct
