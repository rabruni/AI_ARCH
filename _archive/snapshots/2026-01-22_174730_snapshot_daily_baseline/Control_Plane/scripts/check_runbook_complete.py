#!/usr/bin/env python3
"""Check that a runbook markdown file contains no TODO/TBD placeholders.

Usage: python3 check_runbook_complete.py <path-to-md>

Exit codes:
    0 - PASS (no placeholders found)
    1 - FAIL (placeholders found)
    2 - ERROR (file not found)
"""
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_runbook_complete.py <path-to-md>")
        return 2

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return 2

    content = file_path.read_text(encoding="utf-8")

    # Check for placeholder patterns
    placeholders = ["(TODO)", "TODO", "TBD"]
    found = []
    for placeholder in placeholders:
        if placeholder in content:
            found.append(placeholder)

    if found:
        print(f"FAIL: Found placeholders in {file_path.name}: {', '.join(found)}")
        return 1

    print(f"PASS: {file_path.name} contains no TODO/TBD placeholders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
