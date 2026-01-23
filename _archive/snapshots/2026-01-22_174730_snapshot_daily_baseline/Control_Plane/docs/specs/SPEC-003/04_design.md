# Design Specification

## 1. `WORK_ITEM.md` Schema

The artifact consists of YAML front matter (machine-parseable) and structured Markdown sections (human-readable).

### YAML Front Matter (required)
```yaml
---
ID: <Unique ID, e.g., WI-003-01>
Title: <Human-readable title>
Status: <DRAFT | READY | IN_PROGRESS | SUCCEEDED | FAILED>
ALTITUDE: <L4 | L3 | L2 | L1>
---
```

### Required Sections (required headings)

## Objective
A single-sentence, measurable goal for the work.

## Scope: File Permissions
A list of files the agent is authorized to read/modify.

- **MODIFIABLE:**
  - path/to/file_to_change.py
- **READ_ONLY:**
  - path/to/dependency.py

## Implementation Plan
A numbered, sequential, imperative list of steps for the agent.

## Execution Guardrails
- **ASK_CONDITIONS:** if any are true, stop and request clarification.
- **STOP_CONDITIONS:** terminal conditions for success/failure.

## Acceptance Commands
A list of shell commands that verify the Objective; all must exit 0 for success.

## 2. Validation Script: `validate_work_item.py`
A new script `Control_Plane/scripts/validate_work_item.py` will validate:
- YAML front matter exists and includes: ID, Title, Status, ALTITUDE.
- Required sections exist.
- MODIFIABLE list is not empty.
- Acceptance Commands list is not empty.
- Scope paths do not target forbidden directories (e.g. `.git/`, `.github/`, `Control_Plane/`).
(Implementation deferred; spec-only here.)

## 3. Commit Integration
For now, `08_commit.md` will continue using the existing G0-compatible schema (MODE/ALTITUDE/REFERENCES/STOP CONDITIONS). The `WORK_ITEM.md` reference is carried as an additional line in REFERENCES.

Example reference line:
- Work Item: work_items/WI-003-01.md
