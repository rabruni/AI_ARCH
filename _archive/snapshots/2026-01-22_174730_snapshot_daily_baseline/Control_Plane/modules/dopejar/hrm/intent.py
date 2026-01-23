"""HRM Layer 1: Intent Store

The foundation. Tiny. Stable. High authority.

This layer:
- Defines what success looks like
- Declares what we will NOT do (non-goals)
- Holds values and priorities
- Decides when to stop

Memory: Stable, low-frequency, very small, HIGH AUTHORITY.

Intent outranks all other layers. If execution drifts, intent pulls back.
"""
import os
import json
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


# Intent memory location - separate from other memory
HRM_DIR = Path(__file__).parent / "memory"


@dataclass
class Intent:
    """The intent structure. Intentionally small."""
    north_stars: list[str]          # Identity-level priorities (max 5)
    current_success: str            # What success looks like RIGHT NOW
    non_goals: list[str]            # What we will NOT do (hard constraints)
    stop_conditions: list[str]      # When to stop/redirect
    stance: str                     # Current stance: partner | support | challenge


class IntentStore:
    """
    L1: The authority layer.

    This is NOT an agent. It's a store with authority.
    Other layers read from it. Only humans modify it.
    """

    def __init__(self):
        self.intent_file = HRM_DIR / "intent.json"
        self._ensure_exists()

    def _ensure_exists(self):
        """Ensure intent file exists with defaults."""
        HRM_DIR.mkdir(parents=True, exist_ok=True)
        if not self.intent_file.exists():
            self._save(self._default_intent())

    def _default_intent(self) -> Intent:
        """Default intent - the DoPeJar foundation."""
        return Intent(
            north_stars=[
                "family_present",
                "meaningful_tech",
                "financial_independence"
            ],
            current_success="Be a cognitive partner who challenges and grounds, not a task manager who complies",
            non_goals=[
                "endless_analysis",
                "feature_stacking",
                "sycophancy",
                "tactical_without_strategic",
                "compliance_over_partnership"
            ],
            stop_conditions=[
                "user_says_stop",
                "frustration_detected",
                "goal_achieved",
                "stuck_in_loop"
            ],
            stance="partner"
        )

    def _load(self) -> Intent:
        """Load intent from file."""
        with open(self.intent_file, 'r') as f:
            data = json.load(f)
        return Intent(**data)

    def _save(self, intent: Intent):
        """Save intent to file."""
        with open(self.intent_file, 'w') as f:
            json.dump(asdict(intent), f, indent=2)

    # ========================================
    # READ INTERFACE (used by other layers)
    # ========================================

    def get_intent(self) -> Intent:
        """Get current intent. Used by Planner and Evaluator."""
        return self._load()

    def get_success_criteria(self) -> str:
        """What does success look like?"""
        return self._load().current_success

    def get_non_goals(self) -> list[str]:
        """What will we NOT do? Hard constraints."""
        return self._load().non_goals

    def get_stop_conditions(self) -> list[str]:
        """When should we stop or redirect?"""
        return self._load().stop_conditions

    def get_stance(self) -> str:
        """Current stance: partner | support | challenge"""
        return self._load().stance

    def get_north_stars(self) -> list[str]:
        """Identity-level priorities."""
        return self._load().north_stars

    # ========================================
    # AUTHORITY CHECKS
    # ========================================

    def is_non_goal(self, action: str) -> bool:
        """Check if an action violates non-goals."""
        non_goals = self.get_non_goals()
        action_lower = action.lower()
        for ng in non_goals:
            if ng.replace("_", " ") in action_lower or ng in action_lower:
                return True
        return False

    def should_stop(self, signal: str) -> bool:
        """Check if a stop condition is met."""
        conditions = self.get_stop_conditions()
        signal_lower = signal.lower()
        for cond in conditions:
            if cond.replace("_", " ") in signal_lower or cond in signal_lower:
                return True
        return False

    def check_alignment(self, outcome: str) -> dict:
        """
        Check if an outcome aligns with intent.
        Returns alignment assessment.
        """
        intent = self._load()

        # Check against non-goals
        for ng in intent.non_goals:
            if ng.replace("_", " ") in outcome.lower():
                return {
                    "aligned": False,
                    "violation": ng,
                    "type": "non_goal"
                }

        # Check against success criteria
        # (This is a simple check - Evaluator does deeper analysis)
        return {
            "aligned": True,
            "success_criteria": intent.current_success
        }

    # ========================================
    # MODIFICATION (only by explicit user action)
    # ========================================

    def set_north_stars(self, stars: list[str]):
        """Set north stars. User action only."""
        intent = self._load()
        intent.north_stars = stars[:5]  # Max 5
        self._save(intent)

    def set_success(self, success: str):
        """Set current success criteria. User action only."""
        intent = self._load()
        intent.current_success = success
        self._save(intent)

    def add_non_goal(self, non_goal: str):
        """Add a non-goal. User action only."""
        intent = self._load()
        if non_goal not in intent.non_goals:
            intent.non_goals.append(non_goal)
        self._save(intent)

    def set_stance(self, stance: str):
        """Set current stance. User action only."""
        if stance not in ["partner", "support", "challenge"]:
            raise ValueError(f"Invalid stance: {stance}")
        intent = self._load()
        intent.stance = stance
        self._save(intent)

    # ========================================
    # CONTEXT FOR OTHER LAYERS
    # ========================================

    def build_context_for_planner(self) -> str:
        """Build minimal context for Planner layer."""
        intent = self._load()
        return f"""INTENT (L1 - AUTHORITY):
SUCCESS: {intent.current_success}
NORTH_STARS: {', '.join(intent.north_stars)}
NON_GOALS: {', '.join(intent.non_goals)}
STANCE: {intent.stance}
STOP_IF: {', '.join(intent.stop_conditions)}"""

    def build_context_for_evaluator(self) -> str:
        """Build minimal context for Evaluator layer."""
        intent = self._load()
        return f"""INTENT TO EVALUATE AGAINST:
SUCCESS_CRITERIA: {intent.current_success}
NON_GOALS (violations): {', '.join(intent.non_goals)}
STANCE_EXPECTED: {intent.stance}"""
