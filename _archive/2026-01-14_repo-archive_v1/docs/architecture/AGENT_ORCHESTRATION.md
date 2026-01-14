# Agent Orchestration Design

**Version:** 1.0
**Status:** Proposed

---

## Core Principle: Reasoning Proposes, Focus Approves

```
User Input
    │
    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  ALTITUDE HRM                                                              │
│  Determines: What abstraction level? (L4/L3/L2/L1)                        │
│  Does NOT propose agents                                                   │
└─────────────────────────────────┬─────────────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  REASONING HRM                                                             │
│  Determines: What strategy? What agents needed?                           │
│  PROPOSES: AgentBundleProposal (agents + orchestration mode)              │
└─────────────────────────────────┬─────────────────────────────────────────┘
                                  │ proposal
                                  ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  FOCUS HRM (Governance)                                                    │
│  Validates: Does proposal align with stance? commitment?                  │
│  APPROVES/DENIES: Agent activation                                        │
│  EXECUTES: Spins up agents through runtime                                │
└─────────────────────────────────┬─────────────────────────────────────────┘
                                  │ approved
                                  ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  AGENT RUNTIME                                                             │
│  Loads: Agent definitions                                                  │
│  Executes: Per orchestration mode                                          │
│  Validates: All outputs through firewall                                   │
└─────────────────────────────────┬─────────────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  LEARNING HRM                                                              │
│  Records: (signal, strategy, agents, outcome)                             │
│  Does NOT propose or execute agents                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Bundle Proposal (from Reasoning HRM)

### Data Structure

```python
@dataclass
class AgentBundleProposal:
    """What Reasoning HRM produces when it determines agents are needed."""

    # What triggered this
    strategy: str                    # decomposition | verification | exploration | dialogue
    classification: InputClassification

    # What agents are needed
    agents: list[str]                # Agent IDs to activate
    orchestration_mode: str          # pipeline | parallel | voting | hierarchical

    # Mode-specific config
    mode_config: dict
    # For pipeline: {"sequence": ["a", "b", "c"]}
    # For parallel: {"aggregation": "merge" | "select_best"}
    # For voting: {"threshold": 0.6, "tiebreaker": "first"}
    # For hierarchical: {"lead": "agent_a", "delegates": ["b", "c"]}

    # Rationale
    reason: str                      # Why these agents, why this mode
    confidence: float                # How confident in this proposal
    fallback: Optional[str]          # Alternative if denied

class ReasoningHRM:
    def propose_agents(
        self,
        input: str,
        context: HRMContext
    ) -> Optional[AgentBundleProposal]:

        # 1. Classify input
        classification = self.classifier.classify(input, context)

        # 2. Select strategy
        strategy = self.strategy_selector.select(classification)

        # 3. Determine if agents needed
        if strategy.requires_agents:
            agents, mode = self._select_agents(strategy, classification)

            return AgentBundleProposal(
                strategy=strategy.name,
                classification=classification,
                agents=agents,
                orchestration_mode=mode,
                mode_config=self._build_mode_config(mode, agents),
                reason=strategy.reason,
                confidence=strategy.confidence,
                fallback=strategy.fallback
            )

        return None  # No agents needed, can handle directly
```

---

## Focus HRM: Agent Approval Gate

### Validation Rules

```python
class AgentApprovalGate:
    """Focus HRM gate for agent bundle approval."""

    def evaluate(
        self,
        proposal: AgentBundleProposal,
        stance: Stance,
        commitment: Optional[Commitment]
    ) -> GateDecision:

        # Rule 1: Check stance compatibility
        if not self._stance_allows(proposal, stance):
            return GateDecision(
                approved=False,
                reason=f"Stance {stance.value} does not allow {proposal.orchestration_mode}"
            )

        # Rule 2: Check commitment alignment
        if commitment and not self._aligns_with_commitment(proposal, commitment):
            return GateDecision(
                approved=False,
                reason="Proposal does not align with active commitment"
            )

        # Rule 3: Check agent capabilities
        for agent_id in proposal.agents:
            if not self._agent_allowed(agent_id, stance):
                return GateDecision(
                    approved=False,
                    reason=f"Agent {agent_id} not allowed in current stance"
                )

        # Rule 4: Check orchestration mode constraints
        if proposal.orchestration_mode == "hierarchical":
            if not self._hierarchical_allowed(proposal):
                return GateDecision(
                    approved=False,
                    reason="Hierarchical mode requires explicit delegation"
                )

        # Approved
        return GateDecision(
            approved=True,
            reason="Proposal validated",
            transitions_stance_to=self._determine_execution_stance(proposal)
        )

    def _stance_allows(self, proposal: AgentBundleProposal, stance: Stance) -> bool:
        """Check if current stance allows this type of agent work."""
        allowed = {
            Stance.SENSEMAKING: ["exploration", "verification"],
            Stance.DISCOVERY: ["exploration", "decomposition"],
            Stance.EXECUTION: ["pipeline", "parallel", "hierarchical"],
            Stance.EVALUATION: ["voting", "verification"],
        }
        return proposal.strategy in allowed.get(stance, [])
```

### Agent Activation

```python
class FocusHRM:
    def activate_agents(
        self,
        approved_proposal: AgentBundleProposal
    ) -> AgentExecutionHandle:
        """
        Called after gate approves proposal.
        Spins up agents through runtime.
        """
        # 1. Transition stance if needed
        if approved_proposal.requires_stance_transition:
            self.gate_controller.attempt_gate(
                "commitment",
                f"Activating {len(approved_proposal.agents)} agents"
            )

        # 2. Create execution context
        exec_context = AgentExecutionContext(
            problem_id=self.current_problem_id,
            commitment_id=self.commitment.id if self.commitment else None,
            stance=self.stance.current,
            mode=approved_proposal.orchestration_mode,
            mode_config=approved_proposal.mode_config,
        )

        # 3. Spin up agents through runtime
        handle = self.agent_runtime.execute_bundle(
            agents=approved_proposal.agents,
            context=exec_context
        )

        return handle
```

---

## 4 Orchestration Modes

### Mode 1: Pipeline (Serial)

```
Input → Agent A → Output A → Agent B → Output B → Agent C → Final Output
```

**Use Case:** Sequential refinement (draft → edit → review)

**Config:**
```python
{
    "sequence": ["draft_agent", "edit_agent", "review_agent"],
    "pass_output": True,  # Each agent sees previous output
    "stop_on_failure": True
}
```

**Execution:**
```python
def execute_pipeline(agents: list[str], input: str, config: dict) -> str:
    current_output = input
    for agent_id in config["sequence"]:
        agent = load_agent(agent_id)
        result = agent.process(current_output)

        if result.failed and config["stop_on_failure"]:
            return result  # Early exit

        if config["pass_output"]:
            current_output = result.output

    return current_output
```

---

### Mode 2: Parallel (Simultaneous)

```
         ┌─→ Agent A ──→ Output A ─┐
Input ───┼─→ Agent B ──→ Output B ─┼──→ Aggregator → Final
         └─→ Agent C ──→ Output C ─┘
```

**Use Case:** Multi-perspective analysis, speed-critical tasks

**Config:**
```python
{
    "agents": ["analyst_a", "analyst_b", "analyst_c"],
    "aggregation": "merge" | "select_best" | "synthesize",
    "timeout_ms": 5000,
    "min_responses": 2  # Proceed if at least N complete
}
```

**Execution:**
```python
import asyncio

async def execute_parallel(agents: list[str], input: str, config: dict) -> str:
    tasks = [
        asyncio.create_task(run_agent(agent_id, input))
        for agent_id in config["agents"]
    ]

    # Wait for all (or timeout)
    done, pending = await asyncio.wait(
        tasks,
        timeout=config["timeout_ms"] / 1000,
        return_when=asyncio.ALL_COMPLETED
    )

    # Cancel pending if timeout
    for task in pending:
        task.cancel()

    # Aggregate results
    outputs = [task.result() for task in done if not task.cancelled()]

    if len(outputs) < config["min_responses"]:
        raise InsufficientResponses()

    return aggregate(outputs, config["aggregation"])

def aggregate(outputs: list[str], mode: str) -> str:
    if mode == "merge":
        return "\n---\n".join(outputs)
    elif mode == "select_best":
        return max(outputs, key=lambda o: o.confidence)
    elif mode == "synthesize":
        return synthesize_perspectives(outputs)
```

---

### Mode 3: Voting (Consensus)

```
         ┌─→ Agent A ──→ Vote A ─┐
Input ───┼─→ Agent B ──→ Vote B ─┼──→ Tally → Decision
         └─→ Agent C ──→ Vote C ─┘
```

**Use Case:** High-stakes decisions requiring agreement

**Config:**
```python
{
    "voters": ["judge_a", "judge_b", "judge_c"],
    "threshold": 0.6,        # 60% must agree
    "tiebreaker": "first" | "abstain" | "escalate",
    "allow_abstain": True
}
```

**Execution:**
```python
async def execute_voting(agents: list[str], input: str, config: dict) -> VoteResult:
    # Run voters in parallel
    votes = await asyncio.gather(*[
        run_voter(agent_id, input) for agent_id in config["voters"]
    ])

    # Tally
    vote_counts = Counter(v.decision for v in votes if v.decision != "abstain")
    total_votes = len([v for v in votes if v.decision != "abstain"])

    if total_votes == 0:
        return VoteResult(decision="abstain", reason="All voters abstained")

    # Check threshold
    winner, count = vote_counts.most_common(1)[0]
    ratio = count / total_votes

    if ratio >= config["threshold"]:
        return VoteResult(
            decision=winner,
            confidence=ratio,
            votes=votes
        )

    # No consensus - apply tiebreaker
    if config["tiebreaker"] == "first":
        return VoteResult(decision=votes[0].decision, confidence=ratio)
    elif config["tiebreaker"] == "abstain":
        return VoteResult(decision="abstain", reason="No consensus")
    elif config["tiebreaker"] == "escalate":
        raise EscalationRequired("Voting deadlock")
```

---

### Mode 4: Hierarchical (Delegation)

```
                    ┌──────────────┐
                    │  Lead Agent  │
                    │  (Planner)   │
                    └──────┬───────┘
                           │ delegates
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Sub-Agent A│  │ Sub-Agent B│  │ Sub-Agent C│
    │ (Research) │  │ (Analysis) │  │ (Writing)  │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                    ┌─────┴─────┐
                    │Lead Agent │
                    │(Synthesize)│
                    └───────────┘
```

**Use Case:** Complex problems requiring decomposition

**Config:**
```python
{
    "lead": "planner_agent",
    "delegates": ["research_agent", "analysis_agent", "writing_agent"],
    "max_delegation_depth": 2,  # Prevent infinite delegation
    "lead_can_execute": True,   # Lead can do work, not just delegate
    "require_synthesis": True   # Lead must synthesize at end
}
```

**Execution:**
```python
async def execute_hierarchical(lead: str, input: str, config: dict) -> str:
    lead_agent = load_agent(config["lead"])

    # Step 1: Lead plans
    plan = await lead_agent.plan(input)

    # Step 2: Lead delegates subtasks
    subtask_results = {}
    for subtask in plan.subtasks:
        delegate_id = subtask.assigned_to
        if delegate_id not in config["delegates"]:
            raise UnauthorizedDelegation(delegate_id)

        delegate = load_agent(delegate_id)
        result = await delegate.process(subtask.input)
        subtask_results[subtask.id] = result

    # Step 3: Lead synthesizes (if required)
    if config["require_synthesis"]:
        final = await lead_agent.synthesize(subtask_results)
    else:
        final = combine_results(subtask_results)

    return final
```

---

## Agent Runtime

### Core Class

```python
class AgentRuntime:
    """Executes approved agent bundles."""

    def __init__(self, firewall: AgentFirewall):
        self.firewall = firewall
        self.loader = AgentLoader()
        self.active_executions: dict[str, AgentExecutionHandle] = {}

    def execute_bundle(
        self,
        agents: list[str],
        context: AgentExecutionContext
    ) -> AgentExecutionHandle:
        """
        Main entry point. Called by Focus HRM after approval.
        """
        # Create handle for tracking
        handle = AgentExecutionHandle(
            id=generate_id(),
            agents=agents,
            mode=context.mode,
            status="running",
            started_at=datetime.now()
        )
        self.active_executions[handle.id] = handle

        # Execute based on mode
        try:
            if context.mode == "pipeline":
                result = self._execute_pipeline(agents, context)
            elif context.mode == "parallel":
                result = asyncio.run(self._execute_parallel(agents, context))
            elif context.mode == "voting":
                result = asyncio.run(self._execute_voting(agents, context))
            elif context.mode == "hierarchical":
                result = asyncio.run(self._execute_hierarchical(agents, context))

            # Validate through firewall
            validated = self.firewall.validate(result)

            handle.status = "completed"
            handle.result = validated

        except Exception as e:
            handle.status = "failed"
            handle.error = str(e)

        handle.completed_at = datetime.now()
        return handle

    def cancel(self, handle_id: str) -> bool:
        """Cancel running execution."""
        handle = self.active_executions.get(handle_id)
        if handle and handle.status == "running":
            handle.status = "cancelled"
            return True
        return False
```

### Firewall (Output Validation)

```python
class AgentFirewall:
    """Validates all agent outputs before returning."""

    def validate(self, output: AgentOutput) -> AgentOutput:
        # Rule 1: Agents cannot make decisions (only proposals)
        if output.contains_decision():
            raise FirewallViolation("Agents can only propose, not decide")

        # Rule 2: Check for unauthorized capability requests
        for capability in output.requested_capabilities:
            if capability not in ALLOWED_CAPABILITIES:
                raise FirewallViolation(f"Unauthorized capability: {capability}")

        # Rule 3: Validate output structure
        if not output.is_valid_packet():
            raise FirewallViolation("Invalid output packet structure")

        # Rule 4: Check for prompt injection attempts
        if self._detect_injection(output):
            raise FirewallViolation("Potential prompt injection detected")

        return output
```

---

## Summary: Who Does What

| Component | Can Propose Agents | Can Approve Agents | Can Execute Agents |
|-----------|-------------------|--------------------|--------------------|
| **Altitude HRM** | No | No | No |
| **Reasoning HRM** | YES | No | No |
| **Focus HRM** | No | YES | YES (via runtime) |
| **Learning HRM** | No | No | No |
| **Agent Runtime** | No | No | YES (when told) |
| **Agents themselves** | Can request (hierarchical) | No | No |

### Key Constraints

1. **Reasoning proposes**: Based on input classification and strategy
2. **Focus approves**: Based on stance, commitment, and gate rules
3. **Runtime executes**: Only after Focus approves
4. **Firewall validates**: All outputs checked before returning
5. **Agents never self-authorize**: Even in hierarchical mode, delegation is pre-approved
