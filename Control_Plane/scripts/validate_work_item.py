#!/usr/bin/env python3
"""
validate_work_item.py - Validate WORK_ITEM.md contracts.

Usage:
  python3 Control_Plane/scripts/validate_work_item.py <path>
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Tuple


REQUIRED_FIELDS = ["ID", "Title", "Status", "ALTITUDE"]
REQUIRED_SECTIONS = [
    "Objective",
    "Scope: File Permissions",
    "Implementation Plan",
    "Execution Guardrails",
    "Acceptance Commands",
]
FORBIDDEN_PREFIXES = [".git/", ".github/", "Control_Plane/"]
ALLOWLIST_EXACT = {"Control_Plane/scripts/validate_work_item.py"}


def parse_front_matter(text: str) -> Tuple[Dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end_idx = lines[1:].index("---") + 1
    except ValueError:
        return {}, text
    raw = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :])
    data: Dict[str, str] = {}
    for line in raw:
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data, body


def section_text(body: str, heading: str) -> str:
    lines = body.splitlines()
    heading_key = f"## {heading}".lower()
    start = None
    for idx, line in enumerate(lines):
        if line.strip().lower().startswith(heading_key):
            start = idx + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start, len(lines)):
        if lines[idx].strip().startswith("## "):
            end = idx
            break
    return "\n".join(lines[start:end]).strip()


def extract_modifiable(scope: str) -> list[str]:
    paths = []
    for line in scope.splitlines():
        if "MODIFIABLE:" in line:
            _, value = line.split("MODIFIABLE:", 1)
            path = value.strip()
            if path:
                paths.append(path)
    return paths


def has_numbered_step(plan: str) -> bool:
    for line in plan.splitlines():
        stripped = line.strip()
        if stripped and stripped[0].isdigit() and stripped[1:2] == ".":
            return True
    return False


def has_command(commands: str) -> bool:
    for line in commands.splitlines():
        if line.lstrip().startswith("$"):
            return True
    return False


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_work_item.py <path>")
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"[FAIL] Work item not found: {path}")
        return 2

    content = path.read_text(encoding="utf-8")
    front_matter, body = parse_front_matter(content)
    errors: list[str] = []

    if not front_matter:
        errors.append("Missing or invalid YAML front matter")
    else:
        for field in REQUIRED_FIELDS:
            if not front_matter.get(field):
                errors.append(f"Missing required field: {field}")

    for section in REQUIRED_SECTIONS:
        if not section_text(body, section):
            errors.append(f"Missing section: {section}")

    scope = section_text(body, "Scope: File Permissions")
    modifiable_paths = extract_modifiable(scope)
    if not modifiable_paths:
        errors.append("Scope must include at least one MODIFIABLE entry")

    for item in modifiable_paths:
        if item in ALLOWLIST_EXACT:
            continue
        for prefix in FORBIDDEN_PREFIXES:
            if item.startswith(prefix):
                errors.append(f"Forbidden scope path: {item}")

    plan = section_text(body, "Implementation Plan")
    if not has_numbered_step(plan):
        errors.append("Implementation Plan must include at least one numbered step")

    commands = section_text(body, "Acceptance Commands")
    if not has_command(commands):
        errors.append("Acceptance Commands must include at least one command")

    guardrails = section_text(body, "Execution Guardrails")
    if "ASK" not in guardrails or "STOP" not in guardrails:
        errors.append("Execution Guardrails must include ASK and STOP")

    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        return 1

    print("[OK] Work item valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
