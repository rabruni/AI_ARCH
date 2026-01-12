# Startup & Entry Paths

## Purpose
Trace the runtime entry points and startup paths used to launch the system.

## Shell Script Entry (`locked_system/run.sh`)
- Validates `python3` availability and repo structure.
- Activates `venv/` or `.venv/` if present.
- Dispatches modes:
  - Interactive: `python3 -m locked_system.main`
  - Single message: `python3 -m locked_system.main -m "<message>"`
  - Setup: `python3 -m locked_system.setup`
  - Tests: `python3 -m locked_system.setup --test`

## Python Entry (`locked_system/main.py`)
- Delegates to CLI: `locked_system.cli.main.main`.

## CLI Entry (`locked_system/cli/main.py`)
- Parses arguments.
- Loads Config and optional system prompt.
- Creates LLM callable (Claude or placeholder).
- Constructs `LockedLoop` and dispatches:
  - Interactive: `run_interactive` (greeting + REPL loop)
  - Single message: `run_single` (one call to `loop.process`)

## Primary Execution Path (`LockedLoop.process`)
- Handles note intent shortcut.
- Runs perception sensing.
- Runs bootstrap (if active), returning early.
- Runs slow loop tick (gate proposals, stance transitions).
- Runs fast loop execution (HRM + executor).
- Runs continuous evaluation and contrast detection.
- Persists conversation history.
