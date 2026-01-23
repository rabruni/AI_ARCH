"""Spec pack IO utilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


PHASE_DIRS = ["phase0A", "phase1", "phase2", "phase3", "phase4"]
SPEC_FILES = [
    "00_overview.md",
    "01_scope.md",
    "02_assumptions.md",
    "03_constraints.md",
    "04_interface.md",
    "05_architecture.md",
    "06_validation.md",
    "07_registry.md",
]


@dataclass
class SpecPackIO:
    spec_root: Path

    @classmethod
    def for_spec(cls, spec_id: str) -> "SpecPackIO":
        return cls(Path("Control_Plane") / "docs" / "specs" / spec_id)

    def create(self) -> None:
        self.spec_root.mkdir(parents=True, exist_ok=True)
        for filename in SPEC_FILES:
            path = self.spec_root / filename
            if not path.exists():
                title = filename.split("_", 1)[1].rsplit(".", 1)[0].replace("_", " ")
                path.write_text(f"# {title.title()}\n", encoding="utf-8")

        artifacts_dir = self.spec_root / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        for phase in PHASE_DIRS:
            (artifacts_dir / phase).mkdir(exist_ok=True)

        session_path = artifacts_dir / "session.json"
        if not session_path.exists():
            session_path.write_text("{}\n", encoding="utf-8")
        history_path = artifacts_dir / "session_history.jsonl"
        if not history_path.exists():
            history_path.write_text("", encoding="utf-8")

    def synthesize_spec_md(self) -> Path:
        output = self.spec_root / "SPEC.md"
        toc_lines = ["# SPEC", "", "## Table of Contents"]
        body_lines: List[str] = []
        for filename in SPEC_FILES:
            section_title = filename.split("_", 1)[1].rsplit(".", 1)[0].replace("_", " ")
            anchor = section_title.lower().replace(" ", "-")
            toc_lines.append(f"- [{section_title.title()}](#{anchor})")
            content = (self.spec_root / filename).read_text(encoding="utf-8")
            body_lines.append(content.rstrip())
        output.write_text("\n".join(toc_lines + [""] + body_lines) + "\n", encoding="utf-8")
        return output
