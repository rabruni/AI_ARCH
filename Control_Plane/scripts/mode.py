#!/usr/bin/env python3
"""
Mode - Mode Detection and Enforcement (BOOT-013)

Purpose: Detect system mode and enforce operation constraints.

Modes:
  BUILD     - Work to be done (missing items exist)
  STABILIZE - All selected items active, maintenance only
  RESET     - Explicit reset requested, archive operations

Usage:
    python Control_Plane/scripts/mode.py              # Show current mode
    python Control_Plane/scripts/mode.py check <verb> # Check if verb allowed
    python Control_Plane/scripts/mode.py set <mode>   # Set mode override

Exit codes:
    0 = OK / Allowed
    1 = Not allowed in current mode
    2 = Invalid mode or verb
"""

import csv
import json
import sys
from pathlib import Path
from typing import Optional


def get_repo_root() -> Path:
    """Find repository root (contains .git/)."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


REPO_ROOT = get_repo_root()
CONTROL_PLANE = REPO_ROOT / "Control_Plane"
MODE_FILE = CONTROL_PLANE / "generated" / "mode.json"

VALID_MODES = ["BUILD", "STABILIZE", "RESET"]

# Mode rules: which verbs are allowed/warned/blocked in each mode
MODE_RULES = {
    "BUILD": {
        "install": "allowed",      # Primary activity
        "update": "allowed",       # Can update during build
        "verify": "allowed",       # Always allowed
        "uninstall": "warn",       # Unusual during build
    },
    "STABILIZE": {
        "install": "warn",         # Should be stable, warn on new installs
        "update": "allowed",       # Maintenance updates OK
        "verify": "allowed",       # Always allowed
        "uninstall": "warn",       # Warn before removing
    },
    "RESET": {
        "install": "blocked",      # No new installs during reset
        "update": "blocked",       # No updates during reset
        "verify": "allowed",       # Can verify before archive
        "uninstall": "allowed",    # Primary activity
    },
}


def find_all_registries() -> list[Path]:
    """Find all CSV registries in Control_Plane."""
    registries = []

    # Root registries
    root_reg = CONTROL_PLANE / "registries"
    if root_reg.is_dir():
        registries.extend(root_reg.glob("*.csv"))

    # Module registries
    modules_dir = CONTROL_PLANE / "modules"
    if modules_dir.is_dir():
        registries.extend(modules_dir.glob("**/registries/*.csv"))

    # Init registry
    init_reg = CONTROL_PLANE / "init" / "init_registry.csv"
    if init_reg.is_file():
        registries.append(init_reg)

    # Boot OS registry
    boot_reg = CONTROL_PLANE / "boot_os_registry.csv"
    if boot_reg.is_file():
        registries.append(boot_reg)

    return registries


def count_registry_stats() -> dict:
    """Count items by status across all registries."""
    stats = {
        "total": 0,
        "selected": 0,
        "active": 0,
        "missing": 0,
        "draft": 0,
        "deprecated": 0,
    }

    for reg_path in find_all_registries():
        try:
            with open(reg_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats["total"] += 1

                    selected = row.get("selected", "").strip().lower()
                    status = row.get("status", "").strip().lower()

                    if selected == "yes":
                        stats["selected"] += 1

                    if status == "active":
                        stats["active"] += 1
                    elif status == "missing":
                        stats["missing"] += 1
                    elif status == "draft":
                        stats["draft"] += 1
                    elif status == "deprecated":
                        stats["deprecated"] += 1
        except Exception:
            continue

    return stats


def load_mode_override() -> Optional[str]:
    """Load mode override from file if exists."""
    if MODE_FILE.is_file():
        try:
            with open(MODE_FILE) as f:
                data = json.load(f)
                return data.get("mode_override")
        except Exception:
            pass
    return None


def save_mode_override(mode: Optional[str]):
    """Save mode override to file."""
    MODE_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if MODE_FILE.is_file():
        try:
            with open(MODE_FILE) as f:
                data = json.load(f)
        except Exception:
            pass

    if mode:
        data["mode_override"] = mode
    elif "mode_override" in data:
        del data["mode_override"]

    with open(MODE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def detect_mode() -> tuple[str, str]:
    """
    Detect current mode based on registry state.
    Returns (mode, reason).
    """
    # Check for explicit override first
    override = load_mode_override()
    if override and override in VALID_MODES:
        return (override, "explicit override")

    # Auto-detect based on registry state
    stats = count_registry_stats()

    # If there are missing items that are selected, we're in BUILD
    if stats["missing"] > 0:
        return ("BUILD", f"{stats['missing']} items with status=missing")

    # If there are draft items, still BUILD
    if stats["draft"] > 0:
        return ("BUILD", f"{stats['draft']} items with status=draft")

    # If all selected items are active, STABILIZE
    if stats["selected"] > 0 and stats["active"] >= stats["selected"]:
        return ("STABILIZE", "all selected items are active")

    # Default to BUILD
    return ("BUILD", "default mode")


def check_verb_allowed(verb: str, mode: Optional[str] = None) -> tuple[str, str]:
    """
    Check if a verb is allowed in the current/specified mode.
    Returns (status, message) where status is 'allowed', 'warn', or 'blocked'.
    """
    if mode is None:
        mode, _ = detect_mode()

    verb = verb.lower()

    if mode not in MODE_RULES:
        return ("allowed", f"unknown mode {mode}, allowing")

    if verb not in MODE_RULES[mode]:
        return ("allowed", f"unknown verb {verb}, allowing")

    status = MODE_RULES[mode][verb]

    messages = {
        "allowed": f"{verb} is allowed in {mode} mode",
        "warn": f"{verb} is unusual in {mode} mode - proceed with caution",
        "blocked": f"{verb} is blocked in {mode} mode",
    }

    return (status, messages.get(status, ""))


def show_mode():
    """Display current mode and stats."""
    mode, reason = detect_mode()
    stats = count_registry_stats()
    override = load_mode_override()

    print("=" * 50)
    print("CURRENT MODE")
    print("=" * 50)
    print(f"\n  Mode: {mode}")
    print(f"  Reason: {reason}")
    if override:
        print(f"  Override: {override} (set explicitly)")
    print()
    print("  Registry Stats:")
    print(f"    Total items:    {stats['total']}")
    print(f"    Selected:       {stats['selected']}")
    print(f"    Active:         {stats['active']}")
    print(f"    Missing:        {stats['missing']}")
    print(f"    Draft:          {stats['draft']}")
    print(f"    Deprecated:     {stats['deprecated']}")
    print()
    print("  Verb Permissions:")
    for verb in ["install", "update", "verify", "uninstall"]:
        status, _ = check_verb_allowed(verb, mode)
        symbol = {"allowed": "✓", "warn": "⚠", "blocked": "✗"}[status]
        print(f"    [{symbol}] {verb}: {status}")
    print()
    print("=" * 50)


def main():
    if len(sys.argv) < 2:
        show_mode()
        return 0

    command = sys.argv[1].lower()

    if command == "check":
        if len(sys.argv) < 3:
            print("Usage: mode.py check <verb>")
            return 2

        verb = sys.argv[2]
        status, message = check_verb_allowed(verb)
        mode, _ = detect_mode()

        print(f"\nMode: {mode}")
        print(f"Verb: {verb}")
        print(f"Status: {status}")
        print(f"Message: {message}\n")

        if status == "blocked":
            return 1
        return 0

    elif command == "set":
        if len(sys.argv) < 3:
            print("Usage: mode.py set <mode>")
            print(f"Valid modes: {', '.join(VALID_MODES)}")
            print("Use 'mode.py set auto' to clear override")
            return 2

        new_mode = sys.argv[2].upper()

        if new_mode == "AUTO":
            save_mode_override(None)
            print("Mode override cleared. Auto-detection enabled.")
            show_mode()
            return 0

        if new_mode not in VALID_MODES:
            print(f"Invalid mode: {new_mode}")
            print(f"Valid modes: {', '.join(VALID_MODES)}")
            return 2

        save_mode_override(new_mode)
        print(f"Mode override set to: {new_mode}")
        show_mode()
        return 0

    elif command == "rules":
        print("\nMODE RULES")
        print("=" * 50)
        for mode in VALID_MODES:
            print(f"\n{mode}:")
            for verb, status in MODE_RULES[mode].items():
                symbol = {"allowed": "✓", "warn": "⚠", "blocked": "✗"}[status]
                print(f"  [{symbol}] {verb}: {status}")
        print()
        return 0

    else:
        print(f"Unknown command: {command}")
        print("Commands: check, set, rules")
        return 2


if __name__ == "__main__":
    sys.exit(main())
