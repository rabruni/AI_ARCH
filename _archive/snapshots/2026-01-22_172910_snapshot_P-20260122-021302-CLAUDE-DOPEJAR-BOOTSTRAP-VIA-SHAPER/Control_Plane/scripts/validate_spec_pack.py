#!/usr/bin/env python3
"""
validate_spec_pack.py - Validate spec pack completeness

Purpose: Ensure spec packs are complete and ready for implementation.

Usage:
    python3 Control_Plane/scripts/validate_spec_pack.py --target SPEC-001
    python3 Control_Plane/scripts/validate_spec_pack.py --target SPEC-001 --force
    python3 Control_Plane/scripts/validate_spec_pack.py --all

Exit codes:
    0 = Valid (all checks pass)
    1 = Invalid (missing files or incomplete content)
    2 = Target not found
    3 = Invalid arguments
"""

import argparse
import re
import sys
from pathlib import Path

# Use canonical library
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Control_Plane.lib import REPO_ROOT, CONTROL_PLANE

# Paths
SPECS_DIR = CONTROL_PLANE / "docs" / "specs"

# Required files (9 files)
REQUIRED_FILES = [
    "00_overview.md",
    "01_problem.md",
    "02_solution.md",
    "03_requirements.md",
    "04_design.md",
    "05_testing.md",
    "06_rollout.md",
    "07_registry.md",
    "08_commit.md",
]

# Required headings in 08_commit.md (case-insensitive)
COMMIT_REQUIRED_HEADINGS = ["mode", "altitude", "references", "stop conditions"]
COMMIT_REQUIRED_REFS = ["goal", "non-goals", "acceptance"]

# Patterns that indicate incomplete content
INCOMPLETE_PATTERNS = [
    r"\{\{[^}]+\}\}",           # {{placeholder}}
    r"^\s*TBD\s*$",             # TBD on its own line
    r"^\s*TODO\s*$",            # TODO on its own line
    r"^\s*\(TODO\)\s*$",        # (TODO) on its own line
]


class ValidationResult:
    """Result of spec pack validation."""

    def __init__(self, spec_id: str):
        self.spec_id = spec_id
        self.errors = []
        self.warnings = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def report(self) -> str:
        lines = [f"\nValidation: {self.spec_id}", "=" * 50]

        if self.errors:
            lines.append("\nErrors:")
            for e in self.errors:
                lines.append(f"  [FAIL] {e}")

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  [WARN] {w}")

        lines.append("")
        lines.append("-" * 50)
        if self.valid:
            if self.warnings:
                lines.append(f"Result: VALID (with {len(self.warnings)} warnings)")
            else:
                lines.append("Result: VALID")
        else:
            lines.append(f"Result: INVALID ({len(self.errors)} errors)")

        return "\n".join(lines)


def find_incomplete_markers(content: str) -> list:
    """Find incomplete content markers in text."""
    found = []
    for i, line in enumerate(content.split("\n"), 1):
        for pattern in INCOMPLETE_PATTERNS:
            matches = re.findall(pattern, line, re.MULTILINE)
            for match in matches:
                found.append((i, match.strip()))
    return found


def validate_commit_file(file_path: Path, result: "ValidationResult") -> None:
    """Validate 08_commit.md structure and content."""
    content = file_path.read_text(encoding="utf-8")

    # Parse sections (case-insensitive)
    sections: dict = {}
    current_heading = None
    current_lines: list = []

    for line in content.splitlines():
        heading_match = re.match(r"^##\s+(.+)$", line, re.IGNORECASE)
        if heading_match:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines)
            current_heading = heading_match.group(1).strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines)

    # Check required headings
    for heading in COMMIT_REQUIRED_HEADINGS:
        if heading not in sections:
            result.error(f"08_commit.md: Missing required section: ## {heading.upper()}")

    # Check MODE value
    if "mode" in sections:
        mode = sections["mode"].strip().upper()
        if mode not in ("EXPLORE", "COMMIT"):
            result.error(f"08_commit.md: MODE must be EXPLORE or COMMIT, got: '{mode}'")

    # Check ALTITUDE value
    if "altitude" in sections:
        altitude = sections["altitude"].strip().upper()
        if altitude not in ("L4", "L3", "L2", "L1"):
            result.error(f"08_commit.md: ALTITUDE must be L4/L3/L2/L1, got: '{altitude}'")

    # Check REFERENCES section has required keys
    if "references" in sections:
        refs_content = sections["references"].lower()
        for ref in COMMIT_REQUIRED_REFS:
            if f"{ref}:" not in refs_content:
                result.error(f"08_commit.md: REFERENCES missing required line: {ref}")

    # Check STOP CONDITIONS has at least 1 bullet
    if "stop conditions" in sections:
        bullets = [
            line for line in sections["stop conditions"].splitlines()
            if line.strip().startswith("-")
        ]
        if not bullets:
            result.error("08_commit.md: STOP CONDITIONS must have at least 1 bullet point")


def validate_spec_pack(target: str, force: bool = False) -> int:
    """Validate a spec pack.

    Args:
        target: Spec pack ID
        force: If True, return 0 even if invalid (for CI override)

    Returns:
        Exit code (0=valid, 1=invalid, 2=not found)
    """
    target_dir = SPECS_DIR / target
    result = ValidationResult(target)

    # Check directory exists
    if not target_dir.is_dir():
        print(f"[FAIL] Spec pack not found: {target}")
        print(f"       Expected: {target_dir.relative_to(REPO_ROOT)}")
        return 2

    # Check required files exist
    for filename in REQUIRED_FILES:
        file_path = target_dir / filename
        if not file_path.is_file():
            result.error(f"Missing file: {filename}")
        else:
            # Check for incomplete content
            content = file_path.read_text()

            # Check file is not empty
            if len(content.strip()) < 50:
                result.warn(f"{filename}: Very short content ({len(content)} chars)")

            # Check for placeholder markers
            markers = find_incomplete_markers(content)
            for line_num, marker in markers:
                result.warn(f"{filename}:{line_num}: Incomplete marker '{marker}'")

            # Special validation for 08_commit.md
            if filename == "08_commit.md":
                validate_commit_file(file_path, result)

            if filename == "05_testing.md":
                heredoc_markers = ["<<EOF", "<<'EOF'", "<<'PY'", "<<'"]
                if any(marker in content for marker in heredoc_markers):
                    result.error(
                        "05_testing.md: G3 executes only the first $ line; "
                        "heredocs are not supported. Use a single-line '$ <command>' "
                        "and call a script for complex logic."
                    )
                dollar_lines = [
                    line for line in content.splitlines()
                    if line.lstrip().startswith("$")
                ]
                if len(dollar_lines) > 1:
                    result.error(
                        "05_testing.md: G3 executes only the first $ line; "
                        "use a single-line '$ <command>' and call a script for complex logic."
                    )

    # Check for README (optional but recommended)
    if not (target_dir / "README.md").is_file():
        result.warn("No README.md (optional)")

    # Print report
    print(result.report())

    # Return code
    if force:
        print("\n[FORCE] Returning success despite validation result")
        return 0

    return 0 if result.valid else 1


def validate_all(force: bool = False) -> int:
    """Validate all spec packs.

    Returns:
        Exit code (0=all valid, 1=some invalid)
    """
    if not SPECS_DIR.is_dir():
        print("[INFO] No specs directory found")
        return 0

    spec_dirs = [d for d in SPECS_DIR.iterdir() if d.is_dir()]
    if not spec_dirs:
        print("[INFO] No spec packs found")
        return 0

    print(f"Validating {len(spec_dirs)} spec packs...")
    print("=" * 50)

    results = {}
    for spec_dir in sorted(spec_dirs):
        spec_id = spec_dir.name
        exit_code = validate_spec_pack(spec_id, force=False)
        results[spec_id] = exit_code

    # Summary
    valid = sum(1 for r in results.values() if r == 0)
    invalid = sum(1 for r in results.values() if r == 1)
    not_found = sum(1 for r in results.values() if r == 2)

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"  Total:     {len(results)}")
    print(f"  Valid:     {valid}")
    print(f"  Invalid:   {invalid}")
    print(f"  Not found: {not_found}")

    if invalid > 0:
        print("\nInvalid spec packs:")
        for spec_id, code in results.items():
            if code == 1:
                print(f"  - {spec_id}")

    if force:
        print("\n[FORCE] Returning success despite validation results")
        return 0

    return 0 if invalid == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Validate spec pack completeness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0 = Valid (all checks pass)
  1 = Invalid (missing files or incomplete content)
  2 = Target not found
  3 = Invalid arguments

Examples:
  %(prog)s --target SPEC-001    Validate single spec pack
  %(prog)s --all                Validate all spec packs
  %(prog)s --all --force        Validate all, return 0 regardless
        """,
    )
    parser.add_argument(
        "--target",
        metavar="ID",
        help="Spec pack ID to validate",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all spec packs",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Return success (0) even if validation fails",
    )

    args = parser.parse_args()

    if not args.target and not args.all:
        parser.print_help()
        return 3

    if args.all:
        return validate_all(force=args.force)
    else:
        return validate_spec_pack(args.target, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
