"""The Assist - AI Self-Reflection

Mirror to user retrospective. Analyzes AI's own performance.
Creates the feedback loop: What did Assist do that led to outcomes?

This is meta-learning about the AI itself.
Designed to become its own agent.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import anthropic

from the_assist.config.settings import MEMORY_DIR


# ============================================================
# PATHS
# ============================================================

REFLECTION_DIR = os.path.join(MEMORY_DIR, "ai_reflection")
AI_TRENDS_FILE = os.path.join(REFLECTION_DIR, "ai_trends.json")
OUTCOME_LOG_FILE = os.path.join(REFLECTION_DIR, "outcome_log.json")


# ============================================================
# QUALITY DIMENSIONS
# ============================================================

QUALITY_DIMENSIONS = {
    "conciseness": "Response length appropriate to context",
    "accuracy": "Information provided was correct",
    "actionability": "Response led to clear next steps",
    "tone_match": "Matched user's energy and mode",
    "intuition_quality": "Proactive insights were relevant",
    "memory_relevance": "Surfaced relevant, not stale, context",
    "value_add": "Actually helped vs just responded",
    "trust_building": "Increased or maintained trust"
}


# ============================================================
# CORE CLASS
# ============================================================

class AIReflection:
    """AI self-assessment and outcome analysis."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(REFLECTION_DIR, exist_ok=True)
        if not os.path.exists(AI_TRENDS_FILE):
            self._save_trends(self._default_trends())
        if not os.path.exists(OUTCOME_LOG_FILE):
            with open(OUTCOME_LOG_FILE, 'w') as f:
                json.dump({"outcomes": []}, f)

    def _default_trends(self) -> Dict:
        return {
            "sessions_reflected": 0,
            "quality_scores": {dim: [] for dim in QUALITY_DIMENSIONS},
            "outcome_patterns": [],
            "improvement_areas": [],
            "strengths": [],
            "failure_modes": [],
            "last_updated": None
        }

    def _load_trends(self) -> Dict:
        with open(AI_TRENDS_FILE, 'r') as f:
            return json.load(f)

    def _save_trends(self, trends: Dict):
        trends["last_updated"] = datetime.now().isoformat()
        with open(AI_TRENDS_FILE, 'w') as f:
            json.dump(trends, f, indent=2)

    def _load_outcomes(self) -> Dict:
        with open(OUTCOME_LOG_FILE, 'r') as f:
            return json.load(f)

    def _save_outcomes(self, outcomes: Dict):
        with open(OUTCOME_LOG_FILE, 'w') as f:
            json.dump(outcomes, f, indent=2)

    def reflect_on_session(
        self,
        conversation: List[Dict],
        session_id: int,
        user_retrospective: Optional[Dict] = None,
        session_feedback: Optional[Dict] = None
    ) -> Dict:
        """
        AI self-reflection on session performance.

        Uses a "judge" approach - evaluating own responses objectively.

        Args:
            conversation: The full conversation
            session_id: Session number
            user_retrospective: Results from user behavior analysis
            session_feedback: Explicit +1/-1 feedback from user this session

        Returns:
            AI reflection analysis
        """
        if len(conversation) < 2:
            return {"skipped": True, "reason": "conversation_too_short"}

        # Extract just AI responses for analysis
        ai_responses = [
            m["content"] for m in conversation
            if m["role"] == "assistant"
        ]

        user_messages = [
            m["content"] for m in conversation
            if m["role"] == "user"
        ]

        # Build conversation summary
        conversation_text = "\n".join([
            f"{m['role'].upper()}: {m['content'][:300]}"
            for m in conversation[-16:]
        ])

        # Include user retrospective context if available
        user_context = ""
        if user_retrospective and not user_retrospective.get("skipped"):
            user_context = f"""
USER SESSION ANALYSIS (for comparison):
- Session quality: {user_retrospective.get('session_quality', 'unknown')}
- User energy: {user_retrospective.get('behavioral', {}).get('energy', 'unknown')}
- Corrections given to AI: {user_retrospective.get('session_dynamics', {}).get('corrections_given', 0)}
- User stress signals: {user_retrospective.get('behavioral', {}).get('stress_signals', 'unknown')}
"""

        # Include explicit user feedback - THIS IS GROUND TRUTH
        feedback_context = ""
        if session_feedback:
            pos = session_feedback.get('positive_count', 0)
            neg = session_feedback.get('negative_count', 0)
            worked_notes = [f.get('note', '') for f in session_feedback.get('worked', [])]
            didnt_work_notes = [f.get('note', '') for f in session_feedback.get('didnt_work', [])]

            feedback_context = f"""
EXPLICIT USER FEEDBACK THIS SESSION (ground truth - weight heavily):
- Positive feedback (+1): {pos}
- Negative feedback (-1): {neg}
"""
            if worked_notes:
                feedback_context += f"- What worked: {'; '.join(worked_notes[:3])}\n"
            if didnt_work_notes:
                feedback_context += f"- What didn't work: {'; '.join(didnt_work_notes[:3])}\n"

            if pos > 0 and neg == 0:
                feedback_context += "NOTE: User gave positive feedback with no negatives - this suggests effective session.\n"
            elif neg > pos:
                feedback_context += "NOTE: More negative than positive feedback - this suggests issues.\n"

        reflection_prompt = f"""You are an objective evaluator analyzing an AI assistant's performance.
Be critical and honest. The goal is improvement, not validation.

CONVERSATION:
{conversation_text}

{user_context}
{feedback_context}

IMPORTANT: If user gave explicit positive feedback (+1), that is ground truth that the session was effective.
Do not rate as "ineffective" when user explicitly said something worked.

Evaluate the AI assistant's responses and return JSON:
{{
    "quality_scores": {{
        "conciseness": 0.0,      // 0-1: Was response length appropriate?
        "accuracy": 0.0,         // 0-1: Was information correct?
        "actionability": 0.0,    // 0-1: Did responses lead to clear next steps?
        "tone_match": 0.0,       // 0-1: Did AI match user's energy/mode?
        "intuition_quality": 0.0, // 0-1: Were proactive insights relevant?
        "memory_relevance": 0.0, // 0-1: Was context surfaced relevant (not stale)?
        "value_add": 0.0,        // 0-1: Did AI actually help or just respond?
        "trust_building": 0.0    // 0-1: Did responses build or erode trust?
    }},

    "outcome_analysis": {{
        "overall_effectiveness": "effective|mixed|ineffective",
        "user_goal_supported": true,  // Did AI help user achieve their goal?
        "friction_points": ["specific moment of friction"],
        "smooth_moments": ["specific moment that worked well"]
    }},

    "self_critique": {{
        "what_worked": "specific thing AI did well",
        "what_failed": "specific thing AI did poorly",
        "missed_opportunities": ["thing AI should have done but didn't"],
        "overcorrections": ["times AI tried too hard or overexplained"]
    }},

    "pattern_detection": {{
        "ai_tendencies_shown": ["tendency1", "tendency2"],
        "user_corrections_analysis": "what corrections reveal about AI gaps",
        "trust_trajectory": "building|stable|eroding"
    }},

    "improvement_actions": [
        "specific actionable improvement for future sessions"
    ],

    "outcome_attribution": {{
        "positive_outcomes_from_ai": ["outcome AI contributed to"],
        "negative_outcomes_from_ai": ["outcome AI caused or worsened"],
        "neutral_ai_impact": ["areas where AI neither helped nor hurt"]
    }}
}}

Be brutally honest. Rate genuinely - don't inflate scores.
Return ONLY valid JSON."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",  # Can use different model as judge
            max_tokens=1500,
            messages=[{"role": "user", "content": reflection_prompt}]
        )

        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
            reflection = json.loads(text.strip())

            # Add metadata
            reflection["session_id"] = session_id
            reflection["timestamp"] = datetime.now().isoformat()
            reflection["turn_count"] = len(conversation)

            # Save reflection
            reflection_file = os.path.join(
                REFLECTION_DIR,
                f"{datetime.now().strftime('%Y-%m-%d')}_session_{session_id}_reflection.json"
            )
            with open(reflection_file, 'w') as f:
                json.dump(reflection, f, indent=2)

            # Update trends
            self._update_trends(reflection)

            # Log outcome
            self._log_outcome(reflection, user_retrospective)

            return reflection

        except (json.JSONDecodeError, KeyError) as e:
            return {"error": str(e), "skipped": True}

    def _update_trends(self, reflection: Dict):
        """Update AI performance trends."""
        trends = self._load_trends()

        trends["sessions_reflected"] += 1

        # Track quality scores
        scores = reflection.get("quality_scores", {})
        for dim, score in scores.items():
            if dim in trends["quality_scores"]:
                trends["quality_scores"][dim].append(score)
                # Keep last 50
                trends["quality_scores"][dim] = trends["quality_scores"][dim][-50:]

        # Track improvement areas
        for improvement in reflection.get("improvement_actions", []):
            trends["improvement_areas"].append({
                "session": reflection.get("session_id"),
                "action": improvement,
                "timestamp": datetime.now().isoformat()
            })
        trends["improvement_areas"] = trends["improvement_areas"][-30:]

        # Track failure modes
        what_failed = reflection.get("self_critique", {}).get("what_failed")
        if what_failed:
            trends["failure_modes"].append({
                "session": reflection.get("session_id"),
                "failure": what_failed,
                "timestamp": datetime.now().isoformat()
            })
        trends["failure_modes"] = trends["failure_modes"][-20:]

        # Track strengths
        what_worked = reflection.get("self_critique", {}).get("what_worked")
        if what_worked:
            trends["strengths"].append({
                "session": reflection.get("session_id"),
                "strength": what_worked,
                "timestamp": datetime.now().isoformat()
            })
        trends["strengths"] = trends["strengths"][-20:]

        self._save_trends(trends)

    def _log_outcome(self, reflection: Dict, user_retro: Optional[Dict]):
        """Log outcome for pattern analysis."""
        outcomes = self._load_outcomes()

        outcome_entry = {
            "session": reflection.get("session_id"),
            "timestamp": datetime.now().isoformat(),
            "effectiveness": reflection.get("outcome_analysis", {}).get("overall_effectiveness"),
            "trust_trajectory": reflection.get("pattern_detection", {}).get("trust_trajectory"),
            "avg_quality": self._avg_quality(reflection.get("quality_scores", {})),
        }

        # Add user context if available
        if user_retro and not user_retro.get("skipped"):
            outcome_entry["user_state"] = {
                "session_quality": user_retro.get("session_quality"),
                "energy": user_retro.get("behavioral", {}).get("energy"),
                "stress": user_retro.get("behavioral", {}).get("stress_signals"),
                "corrections": user_retro.get("session_dynamics", {}).get("corrections_given", 0)
            }

            # Compute outcome pattern
            outcome_entry["pattern"] = self._compute_pattern(reflection, user_retro)

        outcomes["outcomes"].append(outcome_entry)
        outcomes["outcomes"] = outcomes["outcomes"][-100:]  # Keep last 100

        self._save_outcomes(outcomes)

    def _avg_quality(self, scores: Dict) -> float:
        """Calculate average quality score."""
        if not scores:
            return 0.0
        values = [v for v in scores.values() if isinstance(v, (int, float))]
        return round(sum(values) / len(values), 2) if values else 0.0

    def _compute_pattern(self, reflection: Dict, user_retro: Dict) -> str:
        """Compute the outcome pattern (user state + AI behavior = outcome)."""
        user_energy = user_retro.get("behavioral", {}).get("energy", "unknown")
        user_stress = user_retro.get("behavioral", {}).get("stress_signals", "none")
        ai_effectiveness = reflection.get("outcome_analysis", {}).get("overall_effectiveness", "unknown")
        trust = reflection.get("pattern_detection", {}).get("trust_trajectory", "unknown")

        # Simplified pattern classification
        if ai_effectiveness == "effective" and trust == "building":
            return "positive_reinforcement"
        elif ai_effectiveness == "ineffective" and trust == "eroding":
            return "negative_spiral"
        elif user_stress in ["elevated", "high"] and ai_effectiveness == "effective":
            return "stress_support_success"
        elif user_stress in ["elevated", "high"] and ai_effectiveness != "effective":
            return "stress_support_failure"
        else:
            return "neutral"

    def get_ai_performance_summary(self) -> Dict:
        """Get summary of AI performance trends."""
        trends = self._load_trends()

        # Calculate average scores per dimension
        avg_scores = {}
        for dim, scores in trends.get("quality_scores", {}).items():
            if scores:
                avg_scores[dim] = round(sum(scores) / len(scores), 2)
            else:
                avg_scores[dim] = None

        # Get recent failure modes
        recent_failures = [f["failure"] for f in trends.get("failure_modes", [])[-3:]]

        # Get recent strengths
        recent_strengths = [s["strength"] for s in trends.get("strengths", [])[-3:]]

        # Get improvement areas
        improvements = [i["action"] for i in trends.get("improvement_areas", [])[-5:]]

        # Load outcome patterns
        outcomes = self._load_outcomes()
        pattern_counts = {}
        for o in outcomes.get("outcomes", [])[-20:]:
            pattern = o.get("pattern", "unknown")
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        return {
            "sessions_reflected": trends["sessions_reflected"],
            "avg_quality_scores": avg_scores,
            "overall_avg": round(sum(v for v in avg_scores.values() if v) / len([v for v in avg_scores.values() if v]), 2) if avg_scores else 0,
            "recent_failures": recent_failures,
            "recent_strengths": recent_strengths,
            "improvement_actions": improvements,
            "outcome_patterns": pattern_counts,
            "trend_direction": self._calculate_trend_direction(trends)
        }

    def _calculate_trend_direction(self, trends: Dict) -> str:
        """Determine if AI performance is improving, stable, or declining."""
        # Look at trust_building scores over time
        trust_scores = trends.get("quality_scores", {}).get("trust_building", [])
        if len(trust_scores) < 6:
            return "insufficient_data"

        recent = trust_scores[-5:]
        older = trust_scores[-10:-5] if len(trust_scores) >= 10 else trust_scores[:5]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg > older_avg + 0.1:
            return "improving"
        elif recent_avg < older_avg - 0.1:
            return "declining"
        else:
            return "stable"


# ============================================================
# COMBINED ANALYSIS
# ============================================================

def analyze_session_complete(
    conversation: List[Dict],
    session_id: int,
    user_retrospective: Dict
) -> Tuple[Dict, Dict]:
    """
    Run complete session analysis: user behavior + AI reflection.

    Returns (user_retro, ai_reflection)
    """
    reflector = AIReflection()
    ai_reflection = reflector.reflect_on_session(
        conversation, session_id, user_retrospective
    )
    return user_retrospective, ai_reflection


def get_combined_insights() -> Dict:
    """Get combined insights from both user and AI analysis."""
    from the_assist.core.retrospective import get_behavioral_summary

    user_summary = get_behavioral_summary()
    ai_summary = AIReflection().get_ai_performance_summary()

    return {
        "user": user_summary,
        "ai": ai_summary,
        "alignment": _compute_alignment(user_summary, ai_summary)
    }


def _compute_alignment(user: Dict, ai: Dict) -> Dict:
    """Compute how well AI is aligned with user needs."""
    # Simple alignment metrics
    correction_trend = user.get("correction_trend", "unknown")
    ai_trend = ai.get("trend_direction", "unknown")

    if correction_trend == "improving" and ai_trend == "improving":
        alignment = "strong"
    elif correction_trend == "declining" or ai_trend == "declining":
        alignment = "weak"
    else:
        alignment = "moderate"

    return {
        "alignment_strength": alignment,
        "user_corrections_trending": correction_trend,
        "ai_performance_trending": ai_trend
    }
