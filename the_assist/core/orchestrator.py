"""The Assist - Core Orchestrator

The main brain. Handles conversation, context, and AI interaction.
"""
import os
from datetime import datetime
import anthropic
from typing import Optional

from the_assist.config.settings import MODEL, MAX_TOKENS, PROMPTS_DIR, MEMORY_DIR
from the_assist.core.memory import Memory  # v1 - kept for conversation saving
from the_assist.core.memory_v2 import CompressedMemory, PATTERN_CODES, COACHING_CODES
from the_assist.core.proactive import ProactiveEngine
from the_assist.core.ai_reflection import AIReflection
from the_assist.core.integrity import get_boot_context_for_ai
from the_assist.core.perception_agent import PerceptionAgent
from the_assist.core.hrm_agent import HRMAgent


class Orchestrator:
    """The cognitive core of The Assist."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.memory = CompressedMemory()  # v2 compressed
        self.memory_v1 = Memory()  # v1 kept for conversation saving
        self.proactive = ProactiveEngine()  # Intuition-first interaction
        self.system_prompt = self._load_system_prompt()
        self.conversation_history = []
        self._last_user_input = None  # For reaction tracking

        # Multi-agent architecture - fresh context agents
        self.perception = PerceptionAgent()  # Observes from outside
        self.hrm = HRMAgent()  # Strategic adjustment
        self._last_hrm_injection = ""  # Track for debugging

    def _load_system_prompt(self) -> str:
        """Load the system prompt."""
        path = os.path.join(PROMPTS_DIR, 'system.md')
        with open(path, 'r') as f:
            return f.read()

    def _get_ai_behavioral_guidance(self) -> str:
        """
        Get behavioral guidance from AI reflection - the feedback loop.
        Recent failures, improvements, and patterns inform current behavior.
        """
        try:
            reflector = AIReflection()
            summary = reflector.get_ai_performance_summary()

            guidance_parts = []

            # Recent failures to avoid
            failures = summary.get("recent_failures", [])
            if failures:
                guidance_parts.append("AVOID:" + "|".join(f[:40] for f in failures[-2:]))

            # Improvement actions to implement
            improvements = summary.get("improvement_actions", [])
            if improvements:
                guidance_parts.append("IMPROVE:" + "|".join(i[:40] for i in improvements[-2:]))

            # Recent strengths to continue
            strengths = summary.get("recent_strengths", [])
            if strengths:
                guidance_parts.append("CONTINUE:" + "|".join(s[:40] for s in strengths[-2:]))

            # Trend direction
            trend = summary.get("trend_direction", "unknown")
            if trend in ["declining", "improving"]:
                guidance_parts.append(f"TREND:{trend}")

            # Low-scoring dimensions to focus on
            scores = summary.get("avg_quality_scores", {})
            low_scores = [dim for dim, score in scores.items() if score and score < 0.6]
            if low_scores:
                guidance_parts.append("FOCUS:" + "|".join(low_scores[:3]))

            return "\n".join(guidance_parts) if guidance_parts else ""

        except Exception:
            return ""  # Graceful degradation

    def _build_full_context(self) -> str:
        """Build full system context including memory (v2 compressed)."""
        memory_context = self.memory.build_context()
        ai_guidance = self._get_ai_behavioral_guidance()
        boot_context = get_boot_context_for_ai()
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")

        # Get north stars for anchoring
        mem_state = self.memory.get_state()
        north_stars = mem_state.get("north_stars", [])

        # North star anchor - inject every few exchanges for breadth
        north_star_anchor = ""
        if north_stars and len(self.conversation_history) >= 4:
            north_star_anchor = f"""
NORTH STAR ANCHOR: Every response should connect to at least one of: {', '.join(north_stars)}
If current topic doesn't connect, acknowledge that or pivot to what matters.
"""

        context = f"""{self.system_prompt}

---

# Context

DATE:{date_str}|TIME:{time_str}
{north_star_anchor}
{memory_context}
"""
        # Add boot context if there are warnings/issues
        if boot_context:
            context += f"""
# Boot Status
{boot_context}
NOTE: If there are warnings above, you may want to acknowledge them or explain relevant context to the user.
"""

        # Add AI behavioral guidance if available (the feedback loop)
        if ai_guidance:
            context += f"""
# Self-Calibration (from recent session analysis)
{ai_guidance}
"""
        return context

    def get_opening(self) -> str:
        """Get intuition-based opening instead of generic prompt."""
        return self.proactive.generate_opening()

    def _perception_check(self) -> str:
        """
        Predictive perception: detect TRAJECTORY toward problems, not problems themselves.
        Intervene BEFORE mistakes happen, like Donna would.

        This is anticipatory, not reactive.
        """
        if len(self.conversation_history) < 3:
            return ""  # Need minimal history

        # Get recent exchanges - fewer needed for prediction
        recent = self.conversation_history[-4:]
        recent_text = "\n".join([
            f"{m['role'].upper()}: {m['content'][:200]}"
            for m in recent
        ])

        # Get memory for north stars and coaching
        mem_state = self.memory.get_state()
        north_stars = mem_state.get("north_stars", [])
        coaching = list(mem_state.get("coaching", {}).keys())

        check_prompt = f"""You are a predictive perception system. Anticipate where this conversation is HEADING, not where it is.

RECENT EXCHANGES:
{recent_text}

USER'S NORTH STARS: {north_stars}
LEARNED COACHING: {coaching}

Predict trajectory - look for EARLY signs of:
1. Topic narrowing that will lead to tunnel vision
2. Tactical drift away from strategic value
3. Patterns that previously led to corrections
4. Missed opportunities to connect to north stars
5. Assistant being helpful instead of being a partner

The goal is to intervene BEFORE the problem, not after.

Return JSON:
{{
    "trajectory_concern": true/false,
    "prediction": "what will go wrong if we continue this path",
    "intervention": "what to do NOW to change trajectory, or empty string",
    "opportunity": "what valuable direction we could pivot to"
}}

Think like Donna - she doesn't wait for Harvey to fail. She sees it coming and redirects.
Return ONLY valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Fast model for check
                max_tokens=300,
                messages=[{"role": "user", "content": check_prompt}]
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]

            import json
            result = json.loads(text.strip())

            if result.get("trajectory_concern"):
                parts = []
                if result.get("intervention"):
                    parts.append(f"REDIRECT: {result['intervention']}")
                if result.get("opportunity"):
                    parts.append(f"OPPORTUNITY: {result['opportunity']}")
                if result.get("prediction"):
                    parts.append(f"(Avoiding: {result['prediction']})")
                return "\n".join(parts) if parts else ""
            return ""

        except Exception:
            return ""  # Fail silently - don't break conversation

    def chat(self, user_message: str) -> str:
        """Process a user message and return response."""
        # Track for reaction analysis
        if self._last_user_input is None and len(self.conversation_history) == 0:
            # This is first response after opening - analyze reaction
            reaction = self.proactive.analyze_response_for_reaction(user_message)
            self.proactive.record_reaction(reaction)

        self._last_user_input = user_message

        # IMMEDIATE: Check for explicit blocks in this message
        explicit_blocks = self.perception.detect_explicit_blocks(user_message)
        for block in explicit_blocks:
            if block["topic"] != "_frustration_detected_":
                self.hrm.add_blocked_topic(block["topic"], block["strength"])

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # ============================================================
        # MULTI-AGENT FLOW - Fresh context agents before main call
        # ============================================================

        # Step 1: Perception Agent (fresh context - Chinese wall #1)
        mem_state = self.memory.get_state()
        perception_data = self.perception.perceive(
            self.conversation_history,
            mem_state
        )

        # Step 2: HRM Agent (fresh context - Chinese wall #2)
        hrm_adjustments = self.hrm.adjust_prompt(
            perception_data,
            mem_state
        )

        # Step 3: Build HRM injection for orchestrator
        hrm_injection = self.hrm.build_orchestrator_injection(hrm_adjustments)
        self._last_hrm_injection = hrm_injection  # Track for debugging

        # ============================================================
        # Build context with HRM guidance
        # ============================================================
        system_context = self._build_full_context()

        # Inject HRM guidance (this is where the Chinese walls pay off)
        if hrm_injection:
            system_context += f"\n{hrm_injection}\n"

        # Legacy perception check (kept for redundancy, may remove later)
        perception_injection = self._perception_check()
        if perception_injection:
            system_context += f"""
# Predictive Perception
{perception_injection}
ACT ON THIS: Don't wait for a mistake. Change course now. Be a partner, not a helper.
"""

        # Call Claude
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_context,
            messages=self.conversation_history
        )

        # Extract response
        assistant_message = response.content[0].text

        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Decrement cooldowns after each exchange
        self.hrm.decrement_cooldowns()

        return assistant_message

    def process_for_memory(self, user_input: str, ai_response: str):
        """
        Extract memory items in compressed v2 format.
        AI extracts structured data, not prose.
        Also detects coaching moments (user teaching AI how to behave).
        """
        pattern_codes_str = ", ".join(PATTERN_CODES.keys())
        coaching_codes_str = ", ".join(COACHING_CODES.keys())

        extraction_prompt = f"""Extract memory items from this exchange in COMPRESSED format.

User: {user_input}
Assistant: {ai_response}

Return JSON with these fields (only include if relevant):
{{
    "active": ["topic:status:detail"],     // New active threads, format topic:status:detail
    "commits": ["what:when:context"],      // New commitments, format what:when:context
    "people": [{{"name":"x","rel":"work_colleague|family|friend","tags":["tag1"]}}],
    "patterns": ["code"],                  // User behavior patterns from: {pattern_codes_str}
    "coaching": ["code"],                  // How AI should behave from: {coaching_codes_str}
    "clear_commits": ["topic"]             // Commits that are now done (topic prefix to remove)
}}

IMPORTANT - coaching codes detect when user is teaching AI how to interact better:
- If user asks for bigger picture questions → "ask_impact", "strategic_questions"
- If user wants tasks connected to goals → "connect_layers", "surface_why"
- If user wants more pushback → "push_harder", "challenge_alignment"
- If user wants less explaining → "more_concise", "less_questions"

Be aggressive about compression. Use codes not prose. Return ONLY valid JSON, or {{}} if nothing."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": extraction_prompt}]
        )

        try:
            import json
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
            extracted = json.loads(text.strip())

            # Update compressed memory
            for item in extracted.get('active', []):
                self.memory.add_active(item)

            for item in extracted.get('commits', []):
                self.memory.add_commit(item)

            for topic in extracted.get('clear_commits', []):
                self.memory.clear_commit(topic)

            for person in extracted.get('people', []):
                if isinstance(person, dict) and 'name' in person:
                    self.memory.add_person(
                        person['name'],
                        person.get('rel', 'unknown'),
                        person.get('tags', [])
                    )

            for code in extracted.get('patterns', []):
                self.memory.add_pattern(code)

            # Save coaching instructions (how AI should behave)
            for code in extracted.get('coaching', []):
                self.memory.add_coaching(code)

        except (json.JSONDecodeError, KeyError):
            pass  # Silently fail - memory extraction is nice-to-have

    def end_session(self, summary: Optional[str] = None):
        """End the current session and save conversation."""
        if self.conversation_history:
            # If no summary provided, ask AI to generate one
            if not summary and len(self.conversation_history) > 2:
                summary_prompt = "Summarize this conversation in one sentence for future reference."
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=100,
                    messages=self.conversation_history + [{"role": "user", "content": summary_prompt}]
                )
                summary = response.content[0].text

            # Use v1 memory for conversation archival
            self.memory_v1.save_conversation(self.conversation_history, summary)
            self.conversation_history = []
