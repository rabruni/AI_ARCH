"""Session persistence utilities."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


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
        session = {
            "spec_id": spec_id,
            "flow_key": flow_key,
            "registry_path": registry_path,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "current_phase": phases[0]["id"] if phases else None,
            "phases": {},
        }
        for idx, phase in enumerate(phases):
            max_retries = phase.get("max_retries")
            session["phases"][phase["id"]] = {
                "status": "ready" if idx == 0 else "blocked",
                "retries": 0,
                "max_retries": max_retries if max_retries is not None else 0,
            }
        self.save(session)
        self.append_event("session_initialized", {"spec_id": spec_id, "flow_key": flow_key})
        return session

    def load(self) -> Dict[str, Any]:
        if not self.session_path.exists():
            return {}
        return json.loads(self.session_path.read_text(encoding="utf-8"))

    def save(self, session: Dict[str, Any]) -> None:
        self.session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")

    def append_event(self, event_type: str, data: Dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "data": data,
        }
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
