from __future__ import annotations

from pathlib import Path


def write_output(path: Path, content: str) -> Path:
    target = Path(path)
    if target.exists():
        target = _next_available_path(target)
    target.write_text(content, encoding="utf-8")
    return target


def _next_available_path(path: Path) -> Path:
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
