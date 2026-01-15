#!/usr/bin/env python3
"""
Link - Registry Linking and Relationship Manager (BOOT-019)

Purpose: Manage relationships between registry items and validate dependency graphs.

Usage:
    python link.py deps <item_id>              # Show dependencies for an item
    python link.py dependents <item_id>        # Show items that depend on this
    python link.py graph                       # Show full dependency graph
    python link.py check                       # Check for broken/circular deps
    python link.py orphans                     # Find items with no dependencies
    python link.py roots                       # Find root items (no dependents)

Exit codes:
    0 = Success
    1 = Item not found
    2 = Circular dependency detected
    3 = Broken dependency found
"""

import csv
import sys
from collections import defaultdict
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

# All registries to scan
REGISTRIES = [
    CONTROL_PLANE / "boot_os_registry.csv",
    CONTROL_PLANE / "registries" / "frameworks_registry.csv",
    CONTROL_PLANE / "registries" / "prompts_registry.csv",
    CONTROL_PLANE / "registries" / "modules_registry.csv",
    CONTROL_PLANE / "registries" / "cloud_services_registry.csv",
    CONTROL_PLANE / "registries" / "components_registry.csv",
    CONTROL_PLANE / "init" / "init_registry.csv",
]


def read_registry(registry_path: Path) -> tuple[list[str], list[dict]]:
    """Read a registry file."""
    if not registry_path.is_file():
        return [], []
    with open(registry_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def get_id_column(headers: list[str]) -> Optional[str]:
    """Find the ID column."""
    for h in headers:
        if h.endswith("_id"):
            return h
    return None


def load_all_items() -> dict[str, tuple[dict, Path, str]]:
    """Load all items from all registries. Returns {item_id: (item, registry_path, id_column)}."""
    items = {}
    for reg_path in REGISTRIES:
        if not reg_path.is_file():
            continue
        headers, rows = read_registry(reg_path)
        id_col = get_id_column(headers)
        if not id_col:
            continue
        for row in rows:
            item_id = row.get(id_col, "").upper()
            if item_id:
                items[item_id] = (row, reg_path, id_col)
    return items


def get_dependencies(item: dict) -> list[str]:
    """Extract dependencies from an item."""
    deps_str = item.get("depends_on", "") or item.get("dependencies", "")
    if not deps_str:
        return []
    return [d.strip().upper() for d in deps_str.split(",") if d.strip()]


def build_dependency_graph(items: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Build forward and reverse dependency graphs."""
    forward = defaultdict(list)  # item -> its dependencies
    reverse = defaultdict(list)  # item -> items that depend on it

    for item_id, (item, _, _) in items.items():
        deps = get_dependencies(item)
        forward[item_id] = deps
        for dep in deps:
            reverse[dep].append(item_id)

    return dict(forward), dict(reverse)


def find_circular_deps(forward: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Find circular dependencies using DFS."""
    circular = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for dep in forward.get(node, []):
            if dep not in visited:
                result = dfs(dep)
                if result:
                    return result
            elif dep in rec_stack:
                # Found cycle
                cycle_start = path.index(dep)
                cycle = path[cycle_start:] + [dep]
                for i in range(len(cycle) - 1):
                    circular.append((cycle[i], cycle[i + 1]))
                return True

        path.pop()
        rec_stack.remove(node)
        return False

    for node in forward:
        if node not in visited:
            dfs(node)

    return circular


def find_broken_deps(items: dict, forward: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Find dependencies that reference non-existent items."""
    broken = []
    for item_id, deps in forward.items():
        for dep in deps:
            if dep not in items:
                broken.append((item_id, dep))
    return broken


# === Commands ===

def cmd_deps(item_id: str):
    """Show dependencies for an item."""
    item_id = item_id.upper()
    items = load_all_items()

    if item_id not in items:
        print(f"Item not found: {item_id}")
        return 1

    item, reg_path, id_col = items[item_id]
    deps = get_dependencies(item)

    print(f"\nDependencies for {item_id}")
    print("=" * 60)
    print(f"Name: {item.get('name', '?')}")
    print(f"Registry: {reg_path.relative_to(REPO_ROOT)}")

    if not deps:
        print("\n  (no dependencies)")
    else:
        print(f"\nDirect dependencies ({len(deps)}):")
        for dep in deps:
            if dep in items:
                dep_item = items[dep][0]
                status = dep_item.get("status", "?")
                name = dep_item.get("name", "?")
                print(f"  [✓] {dep}: {name} ({status})")
            else:
                print(f"  [✗] {dep}: NOT FOUND")

        # Transitive dependencies
        all_deps = set()
        queue = list(deps)
        while queue:
            current = queue.pop(0)
            if current in all_deps:
                continue
            all_deps.add(current)
            if current in items:
                queue.extend(get_dependencies(items[current][0]))

        if len(all_deps) > len(deps):
            print(f"\nAll dependencies (transitive): {len(all_deps)}")
            for dep in sorted(all_deps):
                if dep in items:
                    print(f"  {dep}")
                else:
                    print(f"  {dep} [MISSING]")

    return 0


def cmd_dependents(item_id: str):
    """Show items that depend on this item."""
    item_id = item_id.upper()
    items = load_all_items()

    if item_id not in items:
        print(f"Item not found: {item_id}")
        return 1

    item, reg_path, _ = items[item_id]
    _, reverse = build_dependency_graph(items)

    dependents = reverse.get(item_id, [])

    print(f"\nDependents of {item_id}")
    print("=" * 60)
    print(f"Name: {item.get('name', '?')}")

    if not dependents:
        print("\n  (no items depend on this)")
    else:
        print(f"\nDirect dependents ({len(dependents)}):")
        for dep_id in sorted(dependents):
            if dep_id in items:
                dep_item = items[dep_id][0]
                name = dep_item.get("name", "?")
                print(f"  {dep_id}: {name}")

    return 0


def cmd_graph():
    """Show full dependency graph."""
    items = load_all_items()
    forward, reverse = build_dependency_graph(items)

    print("\nDependency Graph")
    print("=" * 60)

    # Group by registry
    by_registry = defaultdict(list)
    for item_id, (item, reg_path, _) in items.items():
        by_registry[str(reg_path.relative_to(REPO_ROOT))].append((item_id, item))

    for reg_path, reg_items in sorted(by_registry.items()):
        print(f"\n[{reg_path}]")
        for item_id, item in sorted(reg_items):
            deps = forward.get(item_id, [])
            name = item.get("name", "?")
            if deps:
                deps_str = ", ".join(deps)
                print(f"  {item_id} → [{deps_str}]")
            else:
                print(f"  {item_id} (root)")

    print(f"\nTotal: {len(items)} items")
    return 0


def cmd_check():
    """Check for broken and circular dependencies."""
    items = load_all_items()
    forward, _ = build_dependency_graph(items)

    print("\nDependency Health Check")
    print("=" * 60)

    # Check for broken deps
    broken = find_broken_deps(items, forward)
    if broken:
        print(f"\n[✗] Broken dependencies ({len(broken)}):")
        for from_id, to_id in broken:
            print(f"  {from_id} → {to_id} (not found)")
    else:
        print("\n[✓] No broken dependencies")

    # Check for circular deps
    circular = find_circular_deps(forward)
    if circular:
        print(f"\n[✗] Circular dependencies ({len(circular)}):")
        for from_id, to_id in circular:
            print(f"  {from_id} → {to_id}")
    else:
        print("[✓] No circular dependencies")

    # Summary
    print()
    print("-" * 60)
    if broken or circular:
        errors = len(broken) + len(circular)
        print(f"✗ Found {errors} dependency issues")
        return 2 if circular else 3
    else:
        print("✓ All dependencies valid")
        return 0


def cmd_orphans():
    """Find items with no dependencies (potential entry points)."""
    items = load_all_items()
    forward, _ = build_dependency_graph(items)

    orphans = [item_id for item_id, deps in forward.items() if not deps]

    print("\nOrphan Items (no dependencies)")
    print("=" * 60)

    for item_id in sorted(orphans):
        if item_id in items:
            item = items[item_id][0]
            name = item.get("name", "?")
            status = item.get("status", "?")
            print(f"  {item_id}: {name} ({status})")

    print(f"\nTotal: {len(orphans)} orphans")
    return 0


def cmd_roots():
    """Find root items (nothing depends on them)."""
    items = load_all_items()
    _, reverse = build_dependency_graph(items)

    # Items with no dependents
    roots = [item_id for item_id in items if item_id not in reverse]

    print("\nRoot Items (no dependents)")
    print("=" * 60)

    for item_id in sorted(roots):
        item = items[item_id][0]
        name = item.get("name", "?")
        status = item.get("status", "?")
        print(f"  {item_id}: {name} ({status})")

    print(f"\nTotal: {len(roots)} roots")
    return 0


def cmd_tree(item_id: str):
    """Show dependency tree for an item."""
    item_id = item_id.upper()
    items = load_all_items()

    if item_id not in items:
        print(f"Item not found: {item_id}")
        return 1

    forward, _ = build_dependency_graph(items)

    print(f"\nDependency Tree for {item_id}")
    print("=" * 60)

    visited = set()

    def print_tree(node, prefix="", is_last=True):
        if node in visited:
            print(f"{prefix}{'└── ' if is_last else '├── '}{node} (circular)")
            return
        visited.add(node)

        connector = "└── " if is_last else "├── "
        if node in items:
            name = items[node][0].get("name", "?")
            print(f"{prefix}{connector}{node}: {name}")
        else:
            print(f"{prefix}{connector}{node} [NOT FOUND]")

        deps = forward.get(node, [])
        for i, dep in enumerate(deps):
            is_dep_last = (i == len(deps) - 1)
            child_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(dep, child_prefix, is_dep_last)

    print_tree(item_id)
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python link.py <command> [args]")
        print("\nCommands:")
        print("  deps <item_id>       Show dependencies for an item")
        print("  dependents <item_id> Show items that depend on this")
        print("  tree <item_id>       Show dependency tree")
        print("  graph                Show full dependency graph")
        print("  check                Check for broken/circular deps")
        print("  orphans              Find items with no dependencies")
        print("  roots                Find items nothing depends on")
        print("\nExamples:")
        print("  python link.py deps BOOT-005")
        print("  python link.py dependents BOOT-001")
        print("  python link.py check")
        return 1

    command = sys.argv[1].lower()

    if command == "deps":
        if len(sys.argv) < 3:
            print("Usage: link.py deps <item_id>")
            return 1
        return cmd_deps(sys.argv[2])
    elif command == "dependents":
        if len(sys.argv) < 3:
            print("Usage: link.py dependents <item_id>")
            return 1
        return cmd_dependents(sys.argv[2])
    elif command == "tree":
        if len(sys.argv) < 3:
            print("Usage: link.py tree <item_id>")
            return 1
        return cmd_tree(sys.argv[2])
    elif command == "graph":
        return cmd_graph()
    elif command == "check":
        return cmd_check()
    elif command == "orphans":
        return cmd_orphans()
    elif command == "roots":
        return cmd_roots()
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
