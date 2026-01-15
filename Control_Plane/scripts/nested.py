#!/usr/bin/env python3
"""
Nested - Nested Registry Loader (BOOT-017)

Purpose: Fully resolve and load nested registries via child_registry_path.

Usage:
    python nested.py tree                    # Show full registry tree
    python nested.py tree <registry>         # Show tree from specific registry
    python nested.py flatten                 # List all items across all registries
    python nested.py check                   # Check for circular dependencies

Exit codes:
    0 = Success
    1 = Registry not found
    2 = Circular dependency detected
"""

import csv
import json
import sys
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


def get_root_registries() -> list[Path]:
    """Get the top-level registries (entry points)."""
    root_reg = CONTROL_PLANE / "registries"
    if root_reg.is_dir():
        return sorted(root_reg.glob("*.csv"))
    return []


def read_registry(reg_path: Path) -> tuple[list[str], list[dict]]:
    """Read a registry and return headers and rows."""
    with open(reg_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def get_id_column(headers: list[str]) -> Optional[str]:
    """Find the ID column (ends with _id)."""
    for h in headers:
        if h.endswith("_id"):
            return h
    return None


class RegistryNode:
    """A node in the registry tree."""

    def __init__(self, path: Path, parent: Optional['RegistryNode'] = None):
        self.path = path
        self.parent = parent
        self.children: list['RegistryNode'] = []
        self.items: list[dict] = []
        self.headers: list[str] = []
        self.id_column: Optional[str] = None
        self.error: Optional[str] = None

    def load(self):
        """Load this registry."""
        try:
            self.headers, self.items = read_registry(self.path)
            self.id_column = get_id_column(self.headers)
        except Exception as e:
            self.error = str(e)

    def get_child_paths(self) -> list[tuple[str, str]]:
        """Get child registry paths from items. Returns [(item_id, path), ...]"""
        children = []
        for item in self.items:
            child_path = item.get("child_registry_path", "").strip()
            if child_path:
                item_id = item.get(self.id_column, "?") if self.id_column else "?"
                children.append((item_id, child_path))
        return children

    def depth(self) -> int:
        """Calculate depth from root."""
        d = 0
        node = self.parent
        while node:
            d += 1
            node = node.parent
        return d

    def rel_path(self) -> str:
        """Get path relative to repo root."""
        try:
            return str(self.path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.path)


class RegistryTree:
    """Full tree of nested registries."""

    def __init__(self):
        self.roots: list[RegistryNode] = []
        self.all_nodes: dict[str, RegistryNode] = {}  # path -> node
        self.circular_deps: list[tuple[str, str]] = []  # [(from, to), ...]

    def load_from_roots(self, root_paths: list[Path]):
        """Load tree starting from root registries."""
        for path in root_paths:
            if str(path) not in self.all_nodes:
                node = RegistryNode(path)
                self.roots.append(node)
                self._load_recursive(node, set())

    def load_from_single(self, path: Path):
        """Load tree starting from a single registry."""
        if str(path) not in self.all_nodes:
            node = RegistryNode(path)
            self.roots.append(node)
            self._load_recursive(node, set())

    def _load_recursive(self, node: RegistryNode, visited: set):
        """Recursively load a node and its children."""
        path_str = str(node.path)

        # Check for circular dependency
        if path_str in visited:
            if node.parent:
                self.circular_deps.append((node.parent.rel_path(), node.rel_path()))
            return

        visited.add(path_str)
        self.all_nodes[path_str] = node

        # Load this node
        node.load()
        if node.error:
            return

        # Load children
        for item_id, child_path in node.get_child_paths():
            resolved = resolve_path(child_path)
            if resolved.is_file():
                child_node = RegistryNode(resolved, parent=node)
                node.children.append(child_node)
                self._load_recursive(child_node, visited.copy())

    def print_tree(self, node: Optional[RegistryNode] = None, prefix: str = ""):
        """Print the tree structure."""
        if node is None:
            # Print all roots
            for i, root in enumerate(self.roots):
                is_last = (i == len(self.roots) - 1)
                self._print_node(root, "", is_last)
        else:
            self._print_node(node, prefix, True)

    def _print_node(self, node: RegistryNode, prefix: str, is_last: bool):
        """Print a single node and its children."""
        connector = "└── " if is_last else "├── "

        # Node info
        item_count = len(node.items)
        child_count = len(node.children)

        status = ""
        if node.error:
            status = f" [ERROR: {node.error}]"
        elif child_count > 0:
            status = f" ({item_count} items, {child_count} children)"
        else:
            status = f" ({item_count} items)"

        print(f"{prefix}{connector}{node.rel_path()}{status}")

        # Children
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            is_child_last = (i == len(node.children) - 1)
            self._print_node(child, child_prefix, is_child_last)

    def flatten(self) -> list[tuple[str, dict, str]]:
        """Get all items from all registries. Returns [(registry_path, item, item_id), ...]"""
        items = []
        for node in self.all_nodes.values():
            for item in node.items:
                item_id = item.get(node.id_column, "?") if node.id_column else "?"
                items.append((node.rel_path(), item, item_id))
        return items

    def stats(self) -> dict:
        """Get statistics about the tree."""
        total_items = 0
        selected = 0
        active = 0
        missing = 0

        for node in self.all_nodes.values():
            for item in node.items:
                total_items += 1
                if item.get("selected", "").lower() == "yes":
                    selected += 1
                status = item.get("status", "").lower()
                if status == "active":
                    active += 1
                elif status == "missing":
                    missing += 1

        return {
            "registries": len(self.all_nodes),
            "total_items": total_items,
            "selected": selected,
            "active": active,
            "missing": missing,
            "circular_deps": len(self.circular_deps),
        }


def find_registry(name: str) -> Optional[Path]:
    """Find a registry by partial name match."""
    # Check root registries
    for reg in get_root_registries():
        if name.lower() in reg.name.lower():
            return reg

    # Check other known locations
    other_paths = [
        CONTROL_PLANE / "boot_os_registry.csv",
        CONTROL_PLANE / "init" / "init_registry.csv",
    ]

    for path in other_paths:
        if path.is_file() and name.lower() in path.name.lower():
            return path

    # Check modules
    modules_dir = CONTROL_PLANE / "modules"
    if modules_dir.is_dir():
        for reg in modules_dir.glob("**/registries/*.csv"):
            if name.lower() in reg.name.lower():
                return reg

    return None


# === Commands ===

def cmd_tree(registry_name: Optional[str] = None):
    """Show registry tree."""
    tree = RegistryTree()

    if registry_name:
        reg_path = find_registry(registry_name)
        if not reg_path:
            print(f"Registry not found: {registry_name}")
            return 1
        tree.load_from_single(reg_path)
    else:
        tree.load_from_roots(get_root_registries())

    print("\nRegistry Tree")
    print("=" * 60)
    tree.print_tree()

    stats = tree.stats()
    print()
    print("-" * 60)
    print(f"Registries: {stats['registries']}")
    print(f"Total items: {stats['total_items']}")
    print(f"  Selected: {stats['selected']}")
    print(f"  Active: {stats['active']}")
    print(f"  Missing: {stats['missing']}")

    if tree.circular_deps:
        print(f"\n⚠ Circular dependencies detected: {len(tree.circular_deps)}")
        for from_path, to_path in tree.circular_deps:
            print(f"  {from_path} → {to_path}")
        return 2

    return 0


def cmd_flatten():
    """List all items across all registries."""
    tree = RegistryTree()
    tree.load_from_roots(get_root_registries())

    items = tree.flatten()

    print("\nAll Items (Flattened)")
    print("=" * 60)

    current_reg = None
    for reg_path, item, item_id in sorted(items, key=lambda x: (x[0], x[2])):
        if reg_path != current_reg:
            print(f"\n[{reg_path}]")
            current_reg = reg_path

        name = item.get("name", "?")
        status = item.get("status", "?")
        print(f"  {item_id:15} {status:10} {name}")

    print(f"\nTotal: {len(items)} items across {len(tree.all_nodes)} registries")
    return 0


def cmd_check():
    """Check for circular dependencies."""
    tree = RegistryTree()
    tree.load_from_roots(get_root_registries())

    print("\nCircular Dependency Check")
    print("=" * 60)

    if tree.circular_deps:
        print(f"\n✗ Found {len(tree.circular_deps)} circular dependencies:\n")
        for from_path, to_path in tree.circular_deps:
            print(f"  {from_path}")
            print(f"    → {to_path}")
            print()
        return 2
    else:
        print("\n✓ No circular dependencies detected")
        stats = tree.stats()
        print(f"\nScanned: {stats['registries']} registries, {stats['total_items']} items")
        return 0


def cmd_export(output_path: Optional[str] = None):
    """Export full tree as JSON."""
    tree = RegistryTree()
    tree.load_from_roots(get_root_registries())

    def node_to_dict(node: RegistryNode) -> dict:
        return {
            "path": node.rel_path(),
            "item_count": len(node.items),
            "items": [
                {
                    "id": item.get(node.id_column, "?") if node.id_column else "?",
                    "name": item.get("name", "?"),
                    "status": item.get("status", "?"),
                }
                for item in node.items
            ],
            "children": [node_to_dict(child) for child in node.children],
        }

    export_data = {
        "roots": [node_to_dict(root) for root in tree.roots],
        "stats": tree.stats(),
        "circular_deps": tree.circular_deps,
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
        print(f"Exported to: {output_path}")
    else:
        print(json.dumps(export_data, indent=2))

    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python nested.py <command> [args]")
        print("\nCommands:")
        print("  tree [registry]    Show registry tree (all or from specific root)")
        print("  flatten            List all items across all registries")
        print("  check              Check for circular dependencies")
        print("  export [file]      Export tree as JSON")
        print("\nExamples:")
        print("  python nested.py tree")
        print("  python nested.py tree frameworks")
        print("  python nested.py flatten")
        print("  python nested.py check")
        print("  python nested.py export tree.json")
        return 1

    command = sys.argv[1].lower()

    if command == "tree":
        registry_name = sys.argv[2] if len(sys.argv) > 2 else None
        return cmd_tree(registry_name)

    elif command == "flatten":
        return cmd_flatten()

    elif command == "check":
        return cmd_check()

    elif command == "export":
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        return cmd_export(output_path)

    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
