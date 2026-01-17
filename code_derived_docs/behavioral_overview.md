# Code-Derived Design Doc (Behavioral Overview)

## Purpose
Provide a code-derived behavioral overview of the Locked System’s two-loop architecture, focusing on how inputs flow through sensing, governance, execution, evaluation, and memory persistence. This description reflects the runtime path in `locked_system.loop.LockedLoop.process` and its supporting components.

## Inputs
- **User input string** passed to `LockedLoop.process(user_input)`.
- **Configuration** via `locked_system.config.Config` (e.g., model, memory paths, system prompt, proposal priority).
- **LLM callable** injected into `LockedLoop` (typically created by `locked_system.cli.main.create_llm`).
- **Persistent state** loaded from memory directories (`SlowMemory`, `FastMemory`, `BridgeMemory`, `History`) and consent checks (`ConsentManager`).

## Outputs
- **Primary output**: `LoopResult` containing the assistant response, stance, altitude, gate transitions, health, and turn number.
- **Side effects**: Updated memory files (commitment, progress, history, conversation), signals recorded, proposals added/cleared, and optional notes captured.

## Key Call Paths / Data Flow
1. **Initialization** (`LockedLoop.__init__`)
   - Creates memory tiers (`SlowMemory`, `FastMemory`, `BridgeMemory`, `History`) and proposal buffer.
   - Instantiates governance (`StanceMachine`, `CommitmentManager`, `GateController`), execution (`HRM`, `Executor`, `ContinuousEvaluator`), sensing (`PerceptionSensor`, `ContrastDetector`), and capabilities (`NoteCaptureCapability`).
   - Loads persisted conversation history if consent allows.

2. **Turn processing** (`LockedLoop.process`)
   - **Phase 0: Note capture shortcut**
     - `_check_note_intent` uses `NoteCaptureCapability` to detect note intent and writes to gated notes if authorized; otherwise proposes a framing gate and temporarily grants delegation before retrying.
   - **Phase 1: Sensing**
     - `_sense` constructs `PerceptionContext` and calls `PerceptionSensor.sense` to emit a `PerceptionReport` (emotional state, urgency, inferred intent, context cues, confidence). Signals are recorded from this report.
   - **Phase 2: Slow loop authority**
     - `_slow_loop_tick` checks commitment expiry (`CommitmentManager.check_expiry`), ticks gate cooldowns, delegation lease expiry, and processes gate proposals via `GateController.process_proposals`, which can transition stances and log transitions to `History`.
   - **Phase 3: Fast loop execution**
     - `_fast_loop_execute` uses `HRM.assess` (horizon/risk/moment) to select an altitude, builds an `ExecutionContext`, and calls `Executor.execute` to generate a response via the injected LLM.
   - **Phase 4: Continuous evaluation**
     - `_post_execution_eval` runs `ContinuousEvaluator.evaluate` to score quality signals and produce gate proposals and contrast reports. It also runs `ContrastDetector.detect` based on `PerceptionReport` + `ExecutionResult` to propose additional gates.
   - **Persistence & signals**
     - Conversation history is appended and persisted (consent-gated), signals are recorded for stance, altitude, health, and progress.

3. **Governance & gating**
   - `GateController` enforces legal stance transitions (`StanceMachine.VALID_TRANSITIONS`), logs transitions to `History`, and handles emergency gates with cooldown.
   - `CommitmentManager` manages an active commitment lease in `SlowMemory` and can propose evaluation when expired.

4. **Execution constraints**
   - `Executor._build_system_prompt` composes behavioral constraints from altitude guidance, stance behavior, and commitment constraints.
   - Responses are truncated to altitude-based word limits and interaction signals are recorded into `FastMemory`.

5. **Proposal routing**
   - `ProposalBuffer` collects gate proposals, perception reports, contrast reports, and bootstrap proposals; proposals are sorted by severity/source priority order when processed by the gate controller.

## Behavioral Invariants (Code-Derived)
- **Slow loop authority**: Only `GateController` changes stance; sensors/evaluators can only propose.
- **Fast loop constraints**: `Executor` must honor altitude limits and stance behaviors, and can be further constrained by active commitments.
- **Consent gating**: Conversation persistence is skipped unless `ConsentManager` allows it.
