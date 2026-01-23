# Design

## Components

### check_runbook_complete.py

Validates markdown file has no TODO/TBD placeholders.

### Interface Contract Runbook

Defines human-control plane-agent contract with sections for Purpose, Scope, Workflow, Artifacts, Validation.

### G3 Test Command

```bash
$ python3 Control_Plane/scripts/validate_spec_pack.py --target SPEC-002 && python3 Control_Plane/scripts/check_runbook_complete.py Control_Plane/runbooks/llm_quality/interface_contract.md
```
