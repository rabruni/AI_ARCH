"""The Assist - Memory Curator (v2)

Maintains memory health using compressed format.
Runs daily for operations, weekly for strategy.

Follows the Donna Principle: silent for routine, surfaces insights.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
import anthropic

from dopejar.config.settings import MODEL, MEMORY_DIR
from dopejar.core.memory_v2 import CompressedMemory, PATTERN_CODES


def _parse_json_response(text: str) -> dict:
    """Parse JSON from AI response, handling markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text.strip())


class MemoryCurator:
    """Curates and maintains memory health."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.memory = CompressedMemory()
        self.curator_file = os.path.join(MEMORY_DIR, "curator", "state.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(self.curator_file), exist_ok=True)
        if not os.path.exists(self.curator_file):
            with open(self.curator_file, 'w') as f:
                json.dump({
                    "last_daily": None,
                    "last_weekly": None,
                    "daily_summaries": [],
                    "weekly_themes": [],
                    "insights": []
                }, f)

    def _get_curator_state(self) -> dict:
        with open(self.curator_file, 'r') as f:
            return json.load(f)

    def _save_curator_state(self, state: dict):
        with open(self.curator_file, 'w') as f:
            json.dump(state, f, indent=2)

    def needs_daily(self) -> bool:
        """Check if daily curation is needed."""
        state = self._get_curator_state()
        if not state.get("last_daily"):
            return True
        last = datetime.fromisoformat(state["last_daily"])
        return datetime.now() - last > timedelta(hours=20)

    def needs_weekly(self) -> bool:
        """Check if weekly curation is needed."""
        state = self._get_curator_state()
        if not state.get("last_weekly"):
            return True
        last = datetime.fromisoformat(state["last_weekly"])
        return datetime.now() - last > timedelta(days=6)

    def run_daily(self) -> Optional[str]:
        """
        Daily curation (L2 Operations):
        - Clean stale active items
        - Archive old commits
        - Generate day summary
        - Surface insight if notable

        Returns insight string if something worth surfacing, else None.
        """
        mem_state = self.memory.get_state()

        curation_prompt = f"""You are a memory curator. Analyze this compressed memory state.

CURRENT STATE:
{json.dumps(mem_state, indent=2)}

Tasks:
1. IDENTIFY stale items in "active" (old or resolved)
2. IDENTIFY done items in "commits" (likely completed)
3. CHECK pattern confidence - any that should increase?
4. GENERATE one-line day summary
5. SURFACE strategic insight if notable (or null)

Return JSON:
{{
    "remove_active": ["topic_prefix1", "topic_prefix2"],  // Active items to remove (by topic prefix)
    "remove_commits": ["topic_prefix1"],                  // Commits that seem done
    "boost_patterns": ["pattern_code"],                   // Patterns to increase confidence
    "day_summary": "compressed one-line summary",
    "insight": "strategic observation or null"
}}

Return ONLY valid JSON."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": curation_prompt}]
        )

        try:
            result = _parse_json_response(response.content[0].text)

            # Apply removals
            state = self.memory.get_state()

            for prefix in result.get("remove_active", []):
                state["active"] = [a for a in state["active"] if not a.startswith(prefix)]

            for prefix in result.get("remove_commits", []):
                state["commits"] = [c for c in state["commits"] if not c.startswith(prefix)]

            for code in result.get("boost_patterns", []):
                if code in state["patterns"]:
                    state["patterns"][code] = min(1.0, state["patterns"][code] + 0.1)

            state["last_update"] = datetime.now().isoformat()
            self.memory._save(state)

            # Update curator state
            cur_state = self._get_curator_state()
            cur_state["last_daily"] = datetime.now().isoformat()

            if result.get("day_summary"):
                cur_state["daily_summaries"].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "summary": result["day_summary"]
                })
                cur_state["daily_summaries"] = cur_state["daily_summaries"][-14:]

            if result.get("insight"):
                cur_state["insights"].append({
                    "timestamp": datetime.now().isoformat(),
                    "insight": result["insight"],
                    "surfaced": False
                })

            self._save_curator_state(cur_state)

            return result.get("insight")

        except (json.JSONDecodeError, KeyError):
            # Mark as run even if failed
            cur_state = self._get_curator_state()
            cur_state["last_daily"] = datetime.now().isoformat()
            self._save_curator_state(cur_state)
            return None

    def run_weekly(self) -> Optional[str]:
        """
        Weekly curation (L3 Strategy):
        - Compress daily summaries into weekly theme
        - Check alignment with north stars

        Returns strategic insight if found.
        """
        cur_state = self._get_curator_state()
        daily_summaries = cur_state.get("daily_summaries", [])[-7:]

        if len(daily_summaries) < 3:
            cur_state["last_weekly"] = datetime.now().isoformat()
            self._save_curator_state(cur_state)
            return None

        mem_state = self.memory.get_state()

        weekly_prompt = f"""Analyze this week's patterns.

DAILY SUMMARIES:
{json.dumps(daily_summaries, indent=2)}

NORTH STARS: {mem_state.get('north_stars', [])}
PRIORITIES: {mem_state.get('priorities', [])}
PATTERNS: {list(mem_state.get('patterns', {}).keys())}

Return JSON:
{{
    "weekly_theme": "2-3 word theme",
    "alignment": "brief note on north star alignment",
    "strategic_insight": "one key observation"
}}

Return ONLY valid JSON."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": weekly_prompt}]
        )

        try:
            result = _parse_json_response(response.content[0].text)

            cur_state["last_weekly"] = datetime.now().isoformat()
            cur_state["weekly_themes"].append({
                "week_of": datetime.now().strftime("%Y-%m-%d"),
                "theme": result.get("weekly_theme", ""),
                "alignment": result.get("alignment", "")
            })
            cur_state["weekly_themes"] = cur_state["weekly_themes"][-8:]

            self._save_curator_state(cur_state)

            return result.get("strategic_insight")

        except (json.JSONDecodeError, KeyError):
            cur_state["last_weekly"] = datetime.now().isoformat()
            self._save_curator_state(cur_state)
            return None

    def run_if_needed(self) -> list[str]:
        """
        Run curation if needed. Returns list of insights to surface.
        Called when The Assist starts.
        """
        insights = []

        if self.needs_weekly():
            weekly_insight = self.run_weekly()
            if weekly_insight:
                insights.append(f"[Weekly] {weekly_insight}")

        if self.needs_daily():
            daily_insight = self.run_daily()
            if daily_insight:
                insights.append(f"[Daily] {daily_insight}")

        return insights

    def get_unsurfaced_insights(self) -> list[str]:
        """Get insights that haven't been shown to user yet."""
        state = self._get_curator_state()
        unsurfaced = []

        for i, insight in enumerate(state.get("insights", [])):
            if not insight.get("surfaced"):
                unsurfaced.append(insight["insight"])
                state["insights"][i]["surfaced"] = True

        if unsurfaced:
            self._save_curator_state(state)

        return unsurfaced
