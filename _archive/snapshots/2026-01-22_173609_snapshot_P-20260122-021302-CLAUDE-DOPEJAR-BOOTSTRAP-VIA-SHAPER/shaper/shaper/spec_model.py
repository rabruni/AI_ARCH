from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


SPEC_META_FIELDS = ["ID", "Title", "Status", "ALTITUDE"]


@dataclass
class SpecModel:
    overview: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    design: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)

    def missing_sections(self) -> List[str]:
        missing = []
        for key in SPEC_META_FIELDS:
            if not self.meta.get(key):
                missing.append(key)
        if not self.overview:
            missing.append("Overview")
        if not self.requirements:
            missing.append("Requirements")
        if not self.design:
            missing.append("Design")
        if not self.tests:
            missing.append("Tests")
        return missing


def render_spec(model: SpecModel) -> str:
    lines: List[str] = ["---"]
    for key in SPEC_META_FIELDS:
        lines.append(f"{key}: {model.meta.get(key, '')}")
    lines.append("---")
    lines.append("")
    lines.append("## Overview")
    lines.extend(_bullet_lines(model.overview))
    lines.append("")
    lines.append("## Requirements")
    lines.extend(_numbered_lines(model.requirements))
    lines.append("")
    lines.append("## Design")
    lines.extend(_bullet_lines(model.design))
    lines.append("")
    lines.append("## Tests")
    lines.extend(_bullet_lines(model.tests))
    lines.append("")
    return "\n".join(lines)


def _bullet_lines(items: List[str]) -> List[str]:
    if not items:
        return []
    return [f"- {item}" for item in items]


def _numbered_lines(items: List[str]) -> List[str]:
    if not items:
        return []
    return [f"{idx + 1}. {item}" for idx, item in enumerate(items)]
