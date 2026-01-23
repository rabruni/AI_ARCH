---
id: F-20260122-DEBUG-CHALLENGE-CLAUDE
relates_to: P-20260122-DEBUG-CHALLENGE-CLAUDE
agent: Claude
status: complete
timestamp: 2026-01-22T20:35:00Z
---

# Debug Findings: auto_loop.py Silent Failure Analysis

## Summary

The script itself runs correctly (v3.0 starts and loops). The **real problem** is that agents receive a generic boot instruction but no information about which specific prompt file to execute.

---

## Root Cause: Prompt File Never Passed to Agent

**Location:** `scripts/auto_loop.py:258-264`

```python
cmd = AGENTS[agent_name].copy()

# Log the specific task being dispatched
log(f"DISPATCHING: {agent_name} -> {prompt_id}")
if prompt_file:
    log(f"  Prompt file: {prompt_file}")  # LOGGED but not USED
log(f"  Command: {' '.join(cmd)}")
```

The `prompt_file` is logged but **never appended to `cmd`**. The agent receives:
```
"Follow Startup & Activation Protocol in AGENTS.md"
```

But should receive something like:
```
"Execute prompt: /_Prompt-Cache_/Claude_Debug_Challenge.md"
```

---

## Impact

Agents launch successfully but:
1. Run generic boot sequence
2. Check STATUS.md for "their" task
3. May pick wrong task or get confused
4. Don't know the specific prompt_id they're supposed to execute

This explains why agents "don't follow well" - they're not given explicit instructions.

---

## Proposed Fix

**Option A: Inject prompt file path into command**

```python
def dispatch_agent(task):
    agent_name = task["agent"]
    prompt_id = task["id"]
    prompt_file = task.get("file", "")

    if agent_name not in AGENTS:
        log(f"Error: Unknown agent {agent_name}")
        return False

    cmd = AGENTS[agent_name].copy()

    # INJECT: Add specific prompt file to command
    if prompt_file:
        prompt_path = f"/_Prompt-Cache_/{prompt_file}"
        # Replace generic instruction with specific one
        cmd[-1] = f"Execute prompt at {prompt_path}. Read and follow instructions in that file."

    log(f"DISPATCHING: {agent_name} -> {prompt_id}")
    log(f"  Prompt file: {prompt_file}")
    log(f"  Command: {' '.join(cmd)}")
    # ... rest of function
```

**Option B: Read prompt content and inject directly**

```python
# Read prompt content and pass it directly
if prompt_file:
    prompt_path = PROMPT_CACHE / prompt_file
    if prompt_path.exists():
        prompt_content = prompt_path.read_text()
        cmd[-1] = f"Execute this task:\n\n{prompt_content}"
```

---

## Secondary Issues Identified

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Hardcoded paths | Lines 40-42 | Medium | Absolute paths won't work on other machines |
| No task-specific instruction | Lines 258-264 | **Critical** | Root cause of agent confusion |
| Generic AGENTS dict | Lines 39-43 | Low | Could use `shutil.which()` for portability |

---

## Verification Steps

After applying fix:
1. Run `python3 scripts/auto_loop.py`
2. Observe log output - should show specific prompt path in command
3. Agent should execute the specific prompt, not generic boot sequence
4. Check feedback file is created for the correct prompt_id

---

## Constraint Note

Per challenge instructions, I have **not applied the fix**. This is a report only.
