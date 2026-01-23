"""Output Safety for Shaper v2.

Rules:
- Never overwrite existing files silently
- If target filename exists, append _1, _2, ... before extension
- Path resolution is a pure function (no filesystem mutations)
- Sequence increments are deterministic
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable


def resolve_output_path(
    base_path: Path,
    exists_check: Callable[[Path], bool] | None = None,
) -> Path:
    """Resolve output path, finding an available filename.

    This is a pure function - it does not modify the filesystem.
    Uses the provided exists_check function to test if paths exist.

    Default filenames:
    - Work item: WORK_ITEM.md
    - Spec: SPEC.md

    If file exists, increments: WORK_ITEM_1.md, WORK_ITEM_2.md, ...

    Args:
        base_path: The desired output path.
        exists_check: Function to check if a path exists.
                      Defaults to Path.exists().

    Returns:
        Available path (original or with suffix).
    """
    if exists_check is None:
        exists_check = lambda p: p.exists()

    if not exists_check(base_path):
        return base_path

    # File exists - find next available sequence
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not exists_check(candidate):
            return candidate
        counter += 1


def write_output(path: Path, content: str) -> Path:
    """Write content to file, never overwriting silently.

    If the target path exists, finds next available sequence number.

    Args:
        path: Desired output path.
        content: Content to write (UTF-8, LF assumed).

    Returns:
        Actual path written to.
    """
    target = resolve_output_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def get_default_filename(altitude: str) -> str:
    """Get default filename for altitude.

    Args:
        altitude: "L3" or "L4"

    Returns:
        Default filename (WORK_ITEM.md or SPEC.md)
    """
    if altitude == "L3":
        return "WORK_ITEM.md"
    elif altitude == "L4":
        return "SPEC.md"
    else:
        raise ValueError(f"Invalid altitude: {altitude}")
