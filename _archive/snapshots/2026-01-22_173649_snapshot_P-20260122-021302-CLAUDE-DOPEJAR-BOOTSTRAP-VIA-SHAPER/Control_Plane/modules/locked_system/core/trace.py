"""Episodic Trace - Single source for history, observability, and learning inputs.

Simplification: All cross-HRM notifications become Event appends.
Consumers query the trace instead of registering callbacks.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional
import json
import uuid


@dataclass
class Event:
    """Universal event for Episodic Trace."""
    id: str
    event_type: str
    timestamp: datetime
    payload: dict
    refs: List[str] = field(default_factory=list)
    problem_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "refs": self.refs,
            "problem_id": self.problem_id,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    @classmethod
    def create(
        cls,
        event_type: str,
        payload: dict,
        problem_id: str = None,
        session_id: str = None,
        refs: List[str] = None
    ) -> 'Event':
        return cls(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=datetime.now(),
            payload=payload,
            refs=refs or [],
            problem_id=problem_id,
            session_id=session_id
        )


class EpisodicTrace:
    """
    Append-only event trace.

    All HRM notifications become Event appends:
    - Altitude transitions
    - Stance changes
    - Agent activations
    - Pattern matches
    - Write completions
    - Decisions

    Consumers query the trace to understand history.
    """

    def __init__(self, storage_path: Optional[Path] = None, session_id: str = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        self._events: List[Event] = []
        self._load()

    def _load(self):
        """Load events from storage."""
        if self.storage_path and self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            self._events.append(Event.from_dict(data))
            except Exception:
                pass  # Start fresh on error

    def _persist(self, event: Event):
        """Append event to storage."""
        if self.storage_path:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'a') as f:
                f.write(json.dumps(event.to_dict()) + "\n")

    def append(self, event: Event) -> str:
        """Append event to trace. Returns event ID."""
        if not event.session_id:
            event.session_id = self.session_id
        self._events.append(event)
        self._persist(event)
        return event.id

    def log(
        self,
        event_type: str,
        payload: dict,
        problem_id: str = None,
        refs: List[str] = None
    ) -> str:
        """Convenience method to create and append an event."""
        event = Event.create(
            event_type=event_type,
            payload=payload,
            problem_id=problem_id,
            session_id=self.session_id,
            refs=refs
        )
        return self.append(event)

    def query(
        self,
        event_type: str = None,
        problem_id: str = None,
        start: datetime = None,
        end: datetime = None,
        limit: int = None
    ) -> List[Event]:
        """Query events with filters."""
        results = self._events

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if problem_id:
            results = [e for e in results if e.problem_id == problem_id]

        if start:
            results = [e for e in results if e.timestamp >= start]

        if end:
            results = [e for e in results if e.timestamp <= end]

        if limit:
            results = results[-limit:]

        return results

    def since(self, timestamp: datetime) -> List[Event]:
        """Get all events since timestamp."""
        return self.query(start=timestamp)

    def get(self, event_id: str) -> Optional[Event]:
        """Get event by ID."""
        for event in self._events:
            if event.id == event_id:
                return event
        return None

    def get_recent(self, n: int = 10) -> List[Event]:
        """Get n most recent events."""
        return self._events[-n:]

    @property
    def count(self) -> int:
        return len(self._events)

    # ─────────────────────────────────────────────────────────────
    # Convenience logging methods for common events
    # ─────────────────────────────────────────────────────────────

    def log_altitude_transition(
        self,
        from_level: str,
        to_level: str,
        reason: str,
        problem_id: str = None
    ) -> str:
        return self.log(
            event_type="altitude_transition",
            payload={"from": from_level, "to": to_level, "reason": reason},
            problem_id=problem_id
        )

    def log_stance_change(
        self,
        from_stance: str,
        to_stance: str,
        via_gate: str,
        problem_id: str = None
    ) -> str:
        return self.log(
            event_type="stance_change",
            payload={"from": from_stance, "to": to_stance, "via_gate": via_gate},
            problem_id=problem_id
        )

    def log_agent_activated(
        self,
        agents: List[str],
        reducer: str,
        problem_id: str = None
    ) -> str:
        return self.log(
            event_type="agent_activated",
            payload={"agents": agents, "reducer": reducer},
            problem_id=problem_id
        )

    def log_decision(
        self,
        decision_type: str,
        decision: str,
        rationale: str,
        problem_id: str = None
    ) -> str:
        return self.log(
            event_type="decision",
            payload={"type": decision_type, "decision": decision, "rationale": rationale},
            problem_id=problem_id
        )

    def log_write(
        self,
        target: str,
        key: str,
        approved: bool,
        problem_id: str = None
    ) -> str:
        return self.log(
            event_type="write_completed",
            payload={"target": target, "key": key, "approved": approved},
            problem_id=problem_id
        )

    def log_error(
        self,
        error_code: str,
        message: str,
        context: dict = None,
        problem_id: str = None
    ) -> str:
        return self.log(
            event_type="error",
            payload={"code": error_code, "message": message, "context": context or {}},
            problem_id=problem_id
        )

    def log_turn(
        self,
        turn_number: int,
        user_input: str,
        response_summary: str,
        problem_id: str = None
    ) -> str:
        return self.log(
            event_type="turn",
            payload={
                "turn": turn_number,
                "input": user_input[:200],  # Truncate for storage
                "response": response_summary[:200]
            },
            problem_id=problem_id
        )


# Global trace instance (can be overridden)
_global_trace: Optional[EpisodicTrace] = None


def get_trace() -> EpisodicTrace:
    """Get or create global trace instance."""
    global _global_trace
    if _global_trace is None:
        _global_trace = EpisodicTrace()
    return _global_trace


def set_trace(trace: EpisodicTrace):
    """Set global trace instance."""
    global _global_trace
    _global_trace = trace
