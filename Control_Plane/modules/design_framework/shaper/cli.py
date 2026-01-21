"""CLI Interface for Shaper v2.

Provides interactive shaping session management.
Does NOT modify Control_Plane/cp.py - integration is manual.

Triggers (case-insensitive, exact match):
- "show me what you have" → reveal
- "turn this into a work item" → converge to L3
- "turn this into a spec" → converge to L4
- "freeze it" → freeze
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Union

from .models import ShaperModel, SpecModel, META_FIELDS
from .router import AltitudeRouter, detect_altitude, CLARIFICATION_PROMPT
from .state_machine import ShaperStateMachine
from .renderers import render_work_item, render_spec
from .context_builder import ConversationBuffer
from .output_safety import write_output, get_default_filename


# Trigger phrases (case-insensitive)
TRIGGER_REVEAL = "show me what you have"
TRIGGER_CONVERGE_L3 = "turn this into a work item"
TRIGGER_CONVERGE_L4 = "turn this into a spec"
TRIGGER_FREEZE = "freeze it"

# Disallowed keywords
DISALLOWED_PATTERNS = [
    ("mode=commit", "MODE=COMMIT is not allowed."),
    ("mode: commit", "MODE=COMMIT is not allowed."),
    ("execute", "execution is not allowed."),
    ("run code", "execution is not allowed."),
    ("modify control plane", "Control Plane modification is not allowed."),
    ("edit control_plane", "Control Plane modification is not allowed."),
    ("bypass", "bypassing gates is not allowed."),
    ("skip gate", "bypassing gates is not allowed."),
    ("infer plan", "cannot invent or infer plan steps."),
    ("add plan steps", "cannot invent or infer plan steps."),
]


def is_trigger(text: str, trigger: str) -> bool:
    """Check if text matches a trigger phrase (case-insensitive, exact)."""
    return text.strip().lower() == trigger


def check_disallowed(text: str) -> str | None:
    """Check if text contains disallowed patterns.

    Returns:
        Refusal message if disallowed, None otherwise.
    """
    lowered = text.lower()
    for pattern, message in DISALLOWED_PATTERNS:
        if pattern in lowered:
            return f"Refuse: {message}"
    return None


class ShaperCli:
    """Interactive Shaper CLI session."""

    def __init__(
        self,
        output_dir: Path | None = None,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ) -> None:
        self.router = AltitudeRouter()
        self.machine = ShaperStateMachine()
        self.model: Union[ShaperModel, SpecModel, None] = None
        self.buffer = ConversationBuffer()
        self.output_dir = output_dir or Path(".")
        self.input_func = input_func
        self.output_func = output_func

    def _output(self, message: str) -> None:
        """Output a message."""
        self.output_func(message)

    def _input(self, prompt: str) -> str:
        """Get input from user."""
        return self.input_func(prompt)

    def _reveal(self) -> str:
        """Generate reveal output."""
        if self.model is None:
            return "No active session."

        self.model.revealed_once = True
        self.machine.reveal()

        altitude = self.router.altitude or "UNDETERMINED"
        lines = [
            f"Altitude: {altitude}",
            f"Mode: {self.machine.mode}",
            "",
        ]

        if isinstance(self.model, ShaperModel):
            lines.extend([
                "Objective:",
                *(self.model.objective or ["(none)"]),
                "",
                "Scope:",
                *(self.model.scope or ["(none)"]),
                "",
                "Plan:",
                *(self.model.plan or ["(none)"]),
                "",
                "Acceptance:",
                *(self.model.acceptance or ["(none)"]),
            ])
        else:  # SpecModel
            lines.extend([
                "Overview:",
                *(self.model.overview or ["(none)"]),
                "",
                "Problem:",
                *(self.model.problem or ["(none)"]),
                "",
                "Non-Goals:",
                *(self.model.non_goals or ["(none)"]),
                "",
                "Phases:",
                *(self.model.phases or ["(none)"]),
                f"(Confirmed: {self.model.phases_confirmed})",
                "",
                "Work Items:",
                *(self.model.work_items or ["(none)"]),
                "",
                "Success Criteria:",
                *(self.model.success_criteria or ["(none)"]),
            ])

        lines.extend([
            "",
            "Metadata:",
        ])
        for key in META_FIELDS:
            value = self.model.meta.get(key, "")
            lines.append(f"- {key}: {value}")

        missing = self.model.missing_sections()
        if missing:
            lines.extend([
                "",
                "Missing:",
                *[f"- {item}" for item in missing],
            ])

        return "\n".join(lines)

    def _converge(self, altitude: str) -> None:
        """Run convergence loop to fill missing sections."""
        if not self.model.revealed_once:
            self._output("Refuse: reveal required before converge.")
            return

        if altitude == "L3":
            questions = {
                "ID": "ID is missing. Provide ID:",
                "Title": "Title is missing. Provide Title:",
                "Status": "Status is missing. Provide Status:",
                "ALTITUDE": "ALTITUDE is missing. Provide ALTITUDE:",
                "Objective": "Objective is missing. State it in one sentence.",
                "Scope": "Scope is missing. List files or directories.",
                "Implementation Plan": "Plan is missing. State the steps you intend to take.",
                "Acceptance Commands": "Acceptance is missing. Provide acceptance commands.",
            }
        else:  # L4
            questions = {
                "ID": "ID is missing. Provide ID:",
                "Title": "Title is missing. Provide Title:",
                "Status": "Status is missing. Provide Status:",
                "ALTITUDE": "ALTITUDE is missing. Provide ALTITUDE:",
                "Overview": "Overview is missing. Describe the overview.",
                "Problem": "Problem is missing. Describe the problem.",
                "Non-Goals": "Non-Goals is missing. List what is out of scope.",
                "Phases": "Phases is missing. List the phases.",
                "Success Criteria": "Success Criteria is missing. Define success.",
            }

        while True:
            missing = self.model.missing_sections()
            if not missing:
                return
            next_item = missing[0]
            self._output(questions.get(next_item, f"{next_item} is missing:"))
            response = self._input("> ").strip()
            if not response:
                continue

            if next_item in META_FIELDS:
                self.model.meta[next_item] = response
            elif isinstance(self.model, ShaperModel):
                if next_item == "Objective":
                    self.model.objective.append(response)
                elif next_item == "Scope":
                    self.model.scope.append(response)
                elif next_item == "Implementation Plan":
                    self.model.plan.append(response)
                elif next_item == "Acceptance Commands":
                    self.model.acceptance.append(response)
            else:  # SpecModel
                if next_item == "Overview":
                    self.model.overview.append(response)
                elif next_item == "Problem":
                    self.model.problem.append(response)
                elif next_item == "Non-Goals":
                    self.model.non_goals.append(response)
                elif next_item == "Phases":
                    self.model.suggest_phase(response)
                    self._output("Phase suggested. Confirm phases? (yes/no)")
                    confirm = self._input("> ").strip().lower()
                    if confirm in ("yes", "y"):
                        self.model.confirm_phases()
                        self._output("Phases confirmed.")
                elif next_item == "Success Criteria":
                    self.model.success_criteria.append(response)

    def _freeze(self) -> str | None:
        """Freeze the current model and render output.

        Returns:
            Rendered artifact content, or None if freeze failed.
        """
        if self.model is None:
            return None

        if not self.model.revealed_once:
            self._output("Refuse: reveal required before freeze.")
            return None

        missing = self.model.missing_sections()
        if missing:
            self._output(f"Cannot freeze. Missing: {', '.join(missing)}")
            return None

        if isinstance(self.model, SpecModel) and not self.model.phases_confirmed:
            self._output("Cannot freeze. L4 phases not confirmed.")
            return None

        # Freeze successful
        if isinstance(self.model, ShaperModel):
            content = render_work_item(self.model)
            filename = get_default_filename("L3")
        else:
            content = render_spec(self.model)
            filename = get_default_filename("L4")

        # Write output
        output_path = write_output(self.output_dir / filename, content)
        self._output(f"Frozen to: {output_path}")

        # Clear buffer and reset
        self.buffer.clear()
        self.model.reset()
        self.machine.reset()
        self.router.reset()
        self.model = None

        return content

    def process_line(self, line: str) -> None:
        """Process a single line of input."""
        # Check for disallowed content
        refusal = check_disallowed(line)
        if refusal:
            self._output(refusal)
            return

        # Check triggers
        if is_trigger(line, TRIGGER_REVEAL):
            self._output(self._reveal())
            return

        if is_trigger(line, TRIGGER_CONVERGE_L3):
            if self.model is None:
                self._start_session("L3")
            self._converge("L3")
            return

        if is_trigger(line, TRIGGER_CONVERGE_L4):
            if self.model is None:
                self._start_session("L4")
            self._converge("L4")
            return

        if is_trigger(line, TRIGGER_FREEZE):
            self._freeze()
            return

        # Regular input - detect altitude and ingest
        if self.model is None:
            route = self.router.try_lock(line)
            if route.altitude == "UNCLEAR":
                self._output(route.clarification or CLARIFICATION_PROMPT)
                return
            self._start_session(route.altitude)

        self.machine.on_edit()
        self.model.ingest(line)

    def _start_session(self, altitude: str) -> None:
        """Start a new shaping session."""
        self.router.lock(altitude)
        self.machine.start_shaping(altitude)
        if altitude == "L3":
            self.model = ShaperModel()
        else:
            self.model = SpecModel()

    def run(self) -> int:
        """Run interactive CLI loop.

        Returns:
            Exit code (0 for success).
        """
        while True:
            try:
                line = self._input("> ")
            except EOFError:
                break
            except KeyboardInterrupt:
                self._output("")
                break

            self.process_line(line)

        return 0


def main() -> int:
    """CLI entry point."""
    cli = ShaperCli()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
