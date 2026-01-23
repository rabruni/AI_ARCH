#!/usr/bin/env python3
"""
Init - Run All Three Layers

Purpose: Single entry point for Control Plane initialization.
Runs: Bootstrap → Validate → Generate Plan

Usage:
    python Control_Plane/scripts/init.py

Exit codes:
    0 = Init OK
    1 = Bootstrap failed
    2 = Validate failed
    3 = Plan generation failed
"""

import subprocess
import sys
import csv
from pathlib import Path

# Use canonical library
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Control_Plane.lib import (
    REPO_ROOT,
    CONTROL_PLANE,
    count_registry_stats,
)


def run_layer(script_name: str, layer_num: int, layer_name: str) -> bool:
    """Run a layer script and return success status."""
    script_path = CONTROL_PLANE / "scripts" / script_name

    print(f"\n{'='*60}")
    print(f"LAYER {layer_num}: {layer_name.upper()}")
    print(f"{'='*60}\n")

    result = subprocess.run(
        ["python3", str(script_path)],
        cwd=REPO_ROOT,
    )

    return result.returncode == 0


def determine_mode(stats: dict) -> str:
    """Determine system mode based on stats."""
    if stats["missing"] > 0:
        return "BUILD"
    elif stats["selected"] == stats["active"]:
        return "STABILIZE"
    else:
        return "BUILD"


def display_agent_roles():
    """Read and display agent role assignments from registry."""
    registry_path = REPO_ROOT / "agent_role_registry.csv"
    
    if not registry_path.exists():
        return

    print(f"\n{'='*60}")
    print("AGENT ROLE ASSIGNMENTS")
    print(f"{'='*60}")
    
    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Find max length for padding
            rows = list(reader)
            if not rows:
                print("  (No roles defined)")
                return

            # Print table
            for row in rows:
                agent = row.get('agent_name', 'Unknown')
                role = row.get('role', 'Unassigned')
                desc = row.get('description', '')
                print(f"  {agent:<10} -> {role:<15} ({desc})")
    except Exception as e:
        print(f"  [Error reading agent registry: {e}]")
    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("CONTROL PLANE INITIALIZATION")
    print("=" * 60)

    # Layer 1: Bootstrap
    if not run_layer("bootstrap.py", 1, "Bootstrap (Environmental)"):
        print("\n[FAIL] INIT FAILED: Bootstrap failed")
        print("   System cannot exist. Fix environmental issues.")
        return 1

    # Layer 2: Validate
    if not run_layer("validate.py", 2, "Validate (Integrity)"):
        print("\n[FAIL] INIT FAILED: Validation failed")
        print("   System exists but data is corrupt. Fix integrity issues.")
        return 2

    # Layer 3: Generate Plan (semantic)
    print(f"\n{'='*60}")
    print("LAYER 3: INIT (Semantic)")
    print(f"{'='*60}\n")

    apply_script = CONTROL_PLANE / "scripts" / "apply_selection.py"
    result = subprocess.run(
        ["python3", str(apply_script)],
        cwd=REPO_ROOT,
    )

    if result.returncode != 0:
        print("\n[FAIL] INIT FAILED: Plan generation failed")
        return 3

    # Final report - use library function
    stats = count_registry_stats()
    mode = determine_mode(stats)

    print(f"\n{'='*60}")
    print("INIT COMPLETE")
    print(f"{'='*60}")
    print(f"  Registries: {stats['registries']} loaded")
    print(f"  Selected:   {stats['selected']} items")
    print(f"  Active:     {stats['active']} items")
    print(f"  Missing:    {stats['missing']} items (to install)")
    print(f"  Mode:       {mode}")
    print(f"  Plan:       Control_Plane/generated/plan.json")
    
    # Display dynamic roles
    display_agent_roles()

    print("\n[OK] Ready to receive commands.")
    print("\nNext steps:")
    print("  - Read plan.json to see pending work")
    print("  - Use verb prompts to execute: install, update, verify, uninstall")

    return 0


if __name__ == "__main__":
    sys.exit(main())
