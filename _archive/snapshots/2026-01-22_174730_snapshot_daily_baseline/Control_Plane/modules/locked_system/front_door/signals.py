"""Signal Detection - Detect patterns in user input for gate proposals.

Detects:
- Formal work signals → WorkDeclarationGate
- Interrupt signals → LaneSwitchGate
- Emotional overload → EvaluationGate
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import re


class SignalType(Enum):
    """Types of signals that can be detected."""
    FORMAL_WORK = "formal_work"         # Starting serious work
    INTERRUPT = "interrupt"             # Context switch request
    EMOTIONAL_OVERLOAD = "emotional_overload"  # Frustration/confusion
    URGENCY = "urgency"                 # Time-sensitive request
    COMPLETION = "completion"           # Work wrapping up
    QUESTION = "question"               # Information request
    NONE = "none"                       # No significant signal


@dataclass
class DetectedSignal:
    """A detected signal from user input."""
    type: SignalType
    confidence: float  # 0.0 - 1.0
    suggested_gate: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    keywords_matched: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'confidence': self.confidence,
            'suggested_gate': self.suggested_gate,
            'context': self.context,
            'keywords_matched': self.keywords_matched,
        }


class SignalDetector:
    """
    Detects signals in user input for gate proposals.

    Rules:
    - Formal work patterns → WorkDeclarationGate
    - Interrupt patterns → LaneSwitchGate
    - Overload patterns → EvaluationGate
    """

    # Keywords for formal work detection
    FORMAL_WORK_PATTERNS = [
        r'\blet\'?s?\s+(start|begin|work\s+on|focus)\b',
        r'\bi\s+need\s+to\s+(write|create|build|develop)\b',
        r'\bworking\s+on\s+(?:a|the|my)\b',
        r'\b(?:project|task|document|report|feature)\s+(?:for|about)\b',
        r'\blet\'?s?\s+(?:get|dive)\s+(?:into|started)\b',
    ]

    # Keywords for interrupt detection
    INTERRUPT_PATTERNS = [
        r'\bquick\s+(?:question|check|look)\b',
        r'\breal\s+quick\b',
        r'\bbefore\s+(?:i\s+forget|we\s+continue)\b',
        r'\bsomething\s+(?:came\s+up|urgent)\b',
        r'\bcan\s+(?:you|we)\s+(?:first|quickly)\b',
        r'\bswitch(?:ing)?\s+(?:to|gears)\b',
    ]

    # Keywords for urgency
    URGENCY_PATTERNS = [
        r'\burgent(?:ly)?\b',
        r'\basap\b',
        r'\bimmediately\b',
        r'\bright\s+now\b',
        r'\bdeadline\b',
        r'\bcritical\b',
        r'\bemergency\b',
    ]

    # Keywords for emotional overload
    OVERLOAD_PATTERNS = [
        r'\bconfused\b',
        r'\bfrustrat(?:ed|ing)\b',
        r'\bdoesn\'?t?\s+(?:work|make\s+sense)\b',
        r'\bstuck\b',
        r'\bhelp\s+me\s+understand\b',
        r'\bwhat\s+(?:am\s+i|are\s+we)\s+doing\b',
        r'\bcan\'?t?\s+figure\b',
        r'\boverwhelm(?:ed|ing)\b',
    ]

    # Keywords for completion
    COMPLETION_PATTERNS = [
        r'\bdone\b',
        r'\bfinished\b',
        r'\bcompleted?\b',
        r'\bwrap(?:ping)?\s+up\b',
        r'\bthat\'?s?\s+(?:it|all)\b',
        r'\blet\'?s?\s+(?:stop|pause|break)\b',
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns."""
        self._formal_work_re = [re.compile(p, re.IGNORECASE) for p in self.FORMAL_WORK_PATTERNS]
        self._interrupt_re = [re.compile(p, re.IGNORECASE) for p in self.INTERRUPT_PATTERNS]
        self._urgency_re = [re.compile(p, re.IGNORECASE) for p in self.URGENCY_PATTERNS]
        self._overload_re = [re.compile(p, re.IGNORECASE) for p in self.OVERLOAD_PATTERNS]
        self._completion_re = [re.compile(p, re.IGNORECASE) for p in self.COMPLETION_PATTERNS]

    def detect(
        self,
        user_input: str,
        emotional_signals: Dict[str, str] = None,
    ) -> DetectedSignal:
        """
        Detect signals in user input.

        Also considers emotional_signals for overload detection.
        """
        emotional_signals = emotional_signals or {}

        # Check for emotional overload first (highest priority)
        if self._is_emotional_overload(user_input, emotional_signals):
            keywords = self._get_matched_keywords(user_input, self._overload_re)
            return DetectedSignal(
                type=SignalType.EMOTIONAL_OVERLOAD,
                confidence=0.9,
                suggested_gate="evaluation",
                context={'trigger': 'overload'},
                keywords_matched=keywords,
            )

        # Check urgency
        urgency_keywords = self._get_matched_keywords(user_input, self._urgency_re)
        is_urgent = len(urgency_keywords) > 0 or emotional_signals.get('urgency') == 'critical'

        # Check for formal work
        formal_keywords = self._get_matched_keywords(user_input, self._formal_work_re)
        if formal_keywords:
            return DetectedSignal(
                type=SignalType.FORMAL_WORK,
                confidence=0.8,
                suggested_gate="work_declaration",
                context={'is_urgent': is_urgent},
                keywords_matched=formal_keywords,
            )

        # Check for interrupt
        interrupt_keywords = self._get_matched_keywords(user_input, self._interrupt_re)
        if interrupt_keywords:
            return DetectedSignal(
                type=SignalType.INTERRUPT,
                confidence=0.7,
                suggested_gate="lane_switch",
                context={'is_urgent': is_urgent},
                keywords_matched=interrupt_keywords,
            )

        # Check for completion
        completion_keywords = self._get_matched_keywords(user_input, self._completion_re)
        if completion_keywords:
            return DetectedSignal(
                type=SignalType.COMPLETION,
                confidence=0.8,
                suggested_gate="evaluation",
                context={'action': 'complete'},
                keywords_matched=completion_keywords,
            )

        # Check for urgency alone
        if is_urgent:
            return DetectedSignal(
                type=SignalType.URGENCY,
                confidence=0.75,
                suggested_gate="lane_switch",
                context={'urgency': 'elevated'},
                keywords_matched=urgency_keywords,
            )

        # Check for simple question
        if user_input.strip().endswith('?'):
            return DetectedSignal(
                type=SignalType.QUESTION,
                confidence=0.5,
                suggested_gate=None,
                context={'is_question': True},
            )

        # No significant signal
        return DetectedSignal(
            type=SignalType.NONE,
            confidence=0.0,
        )

    def _is_emotional_overload(self, user_input: str, emotional_signals: Dict[str, str]) -> bool:
        """Check for emotional overload condition."""
        # From emotional telemetry
        if emotional_signals.get('frustration') == 'high':
            return True
        if emotional_signals.get('cognitive_load') == 'overloaded':
            return True

        # From text patterns
        overload_keywords = self._get_matched_keywords(user_input, self._overload_re)
        return len(overload_keywords) >= 2  # Multiple overload signals

    def _get_matched_keywords(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """Get list of matched keywords."""
        matches = []
        for pattern in patterns:
            found = pattern.findall(text)
            matches.extend(found)
        return matches

    def detect_work_type(self, user_input: str) -> Optional[str]:
        """Detect what type of work is being requested."""
        text_lower = user_input.lower()

        if any(w in text_lower for w in ['write', 'document', 'draft', 'compose']):
            return 'writing'
        if any(w in text_lower for w in ['budget', 'finance', 'expense', 'invoice']):
            return 'finance'
        if any(w in text_lower for w in ['research', 'analyze', 'investigate', 'study']):
            return 'research'
        if any(w in text_lower for w in ['deploy', 'monitor', 'check status', 'ops']):
            return 'ops'

        return None
