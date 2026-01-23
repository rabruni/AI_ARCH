#!/usr/bin/env python3
"""
boot.py - Unified Agent Boot System (v1.0)

Single entry point for ALL agents (interactive and automated).
Lives at repo root = highest altitude = controls everything.

Usage:
  Interactive:  python3 boot.py --agent Claude
  Automated:    python3 boot.py --agent Claude --task /_Prompt-Cache_/file.md
  Check only:   python3 boot.py --status

Output: Structured instructions the agent MUST follow.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Paths
REPO_ROOT = Path(__file__).parent
CONTROL_PLANE = REPO_ROOT / "Control_Plane"
GENERATED = CONTROL_PLANE / "generated"
PROMPT_CACHE = REPO_ROOT / "_Prompt-Cache_"
ACTIVE_ORCH_FILE = GENERATED / "active_orchestrator.json"
AGENT_REGISTRY = CONTROL_PLANE / "config" / "agent_role_registry.csv"
STATUS_FILE = PROMPT_CACHE / "STATUS.md"

# Role definitions (source of truth)
ROLES = {
    "Claude": {
        "role": "Primary Implementer",
        "mission": "Build first-pass implementations and maintain development momentum.",
        "constraints": [
            "Must NOT rewrite the spec to fit implementation",
            "Must treat Codex enforcement as binding",
            "Focus on execution, not governance"
        ],
        "can_write": ["src/", "scripts/", "tests/", "Control_Plane/modules/", "_Prompt-Cache_/"],
        "must_not_write": ["_archive/"]
    },
    "Codex": {
        "role": "Spec Enforcer",
        "mission": "Ensure system conforms to spec. You are the spec made executable.",
        "constraints": [
            "Must NOT refactor product code for style",
            "Must NOT weaken the spec to reduce violations",
            "Optimize for determinism and enforcement"
        ],
        "can_write": ["tests/", "Control_Plane/modules/", "_Prompt-Cache_/"],
        "must_not_write": ["src/", "_archive/"]
    },
    "Gemini": {
        "role": "Validator",
        "mission": "Protect correctness, relevance, and safety. You are the breadth guardian.",
        "constraints": [
            "Must NOT implement code",
            "Must NOT enforce compliance (that's Codex)",
            "Propose spec improvements, don't mandate them"
        ],
        "can_write": ["_Prompt-Cache_/", "docs/"],
        "must_not_write": ["src/", "scripts/", "tests/", "_archive/"]
    },
    "Orchestrator": {
        "role": "Control Authority",
        "mission": "Coordinate flow, preserve role boundaries, ensure correct sequencing.",
        "constraints": [
            "Cannot override Codex compliance verdicts",
            "Cannot rewrite spec alone (route through Gemini)",
            "Protect role boundaries above all"
        ],
        "can_write": ["docs/", "_Prompt-Cache_/", "AGENTS.md", "README.md"],
        "must_not_write": ["src/", "scripts/", "Control_Plane/", "_archive/"]
    }
}


def get_active_orchestrator():
    """Return active orchestrator name or None."""
    if ACTIVE_ORCH_FILE.exists():
        try:
            data = json.loads(ACTIVE_ORCH_FILE.read_text())
            if data.get("status") == "active":
                return data.get("active_orchestrator")
        except:
            pass
    return None


def get_pending_task(agent_name):
    """Find next pending task for agent from STATUS.md."""
    if not STATUS_FILE.exists():
        return None

    content = STATUS_FILE.read_text()
    # Simple parse: look for agent name with "ready" or "sent"
    for line in content.split('\n'):
        if agent_name in line and ('ready' in line.lower() or 'sent' in line.lower()):
            # Extract prompt file if present
            if '`/' in line:
                start = line.find('`/') + 1
                end = line.find('`', start)
                if end > start:
                    return line[start:end]
    return None


def generate_boot_output(agent_name, task_file=None, interactive=False):
    """Generate structured boot instructions for agent."""

    if agent_name not in ROLES:
        return f"ERROR: Unknown agent '{agent_name}'. Valid: {list(ROLES.keys())}"

    base_role = ROLES[agent_name]
    orchestrator = get_active_orchestrator()

    # CRITICAL: If this agent IS the Orchestrator, use Orchestrator role entirely
    is_orchestrator = (orchestrator == agent_name)
    if is_orchestrator:
        role_data = ROLES["Orchestrator"]
        active_role = "Orchestrator"
    else:
        role_data = base_role
        active_role = base_role["role"]

    # Find task if not provided
    if not task_file and interactive:
        task_file = get_pending_task(agent_name)

    # Build output
    output = []
    output.append("=" * 60)
    output.append(f"BOOT: {agent_name} as {active_role}")
    output.append("=" * 60)
    output.append("")
    output.append(f"ROLE: {active_role}")
    output.append(f"MISSION: {role_data['mission']}")
    output.append("")
    output.append("CONSTRAINTS:")
    for c in role_data["constraints"]:
        output.append(f"  - {c}")
    output.append("")

    # Show orchestrator status
    if is_orchestrator:
        output.append("STATUS: You ARE the active Orchestrator.")
    else:
        output.append(f"ORCHESTRATOR: {orchestrator or 'NONE (you may claim)'}")
    output.append("")

    # Write permissions - Orchestrator has stricter scope
    output.append("WRITE SCOPE:")
    output.append(f"  ALLOWED: {', '.join(role_data['can_write'])}")
    output.append(f"  FORBIDDEN: {', '.join(role_data['must_not_write'])}")
    output.append("")

    # Task directive
    output.append("-" * 60)
    if task_file:
        output.append(f"TASK: {task_file}")
        output.append("")
        output.append("DIRECTIVE: Read and execute the task file above.")
        output.append("After completion, write feedback to _Prompt-Cache_/")
    elif interactive:
        output.append("MODE: Interactive")
        output.append("")
        output.append("DIRECTIVE: Check _Prompt-Cache_/STATUS.md for pending tasks.")
        output.append("If none, await user instructions.")
    else:
        output.append("MODE: Automated (no task assigned)")
        output.append("")
        output.append("DIRECTIVE: No pending task. Exiting.")
    output.append("-" * 60)

    return "\n".join(output)


def show_status():
    """Show current system status."""
    orchestrator = get_active_orchestrator()

    print("=" * 60)
    print("SYSTEM STATUS")
    print("=" * 60)
    print(f"Orchestrator: {orchestrator or 'NONE'}")
    print(f"Prompt Cache: {PROMPT_CACHE}")
    print(f"Status File:  {STATUS_FILE.exists()}")
    print("")

    # Show pending tasks per agent
    print("Pending Tasks:")
    for agent in ROLES:
        task = get_pending_task(agent)
        print(f"  {agent}: {task or 'none'}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Unified Agent Boot System")
    parser.add_argument("--agent", "-a", help="Agent name (Claude, Codex, Gemini)")
    parser.add_argument("--task", "-t", help="Task file path (for automated mode)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--status", "-s", action="store_true", help="Show system status")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if not args.agent:
        parser.print_help()
        sys.exit(1)

    output = generate_boot_output(args.agent, args.task, args.interactive)

    if args.json:
        # Structured output for programmatic use
        data = {
            "agent": args.agent,
            "role": ROLES.get(args.agent, {}).get("role"),
            "task": args.task,
            "orchestrator": get_active_orchestrator(),
            "instructions": output
        }
        print(json.dumps(data, indent=2))
    else:
        print(output)


if __name__ == "__main__":
    main()
