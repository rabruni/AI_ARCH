#!/usr/bin/env python3
"""
gate.py - Enforce gates for spec pack workflow

Purpose: Provide deterministic enforcement gates for the Design Framework workflow.

Gates:
    G0 - Goal Qualification (structural validation)
    G1 - Spec Validation (content validation via validate_spec_pack.py)

Usage:
    python3 Control_Plane/scripts/gate.py G0 SPEC-001
    python3 Control_Plane/scripts/gate.py G1 SPEC-001
    python3 Control_Plane/scripts/gate.py --all SPEC-001

Exit codes:
    0 = Gate passed
    1 = Gate failed
    2 = Target missing or invalid
    3 = Invalid arguments
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Use canonical library
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Control_Plane.lib import REPO_ROOT, CONTROL_PLANE

# Paths
SPECS_DIR = CONTROL_PLANE / "docs" / "specs"

# Required files (8 canonical files)
REQUIRED_FILES = [
    "00_overview.md",
    "01_problem.md",
    "02_solution.md",
    "03_requirements.md",
    "04_design.md",
    "05_testing.md",
    "06_rollout.md",
    "07_registry.md",
]

# Forbidden placeholder patterns for G0
# Only match standalone markers, not examples or documentation text
FORBIDDEN_PATTERNS = [
    r"^\s*TBD\s*$",           # TBD on its own line
    r"^\s*TODO\s*$",          # TODO on its own line
    r"^\s*FILL\s*IN\s*$",     # FILL IN on its own line
    r"\|\s*TBD\s*\|",         # TBD as table cell value
    r"\|\s*TODO\s*\|",        # TODO as table cell value
    r"\|\s*FILL\s*IN\s*\|",   # FILL IN as table cell value
    r":\s*TBD\s*$",           # TBD after colon at end of line
    r":\s*TODO\s*$",          # TODO after colon at end of line
]


def log_gate_result(target: str, gate: str, passed: bool, details: list):
    """Write gate result to artifacts/gate_logs/."""
    target_dir = SPECS_DIR / target
    log_dir = target_dir / "artifacts" / "gate_logs"

    if not log_dir.is_dir():
        log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{gate}_{timestamp}.log"

    status = "PASS" if passed else "FAIL"
    lines = [
        f"Gate: {gate}",
        f"Target: {target}",
        f"Timestamp: {datetime.now().isoformat()}",
        f"Status: {status}",
        "",
        "Details:",
    ]
    lines.extend(f"  {d}" for d in details)

    log_file.write_text("\n".join(lines))
    return log_file


def gate_g0(target: str) -> int:
    """G0 - Goal Qualification Gate.

    Validates:
    1. Directory exists at Control_Plane/docs/specs/<target>/
    2. All 8 canonical spec files exist
    3. No file contains forbidden placeholder markers (TBD, TODO, FILL IN)

    Returns:
        0 = pass, 1 = fail, 2 = target missing
    """
    target_dir = SPECS_DIR / target
    details = []
    errors = []

    print(f"\n{'='*60}")
    print(f"GATE G0: Goal Qualification")
    print(f"Target: {target}")
    print(f"{'='*60}\n")

    # Check 1: Directory exists
    if not target_dir.is_dir():
        print(f"[FAIL] Directory not found: {target_dir.relative_to(REPO_ROOT)}")
        details.append(f"Directory not found: {target_dir}")
        log_gate_result(target, "G0", False, details)
        return 2

    details.append(f"Directory exists: {target_dir.relative_to(REPO_ROOT)}")
    print(f"[OK] Directory exists")

    # Check 2: All 8 files exist
    missing_files = []
    for filename in REQUIRED_FILES:
        filepath = target_dir / filename
        if not filepath.is_file():
            missing_files.append(filename)

    if missing_files:
        print(f"\n[FAIL] Missing required files:")
        for f in missing_files:
            print(f"       - {f}")
            errors.append(f"Missing file: {f}")
        details.extend(errors)
        log_gate_result(target, "G0", False, details)
        return 1

    details.append(f"All {len(REQUIRED_FILES)} required files present")
    print(f"[OK] All {len(REQUIRED_FILES)} required files present")

    # Check 3: No forbidden placeholders
    placeholder_errors = []
    for filename in REQUIRED_FILES:
        filepath = target_dir / filename
        content = filepath.read_text()

        for i, line in enumerate(content.split("\n"), 1):
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    match = re.search(pattern, line, re.IGNORECASE)
                    placeholder_errors.append(f"{filename}:{i}: '{match.group().strip()}'")

    if placeholder_errors:
        print(f"\n[FAIL] Found forbidden placeholders:")
        for err in placeholder_errors[:10]:  # Show first 10
            print(f"       {err}")
        if len(placeholder_errors) > 10:
            print(f"       ... and {len(placeholder_errors) - 10} more")
        errors.extend(placeholder_errors)
        details.append(f"Found {len(placeholder_errors)} forbidden placeholders")
        details.extend(errors)
        log_gate_result(target, "G0", False, details)
        return 1

    details.append("No forbidden placeholders found")
    print(f"[OK] No forbidden placeholders found")

    # Gate passed
    print(f"\n{'-'*60}")
    print(f"G0 RESULT: PASS")
    print(f"{'-'*60}")

    log_file = log_gate_result(target, "G0", True, details)
    print(f"\nLog: {log_file.relative_to(REPO_ROOT)}")

    return 0


def gate_g1(target: str) -> int:
    """G1 - Spec Validation Gate.

    Runs validate_spec_pack.py and returns its exit code.

    Returns:
        Exit code from validate_spec_pack.py (0=valid, 1=invalid, 2=not found)
    """
    target_dir = SPECS_DIR / target
    details = []

    print(f"\n{'='*60}")
    print(f"GATE G1: Spec Validation")
    print(f"Target: {target}")
    print(f"{'='*60}\n")

    # Check directory exists first
    if not target_dir.is_dir():
        print(f"[FAIL] Directory not found: {target_dir.relative_to(REPO_ROOT)}")
        details.append(f"Directory not found: {target_dir}")
        log_gate_result(target, "G1", False, details)
        return 2

    # Run validate_spec_pack.py
    validate_script = CONTROL_PLANE / "scripts" / "validate_spec_pack.py"

    if not validate_script.is_file():
        print(f"[FAIL] validate_spec_pack.py not found")
        details.append("validate_spec_pack.py not found")
        log_gate_result(target, "G1", False, details)
        return 1

    print(f"Running: validate_spec_pack.py --target {target}\n")

    result = subprocess.run(
        ["python3", str(validate_script), "--target", target],
        cwd=REPO_ROOT
    )

    passed = result.returncode == 0
    details.append(f"validate_spec_pack.py exit code: {result.returncode}")

    print(f"\n{'-'*60}")
    if passed:
        print(f"G1 RESULT: PASS")
    else:
        print(f"G1 RESULT: FAIL (exit code {result.returncode})")
    print(f"{'-'*60}")

    log_file = log_gate_result(target, "G1", passed, details)
    print(f"\nLog: {log_file.relative_to(REPO_ROOT)}")

    return result.returncode


def gate_all(target: str) -> int:
    """Run all gates (G0, G1) in sequence.

    Returns:
        0 if all gates pass, otherwise the first non-zero exit code
    """
    print(f"\n{'#'*60}")
    print(f"RUNNING ALL GATES FOR: {target}")
    print(f"{'#'*60}")

    # Run G0
    result = gate_g0(target)
    if result != 0:
        print(f"\n[STOP] G0 failed - not proceeding to G1")
        return result

    # Run G1
    result = gate_g1(target)
    if result != 0:
        return result

    print(f"\n{'#'*60}")
    print(f"ALL GATES PASSED: {target}")
    print(f"{'#'*60}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Enforce gates for spec pack workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Gates:
  G0  Goal Qualification - structural validation
  G1  Spec Validation - content validation

Exit codes:
  0 = Gate passed
  1 = Gate failed
  2 = Target missing or invalid
  3 = Invalid arguments

Examples:
  %(prog)s G0 SPEC-001        Run G0 gate on SPEC-001
  %(prog)s G1 SPEC-001        Run G1 gate on SPEC-001
  %(prog)s --all SPEC-001     Run all gates on SPEC-001
        """,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all gates in sequence",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Gate (G0 or G1) and target spec pack ID",
    )

    parsed = parser.parse_args()

    # Handle --all flag
    if parsed.all:
        if not parsed.args:
            print("Usage: gate.py --all <target>")
            return 3
        target = parsed.args[0]
        return gate_all(target)

    # Parse gate and target from positional args
    if len(parsed.args) < 2:
        parser.print_help()
        return 3

    gate = parsed.args[0].upper()
    target = parsed.args[1]

    if gate not in ["G0", "G1"]:
        print(f"Unknown gate: {gate}")
        print("Valid gates: G0, G1")
        return 3

    # Run specified gate
    if gate == "G0":
        return gate_g0(target)
    elif gate == "G1":
        return gate_g1(target)
    else:
        print(f"Unknown gate: {gate}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
