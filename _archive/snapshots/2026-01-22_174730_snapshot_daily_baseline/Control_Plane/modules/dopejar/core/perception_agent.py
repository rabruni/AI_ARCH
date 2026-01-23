"""The Assist - Perception Agent

Fresh-context agent that observes conversation without being inside it.
Like Donna watching through the glass - sees patterns Harvey can't.

Key insight: This agent's context is NOT polluted by the conversation.
It reads history as data, not as participant. This is the Chinese wall.

Outputs:
- elevation_level: L1-L4 (where is the conversation?)
- topic_saturation: topics that are being over-discussed
- trajectory: where is this heading?
- sentiment: user emotional state
- blocked_topics: explicit user requests to stop discussing something
"""
import anthropic
from typing import Optional
from datetime import datetime

from dopejar.config.settings import MODEL


class PerceptionAgent:
    """
    Fresh-context observer of conversation dynamics.

    Runs as separate API call = fresh context window.
    Cannot be polluted by being inside the conversation.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()

    def perceive(self, conversation_history: list, memory_state: dict) -> dict:
        """
        Analyze conversation from the outside.

        This is a FRESH API call - no conversation context pollution.
        The agent sees patterns the orchestrator is blind to.

        Returns structured perception data.
        """
        if len(conversation_history) < 2:
            return self._default_perception()

        # Format conversation for analysis (agent reads as observer, not participant)
        formatted = self._format_for_analysis(conversation_history)

        # Get north stars and patterns for context
        north_stars = memory_state.get("north_stars", [])
        patterns = list(memory_state.get("patterns", {}).keys())
        active_topics = [a.split(":")[0] for a in memory_state.get("active", [])]

        perception_prompt = f"""You are a perception agent. You observe conversations from OUTSIDE.
You are not a participant. You see patterns the participants cannot see.

CONVERSATION HISTORY (you are reading this, not participating):
{formatted}

USER'S NORTH STARS: {north_stars}
KNOWN USER PATTERNS: {patterns}
CURRENTLY ACTIVE TOPICS IN MEMORY: {active_topics}

Analyze and return JSON with these fields:

{{
    "elevation_level": "L1|L2|L3|L4",  // L1=moment, L2=operations, L3=strategy, L4=identity
    "elevation_mismatch": true/false,  // Is conversation at wrong level for topic?
    "topic_saturation": [              // Topics discussed too much
        {{"topic": "x", "mentions": N, "saturation": "low|medium|high|critical"}}
    ],
    "trajectory": {{
        "heading": "tactical_drift|strategic|identity|balanced|stuck",
        "prediction": "what will happen if this continues",
        "intervention_needed": true/false
    }},
    "sentiment": {{
        "user_state": "engaged|frustrated|bored|resistant|exploratory",
        "frustration_signals": ["signal1"],  // empty if none
        "trust_level": "building|stable|eroding"
    }},
    "blocked_topics": [                // Explicit "stop talking about X"
        {{"topic": "x", "strength": "hint|request|demand", "quote": "user's words"}}
    ],
    "north_star_connection": {{
        "connected": true/false,
        "which_stars": ["star1"],  // empty if none
        "opportunity": "how to connect if not connected"
    }},
    "recommended_stance": "challenge|support|redirect|elevate|ground"
}}

CRITICAL RULES:
1. Look for user frustration signals: cursing, repetition, "I said...", caps
2. "Critical" saturation = user has explicitly asked to stop OR 5+ mentions
3. If user says anything like "stop", "enough", "move on" about a topic = blocked
4. Trajectory "stuck" = same topic for 4+ exchanges without progress
5. Elevation mismatch = discussing L2 tasks without L3/L4 context established

Return ONLY valid JSON."""

        try:
            # FRESH API CALL - this is the Chinese wall
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Fast model for perception
                max_tokens=800,
                messages=[{"role": "user", "content": perception_prompt}]
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]

            import json
            return json.loads(text.strip())

        except Exception as e:
            return self._default_perception()

    def _format_for_analysis(self, history: list) -> str:
        """Format conversation history for perception analysis."""
        lines = []
        for i, msg in enumerate(history[-12:], 1):  # Last 12 messages max
            role = msg["role"].upper()
            content = msg["content"][:500]  # Truncate long messages
            lines.append(f"[{i}] {role}: {content}")
        return "\n\n".join(lines)

    def _default_perception(self) -> dict:
        """Default perception when analysis not possible."""
        return {
            "elevation_level": "L2",
            "elevation_mismatch": False,
            "topic_saturation": [],
            "trajectory": {
                "heading": "balanced",
                "prediction": "insufficient data",
                "intervention_needed": False
            },
            "sentiment": {
                "user_state": "engaged",
                "frustration_signals": [],
                "trust_level": "stable"
            },
            "blocked_topics": [],
            "north_star_connection": {
                "connected": False,
                "which_stars": [],
                "opportunity": ""
            },
            "recommended_stance": "support"
        }

    def detect_explicit_blocks(self, user_message: str) -> list:
        """
        Quick check for explicit blocking language in current message.
        Called immediately when new message arrives.

        Returns list of blocked topics if detected.
        """
        block_signals = [
            "stop talking about",
            "enough about",
            "move on from",
            "drop the",
            "forget about",
            "stop bringing up",
            "done with",
            "sick of hearing about",
            "stop mentioning",
        ]

        message_lower = user_message.lower()
        blocks = []

        for signal in block_signals:
            if signal in message_lower:
                # Extract topic after the signal
                idx = message_lower.index(signal) + len(signal)
                remaining = user_message[idx:].strip()
                # Take first few words as topic
                topic = " ".join(remaining.split()[:3]).strip(".,!?")
                if topic:
                    blocks.append({
                        "topic": topic,
                        "strength": "demand",
                        "detected_at": datetime.now().isoformat()
                    })

        # Check for frustration indicators
        if any(word in message_lower for word in ["damn", "hell", "shit", "fuck", "goddamn"]):
            # User is frustrated - weight recent topics as potentially blocked
            blocks.append({
                "topic": "_frustration_detected_",
                "strength": "signal",
                "detected_at": datetime.now().isoformat()
            })

        return blocks
