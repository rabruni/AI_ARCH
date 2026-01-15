#!/usr/bin/env python3
"""
Execute - Verb Execution Engine (BOOT-012)

Purpose: Automate install/update/verify/uninstall operations on registry items.
Input: verb + item_id
Output: Execution result with PASS/FAIL

Usage:
    python Control_Plane/scripts/execute.py install FMWK-001
    python Control_Plane/scripts/execute.py verify BOOT-001
    python Control_Plane/scripts/execute.py update PRMPT-002
    python Control_Plane/scripts/execute.py uninstall FMWK-050

Exit codes:
    0 = Execution OK
    1 = Item not found
    2 = Verb not supported
    3 = Execution failed
"""

import csv
import json
import os
import sys
from datetime import datetime
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

VALID_VERBS = ["install", "update", "verify", "uninstall"]


class ExecutionResult:
    def __init__(self, item_id: str, verb: str):
        self.item_id = item_id
        self.verb = verb
        self.steps = []
        self.success = True
        self.needs_manual = []

    def step_ok(self, step: str):
        self.steps.append(("OK", step))

    def step_fail(self, step: str):
        self.steps.append(("FAIL", step))
        self.success = False

    def step_manual(self, step: str):
        self.steps.append(("MANUAL", step))
        self.needs_manual.append(step)

    def report(self) -> str:
        lines = [
            "=" * 60,
            f"EXECUTE: {self.verb.upper()} {self.item_id}",
            "=" * 60,
            ""
        ]

        for status, step in self.steps:
            symbol = {"OK": "✓", "FAIL": "✗", "MANUAL": "→"}[status]
            lines.append(f"  [{symbol}] {step}")

        lines.append("")
        lines.append("-" * 60)

        if self.success and not self.needs_manual:
            lines.append(f"RESULT: PASS - {self.verb} completed successfully")
        elif self.success and self.needs_manual:
            lines.append(f"RESULT: PARTIAL - {len(self.needs_manual)} steps need manual action")
        else:
            lines.append(f"RESULT: FAIL - {self.verb} failed")

        lines.append("=" * 60)
        return "\n".join(lines)


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


def find_item_by_id(item_id: str) -> Optional[tuple[dict, Path]]:
    """Find an item by ID across all registries."""
    registries = find_all_registries()

    for reg_path in registries:
        try:
            with open(reg_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []

                # Find the ID column (ends with _id)
                id_col = None
                for h in headers:
                    if h.endswith("_id"):
                        id_col = h
                        break

                if not id_col:
                    continue

                for row in reader:
                    if row.get(id_col, "").strip() == item_id:
                        return (row, reg_path)
        except Exception:
            continue

    return None


def resolve_path(path_str: str) -> Path:
    """Resolve a registry path to absolute path."""
    if not path_str:
        return Path()

    # Remove leading slash if present
    if path_str.startswith("/"):
        path_str = path_str[1:]

    # If path starts with Control_Plane, use repo root
    if path_str.startswith("Control_Plane"):
        return REPO_ROOT / path_str

    # Otherwise, path is relative to Control_Plane
    return CONTROL_PLANE / path_str


def execute_verify(item: dict, reg_path: Path, result: ExecutionResult):
    """Execute verify verb on an item."""

    # Step 1: Check artifact exists
    artifact_path = item.get("artifact_path", "").strip()
    if artifact_path:
        full_path = resolve_path(artifact_path)
        if full_path.exists():
            result.step_ok(f"Artifact exists: {artifact_path}")
        else:
            result.step_fail(f"Artifact missing: {artifact_path}")
    else:
        result.step_ok("No artifact_path defined (pack or virtual item)")

    # Step 2: Check status is valid
    status = item.get("status", "").strip()
    valid_statuses = ["missing", "draft", "active", "deprecated"]
    if status in valid_statuses:
        result.step_ok(f"Status valid: {status}")
    else:
        result.step_fail(f"Invalid status: {status}")

    # Step 3: Check dependencies exist (if any)
    depends_on = item.get("depends_on", "").strip()
    if depends_on:
        dep_ids = [d.strip() for d in depends_on.split(",") if d.strip()]
        for dep_id in dep_ids:
            dep_item = find_item_by_id(dep_id)
            if dep_item:
                result.step_ok(f"Dependency found: {dep_id}")
            else:
                result.step_fail(f"Dependency missing: {dep_id}")
    else:
        result.step_ok("No dependencies")

    # Step 4: Content check (manual for now)
    if artifact_path and resolve_path(artifact_path).is_file():
        result.step_manual(f"Review content matches purpose: {artifact_path}")


def execute_install(item: dict, reg_path: Path, result: ExecutionResult):
    """Execute install verb on an item."""

    # Step 1: Check if already installed
    status = item.get("status", "").strip()
    if status == "active":
        result.step_ok("Already installed (status=active)")
        return

    # Step 2: Check dependencies first
    depends_on = item.get("depends_on", "").strip()
    if depends_on:
        dep_ids = [d.strip() for d in depends_on.split(",") if d.strip()]
        for dep_id in dep_ids:
            dep_item = find_item_by_id(dep_id)
            if dep_item:
                dep_status = dep_item[0].get("status", "")
                if dep_status == "active":
                    result.step_ok(f"Dependency ready: {dep_id}")
                else:
                    result.step_fail(f"Dependency not active: {dep_id} (status={dep_status})")
            else:
                result.step_fail(f"Dependency not found: {dep_id}")
    else:
        result.step_ok("No dependencies to check")

    # Step 3: Check artifact path
    artifact_path = item.get("artifact_path", "").strip()
    if artifact_path:
        full_path = resolve_path(artifact_path)
        if full_path.exists():
            result.step_ok(f"Artifact already exists: {artifact_path}")
        else:
            # Need to create - manual action
            result.step_manual(f"Create artifact: {artifact_path}")
    else:
        result.step_ok("No artifact to create (pack or virtual)")

    # Step 4: Registry update needed
    if status != "active":
        result.step_manual(f"Update registry: set status=active in {reg_path.name}")


def execute_update(item: dict, reg_path: Path, result: ExecutionResult):
    """Execute update verb on an item."""

    # Step 1: Verify item exists and is active
    status = item.get("status", "").strip()
    if status != "active":
        result.step_fail(f"Cannot update non-active item (status={status})")
        return

    result.step_ok("Item is active, can be updated")

    # Step 2: Check artifact exists
    artifact_path = item.get("artifact_path", "").strip()
    if artifact_path:
        full_path = resolve_path(artifact_path)
        if full_path.exists():
            result.step_ok(f"Artifact exists: {artifact_path}")
            result.step_manual(f"Review and modify: {artifact_path}")
        else:
            result.step_fail(f"Artifact missing: {artifact_path}")
    else:
        result.step_manual("Update registry row as needed")

    # Step 3: Registry update
    result.step_manual(f"Update last_updated timestamp in {reg_path.name}")


def execute_uninstall(item: dict, reg_path: Path, result: ExecutionResult):
    """Execute uninstall verb on an item."""

    item_id = None
    for key in item:
        if key.endswith("_id"):
            item_id = item[key]
            break

    # Step 1: Check for dependents
    registries = find_all_registries()
    dependents = []

    for other_reg in registries:
        try:
            with open(other_reg, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    depends_on = row.get("depends_on", "")
                    if item_id and item_id in depends_on:
                        for key in row:
                            if key.endswith("_id"):
                                dependents.append(row[key])
                                break
        except Exception:
            continue

    if dependents:
        result.step_fail(f"Has dependents: {', '.join(dependents)}")
        result.step_manual("Remove or update dependents first")
    else:
        result.step_ok("No dependents found")

    # Step 2: Archive artifact (don't delete)
    artifact_path = item.get("artifact_path", "").strip()
    if artifact_path:
        full_path = resolve_path(artifact_path)
        if full_path.exists():
            archive_path = f"_archive/uninstalled/{datetime.now().strftime('%Y-%m-%d')}"
            result.step_manual(f"Move {artifact_path} to {archive_path}")
        else:
            result.step_ok("No artifact to archive")
    else:
        result.step_ok("No artifact defined")

    # Step 3: Update registry
    result.step_manual(f"Set status=deprecated in {reg_path.name}")


def execute(verb: str, item_id: str) -> bool:
    """Main execution function."""

    # Validate verb
    if verb not in VALID_VERBS:
        print(f"ERROR: Invalid verb '{verb}'")
        print(f"Valid verbs: {', '.join(VALID_VERBS)}")
        return False

    # Find item
    found = find_item_by_id(item_id)
    if not found:
        print(f"ERROR: Item '{item_id}' not found in any registry")
        return False

    item, reg_path = found

    # Get item name for display
    item_name = item.get("name", "Unknown")
    print(f"\nFound: {item_id} ({item_name})")
    print(f"Registry: {reg_path.relative_to(REPO_ROOT)}\n")

    # Execute verb
    result = ExecutionResult(item_id, verb)

    if verb == "verify":
        execute_verify(item, reg_path, result)
    elif verb == "install":
        execute_install(item, reg_path, result)
    elif verb == "update":
        execute_update(item, reg_path, result)
    elif verb == "uninstall":
        execute_uninstall(item, reg_path, result)

    print(result.report())

    return result.success


def main():
    if len(sys.argv) < 3:
        print("Usage: python execute.py <verb> <item_id>")
        print(f"Verbs: {', '.join(VALID_VERBS)}")
        print("\nExamples:")
        print("  python execute.py verify BOOT-001")
        print("  python execute.py install FMWK-001")
        return 1

    verb = sys.argv[1].lower()
    item_id = sys.argv[2].upper()

    success = execute(verb, item_id)
    return 0 if success else 3


if __name__ == "__main__":
    sys.exit(main())
