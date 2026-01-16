#!/usr/bin/env python3
"""
apply_spec_pack.py - Create spec pack from templates

Purpose: Initialize a new spec pack directory with all 8 template files.

Usage:
    python3 Control_Plane/scripts/apply_spec_pack.py --target SPEC-001
    python3 Control_Plane/scripts/apply_spec_pack.py --target SPEC-001 --force
    python3 Control_Plane/scripts/apply_spec_pack.py --all

Exit codes:
    0 = Success
    1 = Target already exists (use --force to overwrite)
    2 = Template files not found
    3 = Invalid arguments
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Use canonical library
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Control_Plane.lib import REPO_ROOT, CONTROL_PLANE

# Paths
TEMPLATES_DIR = CONTROL_PLANE / "modules" / "design_framework" / "templates"
SPECS_DIR = REPO_ROOT / "docs" / "specs"

# Template files (8 files)
TEMPLATE_FILES = [
    "00_overview.md",
    "01_problem.md",
    "02_solution.md",
    "03_requirements.md",
    "04_design.md",
    "05_testing.md",
    "06_rollout.md",
    "07_registry.md",
]


def check_templates_exist() -> bool:
    """Verify all template files exist."""
    if not TEMPLATES_DIR.is_dir():
        return False
    for template in TEMPLATE_FILES:
        if not (TEMPLATES_DIR / template).is_file():
            return False
    return True


def apply_spec_pack(target: str, force: bool = False) -> int:
    """Create a new spec pack from templates.

    Args:
        target: Spec pack ID (e.g., SPEC-001)
        force: If True, overwrite existing spec pack

    Returns:
        Exit code (0=success, 1=exists, 2=no templates)
    """
    target_dir = SPECS_DIR / target

    # Check if target exists
    if target_dir.exists() and not force:
        print(f"[FAIL] Spec pack already exists: {target}")
        print(f"       Path: {target_dir.relative_to(REPO_ROOT)}")
        print("       Use --force to overwrite")
        return 1

    # Check templates exist
    if not check_templates_exist():
        print(f"[FAIL] Template files not found")
        print(f"       Expected: {TEMPLATES_DIR.relative_to(REPO_ROOT)}")
        return 2

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy and customize templates
    today = datetime.now().strftime("%Y-%m-%d")
    replacements = {
        "{{SPEC_ID}}": target,
        "{{SPEC_NAME}}": target.replace("-", " ").title(),
        "{{DATE}}": today,
        "{{AUTHOR}}": "TBD",
    }

    copied = 0
    for template in TEMPLATE_FILES:
        src = TEMPLATES_DIR / template
        dst = target_dir / template

        content = src.read_text()
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        dst.write_text(content)
        copied += 1

    print(f"\n[OK] Created spec pack: {target}")
    print(f"     Path: {target_dir.relative_to(REPO_ROOT)}")
    print(f"     Files: {copied}")
    print("\nNext steps:")
    print(f"  1. Edit the 8 files in {target_dir.relative_to(REPO_ROOT)}/")
    print("  2. Replace all {{placeholder}} values")
    print(f"  3. Validate: python3 Control_Plane/scripts/validate_spec_pack.py --target {target}")

    return 0


def apply_all(force: bool = False) -> int:
    """Apply templates to all existing spec pack directories.

    This is useful for updating existing spec packs with new template versions.
    """
    if not SPECS_DIR.is_dir():
        print("[WARN] No specs directory found")
        SPECS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created: {SPECS_DIR.relative_to(REPO_ROOT)}")
        return 0

    spec_dirs = [d for d in SPECS_DIR.iterdir() if d.is_dir()]
    if not spec_dirs:
        print("[INFO] No existing spec packs found")
        return 0

    errors = 0
    for spec_dir in spec_dirs:
        result = apply_spec_pack(spec_dir.name, force=force)
        if result != 0:
            errors += 1

    print(f"\nProcessed: {len(spec_dirs)} spec packs, {errors} errors")
    return 1 if errors > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        description="Create spec pack from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --target SPEC-001        Create new spec pack
  %(prog)s --target SPEC-001 --force  Overwrite existing
  %(prog)s --all                     Update all existing spec packs
        """,
    )
    parser.add_argument(
        "--target",
        metavar="ID",
        help="Spec pack ID to create (e.g., SPEC-001)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Apply to all existing spec packs",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )

    args = parser.parse_args()

    if not args.target and not args.all:
        parser.print_help()
        return 3

    if args.all:
        return apply_all(force=args.force)
    else:
        return apply_spec_pack(args.target, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
