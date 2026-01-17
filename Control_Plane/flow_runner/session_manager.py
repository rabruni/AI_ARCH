"""Session persistence utilities.

Manages session state including:
- Phase status tracking
- Retry and reroute counts
- Event history logging
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Default max retries if not specified in phase config
# Must match DEFAULT_MAX_RETRIES in flow_runner.py
DEFAULT_MAX_RETRIES = 3


@dataclass
class SessionManager:
    artifacts_dir: Path

    @property
    def session_path(self) -> Path:
        return self.artifacts_dir / "session.json"

    @property
    def history_path(self) -> Path:
        return self.artifacts_dir / "session_history.jsonl"

    def init_session(
        self,
        spec_id: str,
        flow_key: str,
        registry_path: str,
        phases: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Initialize a new session with phase tracking.

        Each phase includes:
        - status: blocked|ready|running|waiting_for_input|passed|failed|escalated
        - retries: count of same-phase retries
        - reroute_count: count of times rerouted TO this phase
        - max_retries: limit before escalation
        - last_failure_category: most recent failure type
        """
        session: Dict[str, Any] = {
            "spec_id": spec_id,
            "flow_key": flow_key,
            "registry_path": registry_path,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "current_phase": phases[0]["id"] if phases else None,
            "total_iterations": 0,
            "phases": {},
        }
        for idx, phase in enumerate(phases):
            max_retries = phase.get("max_retries")
            session["phases"][phase["id"]] = {
                "status": "ready" if idx == 0 else "blocked",
                "retries": 0,
                "reroute_count": 0,
                "max_retries": max_retries if max_retries is not None else DEFAULT_MAX_RETRIES,
                "last_failure_category": None,
            }
        self.save(session)
        self.append_event("session_initialized", {"spec_id": spec_id, "flow_key": flow_key})
        return session

    def load(self) -> Dict[str, Any]:
        if not self.session_path.exists():
            return {}
        return json.loads(self.session_path.read_text(encoding="utf-8"))

    def save(self, session: Dict[str, Any]) -> None:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")

    def append_event(self, event_type: str, data: Dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "data": data,
        }
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
