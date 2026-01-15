#!/usr/bin/env python3
"""
Bootstrap - Layer 1: Environmental Checks

Purpose: Make the world safe to exist in.
Checks: Directories, tools, versions, CI, registries (existence only).
Assumes: Nothing.
If fails: System cannot exist.

Usage:
    python Control_Plane/scripts/bootstrap.py

Exit codes:
    0 = Bootstrap OK
    1 = Bootstrap FAIL
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def get_repo_root() -> Path:
    """Find repository root (contains .git/)."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
    # Fallback: look for SYSTEM_CONSTITUTION.md
    for parent in [current] + list(current.parents):
        if (parent / "SYSTEM_CONSTITUTION.md").is_file():
            return parent
    return Path.cwd()


REPO_ROOT = get_repo_root()


class BootstrapResult:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def ok(self, check: str):
        self.checks.append(("OK", check))
        self.passed += 1

    def warn(self, check: str):
        self.checks.append(("WARN", check))
        self.warnings += 1

    def fail(self, check: str, reason: str):
        self.checks.append(("FAIL", f"{check}: {reason}"))
        self.failed += 1

    def report(self) -> str:
        lines = ["=" * 50, "BOOTSTRAP REPORT", "=" * 50, ""]
        for status, msg in self.checks:
            symbol = {"OK": "✓", "WARN": "⚠", "FAIL": "✗"}[status]
            lines.append(f"  [{symbol}] {msg}")
        lines.append("")
        lines.append("-" * 50)
        if self.failed == 0:
            status_msg = f"BOOTSTRAP OK: {self.passed} checks passed"
            if self.warnings > 0:
                status_msg += f" ({self.warnings} warnings)"
            lines.append(status_msg)
            lines.append("System can exist. Run validate.py next.")
        else:
            lines.append(f"BOOTSTRAP FAIL: {self.failed} checks failed")
            lines.append("System cannot exist. Fix issues above.")
        lines.append("=" * 50)
        return "\n".join(lines)


def check_directories(result: BootstrapResult):
    """Check required directories exist."""
    required_dirs = [
        "Control_Plane",
        "Control_Plane/registries",
        "Control_Plane/control_plane/prompts",
        "Control_Plane/scripts",
        "Control_Plane/init",
        "_archive",
        "src",
        "tests",
        "docs",
        "scripts",
    ]

    for dir_path in required_dirs:
        full_path = REPO_ROOT / dir_path
        if full_path.is_dir():
            result.ok(f"Directory exists: {dir_path}/")
        else:
            result.fail(f"Directory missing", dir_path)


def tool_exists(tool: str, version_flag: str) -> bool:
    """Check if a tool exists using multiple methods."""
    # Method 1: shutil.which
    if shutil.which(tool):
        return True

    # Method 2: Try running the command directly
    try:
        result = subprocess.run(
            [tool, version_flag],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Method 3: Try common paths (for git especially)
    common_paths = [
        f"/usr/bin/{tool}",
        f"/usr/local/bin/{tool}",
        f"/opt/homebrew/bin/{tool}",
    ]
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return True

    return False


def check_tools(result: BootstrapResult):
    """Check required tools are installed."""
    # Required tools - bootstrap fails if missing
    required_tools = [
        ("python3", "--version"),
    ]

    # Optional tools - warning if missing, but bootstrap continues
    optional_tools = [
        ("pip3", "--version"),  # pip3 on macOS
        ("git", "--version"),
    ]

    for tool, version_flag in required_tools:
        if tool_exists(tool, version_flag):
            result.ok(f"Tool installed: {tool}")
        else:
            result.fail(f"Tool missing (required)", tool)

    for tool, version_flag in optional_tools:
        if tool_exists(tool, version_flag):
            result.ok(f"Tool installed: {tool}")
        else:
            result.warn(f"Tool not found (optional): {tool}")


def check_versions_pinned(result: BootstrapResult):
    """Check version files exist."""
    version_files = [
        ("requirements.txt", "Python dependencies"),
        ("VERSION", "System version"),
    ]

    for file_path, description in version_files:
        full_path = REPO_ROOT / file_path
        if full_path.is_file():
            result.ok(f"Version pinned: {file_path} ({description})")
        else:
            result.fail(f"Version file missing", f"{file_path} ({description})")


def check_ci_runnable(result: BootstrapResult):
    """Check CI configuration exists."""
    ci_paths = [
        ".github/workflows/ci.yml",
        ".github/workflows/ci.yaml",
    ]

    found = False
    for ci_path in ci_paths:
        if (REPO_ROOT / ci_path).is_file():
            result.ok(f"CI config exists: {ci_path}")
            found = True
            break

    if not found:
        result.fail("CI config missing", ".github/workflows/ci.yml")


def check_registries_present(result: BootstrapResult):
    """Check registry files exist (not their content)."""
    registry_dir = REPO_ROOT / "Control_Plane" / "registries"

    if not registry_dir.is_dir():
        result.fail("Registry directory missing", "Control_Plane/registries/")
        return

    csv_files = list(registry_dir.glob("*.csv"))
    if csv_files:
        result.ok(f"Registries present: {len(csv_files)} CSV files in Control_Plane/registries/")
    else:
        result.fail("No registries found", "Control_Plane/registries/*.csv")


def check_tests_runnable(result: BootstrapResult):
    """Check tests directory exists and has test files."""
    tests_dir = REPO_ROOT / "tests"

    if not tests_dir.is_dir():
        result.fail("Tests directory missing", "tests/")
        return

    test_files = list(tests_dir.glob("test_*.py")) + list(tests_dir.glob("*_test.py"))
    if test_files:
        result.ok(f"Tests present: {len(test_files)} test files in tests/")
    else:
        # Not a failure - tests might be elsewhere or not yet written
        result.ok("Tests directory exists (no test files yet)")


def check_critical_files(result: BootstrapResult):
    """Check critical files exist."""
    critical_files = [
        ("SYSTEM_CONSTITUTION.md", "Canonical governance rules"),
        ("README.md", "Repository documentation"),
        ("Control_Plane/init/init.md", "Bootstrap entry point"),
    ]

    for file_path, description in critical_files:
        full_path = REPO_ROOT / file_path
        if full_path.is_file():
            result.ok(f"Critical file exists: {file_path}")
        else:
            result.fail(f"Critical file missing", f"{file_path} ({description})")


def check_scripts_executable(result: BootstrapResult):
    """Check key scripts exist."""
    scripts = [
        "Control_Plane/scripts/validate_registry.py",
        "Control_Plane/scripts/apply_selection.py",
    ]

    for script_path in scripts:
        full_path = REPO_ROOT / script_path
        if full_path.is_file():
            result.ok(f"Script exists: {script_path}")
        else:
            result.fail(f"Script missing", script_path)


def bootstrap() -> bool:
    """Run all bootstrap checks."""
    result = BootstrapResult()

    print("Running bootstrap checks...\n")

    # Layer 1 checks - pure environmental
    check_directories(result)
    check_tools(result)
    check_versions_pinned(result)
    check_ci_runnable(result)
    check_registries_present(result)
    check_tests_runnable(result)
    check_critical_files(result)
    check_scripts_executable(result)

    print(result.report())

    return result.failed == 0


if __name__ == "__main__":
    success = bootstrap()
    sys.exit(0 if success else 1)
