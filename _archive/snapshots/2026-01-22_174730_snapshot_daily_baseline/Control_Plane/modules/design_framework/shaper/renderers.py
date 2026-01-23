"""Deterministic renderers for Shaper v2 artifacts.

Rendering rules:
- UTF-8 encoding
- LF line endings
- Single trailing newline
- Fixed section ordering
- Identical state produces byte-identical output
- No timestamps, UUIDs, randomness, or environment-dependent data
"""

from __future__ import annotations

from typing import List

from .models import ShaperModel, SpecModel, META_FIELDS


def render_work_item(model: ShaperModel) -> str:
    """Render a ShaperModel as WORK_ITEM.md content.

    Section order (fixed):
    1. YAML front matter
    2. ## Objective (bullet list)
    3. ## Scope: File Permissions (bullet list)
    4. ## Implementation Plan (numbered list)
    5. ## Acceptance Commands (bullet list)

    Args:
        model: The ShaperModel to render.

    Returns:
        Complete WORK_ITEM markdown content with single trailing newline.
    """
    lines: List[str] = []

    # YAML front matter
    lines.append("---")
    for key in META_FIELDS:
        lines.append(f"{key}: {model.meta.get(key, '')}")
    lines.append("---")
    lines.append("")

    # Objective section
    lines.append("## Objective")
    lines.extend(_bullet_lines(model.objective))
    lines.append("")

    # Scope section
    lines.append("## Scope: File Permissions")
    lines.extend(_bullet_lines(model.scope))
    lines.append("")

    # Implementation Plan section
    lines.append("## Implementation Plan")
    lines.extend(_numbered_lines(model.plan))
    lines.append("")

    # Acceptance Commands section
    lines.append("## Acceptance Commands")
    lines.extend(_bullet_lines(model.acceptance))
    lines.append("")

    return "\n".join(lines)


def render_spec(model: SpecModel) -> str:
    """Render a SpecModel as SPEC.md content.

    Section order (fixed):
    1. YAML front matter
    2. ## Overview (bullet list)
    3. ## Problem (bullet list)
    4. ## Non-Goals (bullet list)
    5. ## Phases (numbered list)
    6. ## Work Items (bullet list, only if non-empty)
    7. ## Success Criteria (bullet list)

    Args:
        model: The SpecModel to render.

    Returns:
        Complete SPEC markdown content with single trailing newline.
    """
    lines: List[str] = []

    # YAML front matter
    lines.append("---")
    for key in META_FIELDS:
        lines.append(f"{key}: {model.meta.get(key, '')}")
    lines.append("---")
    lines.append("")

    # Overview section
    lines.append("## Overview")
    lines.extend(_bullet_lines(model.overview))
    lines.append("")

    # Problem section
    lines.append("## Problem")
    lines.extend(_bullet_lines(model.problem))
    lines.append("")

    # Non-Goals section
    lines.append("## Non-Goals")
    lines.extend(_bullet_lines(model.non_goals))
    lines.append("")

    # Phases section
    lines.append("## Phases")
    lines.extend(_numbered_lines(model.phases))
    lines.append("")

    # Work Items section (optional - only include if non-empty)
    if model.work_items:
        lines.append("## Work Items")
        lines.extend(_bullet_lines(model.work_items))
        lines.append("")

    # Success Criteria section
    lines.append("## Success Criteria")
    lines.extend(_bullet_lines(model.success_criteria))
    lines.append("")

    return "\n".join(lines)


def _bullet_lines(items: List[str]) -> List[str]:
    """Convert items to bullet list lines."""
    if not items:
        return []
    return [f"- {item}" for item in items]


def _numbered_lines(items: List[str]) -> List[str]:
    """Convert items to numbered list lines (1., 2., ...)."""
    if not items:
        return []
    return [f"{idx + 1}. {item}" for idx, item in enumerate(items)]
