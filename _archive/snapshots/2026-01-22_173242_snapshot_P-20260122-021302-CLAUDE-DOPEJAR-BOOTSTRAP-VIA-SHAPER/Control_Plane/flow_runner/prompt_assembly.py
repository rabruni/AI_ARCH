"""Prompt assembly for phases."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from .phase_utils import phase_dir_name

def assemble_prompt(
    prompt_key: str | None,
    spec_id: str,
    phase_id: str,
    registry: Dict[str, Any],
    session: Dict[str, Any],
) -> str:
    spec_path = Path("Control_Plane") / "docs" / "specs" / spec_id
    artifacts_dir = spec_path / "artifacts"

    previous_outputs = _collect_previous_outputs(artifacts_dir, phase_id)
    gate_keys = _phase_gate_keys(session, registry, phase_id)
    gates_section = _format_gates(gate_keys, registry)
    constraint_rule = _phase_constraint(session, registry, phase_id)

    lines = [
        "# Flow Phase Prompt",
        f"Spec ID: {spec_id}",
        f"Phase: {phase_id}",
        f"Spec Path: {spec_path}",
        "",
        f"Prompt Key: {prompt_key or ''}",
        "",
        "## Previous Phase Outputs",
    ]
    if previous_outputs:
        lines.extend([f"- {path}" for path in previous_outputs])
    else:
        lines.append("- (none)")

    lines.extend(["", "## Gates Required"])
    if gates_section:
        lines.extend(gates_section)
    else:
        lines.append("- (none)")

    lines.extend(["", "## Constraints"])
    lines.append(constraint_rule or "(none)")

    return "\n".join(lines) + "\n"


def _collect_previous_outputs(artifacts_dir: Path, phase_id: str) -> List[str]:
    outputs = []
    if not artifacts_dir.exists():
        return outputs
    current = phase_dir_name(phase_id).lower()
    for phase_dir in sorted(artifacts_dir.iterdir()):
        if not phase_dir.is_dir() or phase_dir.name.lower() == current:
            continue
        for file_path in sorted(phase_dir.iterdir()):
            if file_path.is_file():
                outputs.append(str(file_path))
    return outputs


def _phase_gate_keys(session: Dict[str, Any], registry: Dict[str, Any], phase_id: str) -> List[str]:
    for flow in registry.get("flows", {}).values():
        for phase in flow.get("phases", []):
            if phase.get("id") == phase_id:
                return phase.get("gate_keys", [])
    return []


def _phase_constraint(session: Dict[str, Any], registry: Dict[str, Any], phase_id: str) -> str | None:
    for flow in registry.get("flows", {}).values():
        for phase in flow.get("phases", []):
            if phase.get("id") == phase_id:
                return phase.get("constraint_rule")
    return None


def _format_gates(gate_keys: List[str], registry: Dict[str, Any]) -> List[str]:
    lines = []
    gates = registry.get("gates", {})
    for key in gate_keys:
        gate_info = gates.get(key) if isinstance(gates, dict) else None
        if gate_info and gate_info.get("purpose"):
            lines.append(f"- {key}: {gate_info['purpose']}")
        else:
            lines.append(f"- {key}")
    return lines
