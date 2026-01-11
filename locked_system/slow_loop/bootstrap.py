"""Bootstrap - First-Contact Protocol.

Simple 2-stage introduction:
1. Intro - Introduce itself as cognitive partner, ask what to call user
2. Connect - Ask about two favorite things to start learning

After bootstrap, transitions to normal operation.
"""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from locked_system.memory.slow import SlowMemory, BootstrapSnapshot
from locked_system.proposals.buffer import BootstrapTransitionProposal


class BootstrapStage(Enum):
    """Bootstrap stages."""
    INTRO = "intro"           # Stage 1: Introduction, ask name
    CONNECT = "connect"       # Stage 2: Ask favorite things
    COMPLETE = "complete"     # Bootstrap complete


@dataclass
class BootstrapState:
    """Current bootstrap state."""
    stage: BootstrapStage
    user_name: Optional[str] = None
    favorite_things: Optional[list] = None
    turns_in_bootstrap: int = 0


class Bootstrap:
    """
    Bootstrap mode controller.

    Simple 2-stage first-contact protocol.
    """

    INTRO_GREETING = (
        "Hey! I'm your Assist - think of me as a cognitive partner, not just a task manager. "
        "I'm here to help you think, remember what matters, and challenge you when needed. "
        "We'll build trust over time. First though - what would you like me to call you?"
    )

    CONNECT_PROMPT = (
        "What are two things you're really into right now? "
        "Could be projects, hobbies, ideas - whatever's got your attention."
    )

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
                user_name=snapshot.user_state_summary if snapshot.user_state_summary else None,
                favorite_things=snapshot.stabilizers.split("|") if snapshot.stabilizers else None
            )
        else:
            # Start fresh
            self._state = BootstrapState(stage=BootstrapStage.INTRO)

    def _infer_stage(self, snapshot: BootstrapSnapshot) -> BootstrapStage:
        """Infer current stage from snapshot."""
        if snapshot.consent_state != "listen_only":
            return BootstrapStage.COMPLETE
        if snapshot.stabilizers:  # Has favorite things
            return BootstrapStage.COMPLETE
        if snapshot.user_state_summary:  # Has name
            return BootstrapStage.CONNECT
        return BootstrapStage.INTRO

    @property
    def is_active(self) -> bool:
        """Check if bootstrap is active."""
        return self._state is not None and self._state.stage != BootstrapStage.COMPLETE

    @property
    def current_stage(self) -> BootstrapStage:
        """Get current stage."""
        return self._state.stage if self._state else BootstrapStage.COMPLETE

    def get_current_prompt(self) -> str:
        """Get prompt for current stage."""
        if not self._state:
            return ""
        if self._state.stage == BootstrapStage.INTRO:
            return self.INTRO_GREETING
        elif self._state.stage == BootstrapStage.CONNECT:
            return self.CONNECT_PROMPT
        return ""

    def get_user_name(self) -> Optional[str]:
        """Get the user's name if known."""
        return self._state.user_name if self._state else None

    def process_input(self, user_input: str) -> dict:
        """
        Process user input during bootstrap.

        Returns dict with:
        - next_prompt: str (if any)
        - transition_proposal: BootstrapTransitionProposal (if complete)
        - user_name: str (if captured)
        """
        if not self._state:
            return {"next_prompt": "", "transition_proposal": None}

        self._state.turns_in_bootstrap += 1
        result = {"next_prompt": "", "transition_proposal": None, "user_name": None}

        if self._state.stage == BootstrapStage.INTRO:
            # Capture name from response
            self._state.user_name = self._extract_name(user_input)
            result["user_name"] = self._state.user_name

            # Move to connect stage
            self._state.stage = BootstrapStage.CONNECT
            result["next_prompt"] = self.CONNECT_PROMPT

        elif self._state.stage == BootstrapStage.CONNECT:
            # Capture favorite things
            self._state.favorite_things = self._extract_interests(user_input)

            # Bootstrap complete!
            self._state.stage = BootstrapStage.COMPLETE
            result["transition_proposal"] = BootstrapTransitionProposal(
                recommended_transition="ready",
                reason="Bootstrap complete - user introduced",
                consent_state="ready_for_commitment"
            )

        self._save_snapshot()
        return result

    def _extract_name(self, user_input: str) -> str:
        """Extract name from user input."""
        # Simple extraction - take the main word(s)
        # Remove common phrases
        cleaned = user_input.lower()
        for phrase in ["call me", "i'm", "my name is", "i am", "you can call me", "just"]:
            cleaned = cleaned.replace(phrase, "")

        # Get the remaining words, capitalize first letter of each
        words = cleaned.strip().split()
        if words:
            return " ".join(w.capitalize() for w in words[:2])  # Max 2 words
        return user_input.strip()[:20]  # Fallback

    def _extract_interests(self, user_input: str) -> list:
        """Extract interests from user input."""
        # Just store the raw input for now - the AI can parse it
        return [user_input]

    def _save_snapshot(self):
        """Save current state to snapshot."""
        if not self._state:
            return

        snapshot = BootstrapSnapshot(
            bootstrap_timestamp=datetime.now(),
            ladder_position="middle",  # Not used in new bootstrap
            user_state_summary=self._state.user_name or "",
            stabilizers="|".join(self._state.favorite_things) if self._state.favorite_things else "",
            one_step_gap="",
            microstep_candidate="",
            consent_state="listen_only" if self._state.stage != BootstrapStage.COMPLETE else "ready_for_commitment"
        )
        self.memory.set_bootstrap(snapshot)

    def complete(self):
        """Force complete bootstrap."""
        if self._state:
            self._state.stage = BootstrapStage.COMPLETE
            self._save_snapshot()

    def get_state_summary(self) -> dict:
        """Get bootstrap state summary."""
        if not self._state:
            return {"active": False}

        return {
            "active": self.is_active,
            "stage": self._state.stage.value,
            "user_name": self._state.user_name,
            "favorite_things": self._state.favorite_things,
            "turns": self._state.turns_in_bootstrap
        }
