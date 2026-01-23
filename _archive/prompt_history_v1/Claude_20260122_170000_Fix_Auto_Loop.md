---
id: P-20260122-170000-CLAUDE-FIX-AUTO-LOOP
target_agent: Claude
exec_order: 17
status: sent
---

# Goal: Fix and Refine Auto Loop Script

The `scripts/auto_loop.py` script successfully ran Claude but failed to run Gemini due to environment inheritance issues. We need to fix this and harden the logic.

## Tasks

1.  **Fix Environment Inheritance**:
    - In `dispatch_agent`, update `subprocess.Popen` to include `env=os.environ.copy()`. This ensures the subprocess inherits PATH, NVM, and other shell variables needed by the `gemini` and `claude` binaries.

2.  **Refine Task Deduplication**:
    - The current `get_next_task` logic checks `INDEX.md` for completion.
    - **Improvement**: Add a fallback check. If a feedback file exists in `_Prompt-Cache_` that matches the pattern `Agent_..._<PromptID>_Feedback.md` (or similar), assume the task is done even if the Index is out of sync.
    - Ensure `completed_prompts` set population is robust.

3.  **Harden Logging**:
    - Ensure all `print` statements use `flush=True`.
    - Log the *exact* command being run (masked if needed, but we don't use secrets in args).

## Quality Gate
- Run `python3 scripts/auto_loop.py --dry-run` (implement a dry run flag if needed, or just check syntax) to ensure it parses.
- Since you cannot easily "test" the loop without launching agents, code review correctness is paramount.

## Deliverables
- Updated `scripts/auto_loop.py`.
- Feedback file with the diff or summary of changes.
