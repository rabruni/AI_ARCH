---
id: F-20260122-DEBUG-CHALLENGE-CODEX
relates_to: P-20260122-DEBUG-CHALLENGE-CODEX
agent: Codex
status: complete
---

# Debug Findings: auto_loop.py Silent Failure

## Summary
The loop itself runs, but dispatched agents are not given the prompt file they are supposed to execute. They receive only a generic startup instruction, so they either do nothing useful or act on the wrong task. This makes the run look "silent" even though the subprocess exits cleanly.

## Root Cause
**Location:** `scripts/auto_loop.py` in `dispatch_agent()`

`prompt_file` is logged but never appended to the command. The subprocess receives only:
```
Follow Startup & Activation Protocol in AGENTS.md
```
which is insufficient to locate the specific task.

## Proposed Fix (snippet)
Pass the prompt file path (or its contents) into the agent command so it executes the intended task.

```python
    cmd = AGENTS[agent_name].copy()

    if prompt_file:
        prompt_path = PROMPT_CACHE / prompt_file
        # Replace the generic instruction with a task-specific one
        cmd[-1] = (
            f"Follow Startup & Activation Protocol in AGENTS.md. "
            f"Execute your challenge: {prompt_path}"
        )
```

Alternative (inline content):
```python
    if prompt_file:
        prompt_path = PROMPT_CACHE / prompt_file
        if prompt_path.exists():
            prompt_text = prompt_path.read_text()
            cmd[-1] = f"Execute this task:\n\n{prompt_text}"
```

## Secondary Contributors (not primary root cause)
- **Silent output:** `stdout` is captured but never logged; only non-zero `stderr` is emitted, so successful runs look empty.
- **Hardcoded paths:** `AGENTS` uses absolute binary paths; on a different machine, `subprocess.Popen` will raise `FileNotFoundError` and the agent never launches.

## Constraint Note
Per instructions, I did not apply changes; this is a report only.
