"""Bootstrap - First-Contact Protocol.

4-stage consent-based sequence:
1. Ladder Anchor (State)
2. Anchor (Stability)
3. Gap (One-step change)
4. Microstep + Permission (Handoff)

Operates in propose-only mode until consent received.
"""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

from locked_system.memory.slow import SlowMemory, BootstrapSnapshot
from locked_system.proposals.buffer import BootstrapTransitionProposal


class BootstrapStage(Enum):
    """Bootstrap stages."""
    LADDER = "ladder"           # Stage 1: Ladder anchor
    ANCHOR = "anchor"           # Stage 2: Stability
    GAP = "gap"                 # Stage 3: One-step change
    MICROSTEP = "microstep"     # Stage 4: Microstep + permission
    COMPLETE = "complete"       # Bootstrap complete


@dataclass
class BootstrapState:
    """Current bootstrap state."""
    stage: BootstrapStage
    ladder_position: Optional[Literal["top", "middle", "bottom"]] = None
    ladder_numeric: Optional[int] = None
    stabilizers: Optional[str] = None
    one_step_gap: Optional[str] = None
    microstep: Optional[str] = None
    consent_state: Literal["listen_only", "propose_structure", "ready_for_commitment"] = "listen_only"
    turns_in_bootstrap: int = 0
    hook_delivered: bool = False


class Bootstrap:
    """
    Bootstrap mode controller.

    Manages first-contact protocol with consent-based handoff.
    """

    STAGE_PROMPTS = {
        BootstrapStage.LADDER: (
            "Imagine a ladder where the top is the best possible life for you "
            "and the bottom is the worst. Where do you feel you're standing right now?"
        ),
        BootstrapStage.ANCHOR: (
            "What's currently happening that keeps you from slipping lower?"
        ),
        BootstrapStage.GAP: (
            "If you moved up just one step, what would be different in your day-to-day?"
        ),
        BootstrapStage.MICROSTEP: (
            "What's one small thing that would make you feel supported "
            "moving toward that next step?"
        ),
    }

    HANDOFF_PROMPT = (
        "Would you like me to keep listening, or would it help "
        "if I started offering structure and ideas?"
    )

    SOFT_TIMEOUT_TURNS = 10

    def __init__(self, slow_memory: SlowMemory):
        self.memory = slow_memory
        self._state: Optional[BootstrapState] = None
        self._load_or_init()

    def _load_or_init(self):
        """Load existing bootstrap or initialize new."""
        snapshot = self.memory.get_bootstrap()
        if snapshot and snapshot.consent_state == "listen_only":
            # Resume bootstrap
            self._state = BootstrapState(
                stage=self._infer_stage(snapshot),
                ladder_position=snapshot.ladder_position,
                stabilizers=snapshot.stabilizers if snapshot.stabilizers else None,
                one_step_gap=snapshot.one_step_gap if snapshot.one_step_gap else None,
                microstep=snapshot.microstep_candidate if snapshot.microstep_candidate else None,
                consent_state=snapshot.consent_state
            )
        else:
            # Start fresh
            self._state = BootstrapState(stage=BootstrapStage.LADDER)

    def _infer_stage(self, snapshot: BootstrapSnapshot) -> BootstrapStage:
        """Infer current stage from snapshot."""
        if snapshot.consent_state != "listen_only":
            return BootstrapStage.COMPLETE
        if snapshot.microstep_candidate:
            return BootstrapStage.COMPLETE
        if snapshot.one_step_gap:
            return BootstrapStage.MICROSTEP
        if snapshot.stabilizers:
            return BootstrapStage.GAP
        if snapshot.ladder_position:
            return BootstrapStage.ANCHOR
        return BootstrapStage.LADDER

    @property
    def is_active(self) -> bool:
        """Check if bootstrap is active."""
        return self._state is not None and self._state.stage != BootstrapStage.COMPLETE

    @property
    def current_stage(self) -> BootstrapStage:
        """Get current stage."""
        return self._state.stage if self._state else BootstrapStage.COMPLETE

    @property
    def consent_state(self) -> str:
        """Get consent state."""
        return self._state.consent_state if self._state else "ready_for_commitment"

    def get_current_prompt(self) -> str:
        """Get prompt for current stage."""
        if not self._state:
            return ""
        return self.STAGE_PROMPTS.get(self._state.stage, "")

    def process_input(self, user_input: str) -> dict:
        """
        Process user input during bootstrap.

        Returns dict with:
        - stage_complete: bool
        - next_prompt: str (if any)
        - transition_proposal: BootstrapTransitionProposal (if consent given)
        - hook: str (if appropriate)
        """
        if not self._state:
            return {"stage_complete": True, "next_prompt": "", "transition_proposal": None}

        self._state.turns_in_bootstrap += 1
        result = {"stage_complete": False, "next_prompt": "", "hook": None, "transition_proposal": None}

        # Check for explicit intent (fast-exit)
        if self._detect_explicit_intent(user_input):
            result["transition_proposal"] = BootstrapTransitionProposal(
                recommended_transition="offer_structure",
                reason="User expressed explicit intent for help",
                consent_state="propose_structure"
            )
            self._state.consent_state = "propose_structure"
            self._state.stage = BootstrapStage.COMPLETE
            self._save_snapshot()
            return result

        # Process based on stage
        if self._state.stage == BootstrapStage.LADDER:
            result = self._process_ladder(user_input)
        elif self._state.stage == BootstrapStage.ANCHOR:
            result = self._process_anchor(user_input)
        elif self._state.stage == BootstrapStage.GAP:
            result = self._process_gap(user_input)
        elif self._state.stage == BootstrapStage.MICROSTEP:
            result = self._process_microstep(user_input)

        # Check for soft timeout
        if self._state.turns_in_bootstrap >= self.SOFT_TIMEOUT_TURNS:
            result["next_prompt"] = self.HANDOFF_PROMPT

        self._save_snapshot()
        return result

    def _process_ladder(self, user_input: str) -> dict:
        """Process ladder stage input."""
        position = self._parse_ladder_position(user_input)
        self._state.ladder_position = position

        # Advance stage
        self._state.stage = BootstrapStage.ANCHOR

        result = {
            "stage_complete": True,
            "next_prompt": self.STAGE_PROMPTS[BootstrapStage.ANCHOR],
            "hook": None,
            "transition_proposal": None
        }

        return result

    def _process_anchor(self, user_input: str) -> dict:
        """Process anchor stage input."""
        self._state.stabilizers = user_input

        # Deliver hook if not yet delivered
        hook = None
        if not self._state.hook_delivered:
            hook = self._generate_hook()
            self._state.hook_delivered = True

        # Advance stage
        self._state.stage = BootstrapStage.GAP

        return {
            "stage_complete": True,
            "next_prompt": self.STAGE_PROMPTS[BootstrapStage.GAP],
            "hook": hook,
            "transition_proposal": None
        }

    def _process_gap(self, user_input: str) -> dict:
        """Process gap stage input."""
        self._state.one_step_gap = user_input

        # Advance stage
        self._state.stage = BootstrapStage.MICROSTEP

        return {
            "stage_complete": True,
            "next_prompt": self.STAGE_PROMPTS[BootstrapStage.MICROSTEP],
            "hook": None,
            "transition_proposal": None
        }

    def _process_microstep(self, user_input: str) -> dict:
        """Process microstep stage input."""
        self._state.microstep = user_input

        # Check for consent in response
        if self._detect_consent(user_input):
            self._state.consent_state = "propose_structure"
            self._state.stage = BootstrapStage.COMPLETE
            return {
                "stage_complete": True,
                "next_prompt": "",
                "hook": None,
                "transition_proposal": BootstrapTransitionProposal(
                    recommended_transition="offer_structure",
                    reason="User consented to structure",
                    consent_state="propose_structure"
                )
            }

        # Otherwise, ask for handoff
        return {
            "stage_complete": True,
            "next_prompt": self.HANDOFF_PROMPT,
            "hook": None,
            "transition_proposal": None
        }

    def _parse_ladder_position(self, user_input: str) -> Literal["top", "middle", "bottom"]:
        """Parse ladder position from input."""
        lower = user_input.lower()

        # Check for explicit position words
        if any(w in lower for w in ["top", "high", "great", "good", "well"]):
            return "top"
        elif any(w in lower for w in ["bottom", "low", "bad", "worst", "terrible"]):
            return "bottom"
        elif any(w in lower for w in ["middle", "okay", "fine", "alright", "so-so"]):
            return "middle"

        # Check for numeric
        for word in lower.split():
            try:
                num = int(word)
                if num >= 8:
                    return "top"
                elif num <= 3:
                    return "bottom"
                else:
                    return "middle"
            except ValueError:
                continue

        # Default to middle
        return "middle"

    def _detect_explicit_intent(self, user_input: str) -> bool:
        """Detect explicit intent for help (fast-exit)."""
        intent_signals = [
            "help me", "i need help", "can you help",
            "plan", "planning", "schedule",
            "organize", "structure",
            "what should i", "how do i"
        ]
        lower = user_input.lower()
        return any(signal in lower for signal in intent_signals)

    def _detect_consent(self, user_input: str) -> bool:
        """Detect consent for structure/ideas."""
        consent_signals = [
            "yes", "sure", "okay", "please",
            "structure", "ideas", "help",
            "go ahead", "that would help"
        ]
        lower = user_input.lower()
        return any(signal in lower for signal in consent_signals)

    def _generate_hook(self) -> str:
        """Generate identity-affirming hook based on ladder position."""
        position = self._state.ladder_position

        hooks = {
            "top": "It sounds like things are in a good place. That clarity is worth protecting.",
            "middle": "Being honest about where you are takes awareness. That's real.",
            "bottom": "You're still here, still trying. That matters."
        }

        return hooks.get(position, "")

    def _save_snapshot(self):
        """Save current state to snapshot."""
        if not self._state:
            return

        snapshot = BootstrapSnapshot(
            bootstrap_timestamp=datetime.now(),
            ladder_position=self._state.ladder_position or "middle",
            user_state_summary="",
            stabilizers=self._state.stabilizers or "",
            one_step_gap=self._state.one_step_gap or "",
            microstep_candidate=self._state.microstep or "",
            consent_state=self._state.consent_state
        )
        self.memory.set_bootstrap(snapshot)

    def complete_with_consent(self, consent: str):
        """Complete bootstrap with given consent state."""
        if self._state:
            self._state.consent_state = consent
            self._state.stage = BootstrapStage.COMPLETE
            self._save_snapshot()

    def get_state_summary(self) -> dict:
        """Get bootstrap state summary."""
        if not self._state:
            return {"active": False}

        return {
            "active": self.is_active,
            "stage": self._state.stage.value,
            "ladder_position": self._state.ladder_position,
            "consent_state": self._state.consent_state,
            "turns": self._state.turns_in_bootstrap
        }
