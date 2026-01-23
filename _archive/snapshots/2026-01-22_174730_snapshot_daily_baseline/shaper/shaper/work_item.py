from __future__ import annotations

from typing import List

from .model import ShaperModel, META_FIELDS


def render_work_item(model: ShaperModel) -> str:
    lines: List[str] = ["---"]
    for key in META_FIELDS:
        lines.append(f"{key}: {model.meta.get(key, '')}")
    lines.append("---")
    lines.append("")
    lines.append("## Objective")
    lines.extend(_section_lines(model.objective))
    lines.append("")
    lines.append("## Scope: File Permissions")
    lines.extend(_section_lines(model.scope))
    lines.append("")
    lines.append("## Implementation Plan")
    lines.extend(_numbered_lines(model.plan))
    lines.append("")
    lines.append("## Acceptance Commands")
    lines.extend(_bullet_lines(model.acceptance))
    lines.append("")
    return "\n".join(lines)


def _section_lines(items: List[str]) -> List[str]:
    if not items:
        return []
    return [f"- {item}" for item in items]


def _numbered_lines(items: List[str]) -> List[str]:
    if not items:
        return []
    return [f"{idx + 1}. {item}" for idx, item in enumerate(items)]


def _bullet_lines(items: List[str]) -> List[str]:
    if not items:
        return []
    return [f"- {item}" for item in items]
