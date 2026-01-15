#!/usr/bin/env python3
"""
Generate MANIFEST.json - Checksums for Critical Files

Purpose: Create integrity manifest for validation layer.
Output: Control_Plane/MANIFEST.json

Usage:
    python Control_Plane/scripts/generate_manifest.py
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def get_repo_root() -> Path:
    """Find repository root (contains .git/)."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


REPO_ROOT = get_repo_root()


def sha256_file(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_critical_files() -> list[str]:
    """List of critical files to checksum (relative to repo root)."""
    return [
        # Constitution and core docs
        "SYSTEM_CONSTITUTION.md",
        "VERSION",

        # Control Plane core
        "Control_Plane/init/init.md",
        "Control_Plane/CLAUDE.md",
        "Control_Plane/control_plane/CONTROL_PLANE_CONTRACT.md",

        # Verb prompts
        "Control_Plane/control_plane/prompts/install.md",
        "Control_Plane/control_plane/prompts/update.md",
        "Control_Plane/control_plane/prompts/verify.md",
        "Control_Plane/control_plane/prompts/uninstall.md",

        # Scripts
        "Control_Plane/scripts/bootstrap.py",
        "Control_Plane/scripts/validate_registry.py",
        "Control_Plane/scripts/apply_selection.py",

        # Root registries
        "Control_Plane/registries/frameworks_registry.csv",
        "Control_Plane/registries/components_registry.csv",
        "Control_Plane/registries/prompts_registry.csv",
    ]


def generate_manifest() -> dict:
    """Generate manifest with checksums."""
    manifest = {
        "version": "1.0.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "generator": "Control_Plane/scripts/generate_manifest.py",
        "checksums": {},
        "missing": [],
    }

    for rel_path in get_critical_files():
        full_path = REPO_ROOT / rel_path
        if full_path.is_file():
            manifest["checksums"][rel_path] = {
                "sha256": sha256_file(full_path),
                "size": full_path.stat().st_size,
            }
        else:
            manifest["missing"].append(rel_path)

    # Add registry count
    registry_dir = REPO_ROOT / "Control_Plane" / "registries"
    if registry_dir.is_dir():
        csv_files = list(registry_dir.glob("*.csv"))
        manifest["registry_count"] = len(csv_files)

    return manifest


def main():
    print("Generating MANIFEST.json...")

    manifest = generate_manifest()

    # Write manifest
    manifest_path = REPO_ROOT / "Control_Plane" / "MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Report
    print(f"\nManifest generated: {manifest_path}")
    print(f"  - Files checksummed: {len(manifest['checksums'])}")
    print(f"  - Files missing: {len(manifest['missing'])}")

    if manifest["missing"]:
        print("\nMissing files:")
        for path in manifest["missing"]:
            print(f"  - {path}")

    return len(manifest["missing"]) == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
