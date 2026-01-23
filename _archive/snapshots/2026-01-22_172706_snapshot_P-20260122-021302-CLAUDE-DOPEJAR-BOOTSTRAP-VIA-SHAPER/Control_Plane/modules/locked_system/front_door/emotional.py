"""Emotional Telemetry - Bounded emotional signal handling.

Uses emotional signals as TELEMETRY only:
- Emergency detection: frustration/confusion → propose EvaluationGate
- Priority routing: urgency → adjust priority weighting
- Attention allocation: overload → compress response options

Does NOT do:
- Empathy, relationship dynamics, motivational reasoning
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class EmotionalSignals:
    """
    Bounded emotional telemetry schema.

    All values are bounded enums - no nuanced inference.
    """
    confidence: str = "medium"      # low | medium | high
    frustration: str = "none"       # none | mild | high
    cognitive_load: str = "medium"  # low | medium | overloaded
    urgency: str = "none"           # none | elevated | critical
    flow: str = "false"             # false | true

    def to_dict(self) -> dict:
        return {
            'confidence': self.confidence,
            'frustration': self.frustration,
            'cognitive_load': self.cognitive_load,
            'urgency': self.urgency,
            'flow': self.flow,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EmotionalSignals':
        return cls(
            confidence=data.get('confidence', 'medium'),
            frustration=data.get('frustration', 'none'),
            cognitive_load=data.get('cognitive_load', 'medium'),
            urgency=data.get('urgency', 'none'),
            flow=data.get('flow', 'false'),
        )


@dataclass
class TelemetryResponse:
    """Response modifications based on emotional telemetry."""
    compress_options: bool = False      # Reduce to 2 choices
    recommend_defer: bool = False       # Suggest deferring switches
    trigger_evaluation: bool = False    # Propose EvaluationGate
    urgency_weight: float = 1.0         # Priority multiplier
    max_options: int = 4                # Max options to show

    def to_dict(self) -> dict:
        return {
            'compress_options': self.compress_options,
            'recommend_defer': self.recommend_defer,
            'trigger_evaluation': self.trigger_evaluation,
            'urgency_weight': self.urgency_weight,
            'max_options': self.max_options,
        }


class EmotionalTelemetry:
    """
    Processes emotional signals for routing decisions.

    Rules (deterministic):
    - frustration=high OR cognitive_load=overloaded → propose EvaluationGate
    - urgency=critical → propose PriorityEscalationGate (advisory)
    - flow=true → avoid interruptions; propose defer instead of switch
    - cognitive_load=overloaded → compress to 2 choices
    """

    def process(self, signals: Dict[str, str]) -> TelemetryResponse:
        """
        Process emotional signals and determine response modifications.

        Args:
            signals: Dict with emotional signal values

        Returns:
            TelemetryResponse with modifications to apply
        """
        if not signals:
            return TelemetryResponse()

        response = TelemetryResponse()

        # Rule 1: Overload detection
        frustration = signals.get('frustration', 'none')
        cognitive_load = signals.get('cognitive_load', 'medium')

        if frustration == 'high' or cognitive_load == 'overloaded':
            response.trigger_evaluation = True
            response.compress_options = True
            response.max_options = 2

        # Rule 2: Flow protection
        flow = signals.get('flow', 'false')
        if flow == 'true':
            response.recommend_defer = True

        # Rule 3: Urgency weighting
        urgency = signals.get('urgency', 'none')
        if urgency == 'critical':
            response.urgency_weight = 2.0
            response.recommend_defer = False  # Override flow
        elif urgency == 'elevated':
            response.urgency_weight = 1.5

        # Rule 4: Cognitive load compression
        if cognitive_load == 'overloaded':
            response.compress_options = True
            response.max_options = 2

        return response

    def should_trigger_evaluation(self, signals: Dict[str, str]) -> bool:
        """Check if signals warrant an EvaluationGate."""
        response = self.process(signals)
        return response.trigger_evaluation

    def should_recommend_defer(self, signals: Dict[str, str]) -> bool:
        """Check if signals recommend deferring lane switches."""
        response = self.process(signals)
        return response.recommend_defer

    def get_max_options(self, signals: Dict[str, str]) -> int:
        """Get max options to show based on cognitive load."""
        response = self.process(signals)
        return response.max_options

    def apply_to_options(
        self,
        options: List[Dict],
        signals: Dict[str, str],
    ) -> List[Dict]:
        """
        Apply telemetry response to a list of options.

        Compresses and reorders based on signals.
        """
        response = self.process(signals)

        # Limit options
        limited = options[:response.max_options]

        # If recommend_defer and there's a defer option, put it first
        if response.recommend_defer:
            defer_options = [o for o in limited if 'defer' in str(o).lower()]
            other_options = [o for o in limited if 'defer' not in str(o).lower()]
            limited = defer_options + other_options

        return limited
