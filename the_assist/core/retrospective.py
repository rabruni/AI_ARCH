"""The Assist - Session Retrospective

Post-session analysis aligned to behavioral frameworks.
Designed to become its own agent. Feeds HRM L4 Identity layer.

Frameworks:
- MBTI: Baseline + shift detection
- Big 5 (OCEAN): Session signals
- Behavioral patterns: Energy, focus, decision style

This is the long-term value keeper.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import anthropic

from the_assist.config.settings import MODEL, MEMORY_DIR


# ============================================================
# PATHS
# ============================================================

RETRO_DIR = os.path.join(MEMORY_DIR, "retrospectives")
TRENDS_FILE = os.path.join(RETRO_DIR, "trends.json")
BASELINE_FILE = os.path.join(RETRO_DIR, "baseline.json")


# ============================================================
# BASELINE PROFILE
# ============================================================

DEFAULT_BASELINE = {
    # MBTI baseline
    "mbti": {
        "type": "ENTP",
        "dimensions": {
            "E_I": 0.7,   # 0=I, 1=E (0.7 = strong E)
            "N_S": 0.8,   # 0=S, 1=N (0.8 = strong N)
            "T_F": 0.6,   # 0=F, 1=T (0.6 = moderate T)
            "J_P": 0.3,   # 0=P, 1=J (0.3 = moderate P)
        }
    },

    # Big 5 baseline (0-1 scale)
    "big5": {
        "openness": 0.85,
        "conscientiousness": 0.5,
        "extraversion": 0.7,
        "agreeableness": 0.6,
        "neuroticism": 0.4
    },

    # Behavioral baseline
    "behavioral": {
        "energy_typical": "high",
        "focus_pattern": "multi-threaded",
        "decision_style": "quick_iterate",
        "communication": "direct_exploratory",
        "stress_response": "action_oriented"
    },

    # Learned over time
    "preferences": {
        "no_ai_self_awareness": True,
        "numbers_over_bullets": True,
        "proactive_nudges": True,
        "concise_responses": True
    },

    "last_updated": None
}


# ============================================================
# CORE CLASS
# ============================================================

class SessionRetrospective:
    """Analyzes sessions for behavioral patterns and learning."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(RETRO_DIR, exist_ok=True)
        if not os.path.exists(BASELINE_FILE):
            self._save_baseline(DEFAULT_BASELINE)
        if not os.path.exists(TRENDS_FILE):
            self._save_trends(self._default_trends())

    def _default_trends(self) -> Dict:
        return {
            "sessions_analyzed": 0,
            "correction_rates": [],        # Per-session correction count
            "intuition_hits": [],          # Per-session hit rate
            "mbti_shifts": [],             # Notable dimension shifts
            "big5_signals": [],            # Session-level signals
            "recurring_topics": {},        # Topic frequency
            "learnings": [],               # Accumulated learnings
            "preference_updates": [],      # When preferences were learned
            "last_updated": None
        }

    def _load_baseline(self) -> Dict:
        with open(BASELINE_FILE, 'r') as f:
            return json.load(f)

    def _save_baseline(self, baseline: Dict):
        baseline["last_updated"] = datetime.now().isoformat()
        with open(BASELINE_FILE, 'w') as f:
            json.dump(baseline, f, indent=2)

    def _load_trends(self) -> Dict:
        with open(TRENDS_FILE, 'r') as f:
            return json.load(f)

    def _save_trends(self, trends: Dict):
        trends["last_updated"] = datetime.now().isoformat()
        with open(TRENDS_FILE, 'w') as f:
            json.dump(trends, f, indent=2)

    def analyze_session(
        self,
        conversation: List[Dict],
        session_id: int,
        intuition_data: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze a completed session.

        Args:
            conversation: List of {"role": "user/assistant", "content": "..."}
            session_id: Current session number
            intuition_data: Data from proactive engine (hits/misses)

        Returns:
            Session analysis dict
        """
        if len(conversation) < 2:
            return {"skipped": True, "reason": "conversation_too_short"}

        baseline = self._load_baseline()

        # Build analysis prompt
        conversation_text = "\n".join([
            f"{m['role'].upper()}: {m['content'][:500]}"
            for m in conversation[-20:]  # Last 20 exchanges max
        ])

        analysis_prompt = f"""Analyze this conversation session for behavioral patterns.

USER BASELINE:
- MBTI: {baseline['mbti']['type']}
- Big 5: O={baseline['big5']['openness']:.1f} C={baseline['big5']['conscientiousness']:.1f} E={baseline['big5']['extraversion']:.1f} A={baseline['big5']['agreeableness']:.1f} N={baseline['big5']['neuroticism']:.1f}
- Typical energy: {baseline['behavioral']['energy_typical']}
- Decision style: {baseline['behavioral']['decision_style']}

CONVERSATION:
{conversation_text}

Analyze and return JSON:
{{
    "session_quality": "productive|moderate|scattered|stuck",

    "mbti_signals": {{
        "observed_type": "ENTP or shifted type",
        "dimension_shifts": {{
            "E_I": 0.0,  // -0.3 to +0.3, negative=more I, positive=more E
            "N_S": 0.0,
            "T_F": 0.0,
            "J_P": 0.0
        }},
        "shift_explanation": "why shifts occurred, if any"
    }},

    "big5_signals": {{
        "openness": "high|baseline|low",
        "conscientiousness": "high|baseline|low",
        "extraversion": "high|baseline|low",
        "agreeableness": "high|baseline|low",
        "neuroticism": "high|baseline|low",
        "notable": "any notable observations"
    }},

    "behavioral": {{
        "energy": "high|medium|low",
        "focus": "concentrated|multi-threaded|scattered",
        "decision_style": "quick|deliberate|avoidant",
        "stress_signals": "none|mild|elevated",
        "communication_mode": "directive|exploratory|venting"
    }},

    "session_dynamics": {{
        "corrections_given": 0,  // Times user corrected the assistant
        "topics": ["topic1", "topic2"],
        "progress_made": true,
        "blockers_identified": ["blocker1"],
        "decisions_made": ["decision1"]
    }},

    "learnings": [
        "specific thing to remember for future"
    ],

    "meta_observations": {{
        "assistant_verbosity": "appropriate|too_high|too_low",
        "intuition_accuracy": "good|mixed|poor",
        "trust_signals": "positive|neutral|negative",
        "what_worked": "specific thing that worked",
        "what_didnt": "specific thing that didn't work"
    }}
}}

Return ONLY valid JSON."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": analysis_prompt}]
        )

        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
            analysis = json.loads(text.strip())

            # Add metadata
            analysis["session_id"] = session_id
            analysis["timestamp"] = datetime.now().isoformat()
            analysis["turn_count"] = len(conversation)

            # Save session retrospective
            session_file = os.path.join(
                RETRO_DIR,
                f"{datetime.now().strftime('%Y-%m-%d')}_session_{session_id}.json"
            )
            with open(session_file, 'w') as f:
                json.dump(analysis, f, indent=2)

            # Update trends
            self._update_trends(analysis)

            # Check for baseline updates
            self._check_baseline_updates(analysis)

            return analysis

        except (json.JSONDecodeError, KeyError) as e:
            return {"error": str(e), "skipped": True}

    def _update_trends(self, analysis: Dict):
        """Update trend tracking with session data."""
        trends = self._load_trends()

        trends["sessions_analyzed"] += 1

        # Track correction rate
        corrections = analysis.get("session_dynamics", {}).get("corrections_given", 0)
        trends["correction_rates"].append(corrections)
        trends["correction_rates"] = trends["correction_rates"][-50:]  # Keep last 50

        # Track topics
        for topic in analysis.get("session_dynamics", {}).get("topics", []):
            trends["recurring_topics"][topic] = trends["recurring_topics"].get(topic, 0) + 1

        # Track learnings
        for learning in analysis.get("learnings", []):
            trends["learnings"].append({
                "session": analysis.get("session_id"),
                "learning": learning,
                "timestamp": datetime.now().isoformat()
            })
        trends["learnings"] = trends["learnings"][-100:]  # Keep last 100

        # Track MBTI shifts
        shifts = analysis.get("mbti_signals", {}).get("dimension_shifts", {})
        significant_shifts = {k: v for k, v in shifts.items() if abs(v) >= 0.2}
        if significant_shifts:
            trends["mbti_shifts"].append({
                "session": analysis.get("session_id"),
                "shifts": significant_shifts,
                "observed_type": analysis.get("mbti_signals", {}).get("observed_type"),
                "timestamp": datetime.now().isoformat()
            })
        trends["mbti_shifts"] = trends["mbti_shifts"][-20:]

        self._save_trends(trends)

    def _check_baseline_updates(self, analysis: Dict):
        """Check if baseline should be updated based on consistent patterns."""
        trends = self._load_trends()

        # If we have enough data, check for consistent shifts
        if trends["sessions_analyzed"] >= 5:
            # Check for consistent MBTI shifts
            recent_shifts = trends["mbti_shifts"][-5:]
            # TODO: Implement shift pattern detection

            # Check for new preferences
            learnings = [l["learning"] for l in trends["learnings"][-10:]]
            # TODO: Detect preference patterns

    def get_trends_summary(self) -> Dict:
        """Get summary of behavioral trends."""
        trends = self._load_trends()
        baseline = self._load_baseline()

        # Calculate averages
        correction_avg = (
            sum(trends["correction_rates"]) / len(trends["correction_rates"])
            if trends["correction_rates"] else 0
        )

        # Top topics
        top_topics = sorted(
            trends["recurring_topics"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Recent learnings
        recent_learnings = [l["learning"] for l in trends["learnings"][-5:]]

        return {
            "sessions_analyzed": trends["sessions_analyzed"],
            "avg_corrections_per_session": round(correction_avg, 2),
            "correction_trend": self._calculate_trend(trends["correction_rates"]),
            "top_topics": top_topics,
            "recent_learnings": recent_learnings,
            "mbti_baseline": baseline["mbti"]["type"],
            "recent_mbti_shifts": trends["mbti_shifts"][-3:] if trends["mbti_shifts"] else []
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate if trend is improving, stable, or declining."""
        if len(values) < 5:
            return "insufficient_data"

        recent = values[-5:]
        older = values[-10:-5] if len(values) >= 10 else values[:5]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg < older_avg * 0.8:
            return "improving"
        elif recent_avg > older_avg * 1.2:
            return "declining"
        else:
            return "stable"

    def get_baseline(self) -> Dict:
        """Get current baseline profile."""
        return self._load_baseline()

    def update_baseline_preference(self, key: str, value: any):
        """Manually update a baseline preference."""
        baseline = self._load_baseline()
        baseline["preferences"][key] = value
        self._save_baseline(baseline)


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def run_retrospective(
    conversation: List[Dict],
    session_id: int,
    intuition_data: Optional[Dict] = None
) -> Dict:
    """Run session retrospective. Called at shutdown."""
    retro = SessionRetrospective()
    return retro.analyze_session(conversation, session_id, intuition_data)


def get_behavioral_summary() -> Dict:
    """Get summary of behavioral trends."""
    retro = SessionRetrospective()
    return retro.get_trends_summary()
