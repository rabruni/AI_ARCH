# HRM Architecture for The Assist

## Directory Structure

```
the_assist/
  hrm/
    __init__.py
    intent.py       # Intent Store - L1
    planner.py      # Planner - L2
    executor.py     # Executor - L3
    evaluator.py    # Evaluator - L4
    loop.py         # HRM Loop orchestration
    memory/
      intent.json       # Tiny, stable, high authority
      plans.json        # Semi-stable, rewritable
      evaluations.json  # Delta-based, time-bounded
```

## Layer Specifications

### L1: Intent Store

**Purpose:** Define success. Hold authority.

**Interface:**
```python
class IntentStore:
    def get_intent() -> Intent
    def is_success(outcome: Outcome) -> bool
    def get_non_goals() -> list[str]
    def get_stop_conditions() -> list[str]
```

**Memory:** `intent.json`
```json
{
  "north_stars": ["family_present", "meaningful_tech", "financial_independence"],
  "current_success": "Be a cognitive partner, not a task manager",
  "non_goals": ["endless analysis", "feature stacking", "sycophancy"],
  "stop_conditions": ["user says stop", "frustration detected", "goal achieved"],
  "authority_rules": [
    "Intent outranks execution",
    "If execution drifts, intent pulls back",
    "Non-goals are hard constraints"
  ]
}
```

**Size:** < 50 lines. Never grows uncontrollably.

---

### L2: Planner

**Purpose:** Break problems into approach. Manage tradeoffs.

**Interface:**
```python
class Planner:
    def plan(intent: Intent, situation: Situation) -> Plan
    def revise(plan: Plan, evaluation: Evaluation) -> Plan
    def get_approach() -> Approach
```

**Inputs:**
- Intent from L1 (what success looks like)
- Situation from L3 (what's happening now)
- Evaluation from L4 (what worked/didn't)

**Outputs:**
- Approach for Executor
- Constraints to enforce
- Altitude to operate at

**Memory:** `plans.json` - session-level, rewritable
```json
{
  "current_plan": {
    "approach": "strategic_exploration",
    "altitude": "L3",
    "constraints": ["no tactical without strategic context"],
    "focus": ["connect to north stars", "challenge when needed"]
  },
  "revision_history": []
}
```

---

### L3: Executor

**Purpose:** Do the work. Report state.

**Interface:**
```python
class Executor:
    def execute(plan: Plan, user_input: str) -> ExecutionResult
    def report_state() -> State
```

**Inputs:**
- Plan from L2 (how to approach this)
- User input (what to respond to)

**Outputs:**
- Response to user
- State report to L4 (what happened, not what it means)

**Memory:** Conversation history. Ephemeral. Disposable after session.

**Key constraint:** Executor does NOT decide meaning. It reports state.

---

### L4: Evaluator

**Purpose:** Compare outcome to intent. Trigger revision.

**Interface:**
```python
class Evaluator:
    def evaluate(intent: Intent, outcome: Outcome) -> Evaluation
    def should_revise_plan() -> bool
    def should_escalate_to_intent() -> bool
```

**Inputs:**
- Intent from L1 (what success looks like)
- Outcome from L3 (what actually happened)

**Outputs:**
- Evaluation (did it work?)
- Revision trigger to L2 if plan needs adjustment
- Escalation trigger to L1 if intent needs clarification

**Memory:** `evaluations.json` - delta-based, time-bounded
```json
{
  "recent_evaluations": [
    {
      "timestamp": "...",
      "outcome": "tactical_drift",
      "matched_intent": false,
      "revision_triggered": true,
      "target": "planner"
    }
  ],
  "patterns": {
    "repeated_failures": [],
    "successful_approaches": []
  }
}
```

---

## The HRM Loop

```
User Input
    ↓
┌─────────────────────────────────────────────┐
│  L1: Intent Store                           │
│  - Provides success criteria                │
│  - Provides non-goals                       │
│  - Has authority over all layers            │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  L2: Planner                                │
│  - Reads intent                             │
│  - Reads situation (from L3 state report)   │
│  - Reads evaluation (from L4)               │
│  - Outputs: approach, constraints, altitude │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  L3: Executor                               │
│  - Receives plan                            │
│  - Processes user input                     │
│  - Generates response                       │
│  - Reports state (not meaning)              │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  L4: Evaluator                              │
│  - Compares outcome to intent               │
│  - Detects drift, errors, success           │
│  - Triggers revision UP to L2               │
│  - Escalates to L1 if needed                │
└─────────────────┴───────────────────────────┘
                  ↑
            Revision loop
```

---

## Memory Type Enforcement

| Layer | Memory File | Characteristics |
|-------|-------------|-----------------|
| Intent | intent.json | Tiny (<50 lines), stable, rarely changes, HIGH AUTHORITY |
| Planner | plans.json | Semi-stable, rewritable per session, pattern-oriented |
| Executor | conversation | Ephemeral, disposable after session |
| Evaluator | evaluations.json | Delta-based, time-bounded, auto-expires |

---

## Key Invariants

1. **Intent has authority.** If any layer conflicts with intent, intent wins.
2. **Layers don't leak.** Executor never modifies intent. Evaluator never executes.
3. **State flows up, meaning flows down.** Lower layers report what happened. Upper layers decide what it means.
4. **Revision is cheap.** Changing the plan doesn't require changing intent. Changing intent doesn't require replaying execution.
5. **Each layer has isolated context.** Fresh API calls for Planner and Evaluator. No context pollution.

---

## What This Replaces

| Old Component | New Layer | Key Change |
|---------------|-----------|------------|
| perception_agent.py | Evaluator (L4) | Only evaluates, doesn't plan |
| hrm_agent.py | Planner (L2) | Only plans, doesn't evaluate |
| orchestrator.py | Executor (L3) | Only executes, doesn't self-correct |
| north_stars in memory | Intent Store (L1) | Has authority, not just data |
