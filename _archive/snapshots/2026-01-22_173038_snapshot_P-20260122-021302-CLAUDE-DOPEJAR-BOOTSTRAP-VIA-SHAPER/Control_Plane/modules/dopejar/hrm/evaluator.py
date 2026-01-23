"""HRM Layer 4: Evaluator

Compares outcome to intent. Triggers revision.

This layer:
- Detects errors
- Compares outcome to intent
- Triggers revision
- Decides whether to escalate

Memory: Delta-based, outcome-focused, time-bounded.

The Evaluator does NOT execute. It does NOT plan.
It only answers: "Did it work? Does it match intent?"
"""
import os
import json
import anthropic
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
from pathlib import Path

from dopejar.hrm.intent import IntentStore, Intent
from dopejar.hrm.executor import ExecutionResult


HRM_DIR = Path(__file__).parent / "memory"


@dataclass
class Evaluation:
    """Evaluation result. Delta-based - what changed, what failed."""
    matched_intent: bool            # Did outcome match intent?
    issue: Optional[str]            # What was the issue if any
    severity: str                   # none | minor | major | critical
    revision_needed: bool           # Should Planner revise?
    escalate_to_intent: bool        # Should Intent be clarified?
    recommendation: str             # What to do next
    outcome_summary: str            # Brief summary of what happened


class Evaluator:
    """
    L4: The evaluation layer.

    Fresh context agent. Compares outcome to intent.
    Does NOT execute. Does NOT plan. Does NOT modify intent.
    Only evaluates and triggers revision.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.intent_store = IntentStore()
        self.evaluations_file = HRM_DIR / "evaluations.json"
        self._ensure_exists()

    def _ensure_exists(self):
        HRM_DIR.mkdir(parents=True, exist_ok=True)
        if not self.evaluations_file.exists():
            self._save_evaluations({
                "recent": [],
                "patterns": {
                    "repeated_issues": [],
                    "successful_approaches": []
                }
            })

    def _load_evaluations(self) -> dict:
        with open(self.evaluations_file, 'r') as f:
            return json.load(f)

    def _save_evaluations(self, data: dict):
        with open(self.evaluations_file, 'w') as f:
            json.dump(data, f, indent=2)

    def evaluate(self, result: ExecutionResult, plan_used: dict) -> Evaluation:
        """
        Evaluate execution result against intent.

        This is a FRESH context API call. No pollution.
        Only sees: intent, outcome, and plan that was used.
        """
        intent = self.intent_store.get_intent()
        intent_context = self.intent_store.build_context_for_evaluator()

        eval_prompt = f"""{intent_context}

PLAN THAT WAS USED:
Approach: {plan_used.get('approach', 'unknown')}
Altitude: {plan_used.get('altitude', 'unknown')}
Stance: {plan_used.get('stance', 'unknown')}
Focus: {plan_used.get('focus', [])}

EXECUTION RESULT (state report from L3):
Response given: "{result.response[:800]}"
Topics discussed: {result.topics_discussed}
Altitude used: {result.altitude_used}
Plan followed: {result.plan_followed}
Deviation: {result.deviation_reason or 'none'}
User signals detected: {result.user_signals}

Evaluate this outcome against intent. Return JSON:
{{
    "matched_intent": true/false,
    "issue": "what went wrong, or null if matched",
    "severity": "none|minor|major|critical",
    "revision_needed": true/false,
    "escalate_to_intent": true/false,
    "recommendation": "what to do next",
    "outcome_summary": "1-sentence summary"
}}

EVALUATION RULES:
1. If user signals include "frustration" or "explicit_stop" → at least "major" severity
2. If plan was not followed → revision needed
3. If non-goals were violated → critical severity
4. If intent success criteria not met → revision needed
5. Escalate to intent if the GOAL itself seems unclear, not just execution
6. Be honest. Don't rationalize failures.

Return ONLY valid JSON."""

        try:
            # FRESH CONTEXT - no pollution
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": eval_prompt}]
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]

            result_data = json.loads(text.strip())

            evaluation = Evaluation(
                matched_intent=result_data.get("matched_intent", True),
                issue=result_data.get("issue"),
                severity=result_data.get("severity", "none"),
                revision_needed=result_data.get("revision_needed", False),
                escalate_to_intent=result_data.get("escalate_to_intent", False),
                recommendation=result_data.get("recommendation", ""),
                outcome_summary=result_data.get("outcome_summary", "")
            )

            # Record evaluation
            self._record_evaluation(evaluation)

            return evaluation

        except Exception as e:
            # Fallback - assume OK but note the error
            return Evaluation(
                matched_intent=True,
                issue=f"Evaluation error: {str(e)}",
                severity="minor",
                revision_needed=False,
                escalate_to_intent=False,
                recommendation="Continue with current approach",
                outcome_summary="Evaluation failed, assuming success"
            )

    def _record_evaluation(self, evaluation: Evaluation):
        """Record evaluation to delta-based memory."""
        data = self._load_evaluations()

        # Add to recent
        data["recent"].append({
            "evaluation": asdict(evaluation),
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last 20 (time-bounded)
        data["recent"] = data["recent"][-20:]

        # Track patterns
        if evaluation.issue:
            data["patterns"]["repeated_issues"].append(evaluation.issue)
            data["patterns"]["repeated_issues"] = data["patterns"]["repeated_issues"][-10:]

        if evaluation.matched_intent and evaluation.severity == "none":
            data["patterns"]["successful_approaches"].append(evaluation.outcome_summary)
            data["patterns"]["successful_approaches"] = data["patterns"]["successful_approaches"][-10:]

        self._save_evaluations(data)

    def should_revise_plan(self, evaluation: Evaluation) -> bool:
        """Check if plan revision is needed."""
        return evaluation.revision_needed or evaluation.severity in ["major", "critical"]

    def should_escalate_to_intent(self, evaluation: Evaluation) -> bool:
        """Check if intent clarification is needed."""
        return evaluation.escalate_to_intent

    def get_revision_context(self, evaluation: Evaluation, result: ExecutionResult) -> dict:
        """
        Build context for Planner revision.

        This is what flows UP to L2.
        """
        return {
            "revision_needed": True,
            "issue": evaluation.issue,
            "severity": evaluation.severity,
            "recommendation": evaluation.recommendation,
            "outcome_summary": evaluation.outcome_summary,
            "user_sentiment": "frustrated" if "frustration" in (result.user_signals or []) else "engaged",
            "last_user_input": "",  # Will be filled by loop
            "conversation_length": 0,  # Will be filled by loop
            "recent_topics": result.topics_discussed
        }

    def get_patterns(self) -> dict:
        """Get evaluation patterns for analysis."""
        data = self._load_evaluations()
        return data.get("patterns", {})

    def get_recent_evaluations(self, n: int = 5) -> list[dict]:
        """Get recent evaluations."""
        data = self._load_evaluations()
        return data.get("recent", [])[-n:]

    def clear_old_evaluations(self, days: int = 7):
        """Clear evaluations older than N days. Time-bounded cleanup."""
        data = self._load_evaluations()
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        data["recent"] = [
            e for e in data.get("recent", [])
            if datetime.fromisoformat(e["timestamp"]).timestamp() > cutoff
        ]
        self._save_evaluations(data)

    def reset(self):
        """Reset evaluator state for new session."""
        self._save_evaluations({
            "recent": [],
            "patterns": {
                "repeated_issues": [],
                "successful_approaches": []
            }
        })
