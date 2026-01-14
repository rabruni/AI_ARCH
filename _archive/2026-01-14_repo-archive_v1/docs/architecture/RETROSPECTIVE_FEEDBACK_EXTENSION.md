# Retrospective & Feedback Extension Proposal

## Current State (Altitude HRM Only)

### SessionRetrospective (the_assist/core/retrospective.py)
- Analyzes sessions for behavioral patterns (MBTI, Big5)
- Tracks corrections, topics, learnings
- Updates baseline profile over time
- Stores trends for long-term learning

### Feedback (the_assist/core/feedback.py)
- Simple log: worked/didnt_work/suggestion/observation
- Tagged, timestamped entries
- Session-scoped retrieval

---

## Value Proposition: Extend to All 4 HRMs

Each HRM can benefit from retrospective analysis and feedback loops:

| HRM | What to Learn | Feedback Signals |
|-----|---------------|------------------|
| **Altitude** | User behavioral patterns, communication preferences | Corrections, engagement quality |
| **Focus** | Gate accuracy, stance transition quality | Gate rejections, consent patterns |
| **Reasoning** | Strategy effectiveness, escalation accuracy | Strategy success/failure, routing outcomes |
| **Learning** | Pattern accuracy, generalization quality | Pattern hits/misses, trim accuracy |

---

## Proposed Architecture

### Unified Feedback Types (Per HRM)

```python
# shared/feedback/types.py

HRM_FEEDBACK_TYPES = {
    "altitude": {
        "worked": "AI response was appropriate",
        "didnt_work": "AI response missed the mark",
        "correction": "User explicitly corrected AI",
        "intuition_hit": "Proactive suggestion landed",
        "intuition_miss": "Proactive suggestion ignored/dismissed"
    },
    "focus": {
        "gate_correct": "Gate decision was right",
        "gate_wrong": "Gate should have allowed/denied",
        "stance_stuck": "Stayed in stance too long",
        "stance_rushed": "Left stance too quickly",
        "consent_friction": "User annoyed by consent request"
    },
    "reasoning": {
        "strategy_worked": "Strategy selection was effective",
        "strategy_failed": "Strategy didn't solve problem",
        "escalation_correct": "Escalation was needed",
        "escalation_unnecessary": "Escalation was overkill",
        "deescalation_missed": "Could have handled faster"
    },
    "learning": {
        "pattern_hit": "Recognized pattern correctly",
        "pattern_miss": "Pattern didn't apply",
        "generalization_good": "Abstraction was helpful",
        "generalization_wrong": "Abstraction was too broad/narrow",
        "trim_regret": "Trimmed pattern we needed"
    }
}
```

### Retrospective Analysis (Per HRM)

```python
# shared/retrospective/analyzers.py

class HRMRetrospective:
    """Base class for HRM-specific retrospective analysis."""

    def __init__(self, hrm_name: str):
        self.hrm_name = hrm_name
        self.feedback_types = HRM_FEEDBACK_TYPES[hrm_name]

    def analyze_session(self, session_data: dict) -> dict:
        """Override in subclass for HRM-specific analysis."""
        raise NotImplementedError


class FocusRetrospective(HRMRetrospective):
    """Analyzes Focus HRM session for gate/stance patterns."""

    def __init__(self):
        super().__init__("focus")

    def analyze_session(self, session_data: dict) -> dict:
        """
        Analyze Focus HRM session.

        Looks for:
        - Gate decision accuracy
        - Stance transition patterns
        - Consent friction points
        - Lane switching efficiency
        """
        return {
            "gate_decisions": self._analyze_gates(session_data),
            "stance_flow": self._analyze_stances(session_data),
            "consent_patterns": self._analyze_consent(session_data),
            "lane_efficiency": self._analyze_lanes(session_data),
            "learnings": self._extract_learnings(session_data)
        }

    def _analyze_gates(self, data: dict) -> dict:
        """Analyze gate decision quality."""
        gates = data.get("gate_events", [])
        return {
            "total": len(gates),
            "approved": len([g for g in gates if g["decision"] == "approve"]),
            "denied": len([g for g in gates if g["decision"] == "deny"]),
            "user_overrides": len([g for g in gates if g.get("user_override")]),
            # High override rate = gates too strict
            "override_rate": len([g for g in gates if g.get("user_override")]) / max(len(gates), 1)
        }

    def _analyze_stances(self, data: dict) -> dict:
        """Analyze stance transition patterns."""
        transitions = data.get("stance_transitions", [])
        return {
            "total_transitions": len(transitions),
            "stuck_instances": len([t for t in transitions if t.get("duration_turns", 0) > 10]),
            "rushed_instances": len([t for t in transitions if t.get("duration_turns", 0) < 2]),
            "flow": [t["to_stance"] for t in transitions]
        }


class ReasoningRetrospective(HRMRetrospective):
    """Analyzes Reasoning HRM session for strategy effectiveness."""

    def __init__(self):
        super().__init__("reasoning")

    def analyze_session(self, session_data: dict) -> dict:
        """
        Analyze Reasoning HRM session.

        Looks for:
        - Strategy selection accuracy
        - Escalation patterns
        - Routing efficiency
        """
        return {
            "strategies_used": self._analyze_strategies(session_data),
            "escalation_patterns": self._analyze_escalations(session_data),
            "routing_accuracy": self._analyze_routing(session_data),
            "learnings": self._extract_learnings(session_data)
        }

    def _analyze_strategies(self, data: dict) -> dict:
        """Analyze strategy effectiveness."""
        strategies = data.get("strategy_events", [])
        return {
            "total": len(strategies),
            "by_type": self._group_by_type(strategies),
            "success_rate": self._calculate_success_rate(strategies),
            "avg_turns_to_resolve": self._avg_resolution_time(strategies)
        }


class LearningRetrospective(HRMRetrospective):
    """Analyzes Learning HRM session for pattern accuracy."""

    def __init__(self):
        super().__init__("learning")

    def analyze_session(self, session_data: dict) -> dict:
        """
        Analyze Learning HRM session.

        Looks for:
        - Pattern recognition accuracy
        - Generalization quality
        - Trim decisions
        """
        return {
            "pattern_performance": self._analyze_patterns(session_data),
            "generalizations": self._analyze_generalizations(session_data),
            "trim_decisions": self._analyze_trims(session_data),
            "learnings": self._extract_learnings(session_data)
        }

    def _analyze_patterns(self, data: dict) -> dict:
        """Analyze pattern hit/miss rates."""
        patterns = data.get("pattern_events", [])
        return {
            "total_matches": len(patterns),
            "hits": len([p for p in patterns if p["outcome"] == "hit"]),
            "misses": len([p for p in patterns if p["outcome"] == "miss"]),
            "hit_rate": len([p for p in patterns if p["outcome"] == "hit"]) / max(len(patterns), 1),
            "top_patterns": self._top_patterns(patterns)
        }
```

---

## Cross-HRM Learning

### Signal Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SESSION END                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Each HRM runs its retrospective analyzer                   │
│                                                             │
│  AltitudeRetrospective.analyze_session()                    │
│  FocusRetrospective.analyze_session()                       │
│  ReasoningRetrospective.analyze_session()                   │
│  LearningRetrospective.analyze_session()                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Cross-HRM Correlation                                       │
│                                                             │
│  • Did gate friction correlate with AI corrections?         │
│  • Did strategy failures precede stance changes?            │
│  • Did pattern misses cause escalations?                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Learning HRM Pattern Update                                 │
│                                                             │
│  New patterns learned from session:                         │
│  • signal→routing→outcome tuples                            │
│  • gate_type→user_override→adjustment                       │
│  • strategy→resolution_time→effectiveness                   │
└─────────────────────────────────────────────────────────────┘
```

### Cross-HRM Signals

| From HRM | Signal | To HRM | Action |
|----------|--------|--------|--------|
| Focus | High gate override rate | Learning | Lower gate sensitivity for this user |
| Reasoning | Strategy X failed 3x | Learning | Deprioritize strategy X for similar inputs |
| Altitude | User corrected L2 response | Focus | Tighten evaluation gate |
| Learning | Pattern A has 80% hit rate | Reasoning | Prioritize routes that use pattern A |

---

## Value by HRM

### Focus HRM (HRM Routing)

**What retrospective adds:**
- Gate accuracy metrics (are we blocking too much? too little?)
- Stance flow analysis (getting stuck? rushing?)
- Consent friction detection (annoying the user?)
- Lane efficiency (switching too often?)

**Feedback examples:**
```python
log_feedback(
    hrm="focus",
    type="gate_wrong",
    note="WriteApprovalGate blocked a simple note, user annoyed",
    context={"gate": "WriteApprovalGate", "action": "note_save"},
    tags=["friction", "write"]
)
```

**Learning outcome:**
- Pattern: "note_save" actions from trusted user → auto-approve after 3 approvals
- Adjustment: Lower WriteApprovalGate sensitivity for notes

### Reasoning HRM (Signal Router)

**What retrospective adds:**
- Strategy effectiveness by input type
- Escalation accuracy (was it needed?)
- De-escalation opportunities missed
- Routing efficiency (shortest path to answer?)

**Feedback examples:**
```python
log_feedback(
    hrm="reasoning",
    type="escalation_unnecessary",
    note="Escalated simple question to L3 reasoning",
    context={"signal": "ambiguous_input", "strategy": "deep_analysis"},
    tags=["overkill", "efficiency"]
)
```

**Learning outcome:**
- Pattern: signals with keywords ["quick", "simple"] → try fast strategy first
- Adjustment: De-escalate "ambiguous" classification when context is short

### Learning HRM (Pattern Memory)

**What retrospective adds:**
- Pattern hit/miss rates
- Generalization quality
- Trim regret detection (trimmed something useful)
- Pattern staleness (old patterns still apply?)

**Feedback examples:**
```python
log_feedback(
    hrm="learning",
    type="trim_regret",
    note="Trimmed 'timeboxing' pattern, user asked about it next session",
    context={"pattern": "timeboxing", "trim_reason": "low_frequency"},
    tags=["regret", "trim"]
)
```

**Learning outcome:**
- Pattern: Increase retention time for patterns with semantic importance
- Adjustment: "timeboxing" reinstated, marked as "protected"

---

## Implementation Order

### Phase 1: Unified Feedback Logger
1. Create `shared/feedback/logger.py`
2. Add HRM-aware feedback types
3. Wire into existing feedback.py

### Phase 2: Focus HRM Retrospective
1. Create `hrm_routing/retrospective/focus.py`
2. Add gate/stance analysis
3. Store Focus-specific trends

### Phase 3: Reasoning HRM Retrospective (when built)
1. Create `the_assist/reasoning/retrospective.py`
2. Add strategy analysis
3. Store Reasoning-specific trends

### Phase 4: Learning HRM Retrospective (when built)
1. Create `the_assist/learning/retrospective.py`
2. Add pattern analysis
3. Store Learning-specific trends

### Phase 5: Cross-HRM Correlation
1. Create `shared/retrospective/correlator.py`
2. Add cross-HRM signal analysis
3. Feed back into Learning HRM

---

## Token Efficiency

All retrospective data should use the same token-efficient format as memory_v2:

```python
# Instead of prose
"The user corrected the assistant three times about being too verbose"

# Use codes
{"hrm": "alt", "sig": "correction", "n": 3, "tags": ["verbose"]}

# Token savings: ~75%
```

---

## Success Criteria

- [ ] Each HRM has its own retrospective analyzer
- [ ] Feedback types are HRM-aware
- [ ] Cross-HRM correlation detects patterns
- [ ] Learning HRM receives signals from all HRMs
- [ ] Token efficiency maintained (65%+ reduction)
- [ ] Retrospectives run < 500ms each
