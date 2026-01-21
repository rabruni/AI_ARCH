from __future__ import annotations

import sys

from .model import ShaperModel
from .work_item import render_work_item


TRIGGER_REVEAL = "show me what you have"
TRIGGER_CONVERGE = "turn this into a work item"
TRIGGER_FREEZE = "freeze it"


def is_trigger(text: str, trigger: str) -> bool:
    return text.strip().lower() == trigger


def disallowed_request(text: str) -> str | None:
    lowered = text.lower()
    if "mode=commit" in lowered or "mode: commit" in lowered:
        return "Refuse: MODE=COMMIT is not allowed."
    if "execute" in lowered or "run code" in lowered:
        return "Refuse: execution is not allowed."
    if "modify control plane" in lowered or "edit control_plane" in lowered:
        return "Refuse: Control Plane modification is not allowed."
    if "bypass" in lowered or "skip gate" in lowered:
        return "Refuse: bypassing gates is not allowed."
    if "infer plan" in lowered or "add plan steps" in lowered:
        return "Refuse: cannot invent or infer plan steps."
    return None


def reveal(model: ShaperModel) -> str:
    model.revealed_once = True
    missing = model.missing_sections()
    lines = [
        "Objective:",
        *(model.objective or ["(none)"]),
        "",
        "Scope:",
        *(model.scope or ["(none)"]),
        "",
        "Plan:",
        *(model.plan or ["(none)"]),
        "",
        "Acceptance:",
        *(model.acceptance or ["(none)"]),
        "",
        "Metadata:",
    ]
    for key in ("ID", "Title", "Status", "ALTITUDE"):
        lines.append(f"- {key}: {model.meta.get(key, '')}")
    if missing:
        lines.append("")
        lines.append("Missing:")
        for item in missing:
            lines.append(f"- {item}")
    return "\n".join(lines)


def converge(model: ShaperModel, input_func=input, output_func=print) -> None:
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
    while True:
        missing = model.missing_sections()
        if not missing:
            return
        next_item = missing[0]
        output_func(questions[next_item])
        response = input_func("> ").strip()
        if not response:
            continue
        if next_item in ("ID", "Title", "Status", "ALTITUDE"):
            model.meta[next_item] = response
        elif next_item == "Objective":
            model.objective.append(response)
        elif next_item == "Scope":
            model.scope.append(response)
        elif next_item == "Implementation Plan":
            model.plan.append(response)
        elif next_item == "Acceptance Commands":
            model.acceptance.append(response)


def process_line(
    model: ShaperModel,
    line: str,
    input_func=input,
    output_func=print,
) -> None:
    refusal = disallowed_request(line)
    if refusal:
        output_func(refusal)
        return

    if is_trigger(line, TRIGGER_REVEAL):
        output_func(reveal(model))
        return
    if is_trigger(line, TRIGGER_CONVERGE):
        if not model.revealed_once:
            output_func("Refuse: reveal required before converge.")
            return
        converge(model, input_func=input_func, output_func=output_func)
        return
    if is_trigger(line, TRIGGER_FREEZE):
        missing = model.missing_sections()
        if missing:
            output_func("Cannot freeze. Missing: " + ", ".join(missing))
            return
        output_func(render_work_item(model))
        model.reset()
        return

    model.ingest(line)


def main() -> int:
    model = ShaperModel()
    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print("")
            break

        process_line(model, line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
