# HRM Interface Specifications

**Version:** 1.0
**Status:** Specification

This document defines the API contracts between all HRM layers and components. These interfaces are the binding contracts for implementation.

---

## 1. Core Data Types

### 1.1 Shared Enums

```python
from enum import Enum
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime

class AltitudeLevel(Enum):
    L4_IDENTITY = "identity"      # Who are we, what do we value?
    L3_STRATEGY = "strategy"      # What's the approach?
    L2_OPERATIONS = "operations"  # How do we execute?
    L1_MOMENT = "moment"          # What's happening now?

class Stance(Enum):
    SENSEMAKING = "sensemaking"   # Exploration + Accuracy
    DISCOVERY = "discovery"       # Exploration + Momentum
    EXECUTION = "execution"       # Exploitation + Momentum
    EVALUATION = "evaluation"     # Exploitation + Accuracy

class GateType(Enum):
    FRAMING = "framing"           # Problem understanding
    COMMITMENT = "commitment"     # Work contract
    EVALUATION = "evaluation"     # Result assessment
    EMERGENCY = "emergency"       # Interrupt
    WRITE_APPROVAL = "write_approval"
    AGENT_APPROVAL = "agent_approval"

class ReducerType(Enum):
    """Reducer strategies for MapReduce orchestration."""
    PASS_THROUGH = "pass_through"   # Pipeline: pass output to next
    MERGE = "merge"                 # Parallel: combine all outputs
    VOTE = "vote"                   # Voting: tally and select winner
    SYNTHESIZE = "synthesize"       # Hierarchical: lead synthesizes delegate outputs

class Complexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

class Stakes(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ConflictLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class BlastRadius(Enum):
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SEVERE = "severe"
```

### 1.2 Context Objects

```python
@dataclass
class HRMContext:
    """Shared context passed between all HRM layers."""

    # Identifiers
    session_id: str
    turn_number: int
    problem_id: Optional[str]

    # Current state
    altitude: AltitudeLevel
    stance: Stance
    commitment_id: Optional[str]
    commitment_turns_remaining: Optional[int]

    # History (last N turns)
    recent_inputs: list[str]
    recent_outputs: list[str]
    recent_decisions: list[dict]

    # Flags
    trace_enabled: bool = False
    debug_mode: bool = False

@dataclass
class TurnInput:
    """Input for a single turn."""

    text: str
    timestamp: datetime
    context: HRMContext

    # Optional metadata
    source: str = "user"           # user | system | agent
    priority: int = 0              # Higher = more urgent
    metadata: dict = None
```

---

## 2. Altitude HRM Interfaces

**Simplification:** No Protocol interfaces. Plain classes with typed methods.

### 2.1 AltitudeGovernor

```python
class AltitudeGovernor:
    """Main class for Altitude HRM. No Protocol needed - single implementation."""

    def __init__(self, config: 'HRMConfig'):
        self.config = config
        self.current_level = config.altitude_default_level

    def classify_input(self, input: TurnInput) -> AltitudeClassification:
        """Determine the altitude level for this input."""
        ...

    def validate_action(self, action: dict, current_level: AltitudeLevel) -> bool:
        """Check if action is appropriate for current altitude. Returns True/False."""
        ...

    def transition(self, to_level: AltitudeLevel, reason: str) -> bool:
        """Attempt to change altitude level. Returns success."""
        ...

@dataclass
class AltitudeClassification:
    level: AltitudeLevel
    confidence: float           # 0.0 - 1.0
    signals: list[str]          # What triggered this classification
    suggested_stance: Optional[Stance]
    allows_agents: bool
```

**Note:** ValidationResult and TransitionResult removed. Methods return bool for simple pass/fail.
Use Event logging for audit trail of transitions.

### 2.2 Altitude Planner

```python
class AltitudePlanner:
    """Planning layer within Altitude HRM."""

    def generate_plan(self, input: TurnInput, classification: AltitudeClassification) -> Plan:
        """Generate a plan appropriate for current altitude."""
        ...

    def validate_plan(self, plan: Plan, stance: Stance) -> bool:
        """Check if plan is allowed by current stance. Returns True/False."""
        ...

@dataclass
class Plan:
    id: str
    steps: list[PlanStep]
    estimated_turns: int
    requires_agents: bool
    agent_suggestion: Optional[str]  # Agent ID if agents needed

@dataclass
class PlanStep:
    order: int
    description: str
    action_type: str              # research | execute | validate | ask
    dependencies: list[int]       # Step IDs this depends on
```

**Note:** PlanValidation removed. validate_plan() returns bool. Log violations as Events.

### 2.3 Altitude Evaluator

```python
class AltitudeEvaluator:
    """Evaluation layer within Altitude HRM."""

    def evaluate_result(self, result: 'ExecutionResult', plan: Plan) -> Evaluation:
        """Assess execution result against plan."""
        ...

    def should_transition(self, evaluation: Evaluation, current_level: AltitudeLevel) -> Optional[AltitudeLevel]:
        """Determine if altitude should change based on evaluation. Returns new level or None."""
        ...

@dataclass
class Evaluation:
    success: bool
    completion_ratio: float       # 0.0 - 1.0
    quality_score: float          # 0.0 - 1.0
    issues: list[str]
    suggestions: list[str]
```

### 2.4 Altitude Executor

```python
class AltitudeExecutor:
    """Execution layer within Altitude HRM."""

    def execute(self, plan: Plan, context: HRMContext) -> 'ExecutionResult':
        """Execute a plan. All writes go through Focus HRM gates."""
        ...

    def request_write_approval(self, write_request: 'WriteRequest') -> bool:
        """Request approval from Focus HRM for a write. Returns True if approved."""
        ...

@dataclass
class ExecutionResult:
    success: bool
    outputs: list[str]
    artifacts_created: list[str]
    turns_used: int
    errors: list[str]

@dataclass
class WriteRequest:
    target: str                   # working_set | shared_reference | episodic | synthesis
    key: str
    value: Any
    signals: WriteSignals
    reason: str
```

---

## 3. Reasoning HRM Interfaces

**Simplification:** No Protocol interfaces. Plain classes with typed methods.

### 3.1 ReasoningRouter

```python
class ReasoningRouter:
    """Main class for Reasoning HRM."""

    def route(self, input: TurnInput) -> RoutingDecision:
        """Determine how to handle this input."""
        ...

    def propose_agents(self, input: TurnInput) -> Optional['AgentBundleProposal']:
        """If agents are needed, propose which ones. Returns None if no agents needed."""
        ...

    def query_patterns(self, input_signature: dict) -> list[PatternMatch]:
        """Query for matching patterns from trace/learning."""
        ...

@dataclass
class RoutingDecision:
    strategy: str                 # quick_answer | decomposition | verification | exploration | dialogue
    confidence: float
    requires_agents: bool
    pattern_match: Optional[str]  # Pattern ID if matched
    escalation_level: int         # 0 = none, 1+ = escalated

@dataclass
class PatternMatch:
    pattern_id: str
    match_confidence: float
    recommended_strategy: str
    evidence_count: int
```

### 3.2 InputClassifier

```python
class InputClassifier:
    """Classifies input for strategy selection."""

    def classify(self, input: TurnInput) -> InputClassification:
        """Analyze input across multiple dimensions."""
        ...

@dataclass
class InputClassification:
    complexity: Complexity
    uncertainty: float            # 0.0 - 1.0
    conflict: ConflictLevel
    stakes: Stakes
    horizon: str                  # immediate | near | far
    domain: list[str]             # Detected topic areas
    confidence: float

    def should_escalate(self) -> bool:
        """Returns True if any dimension indicates escalation needed."""
        return (
            self.complexity == Complexity.COMPLEX or
            self.uncertainty > 0.7 or
            self.conflict != ConflictLevel.NONE or
            self.stakes == Stakes.HIGH
        )
```

### 3.3 StrategySelector

```python
class StrategySelector:
    """Selects reasoning strategy based on classification."""

    def select(self, classification: InputClassification, pattern_matches: list[PatternMatch]) -> StrategySelection:
        """Choose the best strategy for this input."""
        ...

@dataclass
class StrategySelection:
    strategy: str
    confidence: float
    reason: str
    requires_agents: bool
    suggested_reducer: Optional[ReducerType]   # Which reducer for MapReduce
    fallback_strategy: Optional[str]
```

### 3.4 EscalationManager

```python
class EscalationManager:
    """Manages escalation and de-escalation."""

    ESCALATION_THRESHOLD: float = 0.6  # Per user decision

    def should_escalate(self, classification: InputClassification, strategy: StrategySelection) -> bool:
        """Returns True if escalation needed."""
        ...

    def escalate(self, strategy: StrategySelection) -> StrategySelection:
        """Return escalated strategy."""
        ...

    def should_deescalate(self, strategy: StrategySelection, pattern_confidence: float) -> bool:
        """Returns True if de-escalation appropriate."""
        ...

    def deescalate(self, strategy: StrategySelection) -> StrategySelection:
        """Return de-escalated strategy."""
        ...
```

### 3.5 AgentBundleProposal

```python
@dataclass
class AgentBundleProposal:
    """
    What Reasoning HRM produces when agents are needed.
    Sent to Focus HRM for approval.
    """

    # What triggered this
    strategy: str
    classification: InputClassification

    # What agents are needed
    agents: list[str]             # Agent IDs to activate
    reducer: ReducerType          # How to combine outputs (MapReduce)
    parallel: bool = True         # Run agents in parallel?

    # Reducer-specific config
    reducer_config: dict = field(default_factory=dict)
    # PASS_THROUGH: {} (pipeline - each feeds next)
    # MERGE:        {"strategy": "concatenate" | "dedupe"}
    # VOTE:         {"threshold": 0.6, "tiebreaker": "first"}
    # SYNTHESIZE:   {"lead": "agent_a"} (lead synthesizes delegate outputs)

    # Rationale
    reason: str
    confidence: float
    fallback: Optional[str]       # Alternative if denied
```

### 3.6 ActionSelector (Next Best Action)

```python
class ActionSelector:
    """
    Final stage of Reasoning HRM.

    Selects exactly ONE primary action (or micro-batch of 2-3 max) from
    candidates. This is NOT a separate layer - it's the final output of
    Reasoning before Focus HRM governs.

    Key principle: Focus HRM should govern the chosen action, not a bag
    of possibilities. ActionSelector ensures Reasoning emits a single,
    prioritized proposal.
    """

    def select(self, candidates: list['CandidateAction'], context: HRMContext) -> 'SelectedAction':
        """
        Pick the next best action from allowed candidates.

        Uses priority signals:
        - urgency: Time-sensitive? (0.0 - 1.0)
        - dependency: Unblocks other work? (0.0 - 1.0)
        - momentum: Continues current flow? (0.0 - 1.0)
        - energy_cost: Cognitive/resource cost (0.0 - 1.0, lower = better)
        - alignment: Matches current commitment? (0.0 - 1.0)

        Returns exactly ONE primary action with rationale.
        """
        ...

    def should_use_voting(self, candidates: list['CandidateAction'], context: HRMContext) -> bool:
        """
        Determine if voting reducer is warranted.

        Voting is ONLY used when:
        1. High stakes (Stakes.HIGH) AND
        2. Multiple candidates with similar priority scores (within 0.1) AND
        3. Irreversible consequences
        """
        ...

@dataclass
class CandidateAction:
    """A potential action generated during strategy/proposal phase."""

    id: str
    action_type: str              # respond | execute | delegate | ask | wait
    description: str

    # Priority signals
    urgency: float                # 0.0 - 1.0
    dependency_score: float       # How much this unblocks
    momentum_score: float         # How well this continues flow
    energy_cost: float            # Cognitive/resource cost
    alignment_score: float        # Match to current commitment

    # If this action requires agents
    agent_proposal: Optional[AgentBundleProposal]

    # Metadata
    source: str                   # What generated this candidate

@dataclass
class SelectedAction:
    """The single action Reasoning HRM outputs to Focus HRM."""

    # The chosen action
    primary: CandidateAction

    # Why this one?
    rationale: str
    priority_score: float         # Computed from signals

    # Fallback if Focus denies
    fallback: Optional[CandidateAction]

    # Micro-batch (rare, max 2-3)
    # Only when actions are atomic and tightly coupled
    batch: Optional[list[CandidateAction]] = None

    def is_batch(self) -> bool:
        """Returns True if this is a micro-batch, not single action."""
        return self.batch is not None and len(self.batch) > 1

@dataclass
class PrioritySignals:
    """Signals used to compute action priority."""

    urgency: float = 0.0          # Time-sensitive
    dependency: float = 0.0       # Unblocks other work
    momentum: float = 0.0         # Continues current flow
    energy_cost: float = 0.5      # Resource cost (lower = better)
    alignment: float = 1.0        # Matches commitment

    def compute_score(self, weights: dict = None) -> float:
        """
        Compute weighted priority score.

        Default weights favor momentum and alignment (exploitation),
        but can be adjusted based on stance.
        """
        w = weights or {
            "urgency": 0.2,
            "dependency": 0.2,
            "momentum": 0.25,
            "energy_cost": 0.15,  # Inverted in calculation
            "alignment": 0.2
        }
        return (
            w["urgency"] * self.urgency +
            w["dependency"] * self.dependency +
            w["momentum"] * self.momentum +
            w["energy_cost"] * (1 - self.energy_cost) +  # Invert: low cost = high score
            w["alignment"] * self.alignment
        )
```

#### ActionSelector Rules

**What it DOES:**
1. Produce exactly ONE primary action per turn (or micro-batch of 2-3 max)
2. Include rationale explaining why this action was chosen
3. Include fallback if primary is blocked by Focus
4. Apply priority signals to break ties between allowed candidates
5. Trigger voting mode ONLY under explicit high-stakes conditions

**What it MUST NEVER do:**
1. Override Focus stance, gates, or lease rules
2. Schedule work across multiple turns (that's Commitment Manager's job)
3. Create a second priority system conflicting with ProblemRegistry.priority
4. Emit multiple unrelated actions as a "batch"

#### Integration with ReasoningRouter

The ReasoningRouter becomes explicitly two-phase:

```python
class ReasoningRouter:
    """
    Two-phase Reasoning HRM:
    1. Generate phase: Classify input, select strategy, generate candidates
    2. Select phase: Pick the next best action via ActionSelector
    """

    def __init__(
        self,
        classifier: InputClassifier,
        strategy_selector: StrategySelector,
        escalation_manager: EscalationManager,
        action_selector: ActionSelector,
        learning_hrm: Optional['LearningHRM'] = None
    ):
        ...

    def process(self, input: TurnInput) -> SelectedAction:
        """
        Full reasoning pipeline. Returns exactly ONE action for Focus to govern.
        """
        # Phase 1: Generate candidates
        classification = self.classifier.classify(input)
        patterns = self._query_learning(input) if self.learning_hrm else []
        strategy = self.strategy_selector.select(classification, patterns)

        if self.escalation_manager.should_escalate(classification, strategy):
            strategy = self.escalation_manager.escalate(strategy)

        candidates = self._generate_candidates(input, strategy, classification)

        # Phase 2: Select next best action
        selected = self.action_selector.select(candidates, self._get_context())

        return selected  # Single action (or micro-batch) for Focus HRM

    def _generate_candidates(
        self,
        input: TurnInput,
        strategy: StrategySelection,
        classification: InputClassification
    ) -> list[CandidateAction]:
        """Generate candidate actions based on strategy."""
        candidates = []

        # Always include direct response option
        candidates.append(CandidateAction(
            id="respond_direct",
            action_type="respond",
            description="Answer directly without agents",
            urgency=0.3,
            momentum_score=0.8,
            energy_cost=0.2,
            ...
        ))

        # If strategy requires agents, add agent-based candidate
        if strategy.requires_agents:
            proposal = self._build_agent_proposal(strategy, classification)
            candidates.append(CandidateAction(
                id="delegate_agents",
                action_type="delegate",
                description=f"Delegate to agents: {proposal.agents}",
                agent_proposal=proposal,
                ...
            ))

        # If uncertain, add clarification option
        if classification.uncertainty > 0.5:
            candidates.append(CandidateAction(
                id="ask_clarify",
                action_type="ask",
                description="Ask user for clarification",
                urgency=0.1,
                momentum_score=0.3,
                ...
            ))

        return candidates
```

---

## 4. Focus HRM Interfaces

**Simplification:** No Protocol interfaces. Plain classes with typed methods.

### 4.1 StanceMachine

```python
class StanceMachine:
    """4-state exclusive stance machine."""

    def __init__(self):
        self.current = Stance.SENSEMAKING

    def get_current(self) -> Stance:
        """Return current stance."""
        return self.current

    def transition(self, to_stance: Stance, reason: str, via_gate: GateType) -> bool:
        """Attempt stance transition through a gate. Returns success."""
        # Log transition as Event for audit trail
        ...

    def get_allowed_actions(self) -> list[str]:
        """Return actions allowed in current stance."""
        ...
```

**Note:** StanceTransition result type removed. Method returns bool. Log transitions as Events.

### 4.2 GateController

```python
class GateController:
    """Enforces checkpoints for state changes."""

    def __init__(self):
        self.evaluators: dict[GateType, Callable] = {}

    def attempt_gate(self, gate: GateType, context: dict) -> bool:
        """Try to pass through a gate. Returns True if approved."""
        ...

    def register_gate(self, gate: GateType, evaluator: Callable) -> None:
        """Register custom gate evaluator."""
        self.evaluators[gate] = evaluator
```

**Note:** GateDecision result type removed. Method returns bool. Log decisions as Events.

### 4.3 CommitmentManager

```python
class CommitmentManager:
    """Lease-based focus with TTL."""

    def __init__(self):
        self.active: Optional[Commitment] = None

    def create(self, problem_id: str, description: str, turns: int) -> Commitment:
        """Create a new commitment."""
        ...

    def get_active(self) -> Optional[Commitment]:
        """Return current active commitment."""
        return self.active

    def tick(self) -> Optional[Commitment]:
        """Decrement turn counter, return commitment if still active."""
        ...

    def complete(self) -> bool:
        """Mark commitment as complete. Returns success."""
        ...

    def abandon(self, reason: str) -> bool:
        """Abandon commitment with reason. Returns success."""
        ...

@dataclass
class Commitment:
    id: str
    problem_id: str
    description: str
    turns_remaining: int
    turns_total: int
    created_at: datetime
    status: str                   # active | completed | abandoned
```

### 4.4 AgentApprovalGate

```python
class AgentApprovalGate:
    """Gate for validating agent bundle proposals."""

    def evaluate(self, proposal: AgentBundleProposal, stance: Stance, commitment: Optional[Commitment]) -> bool:
        """
        Validate agent proposal against governance state. Returns True if approved.

        Validation Rules:
        1. Check stance compatibility
        2. Check commitment alignment
        3. Check agent authorization
        4. Check reducer compatibility
        """
        ...

    def stance_allows(self, proposal: AgentBundleProposal, stance: Stance) -> bool:
        """
        Check if current stance allows this type of agent work.

        Mapping:
        - SENSEMAKING: exploration, verification
        - DISCOVERY: exploration, decomposition
        - EXECUTION: any reducer
        - EVALUATION: voting, verification
        """
        ...
```

### 4.5 AgentRuntime

**Note:** AgentFirewall is inlined here as `_validate_output()`. No separate firewall class needed.

```python
class AgentRuntime:
    """Executes approved agent bundles using MapReduce pattern."""

    def execute_bundle(self, proposal: AgentBundleProposal, context: 'AgentExecutionContext') -> 'AgentExecutionResult':
        """
        Execute agent bundle using MapReduce:
        1. Map: Run agents (parallel or serial based on proposal.parallel)
        2. Validate: Check each output via _validate_output()
        3. Reduce: Combine outputs using proposal.reducer
        """
        outputs = self._map(proposal.agents, context, parallel=proposal.parallel)
        validated = [self._validate_output(o) for o in outputs]
        return self._reduce(validated, proposal.reducer, proposal.reducer_config)

    def cancel(self, handle_id: str) -> bool:
        """Cancel running execution. Returns success."""
        ...

    def get_status(self, handle_id: str) -> 'AgentExecutionStatus':
        """Get current status of execution."""
        ...

    # ─────────────────────────────────────────────────────────────
    # Inlined Firewall (validation happens in reduce phase)
    # ─────────────────────────────────────────────────────────────

    def _validate_output(self, output: 'AgentOutput') -> 'AgentOutput':
        """
        Validate agent output against security rules.

        Rules:
        1. Agents cannot make decisions (only proposals)
        2. No unauthorized capability requests
        3. Valid output packet structure
        4. No prompt injection attempts

        Raises HRMError.agent_violation() on failure.
        """
        if output.contains_decision():
            raise HRMError.agent_violation("Agents cannot make decisions, only proposals")
        if not output.is_valid_packet():
            raise HRMError.agent_violation("Invalid output packet structure")
        # Additional checks...
        return output

@dataclass
class AgentExecutionContext:
    problem_id: str
    commitment_id: Optional[str]
    stance: Stance
    reducer: ReducerType
    reducer_config: dict

@dataclass
class AgentExecutionResult:
    """Result of MapReduce execution."""
    id: str
    agents: list[str]
    reducer: ReducerType
    success: bool
    result: Optional[Any]
    error: Optional[str]
    duration_ms: int

@dataclass
class AgentExecutionStatus:
    handle_id: str
    status: str                   # pending | running | completed | failed | cancelled
    progress: float               # 0.0 - 1.0
    current_agent: Optional[str]
    outputs_so_far: list[str]

@dataclass
class AgentOutput:
    agent_id: str
    output_type: str              # proposal | data | artifact
    content: Any
    requested_capabilities: list[str]
    metadata: dict

    def contains_decision(self) -> bool:
        """Check if output contains a decision instead of proposal."""
        decision_markers = ["DECISION:", "I have decided", "Final answer:"]
        return any(m in str(self.content) for m in decision_markers)

    def is_valid_packet(self) -> bool:
        """Check if output has valid structure."""
        return self.agent_id and self.output_type in ("proposal", "data", "artifact")
```

**Note:** FirewallViolation exception removed. Use `HRMError.agent_violation()` instead.

---

## 5. Learning HRM Interfaces

**Simplification:** No Protocol interfaces. Plain classes with typed methods.

### 5.1 PatternStore

```python
class PatternStore:
    """Store and query patterns with evidence links."""

    def add_pattern(self, pattern: 'Pattern') -> str:
        """Add a new pattern, return ID."""
        ...

    def get_pattern(self, pattern_id: str) -> Optional['Pattern']:
        """Retrieve pattern by ID."""
        ...

    def search(self, input_signature: dict) -> list[PatternMatch]:
        """Find patterns matching the input signature."""
        ...

    def strengthen(self, pattern_id: str, evidence_id: str) -> None:
        """Increase pattern confidence with new evidence."""
        ...

    def weaken(self, pattern_id: str, reason: str) -> None:
        """Decrease pattern confidence."""
        ...

    def protect(self, pattern_id: str) -> None:
        """Prevent pattern from manual removal. NOTE: No auto-trim per user decision."""
        ...

@dataclass
class Pattern:
    id: str
    pattern_type: str             # strategy | behavior | preference
    input_signature: dict         # What triggers this pattern
    recommended_action: dict      # What to do when triggered
    confidence: float             # 0.0 - 1.0
    evidence_ids: list[str]       # Links to EpisodicTrace
    created_at: datetime
    last_matched_at: Optional[datetime]
    match_count: int
```

### 5.2 FeedbackLoop

```python
class FeedbackLoop:
    """Session analysis and pattern learning."""

    def record_outcome(self, signal: dict, routing: dict, outcome: dict) -> str:
        """Record a signal→routing→outcome tuple. Returns evidence ID."""
        ...

    def analyze_session(self) -> 'SessionAnalysis':
        """Analyze current session for patterns."""
        ...

    def get_patterns_for_signal(self, signal: dict) -> list[PatternMatch]:
        """Query patterns matching a signal (for Reasoning HRM)."""
        ...

@dataclass
class SessionAnalysis:
    session_id: str
    turn_count: int
    outcomes_recorded: int
    patterns_strengthened: list[str]
    patterns_weakened: list[str]
    patterns_created: list[str]
    insights: list[str]

@dataclass
class OutcomeRecord:
    id: str
    signal: dict                  # What triggered the action
    routing: dict                 # How it was routed (strategy, agents, etc.)
    outcome: dict                 # What happened
    success: bool
    timestamp: datetime
```

### 5.3 Generalizer

```python
class Generalizer:
    """Merge similar patterns into abstractions."""

    def find_similar(self, patterns: list[Pattern]) -> list[tuple[Pattern, Pattern, float]]:
        """Find pairs of similar patterns with similarity score."""
        ...

    def merge(self, p1: Pattern, p2: Pattern) -> Pattern:
        """Merge two patterns into a more general one. Preserves evidence from both."""
        ...

    def generalize_batch(self, patterns: list[Pattern]) -> list[Pattern]:
        """Process list, merging similar patterns."""
        ...
```

---

## 6. Memory Bus Interfaces

**Simplification:** No Protocol interfaces. Plain classes with typed methods.

### 6.1 MemoryBus

```python
class MemoryBus:
    """Unified memory access with file locking."""

    def write_to_working(self, problem_id: str, key: str, value: Any) -> bool:
        """Write to problem-isolated Working Set. No gate required (local scope)."""
        ...

    def write_to_shared(self, key: str, value: Any, source: str, signals: 'WriteSignals') -> bool:
        """Write to Shared Reference. Requires WriteGate approval. Returns success."""
        ...

    def log_episode(self, entry: 'EpisodeEntry') -> str:
        """Append to Episodic Trace. Always succeeds (append-only). Returns entry ID."""
        ...

    def add_synthesis(self, pattern: 'SynthesizedPattern', signals: 'WriteSignals') -> bool:
        """Add to Semantic Synthesis. Requires WriteGate approval (high bar). Returns success."""
        ...

    def get_evidence_chain(self, pattern_id: str) -> list['EpisodeEntry']:
        """Get full evidence chain for a pattern."""
        ...
```

### 6.2 WriteGate

```python
class WriteGate:
    """Signal-based write policy decisions."""

    def evaluate(self, request: 'WriteRequest') -> bool:
        """
        Evaluate whether write should proceed. Returns True if approved.

        Rules:
        1. High blast radius → higher confidence threshold
        2. Conflict detected → Working Set only
        3. Low alignment → won't synthesize
        4. Low source quality → Episodic only
        """
        ...

@dataclass
class WriteSignals:
    progress_delta: float         # How much progress this represents
    conflict_level: ConflictLevel
    source_quality: float         # 0.0 - 1.0
    alignment_score: float        # 0.0 - 1.0
    blast_radius: BlastRadius

@dataclass
class WriteDecision:
    approved: bool
    target: str                   # Where write can go (may differ from request)
    reason: str
    conditions: list[str]         # Any conditions on the write
```

### 6.3 Compartment Stores

```python
class WorkingSetStore:
    """Per-problem isolated memory with TTL."""

    def create(self, problem_id: str, ttl_hours: int = 2) -> 'WorkingSet':
        ...

    def get(self, problem_id: str) -> Optional['WorkingSet']:
        ...

    def update(self, problem_id: str, **kwargs) -> None:
        ...

    def expire_stale(self) -> int:
        """Expire stale sets, return count."""
        ...

    def export_summary(self, problem_id: str) -> str:
        """Export summary for archival."""
        ...


class SharedReferenceStore:
    """Versioned, citable cross-problem facts."""

    def get(self, key: str, version: int = None) -> 'SharedReference':
        ...

    def set(self, key: str, value: Any, source: str) -> int:
        """Set value, return new version number."""
        ...

    def list_versions(self, key: str) -> list[int]:
        ...

    def rollback(self, key: str, to_version: int) -> bool:
        ...

    def cite(self, key: str) -> str:
        """Generate citation string."""
        ...


class EpisodicTraceStore:
    """Append-only audit logs."""

    def append(self, entry: 'EpisodeEntry') -> str:
        """Append entry, return ID."""
        ...

    def query(
        self,
        start: datetime = None,
        end: datetime = None,
        problem_id: str = None,
        tags: list[str] = None,
        entry_type: str = None
    ) -> list['EpisodeEntry']:
        ...

    def supersede(self, old_id: str, new_entry: 'EpisodeEntry') -> str:
        """Create new entry that supersedes old one."""
        ...


class SemanticSynthesisStore:
    """Evidence-linked patterns."""

    def add_pattern(self, pattern: 'SynthesizedPattern') -> str:
        ...

    def get_pattern(self, pattern_id: str) -> 'SynthesizedPattern':
        ...

    def search(self, pattern_type: str = None, min_confidence: float = 0.0) -> list['SynthesizedPattern']:
        ...

    def strengthen(self, pattern_id: str, new_evidence_id: str) -> None:
        ...

    def weaken(self, pattern_id: str, reason: str) -> None:
        ...

    def get_evidence_chain(self, pattern_id: str) -> list['EpisodeEntry']:
        ...
```

### 6.4 Memory Data Types

```python
@dataclass
class WorkingSet:
    problem_id: str
    constraints: dict
    assumptions: list[dict]
    open_questions: list[str]
    partial_artifacts: dict
    local_decisions: list[dict]
    created_at: datetime
    expires_at: datetime

@dataclass
class SharedReference:
    key: str
    value: Any
    version: int
    source: str                   # Who set this
    created_at: datetime
    updated_at: datetime

@dataclass
class EpisodeEntry:
    id: str
    timestamp: datetime
    problem_id: Optional[str]
    entry_type: str               # decision | action | observation | reflection
    content: dict
    tags: list[str]
    supersedes: Optional[str]     # ID of entry this supersedes
    superseded_by: Optional[str]  # ID of entry that supersedes this

@dataclass
class SynthesizedPattern:
    id: str
    pattern_type: str
    description: str
    input_signature: dict
    recommended_action: dict
    confidence: float
    evidence_ids: list[str]       # Links to EpisodeEntry
    created_at: datetime
    last_strengthened_at: datetime
```

---

## 7. Tracing Interface

**Simplification:** No Protocol interfaces. Plain classes with typed methods.

### 7.1 Tracer

```python
class Tracer:
    """Observability singleton."""

    def span(self, hrm: str, operation: str, component: str, input_data: str = None) -> 'SpanContext':
        """Create a new span (context manager)."""
        ...

    def event(self, hrm: str, operation: str, status: str = "info", data: dict = None) -> None:
        """Log a single event within current span."""
        ...

    def generate_id(self, hrm: str) -> str:
        """Generate trace ID with HRM prefix. Format: {hrm}_{timestamp}_{random}"""
        ...

@dataclass
class TraceEvent:
    trace_id: str
    parent_id: Optional[str]
    hrm: str                      # altitude | reasoning | focus | learning
    operation: str
    component: str
    status: str                   # started | completed | error | info
    timestamp: datetime
    duration_ms: Optional[int]
    input_summary: Optional[str]
    output_summary: Optional[str]
    metadata: dict

class SpanContext:
    """Context manager for spans."""

    def __enter__(self) -> 'SpanContext':
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    def set_output(self, output: str) -> None:
        ...

    def add_metadata(self, key: str, value: Any) -> None:
        ...
```

---

## 8. Cross-HRM Communication

### 8.1 Message Flow

```
┌───────────────┐     TurnInput      ┌─────────────────┐
│    Entry      │ ─────────────────► │  Altitude HRM   │
│    Point      │                    │  (classify)     │
└───────────────┘                    └────────┬────────┘
                                              │ AltitudeClassification
                                              ▼
                                     ┌─────────────────┐
                                     │  Reasoning HRM  │
                                     │  (route)        │
                                     └────────┬────────┘
                                              │ AgentBundleProposal (optional)
                                              ▼
                                     ┌─────────────────┐
                                     │  Focus HRM      │
                                     │  (approve)      │
                                     └────────┬────────┘
                                              │ GateDecision
                                              ▼
                                     ┌─────────────────┐
                                     │  Agent Runtime  │
                                     │  (execute)      │
                                     └────────┬────────┘
                                              │ ExecutionResult
                                              ▼
                                     ┌─────────────────┐
                                     │  Learning HRM   │
                                     │  (record)       │
                                     └─────────────────┘
```

### 8.2 Inter-HRM Calls

| From | To | Method | Data |
|------|-----|--------|------|
| Altitude | Reasoning | `route(TurnInput)` | Classification + input |
| Reasoning | Focus | `evaluate(AgentBundleProposal)` | Proposal for approval |
| Reasoning | Learning | `get_patterns_for_signal(dict)` | Signal signature |
| Focus | AgentRuntime | `execute_bundle(AgentBundleProposal)` | Approved proposal |
| Focus | MemoryBus | `write_to_*(...)` | Write requests |
| Learning | MemoryBus | `add_synthesis(...)` | Pattern storage |
| All | Tracer | `span(...), event(...)` | Trace data |

### 8.3 Event-Based Communication

**Simplification:** Instead of callback interfaces, use Event logging to EpisodicTrace.
All cross-HRM notifications become Event appends. Consumers query the trace.

```python
# Instead of callbacks, append Events to trace:

# Altitude transition
trace.append(Event(
    event_type="altitude_transition",
    payload={"from": old_level.value, "to": new_level.value, "reason": reason}
))

# Stance change
trace.append(Event(
    event_type="stance_change",
    payload={"from": old_stance.value, "to": new_stance.value, "via_gate": gate.value}
))

# Agent activated
trace.append(Event(
    event_type="agent_activated",
    payload={"agents": handle.agents, "reducer": handle.reducer.value}
))

# Pattern matched
trace.append(Event(
    event_type="pattern_matched",
    payload={"pattern_id": pattern.id, "confidence": confidence}
))

# Write completed
trace.append(Event(
    event_type="write_completed",
    payload={"target": target, "key": key, "approved": approved}
))


# Consumers query trace instead of registering callbacks:
def get_recent_transitions(trace: EpisodicTraceStore, since: datetime) -> list[Event]:
    return trace.query(event_type="altitude_transition", start=since)

def get_agent_activations(trace: EpisodicTraceStore, session_id: str) -> list[Event]:
    return trace.query(event_type="agent_activated", problem_id=session_id)
```

### 8.4 MapReduce Orchestration Pattern

**Simplification:** Instead of 4 separate orchestration modes (Pipeline, Parallel, Voting, Hierarchical),
use a single MapReduce pattern with different reducers.

```python
class Orchestrator:
    """
    Single execution engine for all agent orchestration.

    All modes become Map + Reduce:
    - Pipeline:     Map(serial) + PassThroughReducer
    - Parallel:     Map(parallel) + MergeReducer
    - Voting:       Map(parallel) + VotingReducer
    - Hierarchical: Planning step → Map(parallel) + SynthesisReducer

    Benefits:
    - One timeout implementation
    - One cancellation implementation
    - One retry strategy
    - One test suite
    """

    def __init__(self, runtime: AgentRuntime, timeout_ms: int = 30000):
        self.runtime = runtime
        self.timeout_ms = timeout_ms

    def execute(
        self,
        agents: list[str],
        reducer: 'Reducer',
        parallel: bool = True,
        context: Optional[AgentExecutionContext] = None
    ) -> 'OrchestratorResult':
        """
        Execute agents using MapReduce pattern.

        Args:
            agents: List of agent IDs to run
            reducer: How to combine outputs
            parallel: Run agents in parallel (True) or serial (False)
            context: Execution context

        Returns:
            OrchestratorResult with combined output
        """
        try:
            # Map phase: run all agents
            outputs = self._map(agents, parallel, context)

            # Validate phase: check each output (inlined firewall)
            validated = [self._validate(o) for o in outputs]

            # Reduce phase: combine outputs
            result = reducer.reduce(validated)

            return OrchestratorResult(success=True, result=result)

        except HRMError as e:
            return OrchestratorResult(success=False, error=e)

    def _map(self, agents: list[str], parallel: bool, context) -> list[AgentOutput]:
        """Run agents (parallel or serial)."""
        if parallel:
            # Run all agents concurrently with timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(self._run_agent, a, context): a for a in agents}
                outputs = []
                for future in concurrent.futures.as_completed(futures, timeout=self.timeout_ms/1000):
                    outputs.append(future.result())
                return outputs
        else:
            # Run agents serially, each gets previous output
            outputs = []
            prev_output = None
            for agent in agents:
                output = self._run_agent(agent, context, prev_output)
                outputs.append(output)
                prev_output = output
            return outputs

    def _validate(self, output: AgentOutput) -> AgentOutput:
        """Validate agent output (inlined firewall)."""
        if output.contains_decision():
            raise HRMError.agent_violation("Agents cannot make decisions")
        return output


@dataclass
class OrchestratorResult:
    success: bool
    result: Optional[Any] = None
    error: Optional[HRMError] = None


# ─────────────────────────────────────────────────────────────
# Reducer implementations
# ─────────────────────────────────────────────────────────────

class Reducer:
    """Base class for reducers."""
    def reduce(self, outputs: list[AgentOutput]) -> Any:
        raise NotImplementedError


class PassThroughReducer(Reducer):
    """For pipeline mode: return last output."""
    def reduce(self, outputs: list[AgentOutput]) -> Any:
        return outputs[-1].content if outputs else None


class MergeReducer(Reducer):
    """For parallel mode: merge all outputs."""
    def __init__(self, strategy: str = "concatenate"):
        self.strategy = strategy  # concatenate | dedupe | select_best

    def reduce(self, outputs: list[AgentOutput]) -> Any:
        if self.strategy == "concatenate":
            return [o.content for o in outputs]
        elif self.strategy == "dedupe":
            seen = set()
            result = []
            for o in outputs:
                key = str(o.content)
                if key not in seen:
                    seen.add(key)
                    result.append(o.content)
            return result
        elif self.strategy == "select_best":
            # Select output with highest confidence (if available)
            return max(outputs, key=lambda o: o.metadata.get("confidence", 0)).content
        return [o.content for o in outputs]


class VotingReducer(Reducer):
    """For voting mode: tally votes and select winner."""
    def __init__(self, threshold: float = 0.6, tiebreaker: str = "first"):
        self.threshold = threshold
        self.tiebreaker = tiebreaker  # first | escalate

    def reduce(self, outputs: list[AgentOutput]) -> Any:
        # Count votes for each unique answer
        votes: dict[str, int] = {}
        for o in outputs:
            key = str(o.content)
            votes[key] = votes.get(key, 0) + 1

        # Find winner
        total = len(outputs)
        for answer, count in sorted(votes.items(), key=lambda x: -x[1]):
            if count / total >= self.threshold:
                return answer

        # No winner met threshold
        if self.tiebreaker == "first":
            return outputs[0].content
        else:
            raise HRMError.gate_denied("voting", "No consensus reached, escalation required")


class SynthesisReducer(Reducer):
    """For hierarchical mode: lead agent synthesizes delegate outputs."""
    def __init__(self, lead_agent: str, llm: 'ILLMAdapter'):
        self.lead_agent = lead_agent
        self.llm = llm

    def reduce(self, outputs: list[AgentOutput]) -> Any:
        # Synthesize outputs using lead agent's LLM
        synthesis_prompt = f"Synthesize these outputs into a coherent response:\n"
        for i, o in enumerate(outputs):
            synthesis_prompt += f"\n[Output {i+1}]: {o.content}"

        response = self.llm.chat(
            messages=[Message(role="user", content=synthesis_prompt)],
            system=f"You are {self.lead_agent}, synthesizing delegate outputs."
        )
        return response.content
```

**Usage examples:**

```python
orchestrator = Orchestrator(runtime)

# Pipeline mode (serial execution)
result = orchestrator.execute(
    agents=["researcher", "writer", "editor"],
    reducer=PassThroughReducer(),
    parallel=False
)

# Parallel mode (concurrent, merge results)
result = orchestrator.execute(
    agents=["analyst_1", "analyst_2", "analyst_3"],
    reducer=MergeReducer(strategy="dedupe"),
    parallel=True
)

# Voting mode (concurrent, vote on answer)
result = orchestrator.execute(
    agents=["verifier_1", "verifier_2", "verifier_3"],
    reducer=VotingReducer(threshold=0.6),
    parallel=True
)

# Hierarchical mode (lead synthesizes delegate work)
result = orchestrator.execute(
    agents=["delegate_1", "delegate_2"],
    reducer=SynthesisReducer(lead_agent="lead", llm=llm_adapter),
    parallel=True
)
```

---

## 9. Error Handling

### 9.1 Single Error Type with Codes

**Simplification:** Instead of 12+ exception classes, use one HRMError with error codes.

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class ErrorCode(Enum):
    """All error codes in one place."""
    # Gate errors
    GATE_DENIED = "gate_denied"
    STANCE_VIOLATION = "stance_violation"

    # Write errors
    WRITE_DENIED = "write_denied"
    CONFLICT_DETECTED = "conflict_detected"

    # Reasoning errors
    ESCALATION_REQUIRED = "escalation_required"
    STRATEGY_FAILED = "strategy_failed"

    # Agent errors
    AGENT_VIOLATION = "agent_violation"
    AGENT_TIMEOUT = "agent_timeout"

    # LLM errors
    RATE_LIMIT = "rate_limit"
    TOKEN_LIMIT = "token_limit"
    CONTENT_FILTERED = "content_filtered"
    PROVIDER_ERROR = "provider_error"

    # System errors
    VALIDATION_FAILED = "validation_failed"
    INTERNAL_ERROR = "internal_error"


@dataclass
class HRMError(Exception):
    """
    Single exception type for all HRM errors.

    Usage:
        raise HRMError.gate_denied("commitment", "No active commitment")
        raise HRMError.rate_limit(retry_after_ms=5000)

    Handling:
        try:
            result = do_thing()
        except HRMError as e:
            if e.code == ErrorCode.RATE_LIMIT:
                time.sleep(e.retry_after_ms / 1000)
                retry()
            elif e.recoverable:
                fallback()
            else:
                raise
    """
    code: ErrorCode
    message: str
    recoverable: bool = True
    retry_after_ms: Optional[int] = None
    context: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"

    # ─────────────────────────────────────────────────────────────
    # Factory methods for common errors
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def gate_denied(cls, gate: str, reason: str) -> 'HRMError':
        return cls(
            code=ErrorCode.GATE_DENIED,
            message=reason,
            recoverable=True,
            context={"gate": gate}
        )

    @classmethod
    def stance_violation(cls, stance: str, action: str) -> 'HRMError':
        return cls(
            code=ErrorCode.STANCE_VIOLATION,
            message=f"Action '{action}' not allowed in stance '{stance}'",
            recoverable=True,
            context={"stance": stance, "action": action}
        )

    @classmethod
    def write_denied(cls, target: str, reason: str) -> 'HRMError':
        return cls(
            code=ErrorCode.WRITE_DENIED,
            message=reason,
            recoverable=True,
            context={"target": target}
        )

    @classmethod
    def agent_violation(cls, reason: str) -> 'HRMError':
        return cls(
            code=ErrorCode.AGENT_VIOLATION,
            message=reason,
            recoverable=False,
            context={}
        )

    @classmethod
    def rate_limit(cls, retry_after_ms: int) -> 'HRMError':
        return cls(
            code=ErrorCode.RATE_LIMIT,
            message="Rate limit exceeded",
            recoverable=True,
            retry_after_ms=retry_after_ms
        )

    @classmethod
    def token_limit(cls, limit: int, actual: int) -> 'HRMError':
        return cls(
            code=ErrorCode.TOKEN_LIMIT,
            message=f"Token limit exceeded: {actual} > {limit}",
            recoverable=False,
            context={"limit": limit, "actual": actual}
        )

    @classmethod
    def provider_error(cls, status_code: int, message: str) -> 'HRMError':
        return cls(
            code=ErrorCode.PROVIDER_ERROR,
            message=message,
            recoverable=status_code >= 500,  # Server errors are retryable
            context={"status_code": status_code}
        )


def recover_from_error(error: HRMError) -> dict:
    """
    Suggest recovery action for an error.

    Returns:
        {"action": "retry" | "fallback" | "escalate" | "abort", "delay_ms": int}
    """
    if not error.recoverable:
        return {"action": "abort", "delay_ms": 0}

    if error.code == ErrorCode.RATE_LIMIT:
        return {"action": "retry", "delay_ms": error.retry_after_ms or 1000}

    if error.code in (ErrorCode.GATE_DENIED, ErrorCode.STANCE_VIOLATION):
        return {"action": "fallback", "delay_ms": 0}

    if error.code == ErrorCode.ESCALATION_REQUIRED:
        return {"action": "escalate", "delay_ms": 0}

    return {"action": "retry", "delay_ms": 1000}
```

---

## 10. Configuration Interface

```python
@dataclass
class HRMConfig:
    """Configuration for all HRM layers."""

    # Altitude
    altitude_default_level: AltitudeLevel = AltitudeLevel.L2_OPERATIONS
    altitude_allow_l4_actions: bool = False

    # Reasoning
    escalation_threshold: float = 0.6  # Per user decision
    pattern_match_threshold: float = 0.7
    max_agents_per_bundle: int = 5

    # Focus
    default_stance: Stance = Stance.SENSEMAKING
    max_commitment_turns: int = 10
    agent_execution_timeout_ms: int = 30000

    # Learning
    pattern_creation_threshold: int = 3  # Successes before pattern
    auto_trim_enabled: bool = False      # Per user decision: NO auto-trim

    # Memory
    working_set_default_ttl_hours: int = 2
    memory_file_locking: bool = True     # Per user decision: YES locking

    # Tracing
    trace_enabled: bool = False
    trace_file: str = "trace.jsonl"
```

---

## 11. LLM Adapter Interface

The LLM Adapter abstracts all language model calls. Every HRM component that needs to generate text uses this interface.

### 11.1 Core Adapter Protocol

```python
from typing import Iterator, Optional, Callable
from abc import ABC, abstractmethod

class ILLMAdapter(Protocol):
    """
    Abstract interface for LLM providers.
    All HRM components use this - never call providers directly.
    """

    def chat(
        self,
        messages: list[Message],
        system: str,
        config: Optional[LLMCallConfig] = None
    ) -> LLMResponse:
        """
        Synchronous chat completion.

        Args:
            messages: Conversation history
            system: System prompt (compiled by PromptCompiler)
            config: Optional override for model/temperature/etc.

        Returns:
            LLMResponse with content and metadata
        """
        ...

    def stream(
        self,
        messages: list[Message],
        system: str,
        config: Optional[LLMCallConfig] = None
    ) -> Iterator[StreamChunk]:
        """
        Streaming chat completion.

        Yields:
            StreamChunk with delta content
        """
        ...

    def count_tokens(
        self,
        text: str
    ) -> int:
        """
        Count tokens for budget management.
        """
        ...

    @property
    def provider(self) -> str:
        """Return provider name (anthropic, openai, etc.)"""
        ...

    @property
    def model(self) -> str:
        """Return current model ID."""
        ...
```

### 11.2 Data Types

```python
@dataclass
class Message:
    """Single message in conversation."""
    role: str                     # user | assistant | system
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = None

@dataclass
class LLMCallConfig:
    """Per-call configuration overrides."""
    model: Optional[str] = None           # Override default model
    temperature: Optional[float] = None   # 0.0 - 1.0
    max_tokens: Optional[int] = None
    stop_sequences: Optional[list[str]] = None
    timeout_ms: Optional[int] = None

    # Cost controls
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None

@dataclass
class LLMResponse:
    """Response from synchronous chat."""
    content: str
    model: str
    provider: str

    # Usage stats
    input_tokens: int
    output_tokens: int
    total_tokens: int

    # Metadata
    finish_reason: str            # stop | length | content_filter
    latency_ms: int
    request_id: Optional[str] = None

    def cost_estimate(self, pricing: dict) -> float:
        """Estimate cost based on token counts."""
        input_cost = self.input_tokens * pricing.get("input_per_1k", 0) / 1000
        output_cost = self.output_tokens * pricing.get("output_per_1k", 0) / 1000
        return input_cost + output_cost

@dataclass
class StreamChunk:
    """Single chunk from streaming response."""
    delta: str                    # New content
    accumulated: str              # All content so far
    done: bool                    # Is this the final chunk?
    finish_reason: Optional[str] = None
```

### 11.3 Provider Implementations

```python
class ClaudeAdapter(ILLMAdapter):
    """Anthropic Claude implementation."""

    def __init__(self, config: LLMConfig):
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self._model = config.model or "claude-sonnet-4-20250514"
        self._default_config = config

    def chat(
        self,
        messages: list[Message],
        system: str,
        config: Optional[LLMCallConfig] = None
    ) -> LLMResponse:
        cfg = self._merge_config(config)

        start = time.time()
        response = self.client.messages.create(
            model=cfg.model or self._model,
            max_tokens=cfg.max_tokens or 4096,
            temperature=cfg.temperature or 0.7,
            system=system,
            messages=[{"role": m.role, "content": m.content} for m in messages]
        )
        latency = int((time.time() - start) * 1000)

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            provider="anthropic",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason,
            latency_ms=latency,
            request_id=response.id
        )

    def stream(
        self,
        messages: list[Message],
        system: str,
        config: Optional[LLMCallConfig] = None
    ) -> Iterator[StreamChunk]:
        cfg = self._merge_config(config)
        accumulated = ""

        with self.client.messages.stream(
            model=cfg.model or self._model,
            max_tokens=cfg.max_tokens or 4096,
            temperature=cfg.temperature or 0.7,
            system=system,
            messages=[{"role": m.role, "content": m.content} for m in messages]
        ) as stream:
            for text in stream.text_stream:
                accumulated += text
                yield StreamChunk(
                    delta=text,
                    accumulated=accumulated,
                    done=False
                )

            yield StreamChunk(
                delta="",
                accumulated=accumulated,
                done=True,
                finish_reason=stream.get_final_message().stop_reason
            )

    def count_tokens(self, text: str) -> int:
        # Use anthropic's token counter
        return self.client.count_tokens(text)

    @property
    def provider(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model


class OpenAIAdapter(ILLMAdapter):
    """OpenAI GPT implementation."""

    def __init__(self, config: LLMConfig):
        self.client = openai.OpenAI(api_key=config.api_key)
        self._model = config.model or "gpt-4o"
        self._default_config = config

    def chat(
        self,
        messages: list[Message],
        system: str,
        config: Optional[LLMCallConfig] = None
    ) -> LLMResponse:
        cfg = self._merge_config(config)

        # OpenAI includes system in messages
        all_messages = [{"role": "system", "content": system}]
        all_messages.extend([{"role": m.role, "content": m.content} for m in messages])

        start = time.time()
        response = self.client.chat.completions.create(
            model=cfg.model or self._model,
            max_tokens=cfg.max_tokens or 4096,
            temperature=cfg.temperature or 0.7,
            messages=all_messages
        )
        latency = int((time.time() - start) * 1000)

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider="openai",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            finish_reason=response.choices[0].finish_reason,
            latency_ms=latency,
            request_id=response.id
        )

    # stream() implementation similar...

    @property
    def provider(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model
```

### 11.4 LLM Configuration

```python
@dataclass
class LLMConfig:
    """Global LLM configuration."""

    # Provider selection
    provider: str = "anthropic"           # anthropic | openai
    api_key: Optional[str] = None         # Or use env var
    api_key_env: str = "ANTHROPIC_API_KEY"  # Fallback to env

    # Model defaults
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096

    # Rate limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000

    # Retry policy
    max_retries: int = 3
    retry_delay_ms: int = 1000
    retry_on: list[str] = field(default_factory=lambda: [
        "rate_limit",
        "timeout",
        "server_error"
    ])

    # Cost tracking
    track_costs: bool = True
    cost_alert_threshold: float = 10.0    # Alert if session exceeds $

    @classmethod
    def from_yaml(cls, path: str) -> 'LLMConfig':
        """Load from YAML config file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Load from environment variables."""
        return cls(
            provider=os.getenv("LLM_PROVIDER", "anthropic"),
            api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-20250514"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
        )
```

### 11.5 Adapter Factory

```python
class LLMAdapterFactory:
    """Creates appropriate adapter based on config."""

    _adapters: dict[str, type] = {
        "anthropic": ClaudeAdapter,
        "openai": OpenAIAdapter,
    }

    @classmethod
    def create(cls, config: LLMConfig) -> ILLMAdapter:
        """
        Create adapter for configured provider.

        Usage:
            config = LLMConfig.from_env()
            llm = LLMAdapterFactory.create(config)
            response = llm.chat(messages, system_prompt)
        """
        adapter_class = cls._adapters.get(config.provider)
        if not adapter_class:
            raise ValueError(f"Unknown provider: {config.provider}")

        return adapter_class(config)

    @classmethod
    def register(cls, provider: str, adapter_class: type) -> None:
        """Register custom adapter."""
        cls._adapters[provider] = adapter_class
```

### 11.6 Usage in HRM Components

```python
# Example: How Reasoning HRM uses the adapter

class ReasoningRouter:
    def __init__(
        self,
        llm: ILLMAdapter,          # Injected dependency
        classifier: InputClassifier,
        ...
    ):
        self.llm = llm
        self.classifier = classifier

    def _classify_with_llm(self, input: TurnInput) -> InputClassification:
        """Use LLM for complex classification."""
        response = self.llm.chat(
            messages=[Message(role="user", content=input.text)],
            system=CLASSIFICATION_PROMPT,
            config=LLMCallConfig(
                temperature=0.3,      # Low temp for classification
                max_tokens=500        # Short response needed
            )
        )
        return self._parse_classification(response.content)


# Example: How agents use the adapter

class WritingAgent:
    def __init__(self, llm: ILLMAdapter):
        self.llm = llm

    def generate(self, prompt: str, context: AgentContext) -> str:
        """Generate content using LLM."""
        for chunk in self.llm.stream(
            messages=[Message(role="user", content=prompt)],
            system=self._build_system_prompt(context),
            config=LLMCallConfig(
                temperature=0.8,      # Higher temp for creativity
                max_tokens=2000
            )
        ):
            yield chunk.delta        # Stream to UI

        return chunk.accumulated     # Return full response
```

### 11.7 Error Handling

```python
class LLMError(HRMError):
    """Base class for LLM errors."""
    pass

class RateLimitError(LLMError):
    """Rate limit exceeded."""
    def __init__(self, retry_after_ms: int):
        self.retry_after_ms = retry_after_ms

class TokenLimitError(LLMError):
    """Input or output exceeded token limit."""
    def __init__(self, limit: int, actual: int):
        self.limit = limit
        self.actual = actual

class ContentFilterError(LLMError):
    """Content blocked by safety filter."""
    pass

class ProviderError(LLMError):
    """Provider-side error (5xx, etc.)"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
```

### 11.8 Configuration File Example

```yaml
# config/llm.yaml
provider: anthropic
model: claude-sonnet-4-20250514
temperature: 0.7
max_tokens: 4096

# Rate limiting
requests_per_minute: 60
tokens_per_minute: 100000

# Retry policy
max_retries: 3
retry_delay_ms: 1000
retry_on:
  - rate_limit
  - timeout
  - server_error

# Cost tracking
track_costs: true
cost_alert_threshold: 10.0
```

---

## 12. Governance Kernel

The GovernanceKernel consolidates all policy decisions into a single module. This prevents "configuration sprawl" and ensures tunables are versioned together.

**Location:** `shared/governance/kernel.py`

### 12.1 PolicySurface (Canonical Tunables)

```python
from dataclasses import dataclass, field
from typing import Tuple

@dataclass(frozen=True)
class PolicySurface:
    """
    Single source of truth for all system tunables.
    Intentionally minimal. Version this file carefully.
    """

    # === ARBITRATION ===
    PRIORITY_SCALE: Tuple[int, int] = (1, 10)
    AUTO_PREEMPT_THRESHOLD: float = 0.70
    ASK_BAND_LOW: float = 0.55
    ASK_BAND_HIGH: float = 0.70
    # < 0.55 → queue (no user interrupt)
    # 0.55-0.70 → ask user
    # >= 0.70 → auto preempt

    # PreemptScore weights (must sum to 1.0)
    WEIGHT_PRIORITY: float = 0.30
    WEIGHT_URGENCY: float = 0.25
    WEIGHT_STALENESS: float = 0.20
    WEIGHT_SWITCH_COST: float = 0.25

    # === SIGNAL DERIVATION ===
    CONFLICT_CONFIDENCE_GAP: float = 0.3   # Below this = true ambiguity → HIGH conflict
    BLAST_RADIUS_FILE_THRESHOLD: int = 3   # >3 files = MODERATE

    # LLM signal bounds
    LLM_SIGNAL_FLOOR: float = 0.1
    LLM_SIGNAL_CEILING: float = 0.9
    LLM_SIGNAL_WEIGHT: float = 0.6         # Deterministic gets 0.4

    # === ESCALATION ===
    ESCALATION_THRESHOLD: float = 0.6

    # === PREFERENCE TRUTH ===
    PREFERENCE_PATTERNS: Tuple[str, ...] = (
        r"I prefer",
        r"I hate",
        r"I always",
        r"I never",
        r"I'm the kind of person who",
        r"I like",
        r"I don't like",
        r"I need",
    )

    # === STANCE DEFAULTS (DoPeJar Mode) ===
    NEW_SESSION_STANCE: str = "sensemaking"
    SENSEMAKING_MAX_TURNS: int = 2         # Then transition to execution
    MID_COMMITMENT_STANCE: str = "execution"
    POST_DELIVERY_STANCE: str = "evaluation"
    EVALUATION_MAX_TURNS: int = 1

    # === INTERRUPT BUDGET ===
    # When to surface to user (everything else: handle silently)
    INTERRUPT_CONDITIONS: Tuple[str, ...] = (
        "ask_band",                         # Arbitration ambiguity
        "preference_conflict",              # Action conflicts with canon
        "high_stakes_irreversible",         # SEVERE blast_radius + irreversible
        "you_should_know",                  # Important info, no action needed
    )

    # === RUNTIME ===
    MAX_CONCURRENT_AGENTS: int = 3         # Semaphore for async (even in sync mode)
    AGENT_TIMEOUT_MS: int = 30000

    # === VERSION ===
    VERSION: str = "1.0.0"

    def validate(self) -> bool:
        """Ensure weights sum to 1.0 and thresholds are sane."""
        weights = (
            self.WEIGHT_PRIORITY +
            self.WEIGHT_URGENCY +
            self.WEIGHT_STALENESS +
            self.WEIGHT_SWITCH_COST
        )
        assert abs(weights - 1.0) < 0.01, f"Weights sum to {weights}, must be 1.0"
        assert self.ASK_BAND_LOW < self.ASK_BAND_HIGH < self.AUTO_PREEMPT_THRESHOLD
        assert 0 < self.ESCALATION_THRESHOLD < 1
        return True


# Global singleton
POLICY = PolicySurface()
POLICY.validate()
```

### 12.2 SignalEngine (Deterministic + Bounded LLM)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

class BlastRadius(Enum):
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SEVERE = "severe"

class ConflictLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class DerivedSignals:
    """All signals derived from a single turn/action."""
    conflict_level: ConflictLevel
    blast_radius: BlastRadius
    source_quality: float          # 0.0 - 1.0
    alignment_score: float         # 0.0 - 1.0
    urgency: float                 # 0.0 - 1.0

    # Derivation metadata
    deterministic_components: dict
    llm_adjustments: dict


class SignalEngine:
    """
    Derives all signals for WriteGate and Arbitration.

    Principle: Deterministic signals are authoritative.
    LLM-assisted signals are advisory and bounded.
    """

    def __init__(self, policy: PolicySurface, llm: Optional['ILLMAdapter'] = None):
        self.policy = policy
        self.llm = llm

    def derive(
        self,
        turn_input: 'TurnInput',
        context: 'HRMContext',
        artifacts: List[str],
        agent_outputs: Optional[List['AgentOutput']] = None
    ) -> DerivedSignals:
        """
        Derive all signals for this turn.

        Order of operations:
        1. Compute deterministic signals (authoritative)
        2. Compute LLM-assisted signals (bounded by deterministic constraints)
        3. Return combined DerivedSignals
        """
        det = self._deterministic(turn_input, context, artifacts, agent_outputs)
        llm_adj = self._llm_assisted(turn_input, context) if self.llm else {}

        return DerivedSignals(
            conflict_level=det["conflict_level"],
            blast_radius=det["blast_radius"],
            source_quality=self._bounded_signal(
                det["source_quality_floor"],
                llm_adj.get("source_quality", 0.5)
            ),
            alignment_score=self._bounded_signal(
                det["alignment_floor"],
                llm_adj.get("alignment_score", 0.5)
            ),
            urgency=det["urgency"],
            deterministic_components=det,
            llm_adjustments=llm_adj
        )

    # ─────────────────────────────────────────────────────────────
    # DETERMINISTIC SIGNALS (authoritative)
    # ─────────────────────────────────────────────────────────────

    def _deterministic(
        self,
        turn_input: 'TurnInput',
        context: 'HRMContext',
        artifacts: List[str],
        agent_outputs: Optional[List['AgentOutput']]
    ) -> dict:
        return {
            "conflict_level": self._compute_conflict_level(agent_outputs, context),
            "blast_radius": self._compute_blast_radius(artifacts),
            "source_quality_floor": self._compute_source_quality_floor(turn_input),
            "alignment_floor": self._compute_alignment_floor(context),
            "urgency": self._compute_urgency(turn_input),
        }

    def _compute_blast_radius(self, artifacts: List[str]) -> BlastRadius:
        """
        SEVERE if:
        - Target is SharedReference or SemanticSynthesis

        MODERATE if:
        - Touches >3 artifacts/files
        - Crosses problem boundary

        Else MINIMAL
        """
        severe_targets = {"SharedReference", "SemanticSynthesis", "shared_reference", "semantic_synthesis"}

        for artifact in artifacts:
            if any(t in artifact for t in severe_targets):
                return BlastRadius.SEVERE

        if len(artifacts) > self.policy.BLAST_RADIUS_FILE_THRESHOLD:
            return BlastRadius.MODERATE

        return BlastRadius.MINIMAL

    def _compute_conflict_level(
        self,
        agent_outputs: Optional[List['AgentOutput']],
        context: 'HRMContext'
    ) -> ConflictLevel:
        """
        HIGH if:
        - Two agent outputs disagree AND confidence gap <= 0.3 (true ambiguity)
        - New claim contradicts SharedReference with high confidence

        MEDIUM if:
        - Minor contradictions or missing evidence

        LOW/NONE otherwise

        Key: confidence gap <= 0.3 means true ambiguity.
        If one source is clearly stronger, treat as low conflict.
        """
        if not agent_outputs or len(agent_outputs) < 2:
            return ConflictLevel.NONE

        # Check for agent disagreement
        confidences = [getattr(o, 'confidence', 0.5) for o in agent_outputs]
        if len(set(o.content for o in agent_outputs)) > 1:  # Different outputs
            gap = max(confidences) - min(confidences)
            if gap <= self.policy.CONFLICT_CONFIDENCE_GAP:
                return ConflictLevel.HIGH  # True ambiguity
            else:
                return ConflictLevel.LOW   # One clearly stronger

        # TODO: Check SharedReference contradictions
        return ConflictLevel.NONE

    def _compute_source_quality_floor(self, turn_input: 'TurnInput') -> float:
        """
        Deterministic floor for source quality.
        Based on: citation presence, recency, user confirmation.

        Returns floor value (LLM can raise but not lower).
        """
        floor = 0.3  # Base

        # User direct input gets higher floor
        if turn_input.source == "user":
            floor += 0.2

        # TODO: Add citation counting, recency scoring
        return min(floor, 0.6)  # Cap deterministic at 0.6

    def _compute_alignment_floor(self, context: 'HRMContext') -> float:
        """
        Deterministic floor for alignment score.

        1.0 if matches active commitment
        0.5 if same problem
        0.2 otherwise
        """
        if context.commitment_id:
            return 1.0
        if context.problem_id:
            return 0.5
        return 0.2

    def _compute_urgency(self, turn_input: 'TurnInput') -> float:
        """
        Deterministic urgency from input signals.
        """
        urgency = 0.3  # Base

        # Priority boost
        if hasattr(turn_input, 'priority'):
            urgency += turn_input.priority * 0.05

        # TODO: Keyword detection for urgency markers
        return min(urgency, 1.0)

    # ─────────────────────────────────────────────────────────────
    # LLM-ASSISTED SIGNALS (bounded by deterministic)
    # ─────────────────────────────────────────────────────────────

    def _llm_assisted(self, turn_input: 'TurnInput', context: 'HRMContext') -> dict:
        """
        Get LLM estimates for judgment-call signals.
        These are BOUNDED by deterministic floors/ceilings.
        """
        if not self.llm:
            return {}

        # Simple prompt for signal estimation
        prompt = f"""Rate the following on 0.0-1.0 scale:
        Input: {turn_input.text[:500]}

        source_quality: How well-grounded/cited is this information?
        alignment_score: How relevant is this to the user's stated goals?

        Return JSON: {{"source_quality": X, "alignment_score": Y}}"""

        try:
            response = self.llm.chat(
                messages=[Message(role="user", content=prompt)],
                system="You are a signal estimation engine. Return only JSON.",
                config=LLMCallConfig(temperature=0.1, max_tokens=100)
            )
            return json.loads(response.content)
        except:
            return {}

    def _bounded_signal(self, deterministic_floor: float, llm_estimate: float) -> float:
        """
        Combine deterministic floor with bounded LLM estimate.

        Formula: floor + (ceiling - floor) * llm_weight * llm_estimate
        Always clamped to [0, 1]
        """
        p = self.policy
        ceiling = p.LLM_SIGNAL_CEILING
        floor = max(deterministic_floor, p.LLM_SIGNAL_FLOOR)

        # Weighted combination
        det_weight = 1 - p.LLM_SIGNAL_WEIGHT
        llm_weight = p.LLM_SIGNAL_WEIGHT

        combined = (det_weight * floor) + (llm_weight * llm_estimate)
        return max(floor, min(ceiling, combined))
```

### 12.3 PreemptScoreArbiter

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ArbitrationDisposition(Enum):
    STAY = "stay"           # Continue active problem
    SWITCH = "switch"       # Auto-switch to new problem
    ASK = "ask"             # Ask user (D tie-breaker)
    QUEUE = "queue"         # Queue new problem, don't interrupt

@dataclass
class ArbitrationDecision:
    """Output of the arbiter."""
    active_problem_id: str
    disposition: ArbitrationDisposition
    preempt_score: float
    reason: str
    candidate_problem_id: Optional[str] = None


class PreemptScoreArbiter:
    """
    Implements arbitration policy C (Priority + TTL) with D (ask user) as tie-breaker.

    Uses 4 terms (cleaner than 5):
    - priority_term: normalized priority delta
    - urgency: from SignalEngine
    - staleness: time since active problem progressed
    - switch_cost: context switch penalty (includes finish_penalty)
    """

    def __init__(self, policy: PolicySurface):
        self.policy = policy

    def decide(
        self,
        turn_input: 'TurnInput',
        focus_state: 'FocusState',
        problem_registry: 'ProblemRegistry',
        signals: 'DerivedSignals'
    ) -> ArbitrationDecision:
        """
        Main arbitration entry point.

        Returns ArbitrationDecision with disposition and reason.
        """
        active = problem_registry.get_active()
        candidate = self._identify_candidate(turn_input, problem_registry)

        # No active problem → just switch
        if not active:
            return ArbitrationDecision(
                active_problem_id=candidate.id if candidate else None,
                disposition=ArbitrationDisposition.SWITCH,
                preempt_score=1.0,
                reason="No active problem"
            )

        # Same problem → stay
        if candidate and candidate.id == active.id:
            return ArbitrationDecision(
                active_problem_id=active.id,
                disposition=ArbitrationDisposition.STAY,
                preempt_score=0.0,
                reason="Input relates to active problem"
            )

        # Check emergency gate first
        if self._is_emergency(turn_input, focus_state):
            return ArbitrationDecision(
                active_problem_id=candidate.id if candidate else active.id,
                disposition=ArbitrationDisposition.SWITCH,
                preempt_score=1.0,
                reason="Emergency gate triggered",
                candidate_problem_id=candidate.id if candidate else None
            )

        # Compute PreemptScore
        score = self._compute_preempt_score(
            candidate=candidate,
            active=active,
            signals=signals,
            focus_state=focus_state
        )

        # Apply thresholds
        p = self.policy
        if score >= p.AUTO_PREEMPT_THRESHOLD:
            disposition = ArbitrationDisposition.SWITCH
            reason = f"Auto-preempt: score {score:.2f} >= {p.AUTO_PREEMPT_THRESHOLD}"
        elif score >= p.ASK_BAND_LOW:
            disposition = ArbitrationDisposition.ASK
            reason = f"Ask user: score {score:.2f} in ask-band [{p.ASK_BAND_LOW}, {p.ASK_BAND_HIGH})"
        else:
            disposition = ArbitrationDisposition.QUEUE
            reason = f"Queue: score {score:.2f} < {p.ASK_BAND_LOW}"

        return ArbitrationDecision(
            active_problem_id=active.id,
            disposition=disposition,
            preempt_score=score,
            reason=reason,
            candidate_problem_id=candidate.id if candidate else None
        )

    def _compute_preempt_score(
        self,
        candidate: Optional['Problem'],
        active: 'Problem',
        signals: 'DerivedSignals',
        focus_state: 'FocusState'
    ) -> float:
        """
        PreemptScore formula (4 terms, weights sum to 1.0):

        score = W_priority * priority_term
              + W_urgency * urgency
              + W_staleness * staleness
              + W_switch_cost * (1 - switch_cost)

        Returns: float in [0, 1]
        """
        p = self.policy

        # 1. Priority term: normalize delta to [0, 1]
        p_new = (candidate.priority if candidate else 5) / p.PRIORITY_SCALE[1]
        p_active = active.priority / p.PRIORITY_SCALE[1]
        p_delta = (p_new - p_active + 1) / 2  # Map [-1,1] to [0,1]

        # 2. Urgency: from signals
        urgency = signals.urgency

        # 3. Staleness: time since progress (normalized)
        staleness = self._compute_staleness(active)

        # 4. Switch cost: includes commitment remaining penalty
        switch_cost = self._compute_switch_cost(focus_state)

        # Weighted sum
        score = (
            p.WEIGHT_PRIORITY * p_delta +
            p.WEIGHT_URGENCY * urgency +
            p.WEIGHT_STALENESS * staleness +
            p.WEIGHT_SWITCH_COST * (1 - switch_cost)  # Invert: high cost = low score
        )

        return max(0.0, min(1.0, score))

    def _compute_staleness(self, active: 'Problem') -> float:
        """
        How long since active problem progressed.
        Normalized to [0, 1] over reasonable range.
        """
        if not hasattr(active, 'last_progress_at'):
            return 0.5

        elapsed = (datetime.now() - active.last_progress_at).total_seconds()
        # Normalize: 0 at 0 min, 1 at 30 min
        return min(1.0, elapsed / (30 * 60))

    def _compute_switch_cost(self, focus_state: 'FocusState') -> float:
        """
        Context switch penalty.
        Includes: commitment remaining (don't drop work at finish line)
        """
        cost = 0.3  # Base switch cost

        # Commitment remaining penalty
        if focus_state.commitment:
            remaining_ratio = (
                focus_state.commitment.turns_remaining /
                focus_state.commitment.turns_total
            )
            # High penalty when near completion (low remaining)
            finish_penalty = 1 - remaining_ratio
            cost += 0.4 * finish_penalty

        return min(1.0, cost)

    def _is_emergency(self, turn_input: 'TurnInput', focus_state: 'FocusState') -> bool:
        """Check if emergency gate conditions are met."""
        # TODO: Implement emergency detection
        return False

    def _identify_candidate(
        self,
        turn_input: 'TurnInput',
        problem_registry: 'ProblemRegistry'
    ) -> Optional['Problem']:
        """Identify which problem the input relates to."""
        # TODO: Implement problem identification logic
        return None
```

### 12.4 PreferenceClassifier

```python
import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class PreferenceClass(Enum):
    """
    Preference classification for write-time enforcement.

    EXPLICIT: User stated it clearly → can promote to SharedReference
    INFERRED_CONFIRM_REQUIRED: Pattern detected → needs user YES
    INFERRED_SILENT: Observation only → WorkingSet only
    BEHAVIORAL: Usage pattern → Episodic only, never promotes
    """
    EXPLICIT = "pref_explicit"
    INFERRED_CONFIRM_REQUIRED = "pref_inferred_confirm_required"
    INFERRED_SILENT = "pref_inferred_silent"
    BEHAVIORAL = "pref_behavioral"


@dataclass
class PreferenceClassification:
    """Result of preference classification."""
    preference_class: PreferenceClass
    statement: str
    matched_pattern: Optional[str]
    confidence: float
    can_canonize: bool              # Can write to SharedReference?
    needs_confirmation: bool        # Must ask user first?


class PreferenceClassifier:
    """
    Classifies statements for preference truth model.

    One-shot canonization rule:
    - Tier 1 (auto-canon): Clear preferences stated in context
    - Tier 2 (confirm required): Inferred patterns
    - Tier 3 (silent): Observations only
    - Tier 4 (behavioral): Usage patterns, never promotes

    Canonize immediately if statement matches preference/identity pattern:
    - "I prefer...", "I hate...", "I always...", "I never..."
    - "I'm the kind of person who..."
    - AND the object is a stable preference/habit (not one-off observation)
    """

    def __init__(self, policy: PolicySurface):
        self.policy = policy
        self._patterns = [re.compile(p, re.IGNORECASE) for p in policy.PREFERENCE_PATTERNS]

    def classify(self, statement: str, source: str = "user") -> PreferenceClassification:
        """
        Classify a statement for preference handling.

        Args:
            statement: The text to classify
            source: Who said it (user, agent, system)

        Returns:
            PreferenceClassification with class and permissions
        """
        # Check for explicit preference patterns
        matched_pattern = self._match_preference_pattern(statement)

        if matched_pattern and source == "user":
            # User explicitly stated a preference → Tier 1
            return PreferenceClassification(
                preference_class=PreferenceClass.EXPLICIT,
                statement=statement,
                matched_pattern=matched_pattern,
                confidence=0.9,
                can_canonize=True,
                needs_confirmation=False
            )

        if self._is_behavioral_observation(statement):
            # Usage pattern observation → Tier 4 (behavioral)
            return PreferenceClassification(
                preference_class=PreferenceClass.BEHAVIORAL,
                statement=statement,
                matched_pattern=None,
                confidence=0.7,
                can_canonize=False,
                needs_confirmation=False
            )

        if self._looks_like_preference(statement):
            # Might be a preference but not explicitly stated → Tier 2
            return PreferenceClassification(
                preference_class=PreferenceClass.INFERRED_CONFIRM_REQUIRED,
                statement=statement,
                matched_pattern=None,
                confidence=0.5,
                can_canonize=True,  # Can canonize IF user confirms
                needs_confirmation=True
            )

        # Default: silent observation → Tier 3
        return PreferenceClassification(
            preference_class=PreferenceClass.INFERRED_SILENT,
            statement=statement,
            matched_pattern=None,
            confidence=0.3,
            can_canonize=False,
            needs_confirmation=False
        )

    def _match_preference_pattern(self, statement: str) -> Optional[str]:
        """Check if statement matches explicit preference patterns."""
        for pattern in self._patterns:
            if pattern.search(statement):
                return pattern.pattern
        return None

    def _is_behavioral_observation(self, statement: str) -> bool:
        """Check if this is a behavioral observation (not a stated preference)."""
        behavioral_markers = [
            r"user (often|usually|tends to)",
            r"(noticed|observed) that",
            r"based on (history|past|patterns)",
            r"statistically",
        ]
        for marker in behavioral_markers:
            if re.search(marker, statement, re.IGNORECASE):
                return True
        return False

    def _looks_like_preference(self, statement: str) -> bool:
        """Heuristic: does this look like it might be a preference?"""
        preference_indicators = [
            r"(like|prefer|enjoy|want|need)",
            r"(don't like|hate|avoid|dislike)",
            r"(better|worse|rather)",
        ]
        for indicator in preference_indicators:
            if re.search(indicator, statement, re.IGNORECASE):
                return True
        return False
```

### 12.5 GovernanceKernel (Unified Interface)

```python
@dataclass
class GovernanceKernel:
    """
    Single interface that ties all governance decisions together.

    Usage:
        kernel = GovernanceKernel.create()
        signals = kernel.derive_signals(turn_input, context, artifacts)
        decision = kernel.arbitrate(turn_input, focus_state, problem_registry)
        pref_class = kernel.classify_preference(statement)
    """
    policy: PolicySurface
    signal_engine: SignalEngine
    arbiter: PreemptScoreArbiter
    preference_classifier: PreferenceClassifier

    @classmethod
    def create(cls, llm: Optional['ILLMAdapter'] = None) -> 'GovernanceKernel':
        """Factory method with default policy."""
        policy = PolicySurface()
        policy.validate()

        return cls(
            policy=policy,
            signal_engine=SignalEngine(policy, llm),
            arbiter=PreemptScoreArbiter(policy),
            preference_classifier=PreferenceClassifier(policy)
        )

    def arbitrate(
        self,
        turn_input: 'TurnInput',
        focus_state: 'FocusState',
        problem_registry: 'ProblemRegistry'
    ) -> ArbitrationDecision:
        """
        Main arbitration entry point.

        Derives signals, then decides: stay | switch | ask | queue
        """
        signals = self.signal_engine.derive(
            turn_input=turn_input,
            context=focus_state.context,
            artifacts=[],
            agent_outputs=None
        )

        return self.arbiter.decide(
            turn_input=turn_input,
            focus_state=focus_state,
            problem_registry=problem_registry,
            signals=signals
        )

    def derive_signals(
        self,
        turn_input: 'TurnInput',
        context: 'HRMContext',
        artifacts: list,
        agent_outputs: list = None
    ) -> DerivedSignals:
        """
        Derive all signals for WriteGate and other consumers.
        """
        return self.signal_engine.derive(
            turn_input=turn_input,
            context=context,
            artifacts=artifacts,
            agent_outputs=agent_outputs
        )

    def classify_preference(self, statement: str, source: str = "user") -> PreferenceClassification:
        """
        Classify a statement for preference truth model.
        """
        return self.preference_classifier.classify(statement, source)

    def check_interrupt_condition(self, condition: str) -> bool:
        """
        Check if a condition warrants user interrupt.
        """
        return condition in self.policy.INTERRUPT_CONDITIONS
```

### 12.6 Integration with WriteGate

```python
# Update to WriteGate to use GovernanceKernel

class WriteGate:
    """
    Updated WriteGate that uses GovernanceKernel for signals and preference handling.
    """

    def __init__(self, kernel: GovernanceKernel):
        self.kernel = kernel

    def evaluate(self, request: WriteRequest) -> WriteDecision:
        """
        Evaluate write request using kernel-derived signals.
        """
        signals = request.signals  # Already derived by kernel

        # Check preference class if this is a preference write
        if request.is_preference:
            pref_class = self.kernel.classify_preference(
                str(request.value),
                source=request.source
            )

            # Enforce preference truth model
            if pref_class.preference_class == PreferenceClass.BEHAVIORAL:
                return WriteDecision(
                    approved=True,
                    target="episodic_trace",  # Behavioral → Episodic only
                    reason="Behavioral observation: Episodic only"
                )

            if pref_class.preference_class == PreferenceClass.INFERRED_SILENT:
                return WriteDecision(
                    approved=True,
                    target="working_set",  # Silent → WorkingSet only
                    reason="Inferred silent: WorkingSet only"
                )

            if pref_class.needs_confirmation:
                return WriteDecision(
                    approved=False,
                    target=request.target,
                    reason="Preference requires user confirmation",
                    conditions=["needs_user_confirmation"]
                )

        # Standard WriteGate rules using signals
        if signals.blast_radius == BlastRadius.SEVERE:
            if signals.source_quality < 0.7:
                return WriteDecision(
                    approved=False,
                    target=request.target,
                    reason="SEVERE blast radius requires high source quality"
                )

        if signals.conflict_level == ConflictLevel.HIGH:
            return WriteDecision(
                approved=True,
                target="working_set",  # Conflict → WorkingSet only
                reason="HIGH conflict: redirected to WorkingSet"
            )

        return WriteDecision(
            approved=True,
            target=request.target,
            reason="Write approved"
        )
```

### 12.7 Integration with Focus HRM

```python
# Focus HRM calls kernel for arbitration

class FocusHRM:
    def __init__(self, kernel: GovernanceKernel, ...):
        self.kernel = kernel
        ...

    def process_turn(self, turn_input: TurnInput) -> FocusResult:
        """
        Main turn processing with kernel arbitration.
        """
        # Step 1: Arbitrate (which problem?)
        arbitration = self.kernel.arbitrate(
            turn_input=turn_input,
            focus_state=self._get_focus_state(),
            problem_registry=self.problem_registry
        )

        # Step 2: Handle disposition
        if arbitration.disposition == ArbitrationDisposition.ASK:
            # Surface to user (D tie-breaker)
            return FocusResult(
                action="ask_user",
                message=f"Interrupt current work? (score: {arbitration.preempt_score:.2f})",
                arbitration=arbitration
            )

        if arbitration.disposition == ArbitrationDisposition.SWITCH:
            self._switch_to_problem(arbitration.candidate_problem_id)

        if arbitration.disposition == ArbitrationDisposition.QUEUE:
            self._queue_problem(arbitration.candidate_problem_id)

        # Step 3: Continue with active problem
        return self._execute_turn(turn_input)
```

---

## Appendix: Implementation Checklist

For each interface, implementation must:

- [ ] Implement all methods defined in the Protocol
- [ ] Raise appropriate exceptions on error
- [ ] Emit trace events for key operations
- [ ] Log to EpisodicTrace for audit
- [ ] Respect WriteGate for any memory writes
- [ ] Check gate approval before state changes
- [ ] Update HRMContext appropriately
- [ ] Handle timeouts for async operations
