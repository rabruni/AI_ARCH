"""Lane Store - In-memory lane management with persistence support.

Provides:
- Single active lane enforcement
- Lane lifecycle management (create, activate, pause, resume, complete)
- Paused lane limits to prevent lane explosion
- Persistence hooks for later implementation
"""

from typing import Optional, Dict, List
from datetime import datetime
import json
import os

from locked_system.lanes.models import Lane, LaneKind, LaneStatus, LanePolicy, LaneBudgets


class LaneStore:
    """
    In-memory lane store (V1).

    Invariants:
    - Only one lane may be active at a time
    - Paused lanes are capped (default 5) to prevent explosion
    - Lane IDs must be unique
    """

    MAX_PAUSED_LANES = 5

    def __init__(self, persistence_path: Optional[str] = None):
        self._lanes: Dict[str, Lane] = {}
        self._active_lane_id: Optional[str] = None
        self._persistence_path = persistence_path

        # Load persisted state if available
        if persistence_path and os.path.exists(persistence_path):
            self._load()

    # ---------- Query Methods ----------

    def get_active(self) -> Optional[Lane]:
        """Get the currently active lane."""
        if self._active_lane_id:
            return self._lanes.get(self._active_lane_id)
        return None

    def get(self, lane_id: str) -> Optional[Lane]:
        """Get a lane by ID."""
        return self._lanes.get(lane_id)

    def get_paused(self) -> List[Lane]:
        """Get all paused lanes."""
        return [l for l in self._lanes.values() if l.status == LaneStatus.PAUSED]

    def get_all(self) -> List[Lane]:
        """Get all lanes (active, paused, completed)."""
        return list(self._lanes.values())

    def has_active(self) -> bool:
        """Check if there's an active lane."""
        return self._active_lane_id is not None

    def count_paused(self) -> int:
        """Count paused lanes."""
        return len(self.get_paused())

    # ---------- Lifecycle Methods ----------

    def create(
        self,
        kind: LaneKind,
        goal: str,
        mode: str = "execution",
        expires_hours: int = 4,
        policy: Optional[LanePolicy] = None,
        budgets: Optional[LaneBudgets] = None,
        auto_activate: bool = True,
    ) -> Lane:
        """
        Create a new lane.

        If auto_activate is True and there's no active lane, activates it.
        If there's already an active lane, the new lane starts paused.

        Raises:
            ValueError: If paused lane limit exceeded
        """
        # Check paused lane limit (prevents lane explosion)
        if self.count_paused() >= self.MAX_PAUSED_LANES:
            raise ValueError(
                f"Cannot create lane: {self.count_paused()} paused lanes already exist. "
                f"Complete or remove paused lanes first (max {self.MAX_PAUSED_LANES})."
            )

        lane = Lane.create(
            kind=kind,
            goal=goal,
            mode=mode,
            expires_hours=expires_hours,
            policy=policy,
            budgets=budgets,
        )

        # If there's an active lane, new lane starts paused
        if self.has_active():
            lane.status = LaneStatus.PAUSED
        elif auto_activate:
            self._active_lane_id = lane.lane_id

        self._lanes[lane.lane_id] = lane
        self._persist()

        return lane

    def activate(self, lane_id: str) -> Lane:
        """
        Activate a lane, pausing the current active lane.

        This is the implementation behind LaneSwitchGate.

        Raises:
            ValueError: If lane not found or already completed
        """
        lane = self._lanes.get(lane_id)
        if not lane:
            raise ValueError(f"Lane {lane_id} not found")

        if lane.status == LaneStatus.COMPLETED:
            raise ValueError(f"Cannot activate completed lane {lane_id}")

        # Pause current active lane if exists
        current = self.get_active()
        if current and current.lane_id != lane_id:
            # Don't auto-pause - requires bookmark via pause()
            raise ValueError(
                f"Cannot activate {lane_id}: lane {current.lane_id} is active. "
                f"Pause it first with a bookmark."
            )

        lane.resume() if lane.status == LaneStatus.PAUSED else None
        lane.status = LaneStatus.ACTIVE
        self._active_lane_id = lane.lane_id
        self._persist()

        return lane

    def pause(
        self,
        lane_id: str,
        bookmark: str,
        next_steps: List[str] = None,
        open_questions: List[str] = None,
    ) -> Lane:
        """
        Pause a lane with a snapshot.

        Raises:
            ValueError: If lane not found or not active
        """
        lane = self._lanes.get(lane_id)
        if not lane:
            raise ValueError(f"Lane {lane_id} not found")

        if lane.status != LaneStatus.ACTIVE:
            raise ValueError(f"Cannot pause lane in status {lane.status}")

        lane.pause(bookmark, next_steps, open_questions)

        if self._active_lane_id == lane_id:
            self._active_lane_id = None

        self._persist()
        return lane

    def resume(self, lane_id: str) -> Lane:
        """
        Resume a paused lane, making it active.

        Raises:
            ValueError: If lane not found, not paused, or another lane is active
        """
        lane = self._lanes.get(lane_id)
        if not lane:
            raise ValueError(f"Lane {lane_id} not found")

        if lane.status != LaneStatus.PAUSED:
            raise ValueError(f"Cannot resume lane in status {lane.status}")

        if self.has_active():
            current = self.get_active()
            raise ValueError(
                f"Cannot resume {lane_id}: lane {current.lane_id} is active. "
                f"Pause it first."
            )

        lane.resume()
        self._active_lane_id = lane.lane_id
        self._persist()

        return lane

    def complete(self, lane_id: str, final_summary: str = None) -> Lane:
        """
        Complete and seal a lane.

        Raises:
            ValueError: If lane not found
        """
        lane = self._lanes.get(lane_id)
        if not lane:
            raise ValueError(f"Lane {lane_id} not found")

        was_active = (self._active_lane_id == lane_id)
        lane.complete(final_summary)

        if was_active:
            self._active_lane_id = None

        self._persist()
        return lane

    def remove(self, lane_id: str) -> bool:
        """
        Remove a completed lane from the store.

        Only completed lanes can be removed.

        Returns:
            True if removed, False if not found or not completed
        """
        lane = self._lanes.get(lane_id)
        if not lane or lane.status != LaneStatus.COMPLETED:
            return False

        del self._lanes[lane_id]
        self._persist()
        return True

    # ---------- Budget Enforcement ----------

    def check_budget(self, lane_id: str, tool_requests: int) -> bool:
        """
        Check if tool request count is within lane budget.

        Returns:
            True if within budget, False otherwise
        """
        lane = self._lanes.get(lane_id)
        if not lane:
            return False
        return tool_requests <= lane.budgets.max_tool_requests_per_turn

    def get_budgets(self, lane_id: str) -> Optional[LaneBudgets]:
        """Get budgets for a lane."""
        lane = self._lanes.get(lane_id)
        return lane.budgets if lane else None

    # ---------- Lease Management ----------

    def check_expired_leases(self) -> List[Lane]:
        """
        Check for lanes with expired leases.

        Returns list of lanes needing EvaluationGate to renew/close.
        """
        expired = []
        for lane in self._lanes.values():
            if lane.status == LaneStatus.ACTIVE and lane.is_lease_expired():
                expired.append(lane)
        return expired

    def renew_lease(self, lane_id: str, expires_hours: int = 4) -> Lane:
        """
        Renew a lane's lease.

        Raises:
            ValueError: If lane not found
        """
        from datetime import timedelta

        lane = self._lanes.get(lane_id)
        if not lane:
            raise ValueError(f"Lane {lane_id} not found")

        lane.lease.expires_at_utc = datetime.utcnow() + timedelta(hours=expires_hours)
        lane.updated_at = datetime.utcnow()
        self._persist()

        return lane

    # ---------- Persistence ----------

    def _persist(self):
        """Persist state to disk if path configured."""
        if not self._persistence_path:
            return

        data = {
            'active_lane_id': self._active_lane_id,
            'lanes': {lid: lane.to_dict() for lid, lane in self._lanes.items()},
        }

        os.makedirs(os.path.dirname(self._persistence_path), exist_ok=True)
        with open(self._persistence_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load state from disk."""
        if not self._persistence_path or not os.path.exists(self._persistence_path):
            return

        try:
            with open(self._persistence_path, 'r') as f:
                data = json.load(f)

            self._active_lane_id = data.get('active_lane_id')
            self._lanes = {
                lid: Lane.from_dict(ldata)
                for lid, ldata in data.get('lanes', {}).items()
            }
        except (json.JSONDecodeError, KeyError) as e:
            # Corrupted file - start fresh
            self._lanes = {}
            self._active_lane_id = None

    # ---------- Context for Tagging ----------

    def get_lane_context(self) -> dict:
        """
        Get current lane context for tagging packets/requests.

        Returns dict with lane_id and budgets if active lane exists.
        """
        lane = self.get_active()
        if not lane:
            return {'lane_id': None, 'budgets': None}

        return {
            'lane_id': lane.lane_id,
            'budgets': lane.budgets.to_dict(),
            'lease_mode': lane.lease.mode,
            'lease_goal': lane.lease.goal,
        }
