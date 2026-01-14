"""HRM Layer 2: Planner

Takes intent + situation, outputs approach.

This layer:
- Breaks problems into parts
- Chooses approaches
- Allocates effort
- Manages tradeoffs

Memory: Semi-stable, rewritable, pattern-oriented.

The Planner does NOT execute. It does NOT evaluate.
It only decides HOW to approach the current situation given the intent.
"""
import os
import json
import anthropic
from dataclasses import dataclass, asdict, field
from typing import Optional
from datetime import datetime
from pathlib import Path

from the_assist.hrm.intent import IntentStore, Intent


HRM_DIR = Path(__file__).parent / "memory"


@dataclass
class Plan:
    """The plan structure. What approach to take."""
    approach: str                   # strategic | tactical | exploratory | grounding
    altitude: str                   # L1 | L2 | L3 | L4 (what level to operate at)
    constraints: list[str]          # Hard constraints from intent
    focus: list[str]                # What to focus on this exchange
    blocked_topics: list[str]       # Topics to avoid
    stance: str                     # partner | support | challenge
    revision_reason: Optional[str] = None  # Why was plan revised


@dataclass
class Situation:
    """Current situation reported by Executor."""
    user_input: str
    conversation_length: int
    recent_topics: list[str]
    user_sentiment: str             # engaged | frustrated | exploratory | resistant
    last_outcome: Optional[str] = None


class Planner:
    """
    L2: The planning layer.

    Fresh context agent. Reads intent, reads situation, outputs plan.
    Does NOT execute. Does NOT evaluate.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.intent_store = IntentStore()
        self.plans_file = HRM_DIR / "plans.json"
        self._ensure_exists()

    def _ensure_exists(self):
        HRM_DIR.mkdir(parents=True, exist_ok=True)
        if not self.plans_file.exists():
            self._save_plans({
                "current_plan": None,
                "revision_history": []
            })

    def _load_plans(self) -> dict:
        with open(self.plans_file, 'r') as f:
            return json.load(f)

    def _save_plans(self, data: dict):
        with open(self.plans_file, 'w') as f:
            json.dump(data, f, indent=2)

    def plan(self, situation: Situation, evaluation: Optional[dict] = None) -> Plan:
        """
        Generate a plan given situation and optional evaluation feedback.

        This is a FRESH context API call. No pollution from conversation.
        """
        intent = self.intent_store.get_intent()
        intent_context = self.intent_store.build_context_for_planner()

        # Include evaluation feedback if revision is needed
        eval_context = ""
        if evaluation and evaluation.get("revision_needed"):
            eval_context = f"""
EVALUATION FEEDBACK (from L4 - revision triggered):
Issue: {evaluation.get('issue', 'unknown')}
Recommendation: {evaluation.get('recommendation', 'adjust approach')}
"""

        plan_prompt = f"""{intent_context}

SITUATION (from L3 Executor):
User input: "{situation.user_input[:500]}"
Conversation length: {situation.conversation_length} exchanges
Recent topics: {situation.recent_topics}
User sentiment: {situation.user_sentiment}
Last outcome: {situation.last_outcome or 'none'}
{eval_context}

Generate a plan. You are the PLANNER - you decide approach, not execution.

Return JSON:
{{
    "approach": "strategic|tactical|exploratory|grounding",
    "altitude": "L1|L2|L3|L4",
    "constraints": ["list of hard constraints from intent"],
    "focus": ["what to focus on this exchange"],
    "blocked_topics": ["topics to avoid"],
    "stance": "partner|support|challenge",
    "reasoning": "brief explanation of why this plan"
}}

RULES:
1. If user sentiment is "frustrated", stance should be "support" and focus on acknowledgment
2. If conversation is tactical without strategic context, altitude should be L3 or L4
3. Non-goals from intent are HARD constraints - add to constraints list
4. If evaluation triggered revision, address the issue in your plan
5. Blocked topics should include anything over-discussed or explicitly rejected

Return ONLY valid JSON."""

        try:
            # FRESH CONTEXT - no conversation pollution
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                messages=[{"role": "user", "content": plan_prompt}]
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]

            result = json.loads(text.strip())

            plan = Plan(
                approach=result.get("approach", "strategic"),
                altitude=result.get("altitude", "L2"),
                constraints=result.get("constraints", []),
                focus=result.get("focus", []),
                blocked_topics=result.get("blocked_topics", []),
                stance=result.get("stance", intent.stance),
                revision_reason=evaluation.get("issue") if evaluation else None
            )

            # Save to memory
            self._record_plan(plan)

            return plan

        except Exception as e:
            # Fallback plan
            return Plan(
                approach="strategic",
                altitude="L3",
                constraints=intent.non_goals,
                focus=["understand user needs"],
                blocked_topics=[],
                stance=intent.stance
            )

    def revise(self, current_plan: Plan, evaluation: dict) -> Plan:
        """
        Revise plan based on evaluation feedback.
        Cheap revision - doesn't require replaying execution.
        """
        # Build situation from evaluation
        situation = Situation(
            user_input=evaluation.get("last_user_input", ""),
            conversation_length=evaluation.get("conversation_length", 0),
            recent_topics=evaluation.get("recent_topics", []),
            user_sentiment=evaluation.get("user_sentiment", "engaged"),
            last_outcome=evaluation.get("outcome_summary", None)
        )

        # Plan with evaluation feedback
        return self.plan(situation, evaluation)

    def get_current_plan(self) -> Optional[Plan]:
        """Get the current plan if one exists."""
        data = self._load_plans()
        if data.get("current_plan"):
            return Plan(**data["current_plan"])
        return None

    def _record_plan(self, plan: Plan):
        """Record plan to memory."""
        data = self._load_plans()

        # Move current to history
        if data.get("current_plan"):
            data["revision_history"].append({
                "plan": data["current_plan"],
                "timestamp": datetime.now().isoformat()
            })
            # Keep only last 10 revisions
            data["revision_history"] = data["revision_history"][-10:]

        data["current_plan"] = asdict(plan)
        self._save_plans(data)

    def build_context_for_executor(self, plan: Plan) -> str:
        """Build context for Executor layer."""
        return f"""PLAN (L2 - follow this approach):
APPROACH: {plan.approach}
ALTITUDE: {plan.altitude} ({"moment" if plan.altitude == "L1" else "operations" if plan.altitude == "L2" else "strategy" if plan.altitude == "L3" else "identity"})
STANCE: {plan.stance}
FOCUS: {', '.join(plan.focus)}
CONSTRAINTS: {', '.join(plan.constraints)}
BLOCKED_TOPICS: {', '.join(plan.blocked_topics) if plan.blocked_topics else 'none'}
{"REVISION NOTE: " + plan.revision_reason if plan.revision_reason else ""}"""

    def clear_blocked_topic(self, topic: str):
        """Remove a topic from blocked list."""
        data = self._load_plans()
        if data.get("current_plan"):
            blocked = data["current_plan"].get("blocked_topics", [])
            data["current_plan"]["blocked_topics"] = [
                t for t in blocked if topic.lower() not in t.lower()
            ]
            self._save_plans(data)

    def reset(self):
        """Reset planner state for new session."""
        self._save_plans({
            "current_plan": None,
            "revision_history": []
        })
