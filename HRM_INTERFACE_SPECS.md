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

class OrchestrationMode(Enum):
    PIPELINE = "pipeline"         # Serial execution
    PARALLEL = "parallel"         # Async with aggregation
    VOTING = "voting"             # Consensus with threshold
    HIERARCHICAL = "hierarchical" # Lead + delegates

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

### 2.1 AltitudeGovernor

```python
class IAltitudeGovernor(Protocol):
    """Main interface for Altitude HRM."""

    def classify_input(
        self,
        input: TurnInput
    ) -> AltitudeClassification:
        """
        Determine the altitude level for this input.

        Returns:
            AltitudeClassification with level and confidence
        """
        ...

    def validate_action(
        self,
        action: dict,
        current_level: AltitudeLevel
    ) -> ValidationResult:
        """
        Check if an action is appropriate for current altitude.

        Returns:
            ValidationResult with allowed/denied and reason
        """
        ...

    def transition(
        self,
        to_level: AltitudeLevel,
        reason: str
    ) -> TransitionResult:
        """
        Attempt to change altitude level.

        Returns:
            TransitionResult with success/failure and new state
        """
        ...

@dataclass
class AltitudeClassification:
    level: AltitudeLevel
    confidence: float           # 0.0 - 1.0
    signals: list[str]          # What triggered this classification
    suggested_stance: Optional[Stance]
    allows_agents: bool

@dataclass
class ValidationResult:
    allowed: bool
    reason: str
    suggested_level: Optional[AltitudeLevel]

@dataclass
class TransitionResult:
    success: bool
    from_level: AltitudeLevel
    to_level: AltitudeLevel
    reason: str
```

### 2.2 Altitude Planner

```python
class IAltitudePlanner(Protocol):
    """Planning layer within Altitude HRM."""

    def generate_plan(
        self,
        input: TurnInput,
        classification: AltitudeClassification
    ) -> Plan:
        """
        Generate a plan appropriate for current altitude.
        """
        ...

    def validate_plan(
        self,
        plan: Plan,
        stance: Stance
    ) -> PlanValidation:
        """
        Check if plan is allowed by current stance.
        """
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

@dataclass
class PlanValidation:
    valid: bool
    violations: list[str]
    suggested_modifications: list[dict]
```

### 2.3 Altitude Evaluator

```python
class IAltitudeEvaluator(Protocol):
    """Evaluation layer within Altitude HRM."""

    def evaluate_result(
        self,
        result: ExecutionResult,
        plan: Plan
    ) -> Evaluation:
        """
        Assess execution result against plan.
        """
        ...

    def should_transition(
        self,
        evaluation: Evaluation,
        current_level: AltitudeLevel
    ) -> Optional[AltitudeLevel]:
        """
        Determine if altitude should change based on evaluation.
        """
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
class IAltitudeExecutor(Protocol):
    """Execution layer within Altitude HRM."""

    def execute(
        self,
        plan: Plan,
        context: HRMContext
    ) -> ExecutionResult:
        """
        Execute a plan. All writes go through Focus HRM gates.
        """
        ...

    def request_write_approval(
        self,
        write_request: WriteRequest
    ) -> WriteDecision:
        """
        Request approval from Focus HRM for a write operation.
        """
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

### 3.1 ReasoningRouter

```python
class IReasoningRouter(Protocol):
    """Main interface for Reasoning HRM."""

    def route(
        self,
        input: TurnInput
    ) -> RoutingDecision:
        """
        Determine how to handle this input.

        Returns:
            RoutingDecision with strategy and optional agent proposal
        """
        ...

    def propose_agents(
        self,
        input: TurnInput
    ) -> Optional[AgentBundleProposal]:
        """
        If agents are needed, propose which ones and how.

        Returns:
            AgentBundleProposal or None if no agents needed
        """
        ...

    def query_patterns(
        self,
        input_signature: dict
    ) -> list[PatternMatch]:
        """
        Query Learning HRM for matching patterns.
        """
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
class IInputClassifier(Protocol):
    """Classifies input for strategy selection."""

    def classify(
        self,
        input: TurnInput
    ) -> InputClassification:
        """
        Analyze input across multiple dimensions.
        """
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
class IStrategySelector(Protocol):
    """Selects reasoning strategy based on classification."""

    def select(
        self,
        classification: InputClassification,
        pattern_matches: list[PatternMatch]
    ) -> StrategySelection:
        """
        Choose the best strategy for this input.
        """
        ...

@dataclass
class StrategySelection:
    strategy: str
    confidence: float
    reason: str
    requires_agents: bool
    suggested_mode: Optional[OrchestrationMode]
    fallback_strategy: Optional[str]
```

### 3.4 EscalationManager

```python
class IEscalationManager(Protocol):
    """Manages escalation and de-escalation."""

    ESCALATION_THRESHOLD: float = 0.6  # Per user decision

    def should_escalate(
        self,
        classification: InputClassification,
        strategy: StrategySelection
    ) -> bool:
        """
        Returns True if escalation needed.
        """
        ...

    def escalate(
        self,
        strategy: StrategySelection
    ) -> StrategySelection:
        """
        Return escalated strategy.
        """
        ...

    def should_deescalate(
        self,
        strategy: StrategySelection,
        pattern_confidence: float
    ) -> bool:
        """
        Returns True if de-escalation appropriate.
        """
        ...

    def deescalate(
        self,
        strategy: StrategySelection
    ) -> StrategySelection:
        """
        Return de-escalated strategy.
        """
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
    orchestration_mode: OrchestrationMode

    # Mode-specific config
    mode_config: dict
    # Pipeline:     {"sequence": ["a", "b", "c"]}
    # Parallel:     {"aggregation": "merge" | "select_best", "timeout_ms": 5000}
    # Voting:       {"threshold": 0.6, "tiebreaker": "first" | "abstain" | "escalate"}
    # Hierarchical: {"lead": "agent_a", "delegates": ["b", "c"], "max_depth": 2}

    # Rationale
    reason: str
    confidence: float
    fallback: Optional[str]       # Alternative if denied
```

### 3.6 ActionSelector (Next Best Action)

```python
class IActionSelector(Protocol):
    """
    Final stage of Reasoning HRM.

    Selects exactly ONE primary action (or micro-batch of 2-3 max) from
    candidates. This is NOT a separate layer - it's the final output of
    Reasoning before Focus HRM governs.

    Key principle: Focus HRM should govern the chosen action, not a bag
    of possibilities. ActionSelector ensures Reasoning emits a single,
    prioritized proposal.
    """

    def select(
        self,
        candidates: list[CandidateAction],
        context: HRMContext
    ) -> SelectedAction:
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

    def should_use_voting(
        self,
        candidates: list[CandidateAction],
        context: HRMContext
    ) -> bool:
        """
        Determine if voting mode is warranted.

        Voting is ONLY used when:
        1. High stakes (Stakes.HIGH) AND
        2. Multiple candidates with similar priority scores (within 0.1) AND
        3. Irreversible consequences

        This prevents voting from becoming a default "committee" pattern.
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
        classifier: IInputClassifier,
        strategy_selector: IStrategySelector,
        escalation_manager: IEscalationManager,
        action_selector: IActionSelector,      # NEW: Final selection stage
        learning_hrm: Optional[LearningHRM] = None
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

### 4.1 StanceMachine

```python
class IStanceMachine(Protocol):
    """4-state exclusive stance machine."""

    def get_current(self) -> Stance:
        """Return current stance."""
        ...

    def transition(
        self,
        to_stance: Stance,
        reason: str,
        via_gate: GateType
    ) -> StanceTransition:
        """
        Attempt stance transition through a gate.
        """
        ...

    def get_allowed_actions(self) -> list[str]:
        """
        Return actions allowed in current stance.
        """
        ...

@dataclass
class StanceTransition:
    success: bool
    from_stance: Stance
    to_stance: Stance
    via_gate: GateType
    reason: str
    timestamp: datetime
```

### 4.2 GateController

```python
class IGateController(Protocol):
    """Enforces checkpoints for state changes."""

    def attempt_gate(
        self,
        gate: GateType,
        context: dict
    ) -> GateDecision:
        """
        Try to pass through a gate.
        """
        ...

    def register_gate(
        self,
        gate: GateType,
        evaluator: Callable
    ) -> None:
        """
        Register custom gate evaluator.
        """
        ...

@dataclass
class GateDecision:
    approved: bool
    gate: GateType
    reason: str
    transitions_stance_to: Optional[Stance]
    metadata: dict = None
```

### 4.3 CommitmentManager

```python
class ICommitmentManager(Protocol):
    """Lease-based focus with TTL."""

    def create(
        self,
        problem_id: str,
        description: str,
        turns: int
    ) -> Commitment:
        """
        Create a new commitment.
        """
        ...

    def get_active(self) -> Optional[Commitment]:
        """
        Return current active commitment.
        """
        ...

    def tick(self) -> Optional[Commitment]:
        """
        Decrement turn counter, return commitment if still active.
        """
        ...

    def complete(self) -> bool:
        """
        Mark commitment as complete.
        """
        ...

    def abandon(self, reason: str) -> bool:
        """
        Abandon commitment with reason.
        """
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
class IAgentApprovalGate(Protocol):
    """Gate for validating agent bundle proposals."""

    def evaluate(
        self,
        proposal: AgentBundleProposal,
        stance: Stance,
        commitment: Optional[Commitment]
    ) -> GateDecision:
        """
        Validate agent proposal against governance state.

        Validation Rules:
        1. Check stance compatibility
        2. Check commitment alignment
        3. Check agent authorization
        4. Check orchestration mode constraints
        """
        ...

    def stance_allows(
        self,
        proposal: AgentBundleProposal,
        stance: Stance
    ) -> bool:
        """
        Check if current stance allows this type of agent work.

        Mapping:
        - SENSEMAKING: exploration, verification
        - DISCOVERY: exploration, decomposition
        - EXECUTION: pipeline, parallel, hierarchical
        - EVALUATION: voting, verification
        """
        ...
```

### 4.5 AgentRuntime

```python
class IAgentRuntime(Protocol):
    """Executes approved agent bundles."""

    def execute_bundle(
        self,
        proposal: AgentBundleProposal,
        context: AgentExecutionContext
    ) -> AgentExecutionHandle:
        """
        Spin up and execute agent bundle.
        """
        ...

    def cancel(
        self,
        handle_id: str
    ) -> bool:
        """
        Cancel running execution.
        """
        ...

    def get_status(
        self,
        handle_id: str
    ) -> AgentExecutionStatus:
        """
        Get current status of execution.
        """
        ...

@dataclass
class AgentExecutionContext:
    problem_id: str
    commitment_id: Optional[str]
    stance: Stance
    mode: OrchestrationMode
    mode_config: dict

@dataclass
class AgentExecutionHandle:
    id: str
    agents: list[str]
    mode: OrchestrationMode
    status: str                   # pending | running | completed | failed | cancelled
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Any]
    error: Optional[str]

@dataclass
class AgentExecutionStatus:
    handle_id: str
    status: str
    progress: float               # 0.0 - 1.0
    current_agent: Optional[str]
    outputs_so_far: list[str]
```

### 4.6 AgentFirewall

```python
class IAgentFirewall(Protocol):
    """Validates all agent outputs before returning."""

    def validate(
        self,
        output: AgentOutput
    ) -> AgentOutput:
        """
        Validate agent output against security rules.

        Rules:
        1. Agents cannot make decisions (only proposals)
        2. No unauthorized capability requests
        3. Valid output packet structure
        4. No prompt injection attempts

        Raises:
            FirewallViolation if validation fails
        """
        ...

@dataclass
class AgentOutput:
    agent_id: str
    output_type: str              # proposal | data | artifact
    content: Any
    requested_capabilities: list[str]
    metadata: dict

    def contains_decision(self) -> bool:
        """Check if output contains a decision instead of proposal."""
        ...

    def is_valid_packet(self) -> bool:
        """Check if output has valid structure."""
        ...

class FirewallViolation(Exception):
    def __init__(self, rule: str, message: str):
        self.rule = rule
        self.message = message
```

---

## 5. Learning HRM Interfaces

### 5.1 PatternStore

```python
class IPatternStore(Protocol):
    """Store and query patterns with evidence links."""

    def add_pattern(
        self,
        pattern: Pattern
    ) -> str:
        """
        Add a new pattern, return ID.
        """
        ...

    def get_pattern(
        self,
        pattern_id: str
    ) -> Optional[Pattern]:
        """
        Retrieve pattern by ID.
        """
        ...

    def search(
        self,
        input_signature: dict
    ) -> list[PatternMatch]:
        """
        Find patterns matching the input signature.
        """
        ...

    def strengthen(
        self,
        pattern_id: str,
        evidence_id: str
    ) -> None:
        """
        Increase pattern confidence with new evidence.
        """
        ...

    def weaken(
        self,
        pattern_id: str,
        reason: str
    ) -> None:
        """
        Decrease pattern confidence.
        """
        ...

    def protect(
        self,
        pattern_id: str
    ) -> None:
        """
        Prevent pattern from manual removal.
        NOTE: No auto-trim per user decision.
        """
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
class IFeedbackLoop(Protocol):
    """Session analysis and pattern learning."""

    def record_outcome(
        self,
        signal: dict,
        routing: dict,
        outcome: dict
    ) -> str:
        """
        Record a signal→routing→outcome tuple.
        Returns evidence ID.
        """
        ...

    def analyze_session(self) -> SessionAnalysis:
        """
        Analyze current session for patterns.
        """
        ...

    def get_patterns_for_signal(
        self,
        signal: dict
    ) -> list[PatternMatch]:
        """
        Query patterns matching a signal (for Reasoning HRM).
        """
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
class IGeneralizer(Protocol):
    """Merge similar patterns into abstractions."""

    def find_similar(
        self,
        patterns: list[Pattern]
    ) -> list[tuple[Pattern, Pattern, float]]:
        """
        Find pairs of similar patterns with similarity score.
        """
        ...

    def merge(
        self,
        p1: Pattern,
        p2: Pattern
    ) -> Pattern:
        """
        Merge two patterns into a more general one.
        Preserves evidence from both.
        """
        ...

    def generalize_batch(
        self,
        patterns: list[Pattern]
    ) -> list[Pattern]:
        """
        Process list, merging similar patterns.
        """
        ...
```

---

## 6. Memory Bus Interfaces

### 6.1 MemoryBus

```python
class IMemoryBus(Protocol):
    """Unified memory access with file locking."""

    def write_to_working(
        self,
        problem_id: str,
        key: str,
        value: Any
    ) -> bool:
        """
        Write to problem-isolated Working Set.
        No gate required (local scope).
        """
        ...

    def write_to_shared(
        self,
        key: str,
        value: Any,
        source: str,
        signals: WriteSignals
    ) -> WriteDecision:
        """
        Write to Shared Reference.
        Requires WriteGate approval.
        """
        ...

    def log_episode(
        self,
        entry: EpisodeEntry
    ) -> str:
        """
        Append to Episodic Trace.
        Always succeeds (append-only).
        Returns entry ID.
        """
        ...

    def add_synthesis(
        self,
        pattern: SynthesizedPattern,
        signals: WriteSignals
    ) -> WriteDecision:
        """
        Add to Semantic Synthesis.
        Requires WriteGate approval (high bar).
        """
        ...

    def get_evidence_chain(
        self,
        pattern_id: str
    ) -> list[EpisodeEntry]:
        """
        Get full evidence chain for a pattern.
        """
        ...
```

### 6.2 WriteGate

```python
class IWriteGate(Protocol):
    """Signal-based write policy decisions."""

    def evaluate(
        self,
        request: WriteRequest
    ) -> WriteDecision:
        """
        Evaluate whether write should proceed.

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
class IWorkingSetStore(Protocol):
    """Per-problem isolated memory with TTL."""

    def create(
        self,
        problem_id: str,
        ttl_hours: int = 2
    ) -> WorkingSet:
        ...

    def get(
        self,
        problem_id: str
    ) -> Optional[WorkingSet]:
        ...

    def update(
        self,
        problem_id: str,
        **kwargs
    ) -> None:
        ...

    def expire_stale(self) -> int:
        """Expire stale sets, return count."""
        ...

    def export_summary(
        self,
        problem_id: str
    ) -> str:
        """Export summary for archival."""
        ...

class ISharedReferenceStore(Protocol):
    """Versioned, citable cross-problem facts."""

    def get(
        self,
        key: str,
        version: int = None
    ) -> SharedReference:
        ...

    def set(
        self,
        key: str,
        value: Any,
        source: str
    ) -> int:
        """Set value, return new version number."""
        ...

    def list_versions(
        self,
        key: str
    ) -> list[int]:
        ...

    def rollback(
        self,
        key: str,
        to_version: int
    ) -> bool:
        ...

    def cite(
        self,
        key: str
    ) -> str:
        """Generate citation string."""
        ...

class IEpisodicTraceStore(Protocol):
    """Append-only audit logs."""

    def append(
        self,
        entry: EpisodeEntry
    ) -> str:
        """Append entry, return ID."""
        ...

    def query(
        self,
        start: datetime = None,
        end: datetime = None,
        problem_id: str = None,
        tags: list[str] = None,
        entry_type: str = None
    ) -> list[EpisodeEntry]:
        ...

    def supersede(
        self,
        old_id: str,
        new_entry: EpisodeEntry
    ) -> str:
        """Create new entry that supersedes old one."""
        ...

class ISemanticSynthesisStore(Protocol):
    """Evidence-linked patterns."""

    def add_pattern(
        self,
        pattern: SynthesizedPattern
    ) -> str:
        ...

    def get_pattern(
        self,
        pattern_id: str
    ) -> SynthesizedPattern:
        ...

    def search(
        self,
        pattern_type: str = None,
        min_confidence: float = 0.0
    ) -> list[SynthesizedPattern]:
        ...

    def strengthen(
        self,
        pattern_id: str,
        new_evidence_id: str
    ) -> None:
        ...

    def weaken(
        self,
        pattern_id: str,
        reason: str
    ) -> None:
        ...

    def get_evidence_chain(
        self,
        pattern_id: str
    ) -> list[EpisodeEntry]:
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

### 7.1 Tracer

```python
class ITracer(Protocol):
    """Observability singleton."""

    def span(
        self,
        hrm: str,
        operation: str,
        component: str,
        input_data: str = None
    ) -> SpanContext:
        """
        Create a new span (context manager).
        """
        ...

    def event(
        self,
        hrm: str,
        operation: str,
        status: str = "info",
        data: dict = None
    ) -> None:
        """
        Log a single event within current span.
        """
        ...

    def generate_id(
        self,
        hrm: str
    ) -> str:
        """
        Generate trace ID with HRM prefix.
        Format: {hrm}_{timestamp}_{random}
        """
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

### 8.3 Callback Interfaces

```python
class IHRMCallback(Protocol):
    """Callbacks for cross-HRM notification."""

    def on_altitude_transition(
        self,
        from_level: AltitudeLevel,
        to_level: AltitudeLevel,
        reason: str
    ) -> None:
        ...

    def on_stance_change(
        self,
        from_stance: Stance,
        to_stance: Stance,
        via_gate: GateType
    ) -> None:
        ...

    def on_agent_activated(
        self,
        handle: AgentExecutionHandle
    ) -> None:
        ...

    def on_pattern_matched(
        self,
        pattern: Pattern,
        confidence: float
    ) -> None:
        ...

    def on_write_completed(
        self,
        target: str,
        key: str,
        decision: WriteDecision
    ) -> None:
        ...
```

---

## 9. Error Handling

### 9.1 Exception Hierarchy

```python
class HRMError(Exception):
    """Base exception for HRM errors."""
    pass

class AltitudeError(HRMError):
    """Altitude HRM errors."""
    pass

class ReasoningError(HRMError):
    """Reasoning HRM errors."""
    pass

class FocusError(HRMError):
    """Focus HRM errors."""
    pass

class LearningError(HRMError):
    """Learning HRM errors."""
    pass

class MemoryBusError(HRMError):
    """Memory Bus errors."""
    pass

# Specific errors
class GateDeniedError(FocusError):
    """Raised when a gate denies passage."""
    def __init__(self, gate: GateType, reason: str):
        self.gate = gate
        self.reason = reason

class StanceViolationError(FocusError):
    """Raised when action violates current stance."""
    def __init__(self, stance: Stance, action: str):
        self.stance = stance
        self.action = action

class EscalationRequiredError(ReasoningError):
    """Raised when escalation needed but not available."""
    pass

class WriteDeniedError(MemoryBusError):
    """Raised when write gate denies a write."""
    def __init__(self, target: str, reason: str):
        self.target = target
        self.reason = reason
```

### 9.2 Error Recovery

```python
class IErrorRecovery(Protocol):
    """Standard error recovery interface."""

    def can_recover(self, error: HRMError) -> bool:
        """Check if error is recoverable."""
        ...

    def recover(self, error: HRMError) -> RecoveryAction:
        """Suggest recovery action."""
        ...

@dataclass
class RecoveryAction:
    action: str                   # retry | fallback | escalate | abort
    delay_ms: int = 0
    context: dict = None
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
