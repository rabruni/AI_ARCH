"""Reasoning HRM - Input classification, routing, and action selection.

Simplified spec: Plain classes, no protocols, event-based.

Components:
- InputClassifier: Classifies input by complexity, stakes, domain
- ActionRouter: Routes to appropriate agents/capabilities
- ActionSelector: Selects actions based on stance + classification
"""
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from enum import Enum

from locked_system.core.types import (
    Complexity,
    Stakes,
    ConflictLevel,
    InputClassification,
    Stance,
    AltitudeLevel,
)
from locked_system.core.trace import EpisodicTrace


# ─────────────────────────────────────────────────────────────
# Classification Patterns
# ─────────────────────────────────────────────────────────────

COMPLEXITY_PATTERNS = {
    Complexity.COMPLEX: [
        "how should i approach",
        "help me think through",
        "what's the best way to",
        "trade-off", "tradeoff",
        "multiple options",
        "complex", "complicated",
        "analyze", "evaluate",
    ],
    Complexity.MODERATE: [
        "can you help me",
        "what do you think about",
        "should i",
        "which one",
        "compare",
    ],
    Complexity.SIMPLE: [
        "what is",
        "when is",
        "where is",
        "how do i",
        "show me",
        "list",
        "quick question",
    ],
}

STAKES_PATTERNS = {
    Stakes.HIGH: [
        "important", "critical", "urgent",
        "deadline", "money", "budget",
        "legal", "contract", "medical",
        "security", "password", "credential",
        "delete", "remove", "cancel",
        "send", "submit", "publish",
    ],
    Stakes.MEDIUM: [
        "meeting", "presentation",
        "project", "work",
        "client", "customer",
        "schedule", "plan",
    ],
    Stakes.LOW: [
        "curious", "wondering",
        "just", "quick",
        "random", "casual",
        "fun", "interesting",
    ],
}

DOMAIN_PATTERNS = {
    "productivity": ["task", "todo", "calendar", "schedule", "meeting", "deadline"],
    "thinking": ["idea", "think", "consider", "approach", "strategy", "plan"],
    "learning": ["learn", "understand", "explain", "how does", "what is"],
    "emotional": ["feel", "stress", "worried", "happy", "frustrated", "overwhelmed"],
    "technical": ["code", "bug", "error", "system", "software", "api"],
    "creative": ["write", "create", "design", "brainstorm", "imagine"],
}


@dataclass
class ClassificationResult:
    """Full classification result with confidence."""
    classification: InputClassification
    raw_signals: Dict[str, Any]
    pattern_matches: List[str]


# ─────────────────────────────────────────────────────────────
# Input Classifier
# ─────────────────────────────────────────────────────────────

class InputClassifier:
    """
    Classifies user input by multiple dimensions.

    Used by Router to determine strategy.
    """

    def __init__(self, trace: Optional[EpisodicTrace] = None):
        self.trace = trace

    def classify(self, text: str, context: dict = None) -> ClassificationResult:
        """
        Classify input text.

        Returns comprehensive classification for routing decisions.
        """
        text_lower = text.lower()
        context = context or {}

        # Score complexity
        complexity = self._score_complexity(text_lower)

        # Score stakes
        stakes = self._score_stakes(text_lower)

        # Detect domains
        domains = self._detect_domains(text_lower)

        # Estimate uncertainty (more questions = more uncertain)
        uncertainty = self._estimate_uncertainty(text_lower)

        # Detect conflict level
        conflict = self._detect_conflict(text_lower, context)

        # Determine horizon
        horizon = self._determine_horizon(text_lower)

        # Build pattern matches for transparency
        pattern_matches = self._collect_pattern_matches(text_lower)

        classification = InputClassification(
            complexity=complexity,
            uncertainty=uncertainty,
            conflict=conflict,
            stakes=stakes,
            horizon=horizon,
            domain=domains,
            confidence=self._calculate_confidence(pattern_matches)
        )

        result = ClassificationResult(
            classification=classification,
            raw_signals={
                "text_length": len(text),
                "question_count": text.count("?"),
                "urgency_markers": self._count_urgency_markers(text_lower),
            },
            pattern_matches=pattern_matches
        )

        # Log to trace if available
        if self.trace:
            self.trace.log(
                event_type="input_classified",
                payload={
                    "complexity": complexity.value,
                    "stakes": stakes.value,
                    "domains": domains,
                    "uncertainty": uncertainty,
                    "horizon": horizon,
                }
            )

        return result

    def _score_complexity(self, text: str) -> Complexity:
        """Score text complexity based on patterns."""
        scores = {c: 0 for c in Complexity}

        for complexity, patterns in COMPLEXITY_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    scores[complexity] += 1

        # Return highest scoring, default to MODERATE
        max_score = max(scores.values())
        if max_score == 0:
            return Complexity.MODERATE

        for complexity, score in scores.items():
            if score == max_score:
                return complexity
        return Complexity.MODERATE

    def _score_stakes(self, text: str) -> Stakes:
        """Score text stakes based on patterns."""
        scores = {s: 0 for s in Stakes}

        for stakes, patterns in STAKES_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    scores[stakes] += 1

        max_score = max(scores.values())
        if max_score == 0:
            return Stakes.LOW

        for stakes, score in scores.items():
            if score == max_score:
                return stakes
        return Stakes.LOW

    def _detect_domains(self, text: str) -> List[str]:
        """Detect which domains the text relates to."""
        domains = []
        for domain, patterns in DOMAIN_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    if domain not in domains:
                        domains.append(domain)
                    break
        return domains or ["general"]

    def _estimate_uncertainty(self, text: str) -> float:
        """Estimate uncertainty level (0-1)."""
        uncertainty_markers = [
            "maybe", "perhaps", "possibly", "might",
            "not sure", "uncertain", "don't know",
            "should i", "what if", "is it okay",
            "?",
        ]
        count = sum(1 for m in uncertainty_markers if m in text)
        # Normalize to 0-1 with cap at 1.0
        return min(1.0, count * 0.15)

    def _detect_conflict(self, text: str, context: dict) -> ConflictLevel:
        """Detect if there's conflict with existing context."""
        conflict_markers = [
            "but", "however", "although",
            "disagree", "wrong", "incorrect",
            "change my mind", "actually",
        ]
        count = sum(1 for m in conflict_markers if m in text)

        if count >= 3:
            return ConflictLevel.HIGH
        elif count >= 2:
            return ConflictLevel.MEDIUM
        elif count >= 1:
            return ConflictLevel.LOW
        return ConflictLevel.NONE

    def _determine_horizon(self, text: str) -> str:
        """Determine time horizon."""
        immediate_markers = ["now", "right now", "immediately", "asap", "today"]
        near_markers = ["this week", "soon", "next", "tomorrow"]
        far_markers = ["long term", "future", "eventually", "someday", "later"]

        for m in immediate_markers:
            if m in text:
                return "immediate"
        for m in near_markers:
            if m in text:
                return "near"
        for m in far_markers:
            if m in text:
                return "far"
        return "near"  # Default

    def _collect_pattern_matches(self, text: str) -> List[str]:
        """Collect all patterns that matched."""
        matches = []
        all_patterns = {
            **{f"complexity:{c.value}": p for c, p in COMPLEXITY_PATTERNS.items()},
            **{f"stakes:{s.value}": p for s, p in STAKES_PATTERNS.items()},
            **{f"domain:{d}": p for d, p in DOMAIN_PATTERNS.items()},
        }
        for category, patterns in all_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    matches.append(f"{category}:{pattern}")
        return matches

    def _count_urgency_markers(self, text: str) -> int:
        """Count urgency markers."""
        markers = ["urgent", "asap", "now", "immediately", "quick", "fast", "hurry"]
        return sum(1 for m in markers if m in text)

    def _calculate_confidence(self, matches: List[str]) -> float:
        """Calculate confidence based on pattern matches."""
        if len(matches) >= 5:
            return 0.9
        elif len(matches) >= 3:
            return 0.7
        elif len(matches) >= 1:
            return 0.5
        return 0.3


# ─────────────────────────────────────────────────────────────
# Action Types
# ─────────────────────────────────────────────────────────────

class ActionType(Enum):
    """Types of actions the system can take."""
    RESPOND = "respond"           # Direct response
    CLARIFY = "clarify"           # Ask clarifying questions
    DELEGATE = "delegate"         # Delegate to agents
    ESCALATE = "escalate"         # Escalate to higher altitude
    DEFER = "defer"               # Defer for later
    GROUND = "ground"             # Ground in context/values


@dataclass
class ActionPlan:
    """Planned action based on classification + stance."""
    action_type: ActionType
    agents: List[str]             # Agents to involve
    capabilities: List[str]       # Capabilities needed
    altitude_target: Optional[str]  # Target altitude if transitioning
    constraints: List[str]        # Hard constraints
    rationale: str                # Why this action


# ─────────────────────────────────────────────────────────────
# Action Selector
# ─────────────────────────────────────────────────────────────

class ActionSelector:
    """
    Selects appropriate actions based on stance + classification.

    The selector doesn't execute - it only recommends.
    Execution is controlled by the orchestrator.
    """

    # Action matrix: stance x escalation_needed -> action type
    ACTION_MATRIX = {
        (Stance.SENSEMAKING, False): ActionType.CLARIFY,
        (Stance.SENSEMAKING, True): ActionType.GROUND,
        (Stance.DISCOVERY, False): ActionType.DELEGATE,
        (Stance.DISCOVERY, True): ActionType.CLARIFY,
        (Stance.EXECUTION, False): ActionType.RESPOND,
        (Stance.EXECUTION, True): ActionType.ESCALATE,
        (Stance.EVALUATION, False): ActionType.RESPOND,
        (Stance.EVALUATION, True): ActionType.ESCALATE,
    }

    def __init__(self, trace: Optional[EpisodicTrace] = None):
        self.trace = trace
        self._agent_registry: Dict[str, List[str]] = {
            "general": ["default"],
            "productivity": ["task_manager", "calendar"],
            "thinking": ["reasoning", "brainstorm"],
            "learning": ["explainer", "tutor"],
            "emotional": ["empathy", "support"],
            "technical": ["coder", "debugger"],
            "creative": ["writer", "designer"],
        }

    def select(
        self,
        classification: InputClassification,
        current_stance: Stance,
        current_altitude: str = "L2"
    ) -> ActionPlan:
        """
        Select action based on classification and current state.

        Returns an ActionPlan that can be executed by orchestrator.
        """
        should_escalate = classification.should_escalate()

        # Get base action from matrix
        action_type = self.ACTION_MATRIX.get(
            (current_stance, should_escalate),
            ActionType.RESPOND
        )

        # Select agents based on domains
        agents = self._select_agents(classification.domain)

        # Determine capabilities needed
        capabilities = self._select_capabilities(classification, action_type)

        # Determine altitude target if escalating
        altitude_target = None
        if action_type == ActionType.ESCALATE:
            altitude_target = self._get_escalation_target(current_altitude)
        elif action_type == ActionType.GROUND:
            altitude_target = "L4"  # Ground to identity

        # Build constraints from stakes
        constraints = self._build_constraints(classification)

        plan = ActionPlan(
            action_type=action_type,
            agents=agents,
            capabilities=capabilities,
            altitude_target=altitude_target,
            constraints=constraints,
            rationale=self._build_rationale(classification, current_stance, action_type)
        )

        # Log to trace
        if self.trace:
            self.trace.log(
                event_type="action_selected",
                payload={
                    "action_type": action_type.value,
                    "agents": agents,
                    "should_escalate": should_escalate,
                    "altitude_target": altitude_target,
                }
            )

        return plan

    def _select_agents(self, domains: List[str]) -> List[str]:
        """Select agents based on detected domains."""
        agents = []
        for domain in domains:
            domain_agents = self._agent_registry.get(domain, [])
            agents.extend(a for a in domain_agents if a not in agents)
        return agents or ["default"]

    def _select_capabilities(
        self,
        classification: InputClassification,
        action_type: ActionType
    ) -> List[str]:
        """Select capabilities needed for the action."""
        caps = []

        # High stakes may need verification
        if classification.stakes == Stakes.HIGH:
            caps.append("verification")

        # Complex problems may need reasoning
        if classification.complexity == Complexity.COMPLEX:
            caps.append("deep_reasoning")

        # Delegation needs orchestration
        if action_type == ActionType.DELEGATE:
            caps.append("agent_orchestration")

        return caps

    def _get_escalation_target(self, current: str) -> str:
        """Get target altitude for escalation."""
        escalation_map = {
            "L1": "L2",
            "L2": "L3",
            "L3": "L4",
            "L4": "L4",  # Can't go higher
        }
        return escalation_map.get(current, "L3")

    def _build_constraints(self, classification: InputClassification) -> List[str]:
        """Build constraints based on classification."""
        constraints = []

        if classification.stakes == Stakes.HIGH:
            constraints.append("verify_before_action")
            constraints.append("no_irreversible_without_confirmation")

        if classification.conflict != ConflictLevel.NONE:
            constraints.append("acknowledge_conflict")

        if classification.uncertainty > 0.5:
            constraints.append("ask_clarifying_questions")

        return constraints

    def _build_rationale(
        self,
        classification: InputClassification,
        stance: Stance,
        action: ActionType
    ) -> str:
        """Build human-readable rationale for the action."""
        parts = [f"Stance={stance.value}"]

        if classification.should_escalate():
            parts.append("escalation_needed")
        if classification.stakes == Stakes.HIGH:
            parts.append("high_stakes")
        if classification.complexity == Complexity.COMPLEX:
            parts.append("complex")

        parts.append(f"action={action.value}")
        return ", ".join(parts)

    def register_agents(self, domain: str, agents: List[str]):
        """Register agents for a domain."""
        self._agent_registry[domain] = agents


# ─────────────────────────────────────────────────────────────
# Action Router
# ─────────────────────────────────────────────────────────────

@dataclass
class RouteDecision:
    """Decision on how to route the input."""
    classification: InputClassification
    action_plan: ActionPlan
    requires_gate: bool           # Does this need gate approval?
    gate_type: Optional[str]      # Which gate if any


class ActionRouter:
    """
    Routes input to appropriate handlers.

    Combines classifier + selector to produce routing decisions.
    """

    def __init__(self, trace: Optional[EpisodicTrace] = None):
        self.trace = trace
        self.classifier = InputClassifier(trace)
        self.selector = ActionSelector(trace)

    def route(
        self,
        text: str,
        current_stance: Stance,
        current_altitude: str = "L2",
        context: dict = None
    ) -> RouteDecision:
        """
        Route input text to appropriate action.

        Returns a RouteDecision with classification and action plan.
        """
        # Classify
        result = self.classifier.classify(text, context)
        classification = result.classification

        # Select action
        action_plan = self.selector.select(
            classification,
            current_stance,
            current_altitude
        )

        # Determine if gate is needed
        requires_gate, gate_type = self._check_gate_requirement(
            action_plan,
            current_stance
        )

        decision = RouteDecision(
            classification=classification,
            action_plan=action_plan,
            requires_gate=requires_gate,
            gate_type=gate_type
        )

        # Log to trace
        if self.trace:
            self.trace.log(
                event_type="route_decision",
                payload={
                    "action_type": action_plan.action_type.value,
                    "requires_gate": requires_gate,
                    "gate_type": gate_type,
                    "agents": action_plan.agents,
                }
            )

        return decision

    def _check_gate_requirement(
        self,
        plan: ActionPlan,
        current_stance: Stance
    ) -> tuple[bool, Optional[str]]:
        """Check if the action requires gate approval."""
        # Escalation always requires gate
        if plan.action_type == ActionType.ESCALATE:
            return True, "evaluation"

        # Delegation to agents requires approval
        if plan.action_type == ActionType.DELEGATE and len(plan.agents) > 1:
            return True, "agent_approval"

        # High constraints suggest verification
        if "verify_before_action" in plan.constraints:
            return True, "evaluation"

        # Stance change requires framing gate
        if plan.altitude_target and plan.action_type == ActionType.GROUND:
            return True, "framing"

        return False, None


# ─────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────

def classify_input(text: str) -> InputClassification:
    """Quick classification of input."""
    classifier = InputClassifier()
    result = classifier.classify(text)
    return result.classification


def route_input(
    text: str,
    stance: Stance = Stance.SENSEMAKING,
    altitude: str = "L2"
) -> RouteDecision:
    """Quick routing decision for input."""
    router = ActionRouter()
    return router.route(text, stance, altitude)
