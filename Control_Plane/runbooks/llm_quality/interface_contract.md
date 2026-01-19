# Interface Contract

## Purpose

This contract governs interactions between humans, the Control Plane, and worker agents. It defines the handoff protocol for work items, ensuring that all parties understand their responsibilities, required artifacts, and validation criteria before, during, and after task execution.

## Scope

**In Scope:**
- Work item shaping and approval workflow
- Prompt and context packaging for worker agents
- Evidence collection and validation requirements
- Human review checkpoints and escalation paths

**Out of Scope:**
- Internal agent implementation details
- Infrastructure provisioning
- CI/CD pipeline configuration

## Workflow

1. **Shaping**: Human defines work item with clear goals, constraints, and acceptance criteria
2. **Registration**: Work item is registered in the Control Plane with status=pending
3. **Prompt Assembly**: Control Plane assembles prompt from templates + context
4. **Execution**: Worker agent receives prompt and produces artifacts
5. **Gate Validation**: Control Plane runs gates (G0-G3) on produced artifacts
6. **Review**: Human reviews evidence logs and gate results
7. **Completion**: Work item marked complete or routed back for fixes

## Artifacts

| Artifact | Owner | Purpose |
|----------|-------|---------|
| WORK_ITEM.md | Human | Defines goals, scope, and acceptance criteria |
| Prompt.md | Control Plane | Assembled prompt sent to worker agent |
| output.txt | Worker Agent | Raw output from agent execution |
| gate_results.json | Control Plane | Pass/fail status for each gate |
| G3.log | Control Plane | Test command execution log |

## Validation

**Compliance Checks:**
- Work item has non-empty goals and acceptance criteria
- Prompt references correct spec pack and context
- All required artifacts exist after execution
- Gate results show no FAILED status without resolution

**Failure Modes:**
- Missing artifact: Route back to execution phase
- Gate failure: Check category, route to appropriate phase
- Escalation: Human intervention required when max retries exceeded
