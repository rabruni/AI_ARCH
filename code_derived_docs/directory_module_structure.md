# Directory & Module Structure (Code-Observed)

## Purpose
Summarize the code-level module layout relevant to the Locked System runtime and exports. This focuses on Python packages observed in `locked_system/` and the CLI scripts.

## Inputs
- Source files under `locked_system/` (package modules and subpackages).
- Runtime scripts (`locked_system/run.sh`, `locked_system/main.py`, `locked_system/cli/main.py`).

## Outputs
- A structured map of modules and their responsibilities based on code.

## Key Module Map
```
locked_system/
  __init__.py                 # Package exports for core, governance, execution, agents, capabilities, memory, proposals, sensing
  main.py                     # Entry point: delegates to CLI main()
  loop.py                     # LockedLoop orchestration (two-loop core)
  config.py                   # Config dataclass and YAML load/save/validate
  setup.py                    # Environment setup / validation utility
  run.sh                      # Shell wrapper for interactive and single-message modes

  cli/
    main.py                   # CLI runner, LLM creation, interactive UI loop
    session_logger.py         # Timestamped session logging
    chat_ui.py                # Chat UI for interactive mode (used by CLI)

  slow_loop/
    stance.py                 # Stance enum + StanceMachine
    commitment.py             # CommitmentManager and lease handling
    gates.py                  # GateController for stance transitions
    bootstrap.py              # Bootstrap protocol state machine

  fast_loop/
    hrm.py                    # HRM assessment for altitude selection
    executor.py               # Prompt construction + LLM invocation
    continuous_eval.py        # Post-response evaluation + proposals

  sensing/
    perception.py             # Perception sensor producing PerceptionReport
    contrast.py               # Gap detection between need and behavior

  memory/
    slow.py                   # Commitment, decision, bootstrap persistence
    fast.py                   # Progress state + interaction signals
    bridge.py                 # Bridge signals between loops
    history.py                # Gate transition history

  proposals/
    buffer.py                 # ProposalBuffer and proposal/report dataclasses
```

## Key Exports (from `locked_system.__init__`)
- **Core**: `LockedLoop`, `Config`.
- **Governance**: `StanceMachine`, `CommitmentManager`, `GateController`, `DelegationManager`.
- **Execution**: `HRM`, `Executor`, `ContinuousEvaluator`, `PromptCompiler`.
- **Memory**: `SlowMemory`, `FastMemory`, `BridgeMemory`, `History`.
- **Sensing & Proposals**: `PerceptionSensor`, `ContrastDetector`, `ProposalBuffer`, `GateProposal`.

## Key Call Paths / Data Flow
- **Orchestration**: `locked_system.loop.LockedLoop` ties together modules from `slow_loop`, `fast_loop`, `sensing`, `memory`, and `proposals`.
- **CLI**: `locked_system.cli.main` constructs the LLM callable and invokes `LockedLoop.process` via interactive or single-message flow.
