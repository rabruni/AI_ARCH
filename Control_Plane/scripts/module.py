#!/usr/bin/env python3
"""
Module - Module Swapping (BOOT-016)

Purpose: Hot-swap modules like memory bus, reasoning engine, etc.

Usage:
    python module.py list                     # List all swappable modules
    python module.py status                   # Show current module configuration
    python module.py swap <slot> <module_id>  # Swap module in slot
    python module.py reset <slot>             # Reset slot to default
    python module.py validate                 # Validate current configuration

Exit codes:
    0 = Success
    1 = Module/slot not found
    2 = Swap failed
    3 = Validation failed
"""

import csv
import json
import sys
from datetime import datetime, timezone
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
MODULES_REGISTRY = CONTROL_PLANE / "registries" / "modules_registry.csv"
MODULE_CONFIG = CONTROL_PLANE / "generated" / "module_config.json"

# Predefined slots that can have swappable modules
SLOTS = {
    "memory_bus": {
        "name": "Memory Bus",
        "description": "Handles memory storage and retrieval",
        "interface": "MemoryBusInterface",
        "default": None,
    },
    "reasoning_engine": {
        "name": "Reasoning Engine",
        "description": "Core reasoning and decision making",
        "interface": "ReasoningInterface",
        "default": None,
    },
    "llm_provider": {
        "name": "LLM Provider",
        "description": "Language model API provider",
        "interface": "LLMProviderInterface",
        "default": None,
    },
    "vector_store": {
        "name": "Vector Store",
        "description": "Vector embeddings storage",
        "interface": "VectorStoreInterface",
        "default": None,
    },
    "cache": {
        "name": "Cache",
        "description": "Caching layer",
        "interface": "CacheInterface",
        "default": None,
    },
}


def load_module_config() -> dict:
    """Load current module configuration."""
    if MODULE_CONFIG.is_file():
        try:
            with open(MODULE_CONFIG) as f:
                return json.load(f)
        except Exception:
            pass

    # Default config
    return {
        "slots": {slot: None for slot in SLOTS},
        "last_updated": None,
        "history": [],
    }


def save_module_config(config: dict):
    """Save module configuration."""
    MODULE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    config["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(MODULE_CONFIG, "w") as f:
        json.dump(config, f, indent=2)


def read_modules_registry() -> tuple[list[str], list[dict]]:
    """Read modules registry."""
    if not MODULES_REGISTRY.is_file():
        return [], []

    with open(MODULES_REGISTRY, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def find_module_by_id(module_id: str) -> Optional[dict]:
    """Find a module by ID."""
    _, rows = read_modules_registry()
    for row in rows:
        if row.get("module_id", "").upper() == module_id.upper():
            return row
    return None


def get_modules_for_slot(slot: str) -> list[dict]:
    """Get all modules compatible with a slot."""
    _, rows = read_modules_registry()
    return [r for r in rows if r.get("slot", "").lower() == slot.lower()]


def resolve_path(path_str: str) -> Path:
    """Resolve a module path."""
    if not path_str:
        return Path()
    if path_str.startswith("/"):
        path_str = path_str[1:]
    if path_str.startswith("Control_Plane"):
        return REPO_ROOT / path_str
    return CONTROL_PLANE / path_str


# === Commands ===

def cmd_list():
    """List all swappable modules."""
    _, rows = read_modules_registry()

    if not rows:
        print("\nNo modules registry found.")
        print(f"Create: {MODULES_REGISTRY.relative_to(REPO_ROOT)}")
        print("\nOr run: python module.py init")
        return 0

    print("\nAvailable Modules")
    print("=" * 70)

    # Group by slot
    by_slot = {}
    for row in rows:
        slot = row.get("slot", "other")
        if slot not in by_slot:
            by_slot[slot] = []
        by_slot[slot].append(row)

    for slot, modules in sorted(by_slot.items()):
        slot_info = SLOTS.get(slot, {"name": slot.title()})
        print(f"\n[{slot_info['name']}]")

        for mod in modules:
            mod_id = mod.get("module_id", "?")
            name = mod.get("name", "?")
            status = mod.get("status", "?")
            print(f"  {name:30} {status:10} ({mod_id})")

    print(f"\nTotal: {len(rows)} modules")
    return 0


def cmd_status():
    """Show current module configuration."""
    config = load_module_config()

    print("\nModule Configuration")
    print("=" * 70)

    for slot_id, slot_info in SLOTS.items():
        current = config["slots"].get(slot_id)
        slot_name = slot_info["name"]

        if current:
            mod = find_module_by_id(current)
            mod_name = mod.get("name", "?") if mod else "Unknown"
            print(f"  {slot_name:20} → {current} ({mod_name})")
        else:
            print(f"  {slot_name:20} → (not configured)")

    if config.get("last_updated"):
        print(f"\nLast updated: {config['last_updated']}")

    return 0


def cmd_swap(slot: str, module_id: str):
    """Swap a module in a slot."""
    slot = slot.lower()

    if slot not in SLOTS:
        print(f"Unknown slot: {slot}")
        print(f"Available slots: {', '.join(SLOTS.keys())}")
        return 1

    module = find_module_by_id(module_id)
    if not module:
        print(f"Module not found: {module_id}")
        return 1

    module_slot = module.get("slot", "").lower()
    if module_slot != slot:
        print(f"Module {module_id} is for slot '{module_slot}', not '{slot}'")
        return 2

    # Check module status
    status = module.get("status", "").lower()
    if status != "active":
        print(f"Warning: Module status is '{status}', not 'active'")

    # Check artifact exists
    artifact_path = module.get("artifact_path", "")
    if artifact_path:
        resolved = resolve_path(artifact_path)
        if not resolved.exists():
            print(f"Warning: Artifact not found: {artifact_path}")

    # Perform swap
    config = load_module_config()
    old_module = config["slots"].get(slot)

    config["slots"][slot] = module_id.upper()
    config["history"].append({
        "action": "swap",
        "slot": slot,
        "from": old_module,
        "to": module_id.upper(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Keep history manageable
    if len(config["history"]) > 100:
        config["history"] = config["history"][-50:]

    save_module_config(config)

    print(f"\nSwapped {SLOTS[slot]['name']}")
    if old_module:
        print(f"  From: {old_module}")
    print(f"  To:   {module_id.upper()}")
    print(f"\nModule: {module.get('name', '?')}")

    return 0


def cmd_reset(slot: str):
    """Reset a slot to unconfigured."""
    slot = slot.lower()

    if slot not in SLOTS:
        print(f"Unknown slot: {slot}")
        return 1

    config = load_module_config()
    old_module = config["slots"].get(slot)

    if not old_module:
        print(f"Slot '{slot}' is already unconfigured")
        return 0

    config["slots"][slot] = None
    config["history"].append({
        "action": "reset",
        "slot": slot,
        "from": old_module,
        "to": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    save_module_config(config)

    print(f"\nReset {SLOTS[slot]['name']}")
    print(f"  Removed: {old_module}")

    return 0


def cmd_validate():
    """Validate current module configuration."""
    config = load_module_config()

    print("\nValidating Module Configuration")
    print("=" * 70)

    errors = 0
    warnings = 0

    for slot_id, module_id in config["slots"].items():
        slot_info = SLOTS.get(slot_id, {"name": slot_id})
        slot_name = slot_info["name"]

        if not module_id:
            print(f"  [⚠] {slot_name}: Not configured")
            warnings += 1
            continue

        module = find_module_by_id(module_id)
        if not module:
            print(f"  [✗] {slot_name}: Module {module_id} not found in registry")
            errors += 1
            continue

        # Check artifact
        artifact_path = module.get("artifact_path", "")
        if artifact_path:
            resolved = resolve_path(artifact_path)
            if resolved.exists():
                print(f"  [✓] {slot_name}: {module_id} ({module.get('name', '?')})")
            else:
                print(f"  [✗] {slot_name}: Artifact missing: {artifact_path}")
                errors += 1
        else:
            print(f"  [⚠] {slot_name}: {module_id} (no artifact path)")
            warnings += 1

    print()
    print("-" * 70)
    if errors == 0:
        print(f"✓ Configuration valid ({warnings} warnings)")
        return 0
    else:
        print(f"✗ Configuration invalid: {errors} errors, {warnings} warnings")
        return 3


def cmd_init_registry():
    """Create initial modules registry."""
    if MODULES_REGISTRY.is_file():
        print(f"Registry already exists: {MODULES_REGISTRY.relative_to(REPO_ROOT)}")
        return 0

    MODULES_REGISTRY.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "module_id",
        "name",
        "slot",
        "selected",
        "status",
        "artifact_path",
        "interface",
        "version",
        "description",
    ]

    # Example modules
    examples = [
        {
            "module_id": "MOD-MEM-001",
            "name": "File Memory Bus",
            "slot": "memory_bus",
            "selected": "no",
            "status": "draft",
            "artifact_path": "",
            "interface": "MemoryBusInterface",
            "version": "0.1.0",
            "description": "Simple file-based memory storage",
        },
        {
            "module_id": "MOD-MEM-002",
            "name": "Redis Memory Bus",
            "slot": "memory_bus",
            "selected": "no",
            "status": "missing",
            "artifact_path": "",
            "interface": "MemoryBusInterface",
            "version": "0.1.0",
            "description": "Redis-backed memory storage",
        },
        {
            "module_id": "MOD-LLM-001",
            "name": "Anthropic Provider",
            "slot": "llm_provider",
            "selected": "no",
            "status": "draft",
            "artifact_path": "",
            "interface": "LLMProviderInterface",
            "version": "0.1.0",
            "description": "Claude API provider",
        },
        {
            "module_id": "MOD-LLM-002",
            "name": "OpenAI Provider",
            "slot": "llm_provider",
            "selected": "no",
            "status": "missing",
            "artifact_path": "",
            "interface": "LLMProviderInterface",
            "version": "0.1.0",
            "description": "GPT API provider",
        },
    ]

    with open(MODULES_REGISTRY, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for ex in examples:
            row = {h: ex.get(h, "") for h in headers}
            writer.writerow(row)

    print(f"Created: {MODULES_REGISTRY.relative_to(REPO_ROOT)}")
    print(f"Added {len(examples)} example modules")
    print("\nSlots available:")
    for slot_id, slot_info in SLOTS.items():
        print(f"  {slot_id}: {slot_info['description']}")

    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python module.py <command> [args]")
        print("\nCommands:")
        print("  list                     List all swappable modules")
        print("  status                   Show current module configuration")
        print("  swap <slot> <module_id>  Swap module in slot")
        print("  reset <slot>             Reset slot to unconfigured")
        print("  validate                 Validate current configuration")
        print("  init                     Create initial modules_registry.csv")
        print("\nSlots:")
        for slot_id, slot_info in SLOTS.items():
            print(f"  {slot_id:20} {slot_info['description']}")
        return 1

    command = sys.argv[1].lower()

    if command == "list":
        return cmd_list()
    elif command == "status":
        return cmd_status()
    elif command == "swap":
        if len(sys.argv) < 4:
            print("Usage: module.py swap <slot> <module_id>")
            return 1
        return cmd_swap(sys.argv[2], sys.argv[3])
    elif command == "reset":
        if len(sys.argv) < 3:
            print("Usage: module.py reset <slot>")
            return 1
        return cmd_reset(sys.argv[2])
    elif command == "validate":
        return cmd_validate()
    elif command == "init":
        return cmd_init_registry()
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
