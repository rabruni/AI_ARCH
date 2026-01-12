# Directory & Module Structure (Code-Observed)

## Purpose
Document the repository’s code structure and what each module provides, based solely on code.

## Top-Level (locked_system/)
- `__init__.py`: Public exports for core classes and submodules.
- `config.py`: Configuration dataclass (model selection, memory paths, prompts).
- `loop.py`: Main orchestration loop (slow/fast loops, sensing, persistence).
- `main.py`: Entry point wrapper calling CLI main.
- `notes.py`: Note intent detection and note persistence.
- `run.sh`: Shell runner for interactive/message/setup/test modes.
- `setup.py`: Setup and test utilities.

## CLI (locked_system/cli/)
- `main.py`: CLI argument parsing, LLM creation, interactive and single-message execution.
- `session_logger.py`: Timestamped conversation log writer.
- `__init__.py`: CLI exports.

## Slow Loop (locked_system/slow_loop/)
- `stance.py`: Stance state machine and transition rules.
- `commitment.py`: Commitment lease manager and expiry proposals.
- `gates.py`: Gate controller for framing/commitment/evaluation/emergency transitions.
- `bootstrap.py`: Staged bootstrap protocol and consent flow.
- `__init__.py`: Slow loop exports.

## Fast Loop (locked_system/fast_loop/)
- `hrm.py`: Horizon/Risk/Moment altitude assessment.
- `executor.py`: System prompt builder + LLM execution + response truncation.
- `continuous_eval.py`: Response quality assessment and gate proposals.
- `__init__.py`: Fast loop exports.

## Sensing (locked_system/sensing/)
- `perception.py`: Heuristic user state detection.
- `contrast.py`: Gap detection between inferred need and observed response.
- `__init__.py`: Sensing exports.

## Memory (locked_system/memory/)
- `slow.py`: Authoritative commitment/decision/bootstrap persistence.
- `fast.py`: Non-authoritative progress/signals/preferences persistence.
- `bridge.py`: Artifact index with decay.
- `history.py`: Session and gate transition logging.
- `__init__.py`: Memory exports.

## Proposals (locked_system/proposals/)
- `buffer.py`: Proposal buffer with severity prioritization.
- `__init__.py`: Proposal exports.
