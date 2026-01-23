"""Phase identifier helpers."""
from __future__ import annotations


def phase_dir_name(phase_id: str) -> str:
    if not phase_id:
        return ""
    if phase_id.lower().startswith("phase"):
        suffix = phase_id[5:]
        return f"phase{suffix}"
    return phase_id
