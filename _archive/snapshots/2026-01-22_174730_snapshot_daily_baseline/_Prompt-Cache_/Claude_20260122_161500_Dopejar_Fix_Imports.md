---
id: P-20260122-161500-CLAUDE-DOPEJAR-FIX-IMPORTS
target_agent: Claude
exec_order: 11
status: sent
relates_to: P-20260122-024732-CLAUDE-DOPEJAR-SHAPE-L3-WORKITEMS-ARCHIVE-MOVE
---

# Goal: Refactor Dopejar Module Imports

The migration of `the_assist` to the `dopejar` module is structurally complete, but the code is non-functional because internal imports still reference `the_assist`.

## Task
You must refactor all Python files in `Control_Plane/modules/dopejar/` to update internal references.

1.  **Search & Replace**:
    - Change `from the_assist` to `from dopejar`
    - Change `import the_assist` to `import dopejar`
2.  **Scope**: All `.py` files under `Control_Plane/modules/dopejar/` recursively.

## Quality Gate (Mandatory)
You MUST execute the following smoke test before reporting completion:

```bash
./venv/bin/python3 -c "import sys; sys.path.insert(0, 'Control_Plane/modules'); from dopejar import main_locked; print('IMPORT SUCCESS')"
```

## Deliverables
1.  **Modified Files**: Update the files in place.
2.  **Run Log**: You MUST include the output of the smoke test in your feedback file.
3.  **Feedback File**: Create `/_Prompt-Cache_/Claude_20260122_161500_Dopejar_Fix_Imports_Feedback.md` and record the result.

**Constraint**: Do not modify application logic. Only change import paths.
