"""The Assist - HRM (Hierarchical Reasoning Model) Agent

Fresh-context agent that adjusts orchestrator behavior based on perception.
Takes perception output + user patterns and produces prompt adjustments.

This is the strategic brain that prevents tactical drift.
It can't be polluted by conversation - it only sees structured data.

The flow:
1. Perception agent outputs structured analysis
2. HRM agent receives analysis + user baseline
3. HRM outputs prompt adjustments/blocks for orchestrator
4. Orchestrator receives ADJUSTED prompt, not raw conversation
"""
import anthropic
from typing import Optional
import os
import json

from the_assist.config.settings import MODEL, MEMORY_DIR


class HRMAgent:
    """
    Fresh-context strategic adjustment agent.

    Reads perception + patterns, outputs orchestrator guidance.
    Cannot see conversation directly - only through perception's lens.
    This is the second Chinese wall.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.blocked_topics_file = os.path.join(MEMORY_DIR, "hrm", "blocked_topics.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(self.blocked_topics_file), exist_ok=True)
        if not os.path.exists(self.blocked_topics_file):
            with open(self.blocked_topics_file, 'w') as f:
                json.dump({"blocked": [], "cooldowns": {}}, f)

    def _load_blocked(self) -> dict:
        try:
            with open(self.blocked_topics_file, 'r') as f:
                return json.load(f)
        except:
            return {"blocked": [], "cooldowns": {}}

    def _save_blocked(self, data: dict):
        with open(self.blocked_topics_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_blocked_topic(self, topic: str, strength: str = "demand"):
        """Add a topic to the blocked list (persists across sessions)."""
        data = self._load_blocked()
        # Check if already blocked
        for b in data["blocked"]:
            if b["topic"].lower() == topic.lower():
                b["strength"] = strength  # Upgrade strength if needed
                self._save_blocked(data)
                return
        data["blocked"].append({
            "topic": topic,
            "strength": strength,
            "added": __import__("datetime").datetime.now().isoformat()
        })
        self._save_blocked(data)

    def add_cooldown(self, topic: str, exchanges: int = 5):
        """Add a topic cooldown (temporary suppression)."""
        data = self._load_blocked()
        data["cooldowns"][topic.lower()] = {
            "remaining": exchanges,
            "added": __import__("datetime").datetime.now().isoformat()
        }
        self._save_blocked(data)

    def decrement_cooldowns(self):
        """Called each exchange to decrement cooldowns."""
        data = self._load_blocked()
        expired = []
        for topic, cd in data["cooldowns"].items():
            cd["remaining"] -= 1
            if cd["remaining"] <= 0:
                expired.append(topic)
        for topic in expired:
            del data["cooldowns"][topic]
        self._save_blocked(data)

    def get_active_blocks(self) -> dict:
        """Get currently blocked topics and cooldowns."""
        return self._load_blocked()

    def adjust_prompt(self, perception: dict, memory_state: dict, user_baseline: dict = None) -> dict:
        """
        Generate prompt adjustments based on perception.

        This is a FRESH API call - no conversation pollution.
        Returns adjustments for orchestrator.
        """
        # Get blocked topics
        blocks = self.get_active_blocks()

        # Add any new blocked topics from perception
        for block in perception.get("blocked_topics", []):
            if block.get("strength") in ["demand", "request"]:
                self.add_blocked_topic(block["topic"], block["strength"])

        # Add cooldowns for saturated topics
        for sat in perception.get("topic_saturation", []):
            if sat.get("saturation") in ["high", "critical"]:
                self.add_cooldown(sat["topic"], exchanges=5)

        # Build context for HRM reasoning
        north_stars = memory_state.get("north_stars", [])
        coaching = memory_state.get("coaching", {})
        patterns = memory_state.get("patterns", {})

        hrm_prompt = f"""You are the HRM (Hierarchical Reasoning Model) agent.
You receive perception data and produce orchestrator adjustments.
You cannot see the conversation - only what perception tells you.

PERCEPTION DATA:
{json.dumps(perception, indent=2)}

BLOCKED TOPICS (explicit user requests - NEVER mention these):
{json.dumps(blocks.get("blocked", []), indent=2)}

TOPIC COOLDOWNS (temporarily suppress):
{json.dumps(blocks.get("cooldowns", {}), indent=2)}

USER'S NORTH STARS: {north_stars}
COACHING CODES (learned interaction patterns): {list(coaching.keys())}
BEHAVIORAL PATTERNS: {list(patterns.keys())}

Generate orchestrator adjustments. Return JSON:

{{
    "elevation_gate": {{
        "current_level": "L1|L2|L3|L4",
        "required_level": "L1|L2|L3|L4",  // Must establish this before descending
        "block_descent": true/false,      // Block tactical until strategic established
        "elevation_prompt": "string to inject if blocking descent"
    }},
    "topic_blocks": [
        {{"topic": "x", "reason": "user_blocked|saturated|cooldown", "substitute": "alternative topic"}}
    ],
    "stance_adjustment": {{
        "recommended": "challenge|support|redirect|elevate|ground",
        "intensity": "gentle|firm|direct",
        "reason": "why this stance"
    }},
    "north_star_injection": {{
        "needed": true/false,
        "prompt": "reminder to connect to north stars if needed"
    }},
    "frustration_response": {{
        "detected": true/false,
        "prompt": "how to handle if frustrated"
    }},
    "coaching_reminders": [
        "specific coaching code to emphasize this exchange"
    ],
    "meta_prompt": "any additional context/instruction to inject into orchestrator"
}}

RULES:
1. If perception shows frustration, stance should be "support" with "direct" intensity
2. If elevation_mismatch, block_descent should be true
3. Blocked topics should NEVER appear in orchestrator output
4. If trajectory is "stuck", recommend "redirect" stance
5. If north_star_connection is false and >4 exchanges, north_star_injection needed

Return ONLY valid JSON."""

        try:
            # FRESH API CALL - second Chinese wall
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Fast model
                max_tokens=800,
                messages=[{"role": "user", "content": hrm_prompt}]
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]

            adjustments = json.loads(text.strip())

            # Ensure topic_blocks includes all blocked/cooldown topics
            existing_blocks = {b["topic"] for b in adjustments.get("topic_blocks", [])}
            for block in blocks.get("blocked", []):
                if block["topic"] not in existing_blocks:
                    adjustments.setdefault("topic_blocks", []).append({
                        "topic": block["topic"],
                        "reason": "user_blocked",
                        "substitute": ""
                    })
            for topic in blocks.get("cooldowns", {}):
                if topic not in existing_blocks:
                    adjustments.setdefault("topic_blocks", []).append({
                        "topic": topic,
                        "reason": "cooldown",
                        "substitute": ""
                    })

            return adjustments

        except Exception as e:
            return self._default_adjustments()

    def _default_adjustments(self) -> dict:
        """Default adjustments when analysis not possible."""
        return {
            "elevation_gate": {
                "current_level": "L2",
                "required_level": "L2",
                "block_descent": False,
                "elevation_prompt": ""
            },
            "topic_blocks": [],
            "stance_adjustment": {
                "recommended": "support",
                "intensity": "gentle",
                "reason": "default"
            },
            "north_star_injection": {
                "needed": False,
                "prompt": ""
            },
            "frustration_response": {
                "detected": False,
                "prompt": ""
            },
            "coaching_reminders": [],
            "meta_prompt": ""
        }

    def build_orchestrator_injection(self, adjustments: dict) -> str:
        """
        Convert adjustments to orchestrator prompt injection.

        This is what gets added to the orchestrator's system context.
        """
        parts = []

        # Elevation gate
        eg = adjustments.get("elevation_gate", {})
        if eg.get("block_descent"):
            parts.append(f"ELEVATION GATE: Must establish {eg.get('required_level', 'L3')} context before discussing {eg.get('current_level', 'L2')} details.")
            if eg.get("elevation_prompt"):
                parts.append(eg["elevation_prompt"])

        # Topic blocks - critical, these must not appear
        blocks = adjustments.get("topic_blocks", [])
        if blocks:
            block_list = [b["topic"] for b in blocks]
            parts.append(f"BLOCKED TOPICS (DO NOT MENTION): {', '.join(block_list)}")
            substitutes = [(b["topic"], b.get("substitute", "")) for b in blocks if b.get("substitute")]
            if substitutes:
                sub_str = ", ".join([f"{t}→{s}" for t, s in substitutes])
                parts.append(f"SUBSTITUTIONS: {sub_str}")

        # Stance
        stance = adjustments.get("stance_adjustment", {})
        if stance.get("recommended"):
            parts.append(f"STANCE: {stance['recommended']} ({stance.get('intensity', 'gentle')})")

        # North star
        ns = adjustments.get("north_star_injection", {})
        if ns.get("needed") and ns.get("prompt"):
            parts.append(f"NORTH STAR REMINDER: {ns['prompt']}")

        # Frustration
        frust = adjustments.get("frustration_response", {})
        if frust.get("detected"):
            parts.append("USER FRUSTRATED: Acknowledge, don't deflect. Be direct.")
            if frust.get("prompt"):
                parts.append(frust["prompt"])

        # Coaching
        coaching = adjustments.get("coaching_reminders", [])
        if coaching:
            parts.append(f"COACHING FOCUS: {', '.join(coaching)}")

        # Meta
        meta = adjustments.get("meta_prompt", "")
        if meta:
            parts.append(meta)

        if parts:
            return "\n# HRM Guidance (follow strictly)\n" + "\n".join(parts)
        return ""
