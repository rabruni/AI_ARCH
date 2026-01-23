#!/usr/bin/env python3
"""
Auto Loop - Refined Agent Orchestration

Purpose: Watches _Prompt-Cache_/INDEX.md for 'sent' tasks and dispatches agents.
Features:
- Daily Snapshotting (Once every 24h)
- Git Checkpoints (Commit on PASS)
- Intelligent Task Selection (Ignores already-answered prompts)
- Verbose Unbuffered Logging

Usage: python3 scripts/auto_loop.py
"""

import time
import subprocess
import sys
import re
import datetime
from pathlib import Path

# Config
POLL_INTERVAL = 15
MAX_RETRIES = 3
PROMPT_CACHE = Path("_Prompt-Cache_")
INDEX_FILE = PROMPT_CACHE / "INDEX.md"
STATUS_FILE = PROMPT_CACHE / "STATUS.md"

# Agent Commands (Absolute Paths)
AGENTS = {
    "Claude": ["/Users/raymondbruni/.local/bin/claude", "--dangerously-skip-permissions", "-p", "Follow Startup & Activation Protocol in AGENTS.md"],
    "Gemini": ["/Users/raymondbruni/.nvm/versions/node/v24.13.0/bin/gemini", "--yolo", "-p", "Follow Startup & Activation Protocol in AGENTS.md"]
}

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def daily_snapshot():
    """Run snapshot only once per day."""
    snapshot_flag = Path(".daily_snapshot_done")
    today = datetime.date.today().isoformat()
    
    if snapshot_flag.exists() and snapshot_flag.read_text().strip() == today:
        return

    log("Performing Daily Baseline Snapshot...")
    subprocess.run(["python3", "scripts/snapshot.py", "daily_baseline"], check=True)
    snapshot_flag.write_text(today)

def create_checkpoint(agent_name, prompt_id):
    """Commit changes to git after a successful run."""
    log(f"Creating Git Checkpoint for {prompt_id}...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", f"auto: {agent_name} completed {prompt_id}"], check=True)
        log("Git Checkpoint Saved.")
    except Exception as e:
        log(f"Git Checkpoint Error: {e}")

def get_next_task():
    """Parse INDEX.md for the next 'sent' task that hasn't been answered."""
    if not INDEX_FILE.exists():
        return None

    content = INDEX_FILE.read_text()
    lines = content.splitlines()
    
    # 1. Identify all prompt_ids that have a feedback entry
    # Feedback entries have type 'feedback' or 'complete' or link to a prompt via 'relates_to'
    completed_prompts = set()
    for line in lines:
        if "feedback" in line.lower() or "complete" in line.lower():
            # Extract the ID it relates to (usually column 8)
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 9:
                relates_to = parts[8].strip(' `')
                if relates_to:
                    completed_prompts.add(relates_to)

    # 2. Find the first 'sent' prompt NOT in the completed set
    header_found = False
    for line in lines:
        if "| created_local" in line:
            header_found = True
            continue
        if not header_found or not line.strip().startswith("|"):
            continue
            
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 7:
            continue
            
        status = parts[6].lower()
        target_agent = parts[4]
        prompt_id = parts[5].strip(' `')
        
        if status == "sent" and prompt_id not in completed_prompts:
            return {
                "agent": target_agent,
                "id": prompt_id,
                "line": line
            }
    return None

def dispatch_agent(task):
    agent_name = task["agent"]
    prompt_id = task["id"]
    
    if agent_name not in AGENTS:
        log(f"Error: Unknown agent {agent_name}")
        return False

    cmd = AGENTS[agent_name]
    log(f"DISPATCHING: {agent_name} -> {prompt_id}")
    
    try:
        # Run agent and capture output for the log
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            log(f"SUCCESS: {agent_name} cycle complete.")
            create_checkpoint(agent_name, prompt_id)
            return True
        else:
            log(f"FAILURE: Agent exited with code {process.returncode}")
            if stderr: log(f"Stderr: {stderr.strip()}")
            return False
    except Exception as e:
        log(f"EXCEPTION: {e}")
        return False

def main():
    log("Auto Loop Engine v2.0 Starting...")
    daily_snapshot()
    
    while True:
        task = get_next_task()
        if task:
            log(f"Next Task: {task['id']} assigned to {task['agent']}")
            if not dispatch_agent(task):
                log("Retrying in 60s...")
                time.sleep(60)
            else:
                log(f"Cooldown {POLL_INTERVAL}s...")
                time.sleep(POLL_INTERVAL)
        else:
            # Idle animation
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()