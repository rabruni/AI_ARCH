"""Flow Runner core logic."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from .adapters import resolve_adapter
from .gate_runner import GateRunner
from .phase_utils import phase_dir_name
from .prompt_assembly import assemble_prompt
from .session_manager import SessionManager
from .spec_pack_io import SpecPackIO


@dataclass
class FlowRunner:
    spec_id: str
    registry_path: Path
    flow_key: str
    repo_root: Path

    def __post_init__(self) -> None:
        self.spec_io = SpecPackIO.for_spec(self.spec_id)
        self.spec_io.create()
        artifacts_dir = self.spec_io.spec_root / "artifacts"
        self.session_manager = SessionManager(artifacts_dir)
        self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.gate_runner = GateRunner(self.repo_root)

    def start(self) -> Dict[str, Any]:
        phases = self._phases_for_flow()
        if not phases:
            raise ValueError(f"Flow key not found or has no phases: {self.flow_key}")
        return self.session_manager.init_session(
            spec_id=self.spec_id,
            flow_key=self.flow_key,
            registry_path=str(self.registry_path),
            phases=phases,
        )

    def status(self) -> Dict[str, Any]:
        return self.session_manager.load()

    def next(self) -> Dict[str, Any]:
        session = self.session_manager.load()
        if not session:
            raise ValueError("Session not initialized")

        phase_id = session.get("current_phase")
        phase_state = session.get("phases", {}).get(phase_id, {})
        status = phase_state.get("status")

        if status == "waiting_for_input":
            return {"status": "waiting_for_input", "phase_id": phase_id}

        if status in ("passed", "failed"):
            self._advance_phase(session, phase_id)
            self.session_manager.save(session)
            return {"status": "advanced", "phase_id": session.get("current_phase")}

        phase = self._phase_by_id(phase_id)
        prompt = assemble_prompt(
            prompt_key=phase.get("prompt_key"),
            spec_id=self.spec_id,
            phase_id=phase_id,
            registry=self.registry,
            session=session,
        )
        adapter = resolve_adapter(phase.get("agent_selector"))

        phase_state["status"] = "running"
        self.session_manager.save(session)

        result = adapter.execute(prompt, {"spec_id": self.spec_id, "phase_id": phase_id})
        if result.get("status") == "completed":
            output = result.get("output") or ""
            return self.done(phase_id=phase_id, output=output)

        phase_state["status"] = "waiting_for_input"
        self._write_prompt(phase_id, prompt)
        self.session_manager.save(session)
        return {"status": "waiting_for_input", "phase_id": phase_id, "prompt": prompt}

    def done(self, phase_id: Optional[str], output: Optional[str]) -> Dict[str, Any]:
        session = self.session_manager.load()
        if not session:
            raise ValueError("Session not initialized")

        phase_id = phase_id or session.get("current_phase")
        if not phase_id:
            raise ValueError("No phase available")

        if output is not None:
            self._write_output(phase_id, output)

        phase = self._phase_by_id(phase_id)
        gate_results = self.gate_runner.run_all(
            phase.get("gate_keys", []),
            self.spec_id,
            phase_id,
        )
        passed = all(result["status"] == "passed" for result in gate_results)

        phase_state = session.get("phases", {}).get(phase_id, {})
        phase_state["status"] = "passed" if passed else "failed"
        self.session_manager.append_event(
            "phase_completed",
            {"phase_id": phase_id, "status": phase_state["status"]},
        )

        if passed:
            self._advance_phase(session, phase_id)
        self.session_manager.save(session)
        return {"status": phase_state["status"], "phase_id": phase_id}

    def resume(self) -> Dict[str, Any]:
        session = self.session_manager.load()
        if not session:
            raise ValueError("Session not initialized")
        phase_id = session.get("current_phase")
        phase_state = session.get("phases", {}).get(phase_id, {})
        if phase_state.get("status") == "waiting_for_input":
            phase_state["status"] = "ready"
            self.session_manager.save(session)
        return self.next()

    def _advance_phase(self, session: Dict[str, Any], phase_id: str) -> None:
        phases = self._phases_for_flow()
        phase_ids = [phase["id"] for phase in phases]
        if phase_id not in phase_ids:
            return
        current_index = phase_ids.index(phase_id)
        if current_index + 1 >= len(phase_ids):
            return
        next_phase_id = phase_ids[current_index + 1]
        session["current_phase"] = next_phase_id
        next_state = session.get("phases", {}).get(next_phase_id, {})
        next_state["status"] = "ready"

    def _phases_for_flow(self) -> list[Dict[str, Any]]:
        flow = self.registry.get("flows", {}).get(self.flow_key)
        if not flow:
            return []
        return flow.get("phases", [])

    def _phase_by_id(self, phase_id: str) -> Dict[str, Any]:
        for phase in self._phases_for_flow():
            if phase.get("id") == phase_id:
                return phase
        raise ValueError(f"Phase not found: {phase_id}")

    def _write_prompt(self, phase_id: str, prompt: str) -> None:
        prompt_path = (
            self.spec_io.spec_root
            / "artifacts"
            / phase_dir_name(phase_id)
            / "prompt.txt"
        )
        prompt_path.write_text(prompt, encoding="utf-8")

    def _write_output(self, phase_id: str, output: str) -> None:
        output_path = (
            self.spec_io.spec_root
            / "artifacts"
            / phase_dir_name(phase_id)
            / "output.txt"
        )
        output_path.write_text(output, encoding="utf-8")
