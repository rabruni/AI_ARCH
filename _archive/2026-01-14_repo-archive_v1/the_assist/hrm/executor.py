"""HRM Layer 3: Executor

Takes plan, does the work, reports state.

This layer:
- Performs reasoning
- Applies rules
- Generates text/responses
- Handles details

Memory: Ephemeral, disposable, high volume (conversation history).

The Executor does NOT decide meaning. It reports STATE.
It does NOT modify intent. It does NOT revise plans.
It follows the plan and reports what happened.
"""
import os
import anthropic
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from pathlib import Path

from the_assist.config.settings import MODEL, MAX_TOKENS, PROMPTS_DIR
from the_assist.hrm.planner import Plan, Planner, Situation


@dataclass
class ExecutionResult:
    """Result of execution. State report for Evaluator."""
    response: str                   # The actual response to user
    topics_discussed: list[str]     # What topics were covered
    altitude_used: str              # What altitude was actually used
    plan_followed: bool             # Did we follow the plan?
    deviation_reason: Optional[str] = None  # Why deviated if not followed
    user_signals: list[str] = None  # Signals detected (frustration, etc.)


class Executor:
    """
    L3: The execution layer.

    This is the only layer that holds conversation context.
    Context is ephemeral - disposable after session.

    Executor receives plan, generates response, reports state.
    Does NOT evaluate. Does NOT plan. Does NOT modify intent.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.system_prompt = self._load_system_prompt()
        self.conversation_history = []  # Ephemeral, disposable

    def _load_system_prompt(self) -> str:
        """Load base system prompt."""
        path = os.path.join(PROMPTS_DIR, 'system.md')
        with open(path, 'r') as f:
            return f.read()

    def execute(self, plan: Plan, user_input: str, planner: Planner,
                history_context: str = None) -> ExecutionResult:
        """
        Execute the plan with the given user input.

        Args:
            plan: The plan to execute
            user_input: User's message
            planner: Planner instance for building context
            history_context: Optional session history for continuity questions

        Returns state report (not meaning).
        """
        # Add user message to ephemeral history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Build system context with plan injection
        plan_context = planner.build_context_for_executor(plan)

        # Include history context if this is a continuity question
        history_section = ""
        if history_context:
            history_section = f"""
---

{history_context}

Use this context to answer questions about previous sessions.
"""

        system_context = f"""{self.system_prompt}

---

{plan_context}
{history_section}
EXECUTOR RULES:
1. Follow the plan. You are executing, not deciding.
2. Stay at the specified altitude ({plan.altitude}).
3. Use the specified stance ({plan.stance}).
4. Respect blocked topics: {', '.join(plan.blocked_topics) if plan.blocked_topics else 'none'}
5. Focus on: {', '.join(plan.focus)}

You report state. You do not decide meaning.
"""

        # Execute - this is the actual API call with conversation context
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_context,
            messages=self.conversation_history
        )

        assistant_message = response.content[0].text

        # Add to ephemeral history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Build state report
        return self._build_state_report(
            user_input=user_input,
            response=assistant_message,
            plan=plan
        )

    def _build_state_report(self, user_input: str, response: str, plan: Plan) -> ExecutionResult:
        """
        Build state report for Evaluator.

        This is a factual report of what happened, not an evaluation.
        """
        # Detect topics (simple extraction)
        topics = self._extract_topics(user_input, response)

        # Detect user signals
        signals = self._detect_signals(user_input)

        # Check if blocked topics were mentioned (deviation)
        deviation = None
        plan_followed = True
        for blocked in plan.blocked_topics:
            if blocked.lower() in response.lower():
                plan_followed = False
                deviation = f"Mentioned blocked topic: {blocked}"
                break

        return ExecutionResult(
            response=response,
            topics_discussed=topics,
            altitude_used=plan.altitude,  # Report what was requested
            plan_followed=plan_followed,
            deviation_reason=deviation,
            user_signals=signals
        )

    def _extract_topics(self, user_input: str, response: str) -> list[str]:
        """Extract topics from exchange. Simple keyword extraction."""
        # This is a simple implementation - could be enhanced
        combined = f"{user_input} {response}".lower()
        topics = []

        # Common topic indicators
        indicators = ["about", "regarding", "discuss", "focus on", "the", "my", "your"]
        words = combined.split()

        for i, word in enumerate(words):
            if word in indicators and i + 1 < len(words):
                next_word = words[i + 1].strip(".,!?")
                if len(next_word) > 3 and next_word not in indicators:
                    topics.append(next_word)

        return list(set(topics))[:5]  # Max 5 topics

    def _detect_signals(self, user_input: str) -> list[str]:
        """Detect user signals from input. Factual detection, not interpretation."""
        signals = []
        input_lower = user_input.lower()

        # Frustration signals
        frustration_words = ["stop", "enough", "damn", "hell", "shit", "fuck", "already", "again"]
        if any(word in input_lower for word in frustration_words):
            signals.append("frustration")

        # Explicit stop signals
        stop_phrases = ["stop talking about", "move on", "drop it", "forget about"]
        if any(phrase in input_lower for phrase in stop_phrases):
            signals.append("explicit_stop")

        # Positive signals
        positive_words = ["+1", "good", "yes", "exactly", "perfect", "thanks"]
        if any(word in input_lower for word in positive_words):
            signals.append("positive")

        # Question signals
        if "?" in user_input:
            signals.append("question")

        # Challenge signals
        if any(word in input_lower for word in ["wrong", "no", "but", "however", "actually"]):
            signals.append("pushback")

        return signals

    def get_situation(self) -> Situation:
        """
        Report current situation for Planner.

        This is state reporting - what IS, not what it MEANS.
        """
        # Extract recent topics from history
        recent_topics = []
        for msg in self.conversation_history[-6:]:
            if msg["role"] == "user":
                topics = self._extract_topics(msg["content"], "")
                recent_topics.extend(topics)

        # Detect current sentiment (factual, from signals)
        sentiment = "engaged"  # default
        if self.conversation_history:
            last_user = None
            for msg in reversed(self.conversation_history):
                if msg["role"] == "user":
                    last_user = msg["content"]
                    break
            if last_user:
                signals = self._detect_signals(last_user)
                if "frustration" in signals:
                    sentiment = "frustrated"
                elif "pushback" in signals:
                    sentiment = "resistant"
                elif "question" in signals:
                    sentiment = "exploratory"

        return Situation(
            user_input=self.conversation_history[-1]["content"] if self.conversation_history else "",
            conversation_length=len(self.conversation_history) // 2,
            recent_topics=list(set(recent_topics))[:5],
            user_sentiment=sentiment
        )

    def get_history(self) -> list[dict]:
        """Get conversation history (ephemeral memory)."""
        return self.conversation_history

    def clear_history(self):
        """Clear ephemeral memory. Called at session end."""
        self.conversation_history = []
