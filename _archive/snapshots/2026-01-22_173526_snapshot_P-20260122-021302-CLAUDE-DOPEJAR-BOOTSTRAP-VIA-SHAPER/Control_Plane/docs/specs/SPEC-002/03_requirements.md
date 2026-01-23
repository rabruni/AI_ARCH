# Requirements

## Functional Requirements

| ID | Requirement | Verification |
|----|-------------|--------------|
| R1 | Runbook contains no TODO markers | check_runbook_complete.py exits 0 |
| R2 | Spec pack passes validation | validate_spec_pack.py exits 0 |
| R3 | G3 gate produces evidence log | G3.log exists after flow run |

## Acceptance Criteria

- flow_smoke_check.sh --spec=SPEC-002 exits 0
- gate_results.json shows G1, G2, G3 all passed
