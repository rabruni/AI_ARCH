#!/usr/bin/env python3
"""
Prompt - Prompt Management CLI (BOOT-018)

Purpose: Manage prompts registry and execute verb prompts.

Usage:
    python prompt.py list                      # List all prompts
    python prompt.py show <prompt_id>          # Show prompt details and content
    python prompt.py execute <verb> <item_id>  # Execute verb prompt for item
    python prompt.py create <verb> <item_id>   # Create new verb prompt for item
    python prompt.py validate                  # Validate prompts registry

Exit codes:
    0 = Success
    1 = Prompt/item not found
    2 = Execution failed
    3 = Validation failed
"""

import csv
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
PROMPTS_REGISTRY = CONTROL_PLANE / "registries" / "prompts_registry.csv"
FRAMEWORKS_REGISTRY = CONTROL_PLANE / "registries" / "frameworks_registry.csv"

# Standard verb prompts
VERB_PROMPTS = {
    "install": CONTROL_PLANE / "control_plane" / "prompts" / "install.md",
    "update": CONTROL_PLANE / "control_plane" / "prompts" / "update.md",
    "verify": CONTROL_PLANE / "control_plane" / "prompts" / "verify.md",
    "uninstall": CONTROL_PLANE / "control_plane" / "prompts" / "uninstall.md",
}


def resolve_path(path_str: str) -> Path:
    """Resolve a path relative to repo root."""
    if not path_str:
        return Path()
    if path_str.startswith("/"):
        path_str = path_str[1:]
    return REPO_ROOT / path_str


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


def find_item_by_id(item_id: str) -> Optional[tuple[dict, Path, str]]:
    """Find an item by ID across registries. Returns (item, registry_path, id_column)."""
    registries = [
        PROMPTS_REGISTRY,
        FRAMEWORKS_REGISTRY,
        CONTROL_PLANE / "boot_os_registry.csv",
        CONTROL_PLANE / "registries" / "modules_registry.csv",
        CONTROL_PLANE / "registries" / "cloud_services_registry.csv",
        CONTROL_PLANE / "registries" / "components_registry.csv",
    ]

    for reg_path in registries:
        if not reg_path.is_file():
            continue
        headers, rows = read_registry(reg_path)
        id_col = get_id_column(headers)
        if not id_col:
            continue
        for row in rows:
            if row.get(id_col, "").upper() == item_id.upper():
                return row, reg_path, id_col
    return None


def find_prompt_by_id(prompt_id: str) -> Optional[dict]:
    """Find a prompt by ID."""
    _, rows = read_registry(PROMPTS_REGISTRY)
    for row in rows:
        if row.get("prompt_id", "").upper() == prompt_id.upper():
            return row
    return None


def get_verb_prompt_path(item: dict, verb: str) -> Optional[Path]:
    """Get the verb prompt path for an item."""
    # Check item-specific prompt path
    path_key = f"{verb}_prompt_path"
    if path_key in item and item[path_key]:
        resolved = resolve_path(item[path_key])
        if resolved.is_file():
            return resolved
        # Item path doesn't exist, fall through to standard

    # Fall back to standard verb prompt
    if verb in VERB_PROMPTS:
        return VERB_PROMPTS[verb]

    return None


# === Commands ===

def cmd_list():
    """List all prompts."""
    _, rows = read_registry(PROMPTS_REGISTRY)

    if not rows:
        print("\nNo prompts registry found.")
        print(f"Create: {PROMPTS_REGISTRY.relative_to(REPO_ROOT)}")
        return 0

    print("\nPrompts Registry")
    print("=" * 70)

    # Group by domain
    by_domain = {}
    for row in rows:
        domain = row.get("domain", "other")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(row)

    for domain, prompts in sorted(by_domain.items()):
        print(f"\n[{domain}]")
        for p in prompts:
            pid = p.get("prompt_id", "?")
            name = p.get("name", "?")
            status = p.get("status", "?")
            selected = "✓" if p.get("selected", "").lower() == "yes" else " "
            print(f"  [{selected}] {name:35} {status:10} ({pid})")

    print(f"\nTotal: {len(rows)} prompts")
    return 0


def cmd_show(prompt_id: str):
    """Show prompt details and content."""
    prompt = find_prompt_by_id(prompt_id)

    if not prompt:
        print(f"Prompt not found: {prompt_id}")
        return 1

    print(f"\nPrompt: {prompt.get('prompt_id', '?')}")
    print("=" * 70)
    print(f"Name:     {prompt.get('name', '?')}")
    print(f"Domain:   {prompt.get('domain', '?')}")
    print(f"Purpose:  {prompt.get('purpose', '?')}")
    print(f"Status:   {prompt.get('status', '?')}")
    print(f"Selected: {prompt.get('selected', 'no')}")

    artifact_path = prompt.get("artifact_path", "")
    if artifact_path:
        resolved = resolve_path(artifact_path)
        exists = "✓" if resolved.is_file() else "✗"
        print(f"Path:     {artifact_path} [{exists}]")

        if resolved.is_file():
            print("\n--- Content Preview ---")
            content = resolved.read_text()
            lines = content.split("\n")[:30]
            for line in lines:
                print(f"  {line[:80]}")
            if len(content.split("\n")) > 30:
                print("  ...")

    return 0


def cmd_execute(verb: str, item_id: str):
    """Execute a verb prompt for an item."""
    verb = verb.lower()

    if verb not in ["install", "update", "verify", "uninstall"]:
        print(f"Unknown verb: {verb}")
        print("Valid verbs: install, update, verify, uninstall")
        return 1

    result = find_item_by_id(item_id)
    if not result:
        print(f"Item not found: {item_id}")
        return 1

    item, registry_path, id_col = result

    prompt_path = get_verb_prompt_path(item, verb)
    if not prompt_path or not prompt_path.is_file():
        print(f"Prompt file not found for verb: {verb}")
        return 1

    print(f"\nExecuting {verb.upper()} for {item_id}")
    print("=" * 70)
    print(f"Item:     {item.get('name', '?')}")
    print(f"Registry: {registry_path.relative_to(REPO_ROOT)}")
    print(f"Prompt:   {prompt_path.relative_to(REPO_ROOT)}")
    print(f"Status:   {item.get('status', '?')}")

    # Show prompt content
    print("\n--- Prompt Instructions ---")
    print(prompt_path.read_text())

    print("\n--- Item Context ---")
    for key, value in item.items():
        if value:
            print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("Execute this prompt with the item context above.")
    print("After completion, update the registry status accordingly.")

    return 0


def cmd_create(verb: str, item_id: str):
    """Create a custom verb prompt for an item."""
    verb = verb.lower()

    if verb not in ["install", "update", "verify", "uninstall"]:
        print(f"Unknown verb: {verb}")
        return 1

    result = find_item_by_id(item_id)
    if not result:
        print(f"Item not found: {item_id}")
        return 1

    item, registry_path, id_col = result
    item_name = item.get("name", item_id).lower().replace(" ", "_")

    # Create prompt directory if needed
    prompt_dir = CONTROL_PLANE / "prompts" / "custom"
    prompt_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = prompt_dir / f"{verb}_{item_id.lower()}.md"

    if prompt_file.is_file():
        print(f"Prompt already exists: {prompt_file.relative_to(REPO_ROOT)}")
        return 0

    # Get template from standard verb prompt
    template_path = VERB_PROMPTS.get(verb)
    if template_path and template_path.is_file():
        template = template_path.read_text()
    else:
        template = f"# {verb.title()} Prompt for {item_id}\n\n## Purpose\n\n## Procedure\n\n## Success Criteria\n"

    # Customize template
    content = f"""# {verb.title()} Prompt for {item_id}

**Item:** {item.get('name', '?')}
**Purpose:** {item.get('purpose', '?')}
**Generated:** {datetime.now(timezone.utc).isoformat()}

---

{template}

---

## Item-Specific Context

```
{item_id}: {item.get('name', '?')}
artifact_path: {item.get('artifact_path', '?')}
dependencies: {item.get('dependencies', 'none')}
```
"""

    prompt_file.write_text(content)
    print(f"Created: {prompt_file.relative_to(REPO_ROOT)}")
    print(f"\nTo use this custom prompt, update the registry:")
    print(f"  {verb}_prompt_path = /Control_Plane/prompts/custom/{prompt_file.name}")

    return 0


def cmd_validate():
    """Validate prompts registry."""
    _, rows = read_registry(PROMPTS_REGISTRY)

    print("\nValidating Prompts Registry")
    print("=" * 70)

    errors = 0
    warnings = 0

    for row in rows:
        pid = row.get("prompt_id", "?")
        name = row.get("name", "?")
        status = row.get("status", "?")
        artifact_path = row.get("artifact_path", "")

        if not artifact_path:
            print(f"  [⚠] {pid}: No artifact path")
            warnings += 1
            continue

        resolved = resolve_path(artifact_path)

        if status == "active":
            if resolved.is_file():
                print(f"  [✓] {pid}: {name}")
            else:
                print(f"  [✗] {pid}: Artifact missing: {artifact_path}")
                errors += 1
        elif status == "missing":
            if resolved.is_file():
                print(f"  [⚠] {pid}: File exists but status=missing")
                warnings += 1
            else:
                print(f"  [·] {pid}: {name} (not installed)")
        else:
            print(f"  [?] {pid}: Unknown status '{status}'")
            warnings += 1

    # Validate verb prompts
    print("\n--- Verb Prompts ---")
    for verb, path in VERB_PROMPTS.items():
        if path.is_file():
            print(f"  [✓] {verb}: {path.relative_to(REPO_ROOT)}")
        else:
            print(f"  [✗] {verb}: Missing")
            errors += 1

    print()
    print("-" * 70)
    if errors == 0:
        print(f"✓ Validation passed ({warnings} warnings)")
        return 0
    else:
        print(f"✗ Validation failed: {errors} errors, {warnings} warnings")
        return 3


def cmd_verbs():
    """List available verb prompts."""
    print("\nVerb Prompts")
    print("=" * 70)

    for verb, path in VERB_PROMPTS.items():
        exists = "✓" if path.is_file() else "✗"
        print(f"  [{exists}] {verb:12} {path.relative_to(REPO_ROOT)}")

    print("\nUsage: python prompt.py execute <verb> <item_id>")
    print("Example: python prompt.py execute install FMWK-001")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python prompt.py <command> [args]")
        print("\nCommands:")
        print("  list                      List all prompts")
        print("  show <prompt_id>          Show prompt details and content")
        print("  execute <verb> <item_id>  Execute verb prompt for item")
        print("  create <verb> <item_id>   Create custom verb prompt")
        print("  validate                  Validate prompts registry")
        print("  verbs                     List available verb prompts")
        print("\nVerbs: install, update, verify, uninstall")
        print("\nExamples:")
        print("  python prompt.py list")
        print("  python prompt.py show PRMPT-001")
        print("  python prompt.py execute install FMWK-001")
        print("  python prompt.py verbs")
        return 1

    command = sys.argv[1].lower()

    if command == "list":
        return cmd_list()
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: prompt.py show <prompt_id>")
            return 1
        return cmd_show(sys.argv[2])
    elif command == "execute":
        if len(sys.argv) < 4:
            print("Usage: prompt.py execute <verb> <item_id>")
            return 1
        return cmd_execute(sys.argv[2], sys.argv[3])
    elif command == "create":
        if len(sys.argv) < 4:
            print("Usage: prompt.py create <verb> <item_id>")
            return 1
        return cmd_create(sys.argv[2], sys.argv[3])
    elif command == "validate":
        return cmd_validate()
    elif command == "verbs":
        return cmd_verbs()
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
