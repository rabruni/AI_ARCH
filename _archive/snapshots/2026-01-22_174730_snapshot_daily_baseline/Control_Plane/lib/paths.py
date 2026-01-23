#!/usr/bin/env python3
"""
Shared path utilities for Control Plane scripts.
"""
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def get_repo_root() -> Path:
    """Find repository root (contains .git/).

    Cached to avoid repeated filesystem lookups.
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
        # Fallback: look for SYSTEM_CONSTITUTION.md
        if (parent / "SYSTEM_CONSTITUTION.md").is_file():
            return parent
    return Path.cwd()


REPO_ROOT = get_repo_root()
CONTROL_PLANE = REPO_ROOT / "Control_Plane"
REGISTRIES_DIR = CONTROL_PLANE / "registries"
GENERATED_DIR = CONTROL_PLANE / "generated"
SCRIPTS_DIR = CONTROL_PLANE / "scripts"
