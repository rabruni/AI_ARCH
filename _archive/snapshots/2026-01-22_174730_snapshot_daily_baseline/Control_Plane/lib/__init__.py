"""
Control Plane shared library.

Usage:
    from Control_Plane.lib import (
        REPO_ROOT, CONTROL_PLANE,
        read_registry, find_item, count_registry_stats,
        resolve_artifact_path,
        ResultReporter
    )
"""
from .paths import (
    get_repo_root,
    REPO_ROOT,
    CONTROL_PLANE,
    REGISTRIES_DIR,
    GENERATED_DIR,
    SCRIPTS_DIR,
)

from .registry import (
    find_all_registries,
    read_registry,
    write_registry,
    get_id_column,
    find_item,
    find_registry_by_name,
    count_registry_stats,
)

from .resolve import resolve_artifact_path

from .output import ResultReporter

__all__ = [
    # Paths
    "get_repo_root",
    "REPO_ROOT",
    "CONTROL_PLANE",
    "REGISTRIES_DIR",
    "GENERATED_DIR",
    "SCRIPTS_DIR",
    # Registry
    "find_all_registries",
    "read_registry",
    "write_registry",
    "get_id_column",
    "find_item",
    "find_registry_by_name",
    "count_registry_stats",
    # Resolve
    "resolve_artifact_path",
    # Output
    "ResultReporter",
]
