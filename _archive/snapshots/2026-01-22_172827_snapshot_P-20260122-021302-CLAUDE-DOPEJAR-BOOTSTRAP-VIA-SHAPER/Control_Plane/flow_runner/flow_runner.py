"""Flow Runner core logic.

Implements bounce-back routing and escalation:
- Retry: same phase if retries < max_retries
- Reroute: earlier phase based on failure category
- Escalate: when retries exceeded or no valid route

State transitions:
    blocked → ready → running → waiting_for_input → passed/failed/escalated
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .adapters import resolve_adapter
from .gate_runner import GateRunner
from .phase_utils import phase_dir_name
from .prompt_assembly import assemble_prompt
from .session_manager import SessionManager
from .spec_pack_io import SpecPackIO

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_MAX_RETRIES = 3
MAX_TOTAL_ITERATIONS = 20

CATEGORY_ROUTES: Dict[str, Optional[str]] = {
    "GOAL_DEFECT": "Phase0A",
    "SPEC_DEFECT": "Phase1",
    "IMPLEMENTATION_DEFECT": "Phase2",
    "INFRASTRUCTURE_DEFECT": None,  # escalate
    "UNKNOWN": None,                 # escalate
    "NONE": None,                    # no routing (passed)
}

PHASE_ORDER: List[str] = ["Phase0A", "Phase1", "Phase2", "Phase3", "Phase4"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _extract_spec_tree(spec_root: Path) -> Dict[str, Any]:
    """Extracts expected file structure from 07_registry.md."""
    spec_tree: Dict[str, Any] = {}
    registry_md_path = spec_root / "07_registry.md"
    if not registry_md_path.exists():
        return spec_tree

    with open(registry_md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- `") and line.endswith("`"):
                path = line[3:-1]
                spec_tree[path] = "file"
            elif line.startswith("- "):
                path = line[2:]
                spec_tree[path] = "file"

    return spec_tree


# ─────────────────────────────────────────────────────────────────────────────
# FlowRunner
# ─────────────────────────────────────────────────────────────────────────────


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
        """
        Mark phase work as done, run gates, and determine routing.

        Returns routing result with action taken (advance/retry/reroute/escalate).
        """
        session = self.session_manager.load()
        if not session:
            raise ValueError("Session not initialized")

        phase_id = phase_id or session.get("current_phase")
        if not phase_id:
            raise ValueError("No phase available")

        if output is not None:
            self._write_output(phase_id, output)

        # Run gates and determine routing
        routing = self.run_gates_and_route(phase_id, session)
        phase_state = session["phases"][phase_id]

        if routing["passed"]:
            phase_state["status"] = "passed"
            self._advance_phase(session, phase_id)
            self.session_manager.append_event(
                "state_transition",
                {
                    "phase": phase_id,
                    "action": "advance",
                    "reason": "all_gates_passed",
                    "retry_count": phase_state.get("retries", 0),
                    "reroute_count": phase_state.get("reroute_count", 0),
                },
            )
        elif routing["action"] == "retry":
            phase_state["retries"] = phase_state.get("retries", 0) + 1
            phase_state["status"] = "ready"
            self.session_manager.append_event(
                "state_transition",
                {
                    "phase": phase_id,
                    "action": "retry",
                    "reason": routing["reason"],
                    "categories": routing["categories"],
                    "retry_count": phase_state["retries"],
                    "reroute_count": phase_state.get("reroute_count", 0),
                },
            )
        elif routing["action"] == "reroute":
            phase_state["status"] = "failed"
            self._reroute_to_phase(session, routing["target_phase"])
        elif routing["action"] == "escalate":
            phase_state["status"] = "escalated"
            self.session_manager.append_event(
                "state_transition",
                {
                    "phase": phase_id,
                    "action": "escalate",
                    "reason": routing["reason"],
                    "categories": routing.get("categories", []),
                    "retry_count": phase_state.get("retries", 0),
                    "reroute_count": phase_state.get("reroute_count", 0),
                },
            )

        self.session_manager.save(session)
        return {
            "status": phase_state["status"],
            "phase_id": phase_id,
            "action": routing["action"],
            "target_phase": routing.get("target_phase"),
            "reason": routing["reason"],
        }

    def resume(self) -> Dict[str, Any]:
        """
        Resume execution from waiting_for_input or escalated state.

        For escalated phases, this allows human intervention to unblock
        the flow and continue execution.
        """
        session = self.session_manager.load()
        if not session:
            raise ValueError("Session not initialized")

        phase_id = session.get("current_phase")
        phase_state = session.get("phases", {}).get(phase_id, {})
        current_status = phase_state.get("status")

        if current_status in ("waiting_for_input", "escalated"):
            from_status = current_status
            phase_state["status"] = "ready"
            self.session_manager.append_event(
                "state_transition",
                {
                    "phase": phase_id,
                    "action": "resume",
                    "from_status": from_status,
                    "to_status": "ready",
                    "reason": "manual_intervention",
                },
            )
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

    def _phases_for_flow(self) -> List[Dict[str, Any]]:
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
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt, encoding="utf-8")

    def _write_output(self, phase_id: str, output: str) -> None:
        output_path = (
            self.spec_io.spec_root
            / "artifacts"
            / phase_dir_name(phase_id)
            / "output.txt"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")

    # ─────────────────────────────────────────────────────────────────────────
    # Routing Logic
    # ─────────────────────────────────────────────────────────────────────────

    def run_gates_and_route(
        self, phase_id: str, session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes all gates for a phase and determines next action.

        Returns:
            {
                "passed": bool,
                "action": "advance" | "retry" | "reroute" | "escalate",
                "target_phase": str | None,
                "categories": List[str],
                "reason": str
            }
        """
        # Check iteration cap
        session["total_iterations"] = session.get("total_iterations", 0) + 1
        if session["total_iterations"] > MAX_TOTAL_ITERATIONS:
            self.session_manager.append_event(
                "state_transition",
                {
                    "phase": phase_id,
                    "action": "escalate",
                    "reason": "max_iterations_exceeded",
                    "iteration_count": session["total_iterations"],
                },
            )
            return {
                "passed": False,
                "action": "escalate",
                "target_phase": None,
                "categories": [],
                "reason": "max_iterations_exceeded",
            }

        # Build context and run gates
        phase_def = self._phase_by_id(phase_id)
        gate_keys = phase_def.get("gate_keys", [])
        spec_root = self.spec_io.spec_root
        spec_tree = _extract_spec_tree(spec_root)

        context = {
            "workspace_root": str(spec_root),
            "spec_tree": spec_tree,
            "phase_id": phase_id,
            "spec_id": self.spec_id,
        }

        result = self.gate_runner.run_all(context, gate_keys)
        gates = result.get("gates", [])
        failed_gates = [g for g in gates if g.get("status") == "failed"]

        # All passed
        if not failed_gates:
            return {
                "passed": True,
                "action": "advance",
                "target_phase": None,
                "categories": [],
                "reason": "all_gates_passed",
            }

        # Collect failure categories
        categories = [g.get("category", "UNKNOWN") for g in failed_gates]
        phase_state = session["phases"][phase_id]
        phase_state["last_failure_category"] = categories[0] if categories else "UNKNOWN"

        # Determine target phases from categories
        routed_phases = []
        for cat in categories:
            target = CATEGORY_ROUTES.get(cat)
            if target and target in PHASE_ORDER:
                routed_phases.append(target)

        # Find earliest phase (lowest index in PHASE_ORDER)
        target_phase = None
        if routed_phases:
            target_phase = min(routed_phases, key=lambda p: PHASE_ORDER.index(p))

        max_retries = phase_state.get("max_retries", DEFAULT_MAX_RETRIES)

        # Determine action
        if target_phase == phase_id:
            # Same phase: retry if under limit
            if phase_state["retries"] < max_retries:
                return {
                    "passed": False,
                    "action": "retry",
                    "target_phase": phase_id,
                    "categories": categories,
                    "reason": "retry_same_phase",
                }
            else:
                return {
                    "passed": False,
                    "action": "escalate",
                    "target_phase": None,
                    "categories": categories,
                    "reason": "max_retries_exceeded",
                }
        elif target_phase:
            # Different phase: reroute
            return {
                "passed": False,
                "action": "reroute",
                "target_phase": target_phase,
                "categories": categories,
                "reason": f"category_route_to_{target_phase}",
            }
        else:
            # No valid target: escalate
            return {
                "passed": False,
                "action": "escalate",
                "target_phase": None,
                "categories": categories,
                "reason": "no_valid_route",
            }

    def _reroute_to_phase(self, session: Dict[str, Any], target_phase: str) -> None:
        """Reroute execution to an earlier phase."""
        session["current_phase"] = target_phase
        phase_state = session["phases"][target_phase]
        phase_state["status"] = "ready"
        phase_state["reroute_count"] = phase_state.get("reroute_count", 0) + 1
        phase_state["retries"] = 0  # Reset retries on reroute

        self.session_manager.append_event(
            "state_transition",
            {
                "phase": target_phase,
                "action": "reroute",
                "reason": "phase_redirect",
                "reroute_count": phase_state["reroute_count"],
            },
        )
