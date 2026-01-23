from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


META_FIELDS = ["ID", "Title", "Status", "ALTITUDE"]


@dataclass
class ShaperModel:
    objective: List[str] = field(default_factory=list)
    scope: List[str] = field(default_factory=list)
    plan: List[str] = field(default_factory=list)
    acceptance: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)
    revealed_once: bool = False

    def reset(self) -> None:
        self.objective.clear()
        self.scope.clear()
        self.plan.clear()
        self.acceptance.clear()
        self.meta.clear()
        self.revealed_once = False

    def ingest(self, text: str) -> None:
        line = text.strip()
        if not line:
            return
        lowered = line.lower()

        for key in META_FIELDS:
            prefix = f"{key.lower()}:"
            if lowered.startswith(prefix):
                value = line.split(":", 1)[1].strip()
                if value:
                    self.meta[key] = value
                return

        if lowered.startswith("objective:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.objective.append(value)
            return

        if lowered.startswith("scope:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.scope.append(value)
            return

        if lowered.startswith("plan:") or lowered.startswith("step:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.plan.append(value)
            return

        if lowered.startswith("acceptance:") or lowered.startswith("command:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.acceptance.append(value)
            return

        self.objective.append(line)

    def missing_sections(self) -> List[str]:
        missing = []
        for key in META_FIELDS:
            if not self.meta.get(key):
                missing.append(key)
        if not self.objective:
            missing.append("Objective")
        if not self.scope:
            missing.append("Scope")
        if not self.plan:
            missing.append("Implementation Plan")
        if not self.acceptance:
            missing.append("Acceptance Commands")
        return missing
