#!/usr/bin/env python3
"""
Path resolution utilities.
"""
from pathlib import Path
from .paths import REPO_ROOT, CONTROL_PLANE


def resolve_artifact_path(path_str: str) -> Path:
    """Resolve an artifact path to absolute path.

    Handles:
    - Leading slash (relative to repo root)
    - Control_Plane prefix
    - Other paths (relative to repo root)
    """
    if not path_str:
        return Path()

    # Remove leading slash for normalization
    if path_str.startswith("/"):
        path_str = path_str[1:]

    # All artifact paths are relative to repo root
    return REPO_ROOT / path_str
