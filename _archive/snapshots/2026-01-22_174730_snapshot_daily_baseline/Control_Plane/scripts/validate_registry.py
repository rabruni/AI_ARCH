#!/usr/bin/env python3
"""
validate_registry.py

Validates repository structure and CSV registries according to SYSTEM_CONSTITUTION.md.
Rules are single-sourced from the Machine-Enforceable YAML block in the constitution.

Usage:
  python scripts/validate_registry.py
"""
from __future__ import annotations
import csv
import re
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List, Set

# Use canonical library
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Control_Plane.lib import (
    REPO_ROOT,
    CONTROL_PLANE,
    REGISTRIES_DIR,
)

CONSTITUTION_PATH = REPO_ROOT / "SYSTEM_CONSTITUTION.md"


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def warn(msg: str) -> None:
    print(f"WARN: {msg}")


def load_constitution_rules() -> Dict[str, Any]:
    """Extract and parse the YAML block from SYSTEM_CONSTITUTION.md."""
    if not CONSTITUTION_PATH.exists():
        fail(f"Constitution not found: {CONSTITUTION_PATH}")

    content = CONSTITUTION_PATH.read_text(encoding="utf-8")

    # Find YAML block between ```yaml and ```
    match = re.search(r"```yaml\n(.*?)```", content, re.DOTALL)
    if not match:
        fail("No machine-enforceable YAML block found in SYSTEM_CONSTITUTION.md")

    try:
        rules = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        fail(f"Invalid YAML in constitution: {e}")

    return rules


def validate_structure(rules: Dict[str, Any]) -> None:
    """Validate required directories and files exist."""
    print("Validating repository structure...")

    # Required directories
    for dir_path in rules.get("required_directories", []):
        full_path = REPO_ROOT / dir_path
        if not full_path.is_dir():
            fail(f"Required directory missing: {dir_path}")
        print(f"  [OK] {dir_path}/")

    # Required files
    for file_path in rules.get("required_files", []):
        full_path = REPO_ROOT / file_path
        if not full_path.is_file():
            fail(f"Required file missing: {file_path}")
        print(f"  [OK] {file_path}")


def read_csv(path: Path) -> List[Dict[str, str]]:
    """Read CSV file and return list of row dicts."""
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def infer_id_field(rows: List[Dict[str, str]]) -> str:
    """Find the column ending with _id."""
    if not rows:
        return ""
    for key in rows[0].keys():
        if key.endswith("_id"):
            return key
    return ""


def validate_registry(
    path: Path,
    schema: Dict[str, Any],
    control_plane_root: Path
) -> List[Dict[str, str]]:
    """Validate a single registry CSV against the schema."""
    rows = read_csv(path)
    if not rows:
        warn(f"{path.name} is empty")
        return rows

    # Check for ID column
    id_field = infer_id_field(rows)
    if not id_field:
        fail(f"{path}: No *_id column found (required by constitution)")

    # Check required columns
    required_cols = schema.get("required_columns", [])
    headers = set(rows[0].keys())
    for col in required_cols:
        if col == "*_id":
            continue  # Already checked via infer_id_field
        if col not in headers:
            fail(f"{path}: Missing required column '{col}'")

    # Extract enum sets from schema
    status_values = set(schema.get("status_values", []))
    selected_values = set(schema.get("selected_values", []))
    priority_values = set(schema.get("priority_values", []))
    path_columns = schema.get("path_columns_to_validate", [])
    cp_rule = schema.get("control_plane_rule", {})

    # Validate ID uniqueness
    ids = [r.get(id_field, "").strip() for r in rows]
    if any(not x for x in ids):
        fail(f"{path}: Empty {id_field} value found")
    if len(set(ids)) != len(ids):
        seen, dups = set(), set()
        for x in ids:
            if x in seen:
                dups.add(x)
            seen.add(x)
        fail(f"{path}: Duplicate IDs: {sorted(dups)}")

    id_set = set(ids)

    # Validate each row
    for i, row in enumerate(rows, start=2):
        row_id = row.get(id_field, "")
        ctx = f"{path.name}:{i} ({row_id})"

        # Status enum
        status = (row.get("status", "") or "").strip()
        if status and status not in status_values:
            fail(f"{ctx}: Invalid status='{status}' (allowed: {sorted(status_values)})")

        # Selected enum
        selected = (row.get("selected", "") or "").strip()
        if selected and selected not in selected_values:
            fail(f"{ctx}: Invalid selected='{selected}' (allowed: {sorted(selected_values)})")

        # Priority enum (if column exists)
        if "priority" in row:
            priority = (row.get("priority", "") or "").strip()
            if priority and priority not in priority_values:
                fail(f"{ctx}: Invalid priority='{priority}' (allowed: {sorted(priority_values)})")

        # Name required and non-empty
        name = (row.get("name", "") or "").strip()
        if not name:
            fail(f"{ctx}: 'name' column is empty (required by constitution)")

        # Path validation for selected items
        if selected == "yes":
            for col in path_columns:
                if col not in row:
                    continue
                val = (row.get(col, "") or "").strip()
                if not val:
                    continue
                # Resolve path relative to Control_Plane root
                check_path = (control_plane_root / val.lstrip("/")).resolve()
                if not check_path.exists():
                    fail(f"{ctx}: {col}='{val}' file not found (expected: {check_path})")

        # Control plane rule: if trigger column has trigger value, required column must be set
        if cp_rule:
            trigger_col = cp_rule.get("trigger_column", "")
            trigger_vals = [str(v).lower() for v in cp_rule.get("trigger_values", [])]
            required_col = cp_rule.get("required_column", "")

            if trigger_col in row:
                trigger_val = (row.get(trigger_col, "") or "").strip().lower()
                if trigger_val in trigger_vals:
                    required_val = (row.get(required_col, "") or "").strip()
                    if not required_val:
                        fail(f"{ctx}: {trigger_col}='{trigger_val}' requires {required_col} to be set")

        # Dependency validation
        if "dependencies" in row:
            deps_raw = (row.get("dependencies", "") or "").strip()
            if deps_raw:
                deps = [d.strip() for d in deps_raw.split(",") if d.strip()]
                missing = [d for d in deps if d not in id_set]
                if missing:
                    fail(f"{ctx}: Dependencies not found in registry: {missing}")

    return rows


def recurse_child_registries(
    rows: List[Dict[str, str]],
    visited: Set[Path],
    queue: List[Path],
    control_plane_root: Path
) -> None:
    """Find child registries from selected rows and add to queue."""
    for row in rows:
        if (row.get("selected", "") or "").strip() != "yes":
            continue
        child_path_str = (row.get("child_registry_path", "") or "").strip()
        if not child_path_str:
            continue
        child_path = (control_plane_root / child_path_str.lstrip("/")).resolve()
        if not child_path.exists():
            fail(f"Selected row references missing child registry: {child_path_str}")
        if child_path not in visited:
            queue.append(child_path)


def main() -> None:
    print(f"Loading rules from {CONSTITUTION_PATH.name}...")
    rules = load_constitution_rules()
    schema = rules.get("registry_schema", {})

    print(f"Constitution version: {rules.get('version', 'unknown')}")
    print()

    # Validate structure
    validate_structure(rules)
    print()

    # Find root registries
    registries_dir = CONTROL_PLANE_ROOT / "registries"
    if not registries_dir.is_dir():
        fail(f"Registries directory not found: {registries_dir}")

    root_registries = sorted(registries_dir.glob("*_registry.csv"))
    if not root_registries:
        fail("No *_registry.csv files found in Control_Plane/registries/")

    visited: Set[Path] = set()
    queue: List[Path] = []

    # Validate root registries
    print("Validating registries...")
    for reg_path in root_registries:
        rel_path = reg_path.relative_to(CONTROL_PLANE_ROOT)
        print(f"  {rel_path}")
        rows = validate_registry(reg_path, schema, CONTROL_PLANE_ROOT)
        visited.add(reg_path.resolve())
        recurse_child_registries(rows, visited, queue, CONTROL_PLANE_ROOT)

    # BFS through child registries
    while queue:
        reg_path = queue.pop(0).resolve()
        if reg_path in visited:
            continue
        rel_path = reg_path.relative_to(CONTROL_PLANE_ROOT)
        print(f"  {rel_path}")
        rows = validate_registry(reg_path, schema, CONTROL_PLANE_ROOT)
        visited.add(reg_path)
        recurse_child_registries(rows, visited, queue, CONTROL_PLANE_ROOT)

    print()
    print(f"OK: All validations passed ({len(visited)} registries checked)")


if __name__ == "__main__":
    main()
