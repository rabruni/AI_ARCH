#!/usr/bin/env python3
"""
Auto Loop - The Agent Orchestration Heartbeat

Purpose: Watches _Prompt-Cache_/INDEX.md for 'sent' tasks and dispatches agents.
Features:
- Automatic Snapshotting before execution
- Circuit Breaker (Retry Limit)
- Agent Dispatch (Claude/Gemini/Codex)

Usage: python3 scripts/auto_loop.py
"""

import time
import subprocess
import sys
import re
from pathlib import Path

# Config
POLL_INTERVAL = 10  # Seconds
MAX_RETRIES = 3
PROMPT_CACHE = Path("_Prompt-Cache_")
INDEX_FILE = PROMPT_CACHE / "INDEX.md"
STATUS_FILE = PROMPT_CACHE / "STATUS.md"

# Agent Commands (Magic Keys)
AGENTS = {
    "Claude": ["/Users/raymondbruni/.local/bin/claude", "--dangerously-skip-permissions", "-p", "Follow Startup & Activation Protocol in AGENTS.md"],
    "Gemini": ["/Users/raymondbruni/.nvm/versions/node/v24.13.0/bin/gemini", "--yolo", "-p", "Follow Startup & Activation Protocol in AGENTS.md"]
}

def create_checkpoint(agent_name, prompt_id):
    """Commit changes to git after a successful run."""
    print(f"[Checkpoint] Committing changes for {prompt_id}...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        # Use --allow-empty in case the agent made no filesystem changes
        subprocess.run(["git", "commit", "--allow-empty", "-m", f"auto: {agent_name} completed {prompt_id}"], check=True)
        print("[Checkpoint] Success.")
    except Exception as e:
        print(f"[Checkpoint] Error: {e}")

def create_snapshot(label):
    """Call the snapshot script."""
    print(f"\n[Safety] Creating snapshot for {label}...")
    subprocess.run(["python3", "scripts/snapshot.py", label], check=True)

def check_circuit_breaker(prompt_id):
    """Check STATUS.md for retry counts."""
    if not STATUS_FILE.exists():
        return True

    content = STATUS_FILE.read_text()
    # Look for retry_count associated with this thread/ID
    # Simple regex for now: "retry_count: X"
    # In a real impl, we'd need to parse the markdown structure or associate ID to Thread
    # For V1, we scan the whole file for high retry counts as a global safety
    
    matches = re.findall(r"retry_count:\s*(\d+)", content)
    for count in matches:
        if int(count) >= MAX_RETRIES:
            print(f"\n[HALT] Circuit Breaker Tripped! Retry count {count} >= {MAX_RETRIES}.")
            print("Human intervention required in STATUS.md")
            return False
    return True

def get_next_task():
    """Parse INDEX.md for the first 'sent' task."""
    if not INDEX_FILE.exists():
        return None

    lines = INDEX_FILE.read_text().splitlines()
    header_found = False
    
    # Parse table
    for line in lines:
        if line.startswith("| created_local"):
            header_found = True
            continue
        if not header_found or not line.strip().startswith("|"):
            continue
            
        parts = [p.strip() for p in line.split("|")]
        # Schema: | date | exec | type | agent | id | status | ...
        if len(parts) < 7:
            continue
            
        status = parts[6].lower()
        target_agent = parts[4]
        prompt_id = parts[5]
        
        if status == "sent":
            return {
                "agent": target_agent,
                "id": prompt_id,
                "line": line
            }
    return None

def dispatch_agent(task):
    """Run the agent process."""
    agent_name = task["agent"]
    prompt_id = task["id"]
    
    if agent_name not in AGENTS:
        print(f"[Error] Unknown agent: {agent_name}")
        return False

    cmd = AGENTS[agent_name]
    print(f"\n[Dispatch] Launching {agent_name} for task {prompt_id}...")
    
    try:
        # Run agent and wait
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"[Agent Exit] Code: {result.returncode}")
        if result.returncode != 0:
            print(f"[Error] Agent failed:\n{result.stderr}")
            return False
            
        print("[Success] Agent cycle complete.")
        
        # New Git Safety Net
        create_checkpoint(agent_name, prompt_id)
        
        return True
    except Exception as e:
        print(f"[Exception] Failed to run agent: {e}")
        return False

def main():
    print(f"✅ Auto Loop Started. Watching {INDEX_FILE}...")
    print(f"   Max Retries: {MAX_RETRIES}")
    
    while True:
        # 1. Check Circuit Breaker
        if not check_circuit_breaker(None):
            sys.exit(1)

        # 2. Find Work
        task = get_next_task()
        if task:
            print(f"\n⚡ Job Found: {task['id']} ({task['agent']})")
            
            # 3. Snapshot
            create_snapshot(task['id'])
            
            # 4. Dispatch
            if dispatch_agent(task):
                # 5. Wait/Cooldown
                print(f"   Sleeping {POLL_INTERVAL}s before next check...")
                time.sleep(POLL_INTERVAL)
            else:
                print("   [Warn] Agent run failed. Retrying loop in 30s...")
                time.sleep(30)
        else:
            # Idle
            print(".", end="", flush=True)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
