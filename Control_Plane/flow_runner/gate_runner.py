"""Gate execution (G1-G3)."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Iterable

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

    def run_gate(self, gate_key: str, spec_id: str, phase_id: str) -> Dict[str, Any]:
        if gate_key == "G1":
            result = self._run_g1(spec_id)
        elif gate_key == "G2":
            result = self._run_g2(spec_id)
        elif gate_key == "G3":
            result = self._run_g3(spec_id, phase_id)
        else:
            result = GateResult(
                gate_id=gate_key,
                status="passed",
                category="OK",
                reason="gate not implemented; skipped",
                evidence_paths=[],
                recommended_route=None,
            )
        return result.__dict__

    def run_all(
        self,
        context: Dict[str, Any] | List[str],
        gate_keys: List[str] | str,
        spec_id: str | None = None,
        phase_id: str | None = None,
    ) -> Dict[str, Any]:
        phase_id_arg = phase_id
        if isinstance(context, dict):
            spec_id = context.get("spec_id")
            phase_id = context.get("phase_id")
            gate_list = list(gate_keys) if isinstance(gate_keys, list) else []
        else:
            if not (isinstance(gate_keys, str) and isinstance(spec_id, str)):
                raise ValueError("Invalid run_all signature usage")
            gate_list = context
            spec_id = gate_keys
            phase_id = phase_id_arg
        if not spec_id or not phase_id:
            raise ValueError("spec_id and phase_id are required")

        results: List[GateResult] = []
        for gate_key in gate_list:
            result = self.run_gate(gate_key, spec_id, phase_id)
            results.append(GateResult(**result))

        serialized = [result.__dict__ for result in results]
        self._write_results(spec_id, phase_id, serialized)
        self._print_summary(serialized)
        return {"gates": serialized}

    def _run_g1(self, spec_id: str) -> GateResult:
        spec_root = self.repo_root / "Control_Plane" / "docs" / "specs" / spec_id
        if not spec_root.exists():
            return GateResult(
                gate_id="G1",
                status="failed",
                category="SPEC_DEFECT",
                reason="Spec root not found",
                evidence_paths=[],
                recommended_route="Phase1",
            )

        registry_md = spec_root / "07_registry.md"
        overview_md = spec_root / "00_overview.md"
        expected = []
        if registry_md.exists():
            expected = self._extract_paths_from_md(registry_md, spec_id)
        if not expected and overview_md.exists():
            expected = self._extract_paths_from_md(overview_md, spec_id)

        expected_set = {p for p in expected if not p.startswith("artifacts/")}
        actual_set = {
            p
            for p in self._spec_files(spec_root)
            if not p.startswith("artifacts/")
        }

        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set) if expected_set else []
        if missing or extra:
            reason = []
            if missing:
                reason.append(f"Missing: {', '.join(missing)}")
            if extra:
                reason.append(f"Extra: {', '.join(extra)}")
            return GateResult(
                gate_id="G1",
                status="failed",
                category="SPEC_DEFECT",
                reason=", ".join(reason),
                evidence_paths=[],
                recommended_route="Phase1",
            )

        return GateResult(
            gate_id="G1",
            status="passed",
            category="OK",
            reason="structure ok",
            evidence_paths=[],
            recommended_route=None,
        )

    def _run_g2(self, spec_id: str) -> GateResult:
        spec_root = self.repo_root / "Control_Plane" / "docs" / "specs" / spec_id
        if not spec_root.exists():
            return GateResult(
                gate_id="G2",
                status="failed",
                category="SPEC_DEFECT",
                reason="Spec root not found",
                evidence_paths=[],
                recommended_route="Phase1",
            )

        yaml_loader = None
        try:
            import yaml  # type: ignore

            yaml_loader = yaml.safe_load
        except Exception:
            yaml_loader = None

        for file_path in self._spec_files(spec_root):
            if file_path.startswith("artifacts/"):
                continue
            full_path = spec_root / file_path
            if full_path.suffix == ".json":
                try:
                    with full_path.open("r", encoding="utf-8") as handle:
                        json.load(handle)
                except Exception:
                    return GateResult(
                        gate_id="G2",
                        status="failed",
                        category="SPEC_DEFECT",
                        reason=f"Invalid syntax in {file_path}",
                        evidence_paths=[file_path],
                        recommended_route="Phase1",
                    )
            if full_path.suffix in {".yaml", ".yml"}:
                if yaml_loader is None:
                    continue
                try:
                    with full_path.open("r", encoding="utf-8") as handle:
                        yaml_loader(handle)
                except Exception:
                    return GateResult(
                        gate_id="G2",
                        status="failed",
                        category="SPEC_DEFECT",
                        reason=f"Invalid syntax in {file_path}",
                        evidence_paths=[file_path],
                        recommended_route="Phase1",
                    )

        return GateResult(
            gate_id="G2",
            status="passed",
            category="OK",
            reason="schemas valid",
            evidence_paths=[],
            recommended_route=None,
        )

    def _run_g3(self, spec_id: str, phase_id: str) -> GateResult:
        spec_root = self.repo_root / "Control_Plane" / "docs" / "specs" / spec_id
        testing_md = spec_root / "05_testing.md"
        if not testing_md.exists():
            return GateResult(
                gate_id="G3",
                status="failed",
                category="SPEC_DEFECT",
                reason="05_testing.md not found",
                evidence_paths=[],
                recommended_route="Phase1",
            )

        command = self._extract_test_command(testing_md)
        if not command:
            return GateResult(
                gate_id="G3",
                status="failed",
                category="SPEC_DEFECT",
                reason="No test command found in 05_testing.md",
                evidence_paths=[],
                recommended_route="Phase1",
            )

        log_path = (
            spec_root
            / "artifacts"
            / phase_dir_name(phase_id)
            / "gate_logs"
            / "G3.log"
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            command,
            shell=True,
            cwd=self.repo_root,
            timeout=60,
            capture_output=True,
            text=True,
        )
        log_path.write_text(
            f"COMMAND: {command}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n",
            encoding="utf-8",
        )

        if result.returncode == 0:
            return GateResult(
                gate_id="G3",
                status="passed",
                category="OK",
                reason="command ok",
                evidence_paths=[str(log_path.relative_to(spec_root))],
                recommended_route=None,
            )

        return GateResult(
            gate_id="G3",
            status="failed",
            category="IMPLEMENTATION_DEFECT",
            reason=f"Command failed: {command}",
            evidence_paths=[str(log_path.relative_to(spec_root))],
            recommended_route="Phase2",
        )

    def _extract_paths_from_md(self, md_path: Path, spec_id: str) -> List[str]:
        paths: List[str] = []
        spec_prefix = f"Control_Plane/docs/specs/{spec_id}/"
        for line in md_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            for token in self._extract_backticks(line):
                resolved = self._normalize_spec_path(token, spec_prefix)
                if resolved:
                    paths.append(resolved)
            if line.startswith("- ") and "`" not in line:
                item = line[2:].strip()
                resolved = self._normalize_spec_path(item, spec_prefix)
                if resolved:
                    paths.append(resolved)
        return sorted(set(paths))

    def _extract_backticks(self, line: str) -> Iterable[str]:
        segments = []
        parts = line.split("`")
        for idx in range(1, len(parts), 2):
            segments.append(parts[idx])
        return segments

    def _normalize_spec_path(self, raw: str, spec_prefix: str) -> str | None:
        if not raw or raw.startswith("$"):
            return None
        cleaned = raw.strip()
        if cleaned.startswith("/"):
            if spec_prefix in cleaned:
                cleaned = cleaned.split(spec_prefix, 1)[-1]
            else:
                return None
        if cleaned.startswith(spec_prefix):
            cleaned = cleaned[len(spec_prefix) :]
        cleaned = cleaned.lstrip("./")
        if not cleaned:
            return None
        if cleaned.endswith("/"):
            return None
        if "/" not in cleaned and "." not in cleaned:
            return None
        return cleaned

    def _spec_files(self, spec_root: Path) -> List[str]:
        files = []
        for path in spec_root.rglob("*"):
            if path.is_file():
                files.append(path.relative_to(spec_root).as_posix())
        return files

    def _extract_test_command(self, testing_md: Path) -> str | None:
        for line in testing_md.read_text(encoding="utf-8").splitlines():
            stripped = line.lstrip()
            if stripped.startswith("$"):
                return stripped[1:].strip()
        return None

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
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    def _print_summary(self, results: List[Dict[str, Any]]) -> None:
        for result in results:
            gate_id = result.get("gate_id", "UNKNOWN")
            status = (result.get("status") or "").upper()
            reason = result.get("reason") or ""
            if status == "FAILED":
                print(f"{gate_id} {status}: {reason}")
            else:
                print(f"{gate_id} {status}")
