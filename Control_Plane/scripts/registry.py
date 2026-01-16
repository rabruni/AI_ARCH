#!/usr/bin/env python3
"""
Registry - Registry CRUD Operations (BOOT-014)

Purpose: Add, modify, delete, and list registry items.

Usage:
    python registry.py list [registry]           # List all items or specific registry
    python registry.py show <item_id>            # Show item details
    python registry.py add <registry> <fields>   # Add new item
    python registry.py modify <item_id> <fields> # Modify existing item
    python registry.py delete <item_id>          # Mark item as deprecated

Exit codes:
    0 = Success
    1 = Item/Registry not found
    2 = Invalid operation
    3 = Validation failed
"""

import sys
from pathlib import Path
from typing import Optional

# Use canonical library
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Control_Plane.lib import (
    REPO_ROOT,
    CONTROL_PLANE,
    find_all_registries,
    find_registry_by_name,
    read_registry,
    write_registry,
    get_id_column,
    find_item,
)


def parse_fields(args: list[str]) -> dict:
    """Parse field=value arguments into a dict."""
    fields = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            fields[key.strip()] = value.strip()
    return fields


# === Operations ===

def op_list(registry_name: Optional[str] = None):
    """List registries or items in a specific registry."""

    if registry_name:
        reg_path = find_registry_by_name(registry_name)
        if not reg_path:
            print(f"Registry not found: {registry_name}")
            return 1

        headers, rows = read_registry(reg_path)
        id_col = get_id_column(headers)

        print(f"\n{reg_path.relative_to(REPO_ROOT)}")
        print("=" * 60)

        for row in rows:
            item_id = row.get(id_col, "?") if id_col else "?"
            name = row.get("name", "?")
            status = row.get("status", "?")
            print(f"  {name:40} {status:10} ({item_id})")

        print(f"\nTotal: {len(rows)} items")
        return 0

    else:
        # List all registries
        registries = find_all_registries()

        print("\nRegistries")
        print("=" * 60)

        for reg in registries:
            rel_path = reg.relative_to(REPO_ROOT)
            _, rows = read_registry(reg)
            print(f"  {rel_path} ({len(rows)} items)")

        print(f"\nTotal: {len(registries)} registries")
        return 0


def op_show(query: str):
    """Show details of a specific item (by name or ID)."""
    found = find_item(query)

    if not found:
        print(f"Item not found: {query}")
        return 1

    row, reg_path, _ = found
    item_name = row.get("name", query)
    headers, _ = read_registry(reg_path)
    id_col = get_id_column(headers)
    item_id = row.get("id", row.get(id_col or "id", "?"))

    print(f"\n{item_name} ({item_id})")
    print(f"Registry: {reg_path.relative_to(REPO_ROOT)}")
    print("=" * 60)

    for key, value in row.items():
        if value:
            print(f"  {key}: {value}")

    return 0


def op_add(registry_name: str, fields: dict):
    """Add a new item to a registry."""
    reg_path = find_registry_by_name(registry_name)

    if not reg_path:
        print(f"Registry not found: {registry_name}")
        return 1

    headers, rows = read_registry(reg_path)
    id_col = get_id_column(headers)

    if not id_col:
        print(f"Registry has no ID column")
        return 2

    # Check ID is provided
    if id_col not in fields:
        print(f"Must provide {id_col}")
        return 2

    # Check ID doesn't already exist
    new_id = fields[id_col]
    for row in rows:
        if row.get(id_col) == new_id:
            print(f"ID already exists: {new_id}")
            return 3

    # Create new row with defaults
    new_row = {h: "" for h in headers}
    if "status" in headers:
        new_row["status"] = "missing"
    if "selected" in headers:
        new_row["selected"] = "no"

    # Apply provided fields
    for key, value in fields.items():
        if key in headers:
            new_row[key] = value
        else:
            print(f"Warning: Unknown field '{key}' ignored")

    rows.append(new_row)
    write_registry(reg_path, headers, rows)

    print(f"\nAdded: {new_id}")
    print(f"Registry: {reg_path.relative_to(REPO_ROOT)}")
    print("\nFields set:")
    for key, value in new_row.items():
        if value:
            print(f"  {key}: {value}")

    return 0


def op_modify(query: str, fields: dict):
    """Modify an existing item (by name or ID)."""
    found = find_item(query)

    if not found:
        print(f"Item not found: {query}")
        return 1

    row, reg_path, row_idx = found
    item_name = row.get("name", query)
    headers, rows = read_registry(reg_path)

    # Track changes
    changes = []

    for key, value in fields.items():
        if key in headers:
            old_value = rows[row_idx].get(key, "")
            if old_value != value:
                rows[row_idx][key] = value
                changes.append((key, old_value, value))
        else:
            print(f"Warning: Unknown field '{key}' ignored")

    if not changes:
        print("No changes made")
        return 0

    write_registry(reg_path, headers, rows)

    print(f"\nModified: {item_name}")
    print(f"Registry: {reg_path.relative_to(REPO_ROOT)}")
    print("\nChanges:")
    for key, old, new in changes:
        print(f"  {key}: '{old}' -> '{new}'")

    return 0


def op_delete(query: str, force: bool = False):
    """Mark an item as deprecated (soft delete). Supports name or ID."""
    found = find_item(query)

    if not found:
        print(f"Item not found: {query}")
        return 1

    row, reg_path, row_idx = found
    item_name = row.get("name", query)
    headers, rows = read_registry(reg_path)

    current_status = rows[row_idx].get("status", "")

    if current_status == "deprecated":
        print(f"Item already deprecated: {item_name}")
        return 0

    if not force:
        print(f"\nWill deprecate: {item_name}")
        print(f"Current status: {current_status}")
        print("\nUse --force to confirm")
        return 2

    # Soft delete - mark as deprecated
    if "status" in headers:
        rows[row_idx]["status"] = "deprecated"
    if "selected" in headers:
        rows[row_idx]["selected"] = "no"

    write_registry(reg_path, headers, rows)

    print(f"\nDeprecated: {item_name}")
    print(f"Registry: {reg_path.relative_to(REPO_ROOT)}")
    print("Status set to 'deprecated', selected set to 'no'")

    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python registry.py <command> [args]")
        print("\nCommands:")
        print("  list [registry]           List all registries or items in one")
        print("  show <item_id>            Show item details")
        print("  add <registry> <fields>   Add new item (field=value ...)")
        print("  modify <item_id> <fields> Modify item (field=value ...)")
        print("  delete <item_id> [--force] Mark item as deprecated")
        print("\nExamples:")
        print("  python registry.py list")
        print("  python registry.py list boot_os")
        print("  python registry.py show BOOT-001")
        print("  python registry.py add boot_os boot_os_id=BOOT-018 name=\"New Item\"")
        print("  python registry.py modify BOOT-018 status=active")
        print("  python registry.py delete BOOT-018 --force")
        return 1

    command = sys.argv[1].lower()

    if command == "list":
        registry_name = sys.argv[2] if len(sys.argv) > 2 else None
        return op_list(registry_name)

    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: registry.py show <name or id>")
            return 2
        return op_show(sys.argv[2])

    elif command == "add":
        if len(sys.argv) < 4:
            print("Usage: registry.py add <registry> <field=value> ...")
            return 2
        registry_name = sys.argv[2]
        fields = parse_fields(sys.argv[3:])
        return op_add(registry_name, fields)

    elif command == "modify":
        if len(sys.argv) < 4:
            print("Usage: registry.py modify <name or id> <field=value> ...")
            return 2
        query = sys.argv[2]
        fields = parse_fields(sys.argv[3:])
        return op_modify(query, fields)

    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: registry.py delete <name or id> [--force]")
            return 2
        query = sys.argv[2]
        force = "--force" in sys.argv
        return op_delete(query, force)

    else:
        print(f"Unknown command: {command}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
