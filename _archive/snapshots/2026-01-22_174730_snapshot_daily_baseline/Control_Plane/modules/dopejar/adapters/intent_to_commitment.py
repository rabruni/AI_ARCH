"""Intent to Commitment Adapter.

Maps The Assist's Intent model to locked_system's CommitmentLease model.

Intent (the_assist):
- north_stars: Identity-level priorities
- current_success: What success looks like
- non_goals: Hard constraints
- stop_conditions: When to stop
- stance: partner | support | challenge

CommitmentLease (locked_system):
- frame: What we're committed to
- horizon_authority: near | mid | far
- success_criteria: List of success conditions
- non_goals: Things to avoid
- turns_remaining: Lease expiry
"""
from typing import Optional
from locked_system import CommitmentLease, Stance

# Import Intent from dopejar
from dopejar.hrm.intent import Intent, IntentStore


def intent_to_commitment(
    intent: Intent,
    turns: int = 20
) -> CommitmentLease:
    """
    Convert The Assist's Intent to locked_system's CommitmentLease.

    The Intent model is more about identity and values, while
    CommitmentLease is about session-level focus. This adapter
    extracts the actionable commitment from the intent.

    Args:
        intent: The Intent from IntentStore
        turns: Number of turns for the commitment lease

    Returns:
        CommitmentLease configured based on intent
    """
    return CommitmentLease(
        frame=intent.current_success,
        horizon_authority="mid",  # Intent operates at mid-horizon
        success_criteria=[intent.current_success],
        non_goals=intent.non_goals,
        lease_expiry=f"{turns} turns",
        renewal_prompt="Continue with this focus?",
        turns_remaining=turns
    )


def intent_to_behavioral_constraints(intent: Intent) -> dict:
    """
    Extract behavioral constraints from Intent for prompt injection.

    These constraints inform how the agent behaves beyond just
    the commitment frame.

    Args:
        intent: The Intent from IntentStore

    Returns:
        Dict with behavioral constraint context
    """
    return {
        "north_stars": intent.north_stars,
        "stance": intent.stance,
        "stop_conditions": intent.stop_conditions,
        "non_goals": intent.non_goals,
        "success": intent.current_success,
    }


def map_stance_to_locked_stance(assist_stance: str) -> Stance:
    """
    Map The Assist's stance to locked_system's Stance.

    The Assist uses: partner | support | challenge
    locked_system uses: SENSEMAKING | DISCOVERY | EXECUTION | EVALUATION

    This mapping is approximate since the concepts differ:
    - partner -> SENSEMAKING (collaborative exploration)
    - support -> EXECUTION (help complete tasks)
    - challenge -> EVALUATION (question and probe)

    Args:
        assist_stance: The Assist's stance (partner, support, challenge)

    Returns:
        locked_system Stance enum value
    """
    mapping = {
        "partner": Stance.SENSEMAKING,
        "support": Stance.EXECUTION,
        "challenge": Stance.EVALUATION,
    }
    return mapping.get(assist_stance, Stance.SENSEMAKING)


def create_intent_context_for_prompt(intent_store: IntentStore) -> str:
    """
    Create a context string from intent for prompt injection.

    This context can be prepended to prompts to ensure the locked_system
    executor is aware of The Assist's identity-level constraints.

    Args:
        intent_store: The IntentStore instance

    Returns:
        Formatted context string for prompt injection
    """
    intent = intent_store.get_intent()

    return f"""## The Assist Identity Context

North Stars (core priorities): {', '.join(intent.north_stars)}

Current Success Criteria: {intent.current_success}

Non-Goals (avoid these): {', '.join(intent.non_goals)}

Stance: {intent.stance}

Stop Conditions: {', '.join(intent.stop_conditions)}

---
"""
