#!/usr/bin/env python3
"""
Auto Loop - Refined Agent Orchestration (v3.1)

Purpose: Watches _Prompt-Cache_/INDEX.md for 'sent' tasks and dispatches agents.
Features:
- Daily Snapshotting (Once every 24h)
- Git Checkpoints (Commit on PASS)
- Intelligent Task Selection (Column-based completion detection)
- Retry Logic with MAX_RETRIES
- File Locking to prevent duplicate dispatches
- Verbose Unbuffered Logging

Usage: python3 scripts/auto_loop.py
"""

import time
import subprocess
import sys
import re
import datetime
import fcntl
import os
from pathlib import Path

# Config
POLL_INTERVAL = 15
MAX_RETRIES = 3
RETRY_DELAY = 60
PROMPT_CACHE = Path("_Prompt-Cache_")
INDEX_FILE = PROMPT_CACHE / "INDEX.md"
STATUS_FILE = PROMPT_CACHE / "STATUS.md"
LOCK_FILE = Path(".auto_loop.lock")

# Agent Commands (Absolute Paths)
# Claude: --dangerously-skip-permissions bypasses confirmations, -p is print mode, prompt is positional
# Gemini: --yolo auto-approves actions, prompt is positional (deprecated -p flag removed)
# Codex: --dangerously-bypass-approvals-and-sandbox for full auto, prompt is positional
AGENTS = {
    "Claude": ["/Users/raymondbruni/.local/bin/claude", "--dangerously-skip-permissions", "-p", "Follow Startup & Activation Protocol in AGENTS.md"],
    "Gemini": ["/Users/raymondbruni/.nvm/versions/node/v24.13.0/bin/gemini", "--yolo", "Follow Startup & Activation Protocol in AGENTS.md"],
    "Codex": ["/Users/raymondbruni/.nvm/versions/node/v24.13.0/bin/codex", "--dangerously-bypass-approvals-and-sandbox", "Follow Startup & Activation Protocol in AGENTS.md"]
}

# Track retry counts per task
retry_counts = {}

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def acquire_lock():
    """Acquire exclusive lock to prevent multiple instances."""
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        return lock_fd
    except (IOError, OSError):
        return None

def release_lock(lock_fd):
    """Release the lock."""
    if lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        LOCK_FILE.unlink(missing_ok=True)

def daily_snapshot():
    """Run snapshot only once per day."""
    snapshot_flag = Path(".daily_snapshot_done")
    today = datetime.date.today().isoformat()

    if snapshot_flag.exists() and snapshot_flag.read_text().strip() == today:
        return

    log("Performing Daily Baseline Snapshot...")
    try:
        subprocess.run(["python3", "scripts/snapshot.py", "daily_baseline"], check=True)
        snapshot_flag.write_text(today)
    except Exception as e:
        log(f"Snapshot error (non-fatal): {e}")

def create_checkpoint(agent_name, prompt_id):
    """Commit changes to git after a successful run."""
    log(f"Creating Git Checkpoint for {prompt_id}...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", f"auto: {agent_name} completed {prompt_id}"], check=True)
        log("Git Checkpoint Saved.")
    except Exception as e:
        log(f"Git Checkpoint Error: {e}")

def parse_table_row(line):
    """Parse a markdown table row into columns.

    Returns dict with: created_local, exec_order, type, target_agent,
                       prompt_id, status, file, relates_to, goal
    Or None if not a valid data row.
    """
    if not line.strip().startswith("|"):
        return None

    parts = [p.strip() for p in line.split("|")]
    # After split: ['', col1, col2, ..., '']
    # So actual columns are parts[1:-1] or we access by parts[1], parts[2], etc.

    if len(parts) < 10:  # Need at least 10 parts for 9 columns + empty ends
        return None

    # Skip header and separator rows
    if "created_local" in parts[1] or "---" in parts[1]:
        return None

    return {
        "created_local": parts[1],
        "exec_order": parts[2],
        "type": parts[3].lower(),
        "target_agent": parts[4],
        "prompt_id": parts[5].strip(' `'),
        "status": parts[6].lower(),
        "file": parts[7].strip(' `'),
        "relates_to": parts[8].strip(' `'),
        "goal": parts[9] if len(parts) > 9 else ""
    }

def get_feedback_files_on_disk():
    """Scan _Prompt-Cache_ for feedback files that may not be in INDEX.md.

    Returns a dict mapping prompt file stems to their feedback files.
    E.g., 'Gemini_20260122_163000_Auto_Success_Val' -> 'Gemini_20260122_163000_Auto_Success_Val_Feedback.md'
    """
    feedback_files = {}
    if PROMPT_CACHE.exists():
        for f in PROMPT_CACHE.glob("*_Feedback.md"):
            # Extract the base prompt file name (strip _Feedback.md suffix)
            base_name = f.stem.replace("_Feedback", "")
            feedback_files[base_name] = f.name
    return feedback_files

def get_completed_prompts(lines):
    """Get set of prompt IDs that are completed.

    A prompt is complete if:
    1. It has status='complete' (the prompt itself is done)
    2. There's a feedback row with type='feedback' that relates_to it
    3. There's a feedback row with status='passed' or 'complete' that relates_to it
    4. A feedback file exists on disk for the prompt (even if not in INDEX.md)
    """
    completed = set()

    # First, check INDEX.md entries
    for line in lines:
        row = parse_table_row(line)
        if not row:
            continue

        # Case 1: Prompt itself has status=complete
        if row["type"] == "prompt" and row["status"] == "complete":
            completed.add(row["prompt_id"])

        # Case 2: Feedback row exists for a prompt
        if row["type"] == "feedback" and row["relates_to"]:
            completed.add(row["relates_to"])

        # Case 3: Any row with status passed/complete that relates to something
        if row["status"] in ("passed", "complete") and row["relates_to"]:
            completed.add(row["relates_to"])

    # Case 4: Check for feedback files on disk that may not be indexed
    # Build a mapping of file stems to prompt IDs
    file_to_prompt = {}
    for line in lines:
        row = parse_table_row(line)
        if row and row["type"] == "prompt" and row["file"]:
            # Strip .md extension and backticks
            file_stem = row["file"].replace(".md", "").strip('` ')
            file_to_prompt[file_stem] = row["prompt_id"]

    # Check for feedback files on disk
    feedback_files = get_feedback_files_on_disk()
    for file_stem, feedback_file in feedback_files.items():
        if file_stem in file_to_prompt:
            prompt_id = file_to_prompt[file_stem]
            if prompt_id not in completed:
                log(f"Found feedback file on disk for {prompt_id}: {feedback_file}")
                completed.add(prompt_id)

    return completed

def get_next_task():
    """Parse INDEX.md for the next 'sent' task that hasn't been answered."""
    if not INDEX_FILE.exists():
        return None

    content = INDEX_FILE.read_text()
    lines = content.splitlines()

    # Get all completed prompt IDs
    completed_prompts = get_completed_prompts(lines)

    # Find the first 'sent' prompt NOT in the completed set
    # Prefer tasks with exec_order (sorted by exec_order)
    candidates = []

    for line in lines:
        row = parse_table_row(line)
        if not row:
            continue

        # Only process prompts (not feedback)
        if row["type"] != "prompt":
            continue

        # Only sent status
        if row["status"] != "sent":
            continue

        # Only known agents
        if row["target_agent"] not in AGENTS:
            continue

        # Skip if already completed
        if row["prompt_id"] in completed_prompts:
            continue

        # Skip if max retries exceeded
        if retry_counts.get(row["prompt_id"], 0) >= MAX_RETRIES:
            log(f"Skipping {row['prompt_id']} - max retries ({MAX_RETRIES}) exceeded")
            continue

        candidates.append({
            "agent": row["target_agent"],
            "id": row["prompt_id"],
            "exec_order": int(row["exec_order"]) if row["exec_order"].isdigit() else 9999,
            "file": row["file"],
            "line": line
        })

    if not candidates:
        return None

    # Sort by exec_order and return first
    candidates.sort(key=lambda x: x["exec_order"])
    return candidates[0]

def dispatch_agent(task):
    """Dispatch an agent to handle a task."""
    agent_name = task["agent"]
    prompt_id = task["id"]
    prompt_file = task.get("file", "")

    if agent_name not in AGENTS:
        log(f"Error: Unknown agent {agent_name}")
        return False

    cmd = AGENTS[agent_name].copy()

    # FIX: Append specific prompt file to the command instruction
    if prompt_file:
        prompt_path = f"/_Prompt-Cache_/{prompt_file}"
        # Modify the last argument (the instruction) to include the specific task
        cmd[-1] = cmd[-1] + f" Then execute task: {prompt_path}"

    # Log the specific task being dispatched
    log(f"DISPATCHING: {agent_name} -> {prompt_id}")
    if prompt_file:
        log(f"  Prompt file: {prompt_file}")
    log(f"  Command: {' '.join(cmd)}")

    try:
        # Run agent and capture output
        # IMPORTANT: env=os.environ.copy() ensures PATH, NVM, and shell vars are inherited
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path.cwd()),  # Ensure we're in repo root
            env=os.environ.copy()  # Inherit parent environment (PATH, NVM, etc.)
        )
        stdout, stderr = process.communicate(timeout=600)  # 10 minute timeout

        # FIX: Log stdout summary even on success for visibility
        if stdout:
            stdout_lines = stdout.strip().split('\n')
            summary_lines = stdout_lines[-20:] if len(stdout_lines) > 20 else stdout_lines
            log(f"  Agent output ({len(stdout_lines)} lines, last 20):")
            for line in summary_lines:
                log(f"    | {line[:200]}")  # Truncate long lines

        if process.returncode == 0:
            log(f"SUCCESS: {agent_name} cycle complete.")
            # Reset retry count on success
            retry_counts[prompt_id] = 0
            create_checkpoint(agent_name, prompt_id)
            return True
        else:
            log(f"FAILURE: Agent exited with code {process.returncode}")
            if stderr:
                log(f"Stderr: {stderr[:500]}")  # Truncate long errors
            return False

    except subprocess.TimeoutExpired:
        log(f"TIMEOUT: Agent exceeded 10 minute limit")
        process.kill()
        return False
    except Exception as e:
        log(f"EXCEPTION: {e}")
        return False

def main():
    log("Auto Loop Engine v3.1 Starting...")

    # Acquire lock
    lock_fd = acquire_lock()
    if not lock_fd:
        log("ERROR: Another instance is already running (lock file exists)")
        sys.exit(1)

    log("Lock acquired. Starting main loop...")

    try:
        daily_snapshot()

        while True:
            task = get_next_task()
            if task:
                prompt_id = task["id"]
                log(f"Next Task: {prompt_id} assigned to {task['agent']} (exec_order: {task['exec_order']})")

                if not dispatch_agent(task):
                    # Increment retry count
                    retry_counts[prompt_id] = retry_counts.get(prompt_id, 0) + 1
                    remaining = MAX_RETRIES - retry_counts[prompt_id]

                    if remaining > 0:
                        log(f"Retry {retry_counts[prompt_id]}/{MAX_RETRIES} - waiting {RETRY_DELAY}s...")
                        time.sleep(RETRY_DELAY)
                    else:
                        log(f"Max retries reached for {prompt_id}. Moving to next task.")
                        time.sleep(POLL_INTERVAL)
                else:
                    log(f"Cooldown {POLL_INTERVAL}s...")
                    time.sleep(POLL_INTERVAL)
            else:
                # Idle animation
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log("\nShutdown requested...")
    finally:
        release_lock(lock_fd)
        log("Lock released. Goodbye.")

if __name__ == "__main__":
    main()
