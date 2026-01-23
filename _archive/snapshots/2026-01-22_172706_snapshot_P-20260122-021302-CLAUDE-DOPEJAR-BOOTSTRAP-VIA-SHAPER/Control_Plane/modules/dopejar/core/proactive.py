"""The Assist - Proactive Behaviors

Implements intuition-first interaction:
1. Surface what WE think matters (don't ask)
2. Let user react - confirm, correct, or pivot
3. Calibrate based on reaction
4. Escalate to direct questions only after misses

This is the Donna Principle in code.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
import anthropic

from dopejar.config.settings import MODEL, MEMORY_DIR
from dopejar.core.memory_v2 import CompressedMemory, COACHING_CODES


class ProactiveEngine:
    """Generates intuition-based nudges instead of questions."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.memory = CompressedMemory()
        self.state_file = os.path.join(MEMORY_DIR, "proactive", "state.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        if not os.path.exists(self.state_file):
            with open(self.state_file, 'w') as f:
                json.dump({
                    "intuition_history": [],  # Track hits/misses
                    "directness_level": 0,    # 0=soft, 1=medium, 2=direct
                    "last_nudge": None,
                    "consecutive_misses": 0,
                    "session_nudges": []
                }, f)

    def _load_state(self) -> dict:
        with open(self.state_file, 'r') as f:
            return json.load(f)

    def _save_state(self, state: dict):
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def generate_opening(self) -> str:
        """
        Generate an intuition-based opening instead of "What's on your mind?"

        Returns a statement about what WE think matters, inviting reaction.
        """
        mem_state = self.memory.get_state()
        pro_state = self._load_state()

        directness = pro_state.get("directness_level", 0)

        # Get coaching instructions that affect opening format
        coaching = mem_state.get("coaching", {})
        coaching_instructions = []
        for code, confidence in coaching.items():
            if confidence >= 0.7 and code in COACHING_CODES:
                coaching_instructions.append(f"- {code}: {COACHING_CODES[code]}")

        coaching_text = ""
        if coaching_instructions:
            coaching_text = f"""
COACHING INSTRUCTIONS (learned from user corrections - MUST follow):
{chr(10).join(coaching_instructions)}
"""

        # Build context for AI
        now = datetime.now()
        day_of_week = now.strftime("%A")

        prompt = f"""You are The Assist, a cognitive anchor. Generate an OPENING statement.

MEMORY STATE:
{json.dumps(mem_state, indent=2)}

TODAY: {day_of_week}, {now.strftime("%B %d")}
DIRECTNESS LEVEL: {directness} (0=soft intuition, 1=medium, 2=direct question)
CONSECUTIVE MISSES: {pro_state.get("consecutive_misses", 0)}
{coaching_text}
RULES:
- Level 0 (soft): Lead with what YOU think matters. Make a statement, not a question.
  Example: "Gaurav's been the blocker for a while now. That might be worth pushing on."
  Example: "Sunday's patent session is coming up. The prototype mapping could use clarity."

- Level 1 (medium): Slightly more direct, but still intuition-first.
  Example: "I keep seeing Gaurav come up. Is he still the main thing in your way?"

- Level 2 (direct): Ask directly after multiple misses.
  Example: "I've been guessing wrong. What's actually the critical path right now?"

ALSO CONSIDER:
- Forgotten commitments (calendar desync pattern)
- Recurring bottlenecks (people who block repeatedly)
- Time-sensitive items (things with dates)
- Patterns that suggest stress or overload

IMPORTANT: If coaching includes "cap_with_question", you MUST end your opening with
a strategic open-ended question based on what you see across all memory and assessments.

Return JSON:
{{
    "opening": "your opening statement",
    "intuition_target": "topic:reason",  // What you're probing, for tracking
    "confidence": 0.7  // How confident in this intuition
}}

Return ONLY valid JSON."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
            result = json.loads(text.strip())

            # Track this nudge
            pro_state["last_nudge"] = {
                "timestamp": datetime.now().isoformat(),
                "target": result.get("intuition_target", "unknown"),
                "confidence": result.get("confidence", 0.5),
                "resolved": False
            }
            pro_state["session_nudges"].append(pro_state["last_nudge"])
            self._save_state(pro_state)

            return result.get("opening", "What's on your mind?")

        except (json.JSONDecodeError, KeyError):
            return "What's on your mind?"

    def generate_mid_conversation_nudge(self, recent_exchange: str) -> Optional[str]:
        """
        Generate a mid-conversation intuition nudge.

        Called after exchanges to see if we should surface something.
        Returns None if no nudge needed.
        """
        mem_state = self.memory.get_state()
        pro_state = self._load_state()

        # Don't nudge too often
        session_nudges = pro_state.get("session_nudges", [])
        if len(session_nudges) >= 3:
            return None

        prompt = f"""You are The Assist. Based on this exchange, decide if you should surface an intuition.

RECENT EXCHANGE:
{recent_exchange[:1000]}

MEMORY STATE:
{json.dumps(mem_state, indent=2)}

Should you nudge? Only if:
1. User mentioned something that connects to a known pattern/commitment
2. There's a collision or conflict they might not see
3. They seem to be avoiding something important
4. Energy/stress signals suggest checking in

If YES, return JSON:
{{
    "nudge": "your intuition statement (not a question)",
    "reason": "why this nudge"
}}

If NO nudge needed, return:
{{"nudge": null}}

Return ONLY valid JSON."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
            result = json.loads(text.strip())

            nudge = result.get("nudge")
            if nudge:
                pro_state["session_nudges"].append({
                    "timestamp": datetime.now().isoformat(),
                    "nudge": nudge,
                    "reason": result.get("reason", "")
                })
                self._save_state(pro_state)

            return nudge

        except (json.JSONDecodeError, KeyError):
            return None

    def record_reaction(self, reaction_type: str):
        """
        Record how user reacted to our intuition.

        reaction_type: "confirmed" | "corrected" | "ignored" | "pivoted"
        """
        pro_state = self._load_state()

        if pro_state.get("last_nudge"):
            pro_state["last_nudge"]["resolved"] = True
            pro_state["last_nudge"]["reaction"] = reaction_type

            # Track in history
            pro_state["intuition_history"].append({
                "timestamp": datetime.now().isoformat(),
                "target": pro_state["last_nudge"].get("target"),
                "reaction": reaction_type
            })
            pro_state["intuition_history"] = pro_state["intuition_history"][-50:]

            # Adjust directness based on reaction
            if reaction_type == "confirmed":
                pro_state["consecutive_misses"] = 0
                # Lower directness if we're hitting
                pro_state["directness_level"] = max(0, pro_state.get("directness_level", 0) - 1)
            elif reaction_type in ("corrected", "pivoted"):
                pro_state["consecutive_misses"] = pro_state.get("consecutive_misses", 0) + 1
                # Increase directness after misses
                if pro_state["consecutive_misses"] >= 3:
                    pro_state["directness_level"] = min(2, pro_state.get("directness_level", 0) + 1)

            self._save_state(pro_state)

    def analyze_response_for_reaction(self, user_response: str) -> str:
        """
        Analyze user's response to determine reaction type.
        Returns: "confirmed" | "corrected" | "ignored" | "pivoted"
        """
        pro_state = self._load_state()
        last_nudge = pro_state.get("last_nudge", {})

        if not last_nudge or last_nudge.get("resolved"):
            return "ignored"

        prompt = f"""Analyze how the user reacted to this intuition.

OUR INTUITION TARGET: {last_nudge.get("target", "unknown")}

USER'S RESPONSE: {user_response}

Classify the reaction:
- "confirmed": User agreed or engaged with our intuition
- "corrected": User said no, that's not it, and gave the real issue
- "pivoted": User changed topic without addressing our intuition
- "ignored": User didn't engage with our nudge at all

Return ONLY one word: confirmed, corrected, pivoted, or ignored"""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}]
        )

        reaction = response.content[0].text.strip().lower()
        if reaction not in ("confirmed", "corrected", "pivoted", "ignored"):
            reaction = "ignored"

        return reaction

    def get_directness_level(self) -> int:
        """Get current directness level (0-2)."""
        return self._load_state().get("directness_level", 0)

    def get_hit_rate(self) -> float:
        """Get intuition hit rate (confirmed / total)."""
        history = self._load_state().get("intuition_history", [])
        if not history:
            return 0.5
        confirmed = sum(1 for h in history if h.get("reaction") == "confirmed")
        return confirmed / len(history)

    def reset_session(self):
        """Reset session-specific state."""
        pro_state = self._load_state()
        pro_state["session_nudges"] = []
        pro_state["last_nudge"] = None
        self._save_state(pro_state)
