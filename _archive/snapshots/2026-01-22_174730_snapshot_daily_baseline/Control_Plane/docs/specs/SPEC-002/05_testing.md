# Testing

## Acceptance Test

```bash
$ python3 Control_Plane/scripts/validate_spec_pack.py --target SPEC-002 && python3 Control_Plane/scripts/check_runbook_complete.py Control_Plane/runbooks/llm_quality/interface_contract.md
```

## Gate Expectations

| Gate | Expected |
|------|----------|
| G0 | PASSED |
| G1 | PASSED |
| G2 | PASSED |
| G3 | PASSED |
