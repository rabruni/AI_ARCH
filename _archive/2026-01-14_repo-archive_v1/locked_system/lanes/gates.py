"""Lane Gates - Structured checkpoints for lane operations.

Gates are typed checkpoints that:
- Request user input
- Update lane state (pause/resume)
- Produce obligations for the executor

Agents may only REQUEST gates; executor RUNS them.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

from locked_system.lanes.models import Lane, LaneKind, LaneStatus, LanePolicy, LaneBudgets


class LaneSwitchDecision(Enum):
    """Possible decisions from LaneSwitchGate."""
    SWITCH = "switch"           # Switch to new/existing lane
    DEFER = "defer"             # Schedule for later, stay in current
    MICRO_CHECK = "micro_check" # Quick check (< 60s), no writes, no switch
    CANCEL = "cancel"           # User cancelled the switch


@dataclass
class GateResult:
    """Result from gate execution."""
    approved: bool
    decision: Optional[str] = None
    lane_id: Optional[str] = None
    obligations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkDeclarationGate:
    """
    Gate for declaring/activating a work lane.

    Triggers:
    - User starts formal work (detected by front-door)
    - Explicit work declaration command

    Produces:
    - New lane creation OR activation of existing paused lane
    - Lane kind selection
    - Lease configuration (mode, duration, goal)
    """

    # Input context
    detected_kind: Optional[LaneKind] = None
    detected_goal: Optional[str] = None
    is_ideation: bool = False  # True = evaluation mode, False = execution mode
    emotional_signals: Optional[Dict[str, str]] = None

    # User-provided overrides (from gate prompt response)
    user_kind: Optional[LaneKind] = None
    user_goal: Optional[str] = None
    user_mode: Optional[str] = None
    user_duration_hours: Optional[int] = None

    def generate_prompt(self, paused_lanes: List[Lane] = None) -> dict:
        """
        Generate gate prompt for user.

        Returns dict with:
        - message: Human-readable prompt
        - options: Available choices
        - defaults: Suggested defaults based on detection
        """
        paused_lanes = paused_lanes or []

        # Build options
        options = []

        # Option 1: Resume a paused lane
        for lane in paused_lanes:
            if lane.kind == self.detected_kind:
                options.append({
                    'type': 'resume',
                    'lane_id': lane.lane_id,
                    'label': f"Resume: {lane.snapshot.bookmark[:50]}..." if lane.snapshot.bookmark else f"Resume {lane.kind.value} lane",
                    'lane': lane,
                })

        # Option 2: Create new lane
        options.append({
            'type': 'create',
            'label': f"Start new {(self.detected_kind or LaneKind.WRITING).value} lane",
            'kind': self.detected_kind or LaneKind.WRITING,
        })

        # Option 3: Different lane kind
        for kind in LaneKind:
            if kind != self.detected_kind:
                options.append({
                    'type': 'create',
                    'label': f"Start new {kind.value} lane",
                    'kind': kind,
                })

        return {
            'message': self._build_message(),
            'options': options[:5],  # Cap at 5 options
            'defaults': {
                'kind': self.detected_kind or LaneKind.WRITING,
                'goal': self.detected_goal or "Work session",
                'mode': 'evaluation' if self.is_ideation else 'execution',
                'duration_hours': 4,
            },
        }

    def _build_message(self) -> str:
        """Build user-facing gate message."""
        if self.detected_goal:
            return f"Starting work: {self.detected_goal}\n\nHow would you like to proceed?"
        return "It looks like you're starting formal work.\n\nHow would you like to proceed?"

    def execute(self, store: 'LaneStore', user_response: dict = None) -> GateResult:
        """
        Execute the gate and create/activate lane.

        Args:
            store: LaneStore instance
            user_response: User's selection from gate prompt

        Returns:
            GateResult with new/activated lane info
        """
        response = user_response or {}

        # Determine action
        action_type = response.get('type', 'create')
        lane_id = response.get('lane_id')

        if action_type == 'resume' and lane_id:
            # Resume existing lane
            try:
                lane = store.resume(lane_id)
                return GateResult(
                    approved=True,
                    decision='resume',
                    lane_id=lane.lane_id,
                    obligations=['present_bookmark'],
                    metadata={'bookmark': lane.snapshot.bookmark, 'next_steps': lane.snapshot.next_steps},
                )
            except ValueError as e:
                return GateResult(approved=False, metadata={'error': str(e)})

        elif action_type == 'create':
            # Create new lane
            kind = response.get('kind') or self.user_kind or self.detected_kind or LaneKind.WRITING
            goal = response.get('goal') or self.user_goal or self.detected_goal or "Work session"
            mode = response.get('mode') or self.user_mode or ('evaluation' if self.is_ideation else 'execution')
            hours = response.get('duration_hours') or self.user_duration_hours or 4

            try:
                lane = store.create(
                    kind=kind,
                    goal=goal,
                    mode=mode,
                    expires_hours=hours,
                )
                return GateResult(
                    approved=True,
                    decision='create',
                    lane_id=lane.lane_id,
                    obligations=[],
                    metadata={'kind': kind.value, 'goal': goal, 'mode': mode},
                )
            except ValueError as e:
                return GateResult(approved=False, metadata={'error': str(e)})

        return GateResult(approved=False, metadata={'error': 'Invalid action type'})


@dataclass
class LaneSwitchGate:
    """
    Gate for switching lanes or handling interrupts.

    Triggers:
    - User requests different work type
    - Interrupt detected (urgent message, topic change)
    - Explicit lane switch command

    Produces:
    - Pause current lane with bookmark
    - Switch to new/existing lane OR defer OR micro-check
    """

    # Current context
    current_lane_id: Optional[str] = None
    current_kind: Optional[LaneKind] = None

    # Interrupt context
    interrupt_kind: Optional[LaneKind] = None
    interrupt_goal: Optional[str] = None
    interrupt_urgency: str = "none"  # none|elevated|critical
    is_micro_check_eligible: bool = False

    # Emotional context (routing only)
    emotional_signals: Optional[Dict[str, str]] = None

    def generate_prompt(
        self,
        current_lane: Optional[Lane],
        paused_lanes: List[Lane] = None,
    ) -> dict:
        """
        Generate gate prompt for user.

        If flow=true in emotional_signals, recommends defer.
        If urgency=critical, recommends switch.
        """
        paused_lanes = paused_lanes or []
        flow_state = (self.emotional_signals or {}).get('flow', 'false')

        options = []

        # Option 1: Switch (create new or resume existing)
        if self.interrupt_kind and any(l.kind == self.interrupt_kind for l in paused_lanes):
            matching = next(l for l in paused_lanes if l.kind == self.interrupt_kind)
            options.append({
                'type': 'switch',
                'decision': LaneSwitchDecision.SWITCH,
                'lane_id': matching.lane_id,
                'label': f"Switch to: {matching.snapshot.bookmark[:40]}..." if matching.snapshot.bookmark else f"Switch to {matching.kind.value} lane",
            })
        else:
            options.append({
                'type': 'switch',
                'decision': LaneSwitchDecision.SWITCH,
                'label': f"Switch to new {(self.interrupt_kind or LaneKind.WRITING).value} lane",
                'create_new': True,
            })

        # Option 2: Defer (recommended if flow=true)
        defer_label = "Defer for later"
        if flow_state == 'true':
            defer_label = "Defer for later (recommended - you're in flow)"
        options.append({
            'type': 'defer',
            'decision': LaneSwitchDecision.DEFER,
            'label': defer_label,
        })

        # Option 3: Micro-check (if eligible)
        if self.is_micro_check_eligible:
            options.append({
                'type': 'micro_check',
                'decision': LaneSwitchDecision.MICRO_CHECK,
                'label': "Quick check (< 60s, read-only)",
            })

        # Option 4: Cancel
        options.append({
            'type': 'cancel',
            'decision': LaneSwitchDecision.CANCEL,
            'label': "Stay in current lane",
        })

        return {
            'message': self._build_message(current_lane),
            'options': options,
            'recommendation': self._get_recommendation(),
        }

    def _build_message(self, current_lane: Optional[Lane]) -> str:
        """Build user-facing gate message."""
        current_desc = ""
        if current_lane:
            current_desc = f"Current: {current_lane.kind.value} - {current_lane.lease.goal}\n\n"

        if self.interrupt_urgency == 'critical':
            return f"{current_desc}Urgent interrupt detected: {self.interrupt_goal or 'new request'}\n\nHow would you like to handle this?"

        return f"{current_desc}Switching context: {self.interrupt_goal or 'different work detected'}\n\nHow would you like to proceed?"

    def _get_recommendation(self) -> str:
        """Get recommendation based on signals."""
        flow = (self.emotional_signals or {}).get('flow', 'false')

        if self.interrupt_urgency == 'critical':
            return 'switch'
        if flow == 'true':
            return 'defer'
        return 'switch'

    def execute(
        self,
        store: 'LaneStore',
        user_response: dict,
        bookmark: str = None,
        next_steps: List[str] = None,
        open_questions: List[str] = None,
    ) -> GateResult:
        """
        Execute the gate and perform lane operation.

        Args:
            store: LaneStore instance
            user_response: User's selection from gate prompt
            bookmark: Summary of current work (required for switch)
            next_steps: What was planned next
            open_questions: Unresolved questions

        Returns:
            GateResult with decision outcome
        """
        decision = user_response.get('decision', LaneSwitchDecision.CANCEL)

        if decision == LaneSwitchDecision.CANCEL:
            return GateResult(
                approved=True,
                decision='cancel',
                lane_id=self.current_lane_id,
            )

        if decision == LaneSwitchDecision.DEFER:
            # No lane change, just log the deferred item
            return GateResult(
                approved=True,
                decision='defer',
                lane_id=self.current_lane_id,
                obligations=['schedule_deferred'],
                metadata={'deferred_goal': self.interrupt_goal, 'deferred_kind': self.interrupt_kind.value if self.interrupt_kind else None},
            )

        if decision == LaneSwitchDecision.MICRO_CHECK:
            # Temporary read-only context, no lane change
            return GateResult(
                approved=True,
                decision='micro_check',
                lane_id=self.current_lane_id,
                obligations=['enforce_read_only', 'time_limit_60s'],
                metadata={'micro_check_goal': self.interrupt_goal},
            )

        if decision == LaneSwitchDecision.SWITCH:
            # Pause current lane (requires bookmark)
            if self.current_lane_id and not bookmark:
                return GateResult(
                    approved=False,
                    metadata={'error': 'Bookmark required to pause current lane'},
                )

            try:
                # Pause current if exists
                if self.current_lane_id:
                    store.pause(
                        self.current_lane_id,
                        bookmark=bookmark or "Interrupted",
                        next_steps=next_steps,
                        open_questions=open_questions,
                    )

                # Create or resume target lane
                target_lane_id = user_response.get('lane_id')
                create_new = user_response.get('create_new', False)

                if target_lane_id:
                    lane = store.resume(target_lane_id)
                    return GateResult(
                        approved=True,
                        decision='switch_resume',
                        lane_id=lane.lane_id,
                        obligations=['present_bookmark'],
                        metadata={'bookmark': lane.snapshot.bookmark},
                    )
                elif create_new:
                    lane = store.create(
                        kind=self.interrupt_kind or LaneKind.WRITING,
                        goal=self.interrupt_goal or "New work",
                    )
                    return GateResult(
                        approved=True,
                        decision='switch_create',
                        lane_id=lane.lane_id,
                    )

            except ValueError as e:
                return GateResult(approved=False, metadata={'error': str(e)})

        return GateResult(approved=False, metadata={'error': 'Unknown decision'})


@dataclass
class EvaluationGate:
    """
    Gate for evaluating lane lease expiry.

    Triggers:
    - Lease expires_at_utc has passed

    Produces:
    - Lease renewal OR lane completion
    """

    lane_id: str
    current_goal: str
    expired_at: datetime

    def generate_prompt(self, lane: Lane) -> dict:
        """Generate gate prompt for user."""
        return {
            'message': f"Your lease on '{self.current_goal}' has expired.\n\nWould you like to continue or wrap up?",
            'options': [
                {'type': 'renew', 'label': 'Continue (renew for 4 more hours)', 'hours': 4},
                {'type': 'renew', 'label': 'Continue (renew for 1 hour)', 'hours': 1},
                {'type': 'complete', 'label': 'Wrap up and complete lane'},
            ],
        }

    def execute(self, store: 'LaneStore', user_response: dict, final_summary: str = None) -> GateResult:
        """Execute the gate."""
        action = user_response.get('type', 'complete')

        try:
            if action == 'renew':
                hours = user_response.get('hours', 4)
                lane = store.renew_lease(self.lane_id, expires_hours=hours)
                return GateResult(
                    approved=True,
                    decision='renew',
                    lane_id=lane.lane_id,
                    metadata={'new_expires': lane.lease.expires_at_utc.isoformat()},
                )
            else:
                lane = store.complete(self.lane_id, final_summary)
                return GateResult(
                    approved=True,
                    decision='complete',
                    lane_id=lane.lane_id,
                )
        except ValueError as e:
            return GateResult(approved=False, metadata={'error': str(e)})
