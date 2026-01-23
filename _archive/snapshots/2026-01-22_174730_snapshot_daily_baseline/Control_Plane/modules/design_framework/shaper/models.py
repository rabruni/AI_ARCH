"""Models for Shaper v2: ShaperModel (L3) and SpecModel (L4).

ShaperModel handles L3 WORK_ITEM artifacts.
SpecModel handles L4 SPEC artifacts with phase confirmation enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


# YAML front matter keys in required order
META_FIELDS = ["ID", "Title", "Status", "ALTITUDE"]


@dataclass
class ShaperModel:
    """L3 Work Item Model.

    Sections (fixed order):
    1. Objective (bullet list)
    2. Scope: File Permissions (bullet list)
    3. Implementation Plan (numbered list)
    4. Acceptance Commands (bullet list)

    No-inference rule: plan steps only added when explicitly provided.
    """

    objective: List[str] = field(default_factory=list)
    scope: List[str] = field(default_factory=list)
    plan: List[str] = field(default_factory=list)
    acceptance: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)
    revealed_once: bool = False

    def reset(self) -> None:
        """Clear all state for new session."""
        self.objective.clear()
        self.scope.clear()
        self.plan.clear()
        self.acceptance.clear()
        self.meta.clear()
        self.revealed_once = False

    def ingest(self, text: str) -> None:
        """Ingest a line of input into the model.

        Lines are parsed by prefix. Generic lines go to objective.
        Plan steps are ONLY added via explicit 'plan:' or 'step:' prefix.
        """
        line = text.strip()
        if not line:
            return
        lowered = line.lower()

        # Check meta field prefixes first
        for key in META_FIELDS:
            prefix = f"{key.lower()}:"
            if lowered.startswith(prefix):
                value = line.split(":", 1)[1].strip()
                if value:
                    self.meta[key] = value
                return

        # Check section prefixes
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

        # No-inference: plan steps only via explicit prefix
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

        # Generic lines go to objective (no inference to plan)
        self.objective.append(line)

    def missing_sections(self) -> List[str]:
        """Return list of missing required sections."""
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


@dataclass
class SpecModel:
    """L4 Spec Model.

    Sections (fixed order):
    1. Overview (bullet list)
    2. Problem (bullet list)
    3. Non-Goals (bullet list)
    4. Phases (numbered list) - requires confirmation
    5. Work Items (bullet list) - optional, excluded from completeness
    6. Success Criteria (bullet list)

    Phase confirmation: phases can be suggested but cannot be frozen
    until phases_confirmed is True.
    """

    overview: List[str] = field(default_factory=list)
    problem: List[str] = field(default_factory=list)
    non_goals: List[str] = field(default_factory=list)
    phases: List[str] = field(default_factory=list)
    work_items: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)
    revealed_once: bool = False
    phases_confirmed: bool = False
    _suggested_phases: List[str] = field(default_factory=list)

    def reset(self) -> None:
        """Clear all state for new session."""
        self.overview.clear()
        self.problem.clear()
        self.non_goals.clear()
        self.phases.clear()
        self.work_items.clear()
        self.success_criteria.clear()
        self.meta.clear()
        self.revealed_once = False
        self.phases_confirmed = False
        self._suggested_phases.clear()

    def suggest_phase(self, phase: str) -> None:
        """Suggest a phase without confirming it.

        Suggested phases are not ingested until user confirms.
        """
        if phase and phase not in self._suggested_phases:
            self._suggested_phases.append(phase)

    def confirm_phases(self) -> None:
        """Confirm suggested phases, allowing them to be ingested."""
        self.phases_confirmed = True
        for phase in self._suggested_phases:
            if phase not in self.phases:
                self.phases.append(phase)
        self._suggested_phases.clear()

    def ingest(self, text: str) -> None:
        """Ingest a line of input into the model.

        Phases are suggested, not directly ingested, until confirmed.
        """
        line = text.strip()
        if not line:
            return
        lowered = line.lower()

        # Check meta field prefixes first
        for key in META_FIELDS:
            prefix = f"{key.lower()}:"
            if lowered.startswith(prefix):
                value = line.split(":", 1)[1].strip()
                if value:
                    self.meta[key] = value
                return

        # Check section prefixes
        if lowered.startswith("overview:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.overview.append(value)
            return

        if lowered.startswith("problem:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.problem.append(value)
            return

        if lowered.startswith("non-goal:") or lowered.startswith("non-goals:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.non_goals.append(value)
            return

        # Phases are suggested, not directly ingested
        if lowered.startswith("phase:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.suggest_phase(value)
            return

        if lowered.startswith("work-item:") or lowered.startswith("work item:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.work_items.append(value)
            return

        if lowered.startswith("success:") or lowered.startswith("criteria:"):
            value = line.split(":", 1)[1].strip()
            if value:
                self.success_criteria.append(value)
            return

        # Generic lines go to overview
        self.overview.append(line)

    def missing_sections(self) -> List[str]:
        """Return list of missing required sections.

        work_items is optional and excluded from completeness checks.
        """
        missing = []
        for key in META_FIELDS:
            if not self.meta.get(key):
                missing.append(key)
        if not self.overview:
            missing.append("Overview")
        if not self.problem:
            missing.append("Problem")
        if not self.non_goals:
            missing.append("Non-Goals")
        if not self.phases:
            missing.append("Phases")
        # work_items is optional - not included in missing
        if not self.success_criteria:
            missing.append("Success Criteria")
        return missing

    def can_freeze(self) -> bool:
        """Check if model can be frozen.

        Requires phases_confirmed=True and no missing sections.
        """
        if not self.phases_confirmed:
            return False
        return len(self.missing_sections()) == 0
