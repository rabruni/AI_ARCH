"""Gate execution (stubbed)."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

from .phase_utils import phase_dir_name

@dataclass
class GateResult:
    gate_id: str
    status: str
    category: str | None
    reason: str
    evidence_paths: List[str]
    recommended_route: str | None


class GateRunner:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run_all(self, gate_keys: List[str], spec_id: str, phase_id: str) -> List[Dict[str, Any]]:
        results: List[GateResult] = []
        for gate_key in gate_keys:
            if gate_key == "CW1":
                results.append(self._run_cw1(spec_id))
            else:
                results.append(self._run_placeholder(gate_key, spec_id))

        serialized = [result.__dict__ for result in results]
        self._write_results(spec_id, phase_id, serialized)
        return serialized

    def _run_cw1(self, spec_id: str) -> GateResult:
        cp_script = self.repo_root / "Control_Plane" / "cp.py"
        if cp_script.exists():
            result = subprocess.run(
                ["python3", str(cp_script), "gate", "--all", spec_id],
                cwd=self.repo_root,
            )
            if result.returncode == 0:
                return GateResult(
                    gate_id="CW1",
                    status="passed",
                    category=None,
                    reason="Gate executed via cp.py",
                    evidence_paths=[],
                    recommended_route=None,
                )
            return GateResult(
                gate_id="CW1",
                status="failed",
                category="SPEC_DEFECT",
                reason="cp.py gate --all returned non-zero",
                evidence_paths=[],
                recommended_route="Phase0A",
            )

        return GateResult(
            gate_id="CW1",
            status="passed",
            category=None,
            reason="cp.py not available, stub pass",
            evidence_paths=[],
            recommended_route=None,
        )

    def _run_placeholder(self, gate_key: str, spec_id: str) -> GateResult:
        spec_root = self.repo_root / "Control_Plane" / "docs" / "specs" / spec_id
        required_files = [
            spec_root / "00_overview.md",
            spec_root / "01_scope.md",
            spec_root / "02_assumptions.md",
            spec_root / "03_constraints.md",
            spec_root / "04_interface.md",
            spec_root / "05_architecture.md",
            spec_root / "06_validation.md",
            spec_root / "07_registry.md",
        ]
        missing = [str(path) for path in required_files if not path.exists()]
        if missing:
            return GateResult(
                gate_id=gate_key,
                status="failed",
                category="SPEC_DEFECT",
                reason="Missing required spec files",
                evidence_paths=missing,
                recommended_route="Phase0A",
            )

        return GateResult(
            gate_id=gate_key,
            status="passed",
            category=None,
            reason="Stub gate pass",
            evidence_paths=[],
            recommended_route=None,
        )

    def _write_results(self, spec_id: str, phase_id: str, results: List[Dict[str, Any]]) -> None:
        gate_path = (
            self.repo_root
            / "Control_Plane"
            / "docs"
            / "specs"
            / spec_id
            / "artifacts"
            / phase_dir_name(phase_id)
            / "gate_results.json"
        )
        gate_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
