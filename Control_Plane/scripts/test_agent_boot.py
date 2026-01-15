#!/usr/bin/env python3
"""
Test Agent Boot - Validates an LLM agent understands the Control Plane

Usage:
    python3 Control_Plane/scripts/test_agent_boot.py

This script checks if the system is ready for an agent to boot.
Give the output to the agent and ask them to confirm each criterion.
"""

import csv
import subprocess
import sys
from pathlib import Path


def get_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


REPO_ROOT = get_repo_root()
REGISTRY = REPO_ROOT / "Control_Plane" / "registries" / "control_plane_registry.csv"


def check_registry_exists():
    """Check unified registry exists."""
    if REGISTRY.is_file():
        with open(REGISTRY) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        return True, f"control_plane_registry.csv exists ({len(rows)} items)"
    return False, "control_plane_registry.csv NOT FOUND"


def check_old_registries_gone():
    """Check old registries are archived."""
    old_files = [
        "frameworks_registry.csv",
        "modules_registry.csv",
        "prompts_registry.csv",
    ]
    reg_dir = REPO_ROOT / "Control_Plane" / "registries"
    found = [f for f in old_files if (reg_dir / f).exists()]
    if found:
        return False, f"Old registries still active: {found}"
    return True, "Old registries archived (only unified registry active)"


def check_init_works():
    """Check init.py runs successfully."""
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "Control_Plane" / "scripts" / "init.py")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if "Ready to receive commands" in result.stdout:
        return True, "init.py passes all 3 layers"
    return False, f"init.py failed: {result.stderr[:100]}"


def check_name_lookup():
    """Check we can find items by name."""
    with open(REGISTRY) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Find "Definition of Done" by name
    found = [r for r in rows if "Definition of Done" in r.get("name", "")]
    if found:
        return True, f"Name lookup works: 'Definition of Done' → {found[0]['id']}"
    return False, "Name lookup failed"


def get_sample_names():
    """Get sample names for agent testing."""
    with open(REGISTRY) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    samples = {
        "framework": None,
        "module": None,
        "prompt": None,
    }

    for row in rows:
        etype = row.get("entity_type", "")
        if etype in samples and samples[etype] is None:
            samples[etype] = row.get("name", "")

    return samples


def main():
    print("=" * 60)
    print("AGENT BOOT TEST")
    print("=" * 60)
    print()

    checks = [
        ("Unified registry exists", check_registry_exists),
        ("Old registries archived", check_old_registries_gone),
        ("init.py works", check_init_works),
        ("Name lookup works", check_name_lookup),
    ]

    all_pass = True
    for name, check_fn in checks:
        try:
            passed, msg = check_fn()
            symbol = "✓" if passed else "✗"
            print(f"  [{symbol}] {name}")
            print(f"      {msg}")
            if not passed:
                all_pass = False
        except Exception as e:
            print(f"  [✗] {name}")
            print(f"      Error: {e}")
            all_pass = False

    print()
    print("-" * 60)

    if all_pass:
        print("READY FOR AGENT BOOT")
        print()
        print("Test prompts to give the agent:")
        print()

        samples = get_sample_names()

        print("  1. 'Boot the system'")
        print("     → Should run init.py, see 'Ready to receive commands'")
        print()
        print("  2. 'List all frameworks'")
        print(f"     → Should see names like '{samples.get('framework', 'Repo OS Spec')}'")
        print()
        print("  3. 'Show me the modules'")
        print(f"     → Should see names like '{samples.get('module', 'File Memory Bus')}'")
        print()
        print("  4. 'What is Definition of Done?'")
        print("     → Should find by NAME and show details")
        print()
        print("  5. 'Select Local Dev Harness for installation'")
        print("     → Should find by NAME and set selected=yes")
        print()
        print("-" * 60)
        print("SUCCESS CRITERIA:")
        print("  [1] Runs init.py first")
        print("  [2] Uses unified registry (not old files)")
        print("  [3] References items by NAME (not ID)")
        print("  [4] Uses scripts (not cat/grep)")
        print("  [5] Commits with agent suffix")

        return 0
    else:
        print("NOT READY - Fix issues above first")
        return 1


if __name__ == "__main__":
    sys.exit(main())
