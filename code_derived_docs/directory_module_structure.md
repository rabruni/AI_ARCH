# Directory & Module Structure (code-observed)

## Purpose
This document describes the actual directory and module organization of the Locked System based on filesystem inspection, showing how code is organized into functional layers.

## Directory Structure

### Root Level (`locked_system/`)
```
locked_system/
├── __init__.py              # Package initialization
├── loop.py                  # Main orchestration (LockedLoop class)
├── config.py                # Configuration management (Config class)
├── main.py                  # CLI entry point
├── notes.py                 # Note-taking capability
├── run.sh                   # Shell script for running
├── setup.py                 # Package setup
├── README.md                # Documentation (ignored per prompt)
├── agents/                  # Agent implementations
├── capabilities/            # Gated capabilities system
├── cli/                     # Command-line interface
├── core/                    # Core subsystems (governance, execution)
├── fast_loop/               # Fast tempo execution layer
├── memory/                  # Multi-layer memory system
├── proposals/               # Proposal buffer system
├── prompts/                 # System prompts
├── sensing/                 # Perception and sensing
├── signals/                 # Signal collection system
└── slow_loop/               # Slow tempo authority layer
```

### CLI Module (`locked_system/cli/`)
```
cli/
├── __init__.py
├── main.py                  # CLI entry point with LLM integration
├── chat_ui.py               # Interactive chat interface
└── session_logger.py        # Session logging
```

### Fast Loop Module (`locked_system/fast_loop/`)
```
fast_loop/
├── __init__.py
├── executor.py              # Response generation executor
├── hrm.py                   # Hierarchical Reasoning Model
└── continuous_eval.py       # Continuous evaluation
```

### Slow Loop Module (`locked_system/slow_loop/`)
```
slow_loop/
├── __init__.py
├── stance.py                # Stance state machine
├── commitment.py            # Commitment lease management
├── gates.py                 # Gate controller
└── bootstrap.py             # Bootstrap logic
```

### Sensing Module (`locked_system/sensing/`)
```
sensing/
├── __init__.py
├── perception.py            # Perception sensor
└── contrast.py              # Contrast detector
```

### Memory Module (`locked_system/memory/`)
```
memory/
├── __init__.py
├── slow.py                  # Slow memory (commitments/decisions)
├── fast.py                  # Fast memory (execution state)
├── bridge.py                # Bridge memory (artifacts)
├── history.py               # History memory (transitions)
└── consent.py               # Consent management
```

### Proposals Module (`locked_system/proposals/`)
```
proposals/
├── __init__.py
└── buffer.py                # Proposal buffer
```

## Key Module Relationships

### Core Orchestration (`loop.py`)
- **Imports**: All major subsystems (memory, governance, execution, sensing)
- **Coordinates**: Slow loop (authority) and fast loop (execution)
- **Manages**: Turn processing, capability delegation, consent

### Configuration (`config.py`)
- **Provides**: `Config` dataclass with model settings, paths, validation
- **Supports**: YAML loading, directory creation, API key management
- **Used by**: All modules requiring configuration

### CLI Integration (`cli/main.py`)
- **Creates**: LLM callable (Claude or placeholder)
- **Provides**: Interactive and single-message modes
- **Handles**: Session logging, UI management, consent flow

## Module Dependencies

### Import Hierarchy
- **Entry**: `main.py` → `cli/main.py` → `loop.py`
- **Core**: `loop.py` imports all subsystem modules
- **Memory**: All modules import memory components
- **Config**: Passed through constructor chain from CLI

### Key Classes by Module
- `locked_system.loop`: `LockedLoop`, `LoopResult`
- `locked_system.config`: `Config`
- `locked_system.cli.main`: `create_llm()`, `run_interactive()`
- `locked_system.fast_loop.executor`: `Executor`, `ExecutionContext`, `ExecutionResult`
- `locked_system.fast_loop.hrm`: `HRM`, `HRMAssessment`, `Altitude`
- `locked_system.slow_loop.stance`: `StanceMachine`, `Stance`
- `locked_system.slow_loop.commitment`: `CommitmentManager`
- `locked_system.slow_loop.gates`: `GateController`, `GateResult`
- `locked_system.memory.slow`: `SlowMemory`, `CommitmentLease`
- `locked_system.memory.fast`: `FastMemory`, `ProgressState`
- `locked_system.sensing.perception`: `PerceptionSensor`, `PerceptionContext`
- `locked_system.proposals.buffer`: `ProposalBuffer`, `GateProposal`

## File Evidence
- **Directory listing**: `ls -a locked_system/` shows all top-level files
- **Submodule listing**: `ls -a locked_system/{cli,fast_loop,slow_loop,sensing,memory,proposals}` shows module contents
- **Import analysis**: Each module's `__init__.py` and main files show export patterns
- **Class definitions**: Found in respective `.py` files as documented</content>
<parameter name="filePath">/Users/raymondbruni/AI_ARCH/code_derived_docs/directory_module_structure.md