---
id: P-20260122-ADD-PTY-SUPPORT
target_agent: Claude
exec_order: 22
status: sent
---

# Goal: Fix Stdin Issue in Auto Loop

The `auto_loop.py` script is failing to launch agents with the error: `Error: stdin is not a terminal`.

## Task
Modify `scripts/auto_loop.py` to run agent commands using a **Pseudo-Terminal (PTY)**.

1.  Use the `pty` module.
2.  Wrap the `subprocess.Popen` or use `pty.spawn` to trick the agent into thinking it's in a real terminal.
3.  Ensure stdout/stderr are still captured correctly.

## Deliverable
- Updated `scripts/auto_loop.py` that works in the background without TTY errors.
