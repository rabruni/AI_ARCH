---
id: P-20260122-FIX-AUTO-LOOP-LOGIC
target_agent: Claude
status: complete
relates_to: F-20260122-DEBUG-CHALLENGE-CLAUDE, F-20260122-DEBUG-CHALLENGE-CODEX
---

# Goal: Fix Auto Loop Dispatch and Logging Logic

Both Claude and Codex have diagnosed that `scripts/auto_loop.py` fails to pass the specific task instruction to the agent subprocess, and swallows stdout.

## Tasks

1.  **Fix Task Dispatch**:
    - Modify `dispatch_agent` in `scripts/auto_loop.py`.
    - Retrieve the `prompt_file` (from `task["line"]` parsing or passed in `task` dict).
    - Update the CLI command (`cmd`) to include the specific prompt file.
    - **Format**: Append `" Then execute task: /_Prompt-Cache_/<PromptFile>"` to the existing startup protocol string.

2.  **Fix Logging Visibility**:
    - Currently, `process.communicate()` captures stdout but only logs it if `returncode != 0`.
    - **Change**: Log `stdout` (trimmed to last 20 lines or summary) even on **Success**. This ensures `auto_loop.log` shows activity.

3.  **Refine Task Parsing**:
    - Ensure `get_next_task` correctly extracts the filename from the `INDEX.md` line so it can be passed to `dispatch_agent`.

## Quality Gate
- Syntax check the script.
- Ensure no hardcoded paths are broken (keep the ones we have for now, or use `shutil.which` if you want to be fancy, but robustness is priority).

## Deliverables
- Updated `scripts/auto_loop.py`.
- Feedback file confirming the changes.
