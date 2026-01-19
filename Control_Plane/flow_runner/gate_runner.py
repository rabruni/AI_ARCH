"""Gate execution (G0-G3)."""
from __future__ import annotations

import json
import re
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
    evidence: Dict[str, Any] | None = None


class GateRunner:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run_gate(self, gate_key: str, spec_id: str, phase_id: str) -> Dict[str, Any]:
        if gate_key == "G0":
            result = self._run_g0(spec_id)
        elif gate_key == "G1":
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

    def _run_g0(self, spec_id: str) -> GateResult:
        """G0: Ready-to-Test gate. Enforces EXPLORE vs COMMIT mode."""
        spec_root = self.repo_root / "Control_Plane" / "docs" / "specs" / spec_id
        commit_md = spec_root / "08_commit.md"

        if not commit_md.exists():
            return GateResult(
                gate_id="G0",
                status="failed",
                category="GOAL_DEFECT",
                reason="08_commit.md not found. Create it with MODE=COMMIT to proceed.",
                evidence_paths=[],
                recommended_route="Phase0A",
            )

        content = commit_md.read_text(encoding="utf-8")

        # Parse sections (case-insensitive)
        sections = self._parse_commit_sections(content)

        # Check required headings exist
        required_headings = ["mode", "altitude", "references", "stop conditions"]
        missing_headings = [h for h in required_headings if h not in sections]
        if missing_headings:
            return GateResult(
                gate_id="G0",
                status="failed",
                category="GOAL_DEFECT",
                reason=f"08_commit.md missing required sections: {', '.join(missing_headings)}",
                evidence_paths=[],
                recommended_route="Phase0A",
            )

        # Check MODE
        mode_content = sections.get("mode", "").strip().upper()
        if mode_content == "EXPLORE":
            return GateResult(
                gate_id="G0",
                status="failed",
                category="GOAL_DEFECT",
                reason="MODE=EXPLORE: shaping is allowed, but execution is blocked. Set MODE=COMMIT to proceed.",
                evidence_paths=[],
                recommended_route="Phase0A",
            )

        if mode_content != "COMMIT":
            return GateResult(
                gate_id="G0",
                status="failed",
                category="GOAL_DEFECT",
                reason=f"MODE must be EXPLORE or COMMIT, got: '{mode_content}'",
                evidence_paths=[],
                recommended_route="Phase0A",
            )

        # Check ALTITUDE
        altitude = sections.get("altitude", "").strip().upper()
        valid_altitudes = {"L4", "L3", "L2", "L1"}
        if altitude not in valid_altitudes:
            return GateResult(
                gate_id="G0",
                status="failed",
                category="GOAL_DEFECT",
                reason=f"ALTITUDE must be L4/L3/L2/L1, got: '{altitude}'",
                evidence_paths=[],
                recommended_route="Phase0A",
            )

        # Check REFERENCES
        refs_content = sections.get("references", "")
        ref_errors = self._validate_references(refs_content, spec_root)
        if ref_errors:
            return GateResult(
                gate_id="G0",
                status="failed",
                category="GOAL_DEFECT",
                reason=f"REFERENCES errors: {'; '.join(ref_errors)}",
                evidence_paths=[],
                recommended_route="Phase0A",
            )

        # Check STOP CONDITIONS has at least 1 bullet
        stop_content = sections.get("stop conditions", "")
        bullets = [line for line in stop_content.splitlines() if line.strip().startswith("-")]
        if not bullets:
            return GateResult(
                gate_id="G0",
                status="failed",
                category="GOAL_DEFECT",
                reason="STOP CONDITIONS must have at least 1 bullet point",
                evidence_paths=[],
                recommended_route="Phase0A",
            )

        # Check for WORK_ITEM_PATH (optional)
        work_item_path = self._extract_work_item_path(sections, refs_content)
        evidence: Dict[str, Any] | None = None

        if work_item_path:
            # Resolve path relative to spec root
            resolved_path = spec_root / work_item_path
            if not resolved_path.exists():
                return GateResult(
                    gate_id="G0",
                    status="failed",
                    category="GOAL_DEFECT",
                    reason=f"WORK_ITEM_PATH not found: {work_item_path}",
                    evidence_paths=[],
                    recommended_route="Phase0A",
                )

            # Validate work item using validate_work_item.py
            validator_script = self.repo_root / "Control_Plane" / "scripts" / "validate_work_item.py"
            if not validator_script.exists():
                return GateResult(
                    gate_id="G0",
                    status="failed",
                    category="GOAL_DEFECT",
                    reason="validate_work_item.py not found",
                    evidence_paths=[],
                    recommended_route="Phase0A",
                )

            result = subprocess.run(
                ["python3", str(validator_script), str(resolved_path)],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_msg = result.stdout.strip() or result.stderr.strip() or "validation failed"
                return GateResult(
                    gate_id="G0",
                    status="failed",
                    category="GOAL_DEFECT",
                    reason=f"WORK_ITEM validation failed: {error_msg}",
                    evidence_paths=[],
                    recommended_route="Phase0A",
                    evidence={"work_item_path": work_item_path, "work_item_validated": False},
                )

            evidence = {"work_item_path": work_item_path, "work_item_validated": True}

        return GateResult(
            gate_id="G0",
            status="passed",
            category="OK",
            reason=f"MODE=COMMIT, ALTITUDE={altitude}",
            evidence_paths=[],
            recommended_route=None,
            evidence=evidence,
        )

    def _parse_commit_sections(self, content: str) -> Dict[str, str]:
        """Parse 08_commit.md into sections by heading (case-insensitive)."""
        sections: Dict[str, str] = {}
        current_heading = None
        current_lines: List[str] = []

        for line in content.splitlines():
            # Check for ## heading (case-insensitive)
            heading_match = re.match(r"^##\s+(.+)$", line, re.IGNORECASE)
            if heading_match:
                # Save previous section
                if current_heading is not None:
                    sections[current_heading] = "\n".join(current_lines)
                current_heading = heading_match.group(1).strip().lower()
                current_lines = []
            else:
                current_lines.append(line)

        # Save last section
        if current_heading is not None:
            sections[current_heading] = "\n".join(current_lines)

        return sections

    def _validate_references(self, refs_content: str, spec_root: Path) -> List[str]:
        """Validate REFERENCES section. Returns list of error messages."""
        errors: List[str] = []
        required_refs = {"goal", "non-goals", "acceptance"}
        found_refs: Dict[str, str] = {}

        for line in refs_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip leading "- " for markdown list items
            if line.startswith("- "):
                line = line[2:].strip()
            # Match "Key: path#anchor" or "Key: path"
            match = re.match(r"^([^:]+):\s*(.+)$", line, re.IGNORECASE)
            if match:
                key = match.group(1).strip().lower()
                value = match.group(2).strip()
                found_refs[key] = value

        # Check all required refs exist
        for ref in required_refs:
            if ref not in found_refs:
                errors.append(f"Missing reference: {ref}")
            else:
                # Validate file path exists (ignore anchor)
                path_value = found_refs[ref]
                if path_value.lower() != "n/a":
                    # Extract file path (before #)
                    file_path = path_value.split("#")[0].strip()
                    if file_path:
                        full_path = spec_root / file_path
                        if not full_path.exists():
                            errors.append(f"{ref}: file not found: {file_path}")

        return errors

    def _extract_work_item_path(self, sections: Dict[str, str], refs_content: str) -> str | None:
        """Extract WORK_ITEM_PATH from sections or REFERENCES."""
        # Check for dedicated WORK_ITEM_PATH section
        work_item_section = sections.get("work_item_path", "").strip()
        if work_item_section:
            return work_item_section.splitlines()[0].strip()

        # Check for "Work Item:" in REFERENCES
        for line in refs_content.splitlines():
            line = line.strip()
            if line.startswith("- "):
                line = line[2:].strip()
            match = re.match(r"^work\s*item\s*:\s*(.+)$", line, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

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
