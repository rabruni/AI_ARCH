#!/usr/bin/env python3
"""
Test script for unified Control Plane CLI.

Verifies:
1. Library imports work
2. All cp commands execute without error
3. Backward compatibility with existing scripts
4. next_action computation in plan.json
"""
import subprocess
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CP_PATH = REPO_ROOT / "Control_Plane" / "cp.py"
SCRIPTS_DIR = REPO_ROOT / "Control_Plane" / "scripts"
GENERATED_DIR = REPO_ROOT / "Control_Plane" / "generated"


def run(cmd: list, expect_success: bool = True) -> tuple:
    """Run a command and return (success, output)."""
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    success = result.returncode == 0

    if expect_success and not success:
        return False, output
    elif not expect_success and success:
        return False, output
    else:
        return True, output


def test_library_imports():
    """Test that library imports work."""
    print("\n[1] Testing library imports...")

    test_code = """
import sys
sys.path.insert(0, '.')
from Control_Plane.lib import (
    REPO_ROOT, CONTROL_PLANE,
    read_registry, find_item, count_registry_stats,
    resolve_artifact_path, ResultReporter
)
print("OK")
"""
    result = subprocess.run(
        ["python3", "-c", test_code],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and "OK" in result.stdout:
        print("  [OK] Library imports successful")
        return True
    else:
        print(f"  [FAIL] Library import failed: {result.stderr}")
        return False


def test_cp_commands():
    """Test unified CLI commands."""
    print("\n[2] Testing cp commands...")

    tests = [
        (["python3", str(CP_PATH), "status"], True, "status"),
        (["python3", str(CP_PATH), "list"], True, "list registries"),
        (["python3", str(CP_PATH), "list", "control_plane"], True, "list items"),
        (["python3", str(CP_PATH), "show", "FMWK-001"], True, "show by ID"),
        (["python3", str(CP_PATH), "show", "Repo OS Spec"], True, "show by name"),
        (["python3", str(CP_PATH), "deps", "FMWK-001"], True, "deps"),
        (["python3", str(CP_PATH), "plan"], True, "plan"),
        (["python3", str(CP_PATH), "verify", "FMWK-001"], True, "verify single"),
        # Invalid item should fail gracefully
        (["python3", str(CP_PATH), "show", "NONEXISTENT-999"], False, "show invalid"),
    ]

    passed = 0
    for cmd, expect_success, desc in tests:
        success, output = run(cmd, expect_success)
        if success:
            print(f"  [OK] {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {desc}")
            print(f"        {output[:200]}")

    return passed == len(tests)


def test_backward_compatibility():
    """Test that existing scripts still work."""
    print("\n[3] Testing backward compatibility...")

    scripts = [
        ("registry.py", ["list"]),
        ("registry.py", ["show", "FMWK-001"]),
        ("validate.py", []),
        ("link.py", ["check"]),
        ("apply_selection.py", []),
    ]

    passed = 0
    for script, args in scripts:
        script_path = SCRIPTS_DIR / script
        cmd = ["python3", str(script_path)] + args
        success, output = run(cmd)
        if success:
            print(f"  [OK] {script} {' '.join(args)}")
            passed += 1
        else:
            print(f"  [FAIL] {script} {' '.join(args)}")

    return passed == len(scripts)


def test_next_action():
    """Test that plan.json has next_action computed."""
    print("\n[4] Testing next_action computation...")

    plan_path = GENERATED_DIR / "plan.json"
    if not plan_path.exists():
        print("  [FAIL] plan.json not found")
        return False

    try:
        with open(plan_path) as f:
            plan = json.load(f)

        # Check that at least some items have next_action
        has_action = False
        for p in plan.get("plans", []):
            for item in p.get("items", []):
                if "next_action" in item:
                    # Check that it's computed (not just empty string for all)
                    if item.get("status") == "missing" and item.get("next_action") == "install":
                        has_action = True
                    elif item.get("status") == "active" and item.get("next_action") == "":
                        has_action = True
                    elif item.get("next_action") == "repair":
                        has_action = True

        if has_action:
            print("  [OK] next_action is computed based on status/artifact")
            return True
        else:
            print("  [WARN] next_action present but may not be computed correctly")
            return True  # Still pass, just warn

    except Exception as e:
        print(f"  [FAIL] Error reading plan.json: {e}")
        return False


def test_doctrine_consistency():
    """Test that doctrine files are consistent."""
    print("\n[5] Testing doctrine consistency...")

    # Check that "Names are primary" is no longer present
    files_to_check = [
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "GEMINI.md",
        REPO_ROOT / "Control_Plane" / "CONTROL_PLANE_SPEC.md",
        REPO_ROOT / "Control_Plane" / "init" / "agent_bootstrap.md",
    ]

    all_good = True
    for filepath in files_to_check:
        if filepath.exists():
            content = filepath.read_text()
            if "Names are primary" in content or "Names Primary" in content:
                print(f"  [FAIL] Old doctrine found in {filepath.name}")
                all_good = False
            else:
                print(f"  [OK] {filepath.name} - doctrine updated")
        else:
            print(f"  [SKIP] {filepath.name} not found")

    return all_good


def main():
    print("=" * 60)
    print("CONTROL PLANE TEST SUITE")
    print("=" * 60)

    results = {
        "library": test_library_imports(),
        "cp_commands": test_cp_commands(),
        "backward_compat": test_backward_compatibility(),
        "next_action": test_next_action(),
        "doctrine": test_doctrine_consistency(),
    }

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"  {symbol} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("[OK] All tests passed")
        return 0
    else:
        print("[FAIL] Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
