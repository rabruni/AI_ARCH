# Startup & Entry Paths

## Purpose
Document the code-derived entry points for starting the Locked System, including CLI, setup, and shell wrappers.

## Inputs
- Command-line flags and environment variables.
- Optional YAML config file (`Config.from_yaml`).
- Optional system prompt file path.

## Outputs
- Interactive CLI session or single-message response.
- Setup/validation output when using setup mode.

## Entry Points
### 1) Shell wrapper: `locked_system/run.sh`
- **Usage**: `./run.sh` (interactive), `./run.sh -m "message"` (single message), `./run.sh --setup`, `./run.sh --test`, `./run.sh --reset`.
- **Inputs**:
  - Flags: `--debug`, `--message`, `--setup`, `--test`, `--reset`, `--config`, `--json`, `--verbose`.
  - Environment: `ANTHROPIC_API_KEY`, `LOCKED_MEMORY_DIR`.
- **Behavior**: Validates Python, activates venv if present, then dispatches to `python3 -m locked_system.main` or `python3 -m locked_system.setup`.

### 2) Python entry: `locked_system/main.py`
- **Usage**: `python -m locked_system.main [--config ...]`.
- **Behavior**: Delegates directly to `locked_system.cli.main.main`.

### 3) CLI main: `locked_system/cli/main.py`
- **Inputs**:
  - `--config` (YAML), `--message`/`-m`, `--json`, `--system-prompt`, `--debug`.
- **Behavior**:
  - Loads config and optional system prompt.
  - Creates LLM callable via `create_llm` (Claude if API key present, placeholder otherwise).
  - Instantiates `LockedLoop` with config + LLM.
  - Runs interactive REPL (`run_interactive`) or single turn (`run_single`).

### 4) Setup script: `locked_system/setup.py`
- **Usage**: `python -m locked_system.setup [--config] [--test] [--full]`.
- **Behavior**:
  - Creates memory directories, validates imports/config, optionally creates example config, and can run a loop test or API connectivity test.

## Key Call Paths / Data Flow
- **Interactive path**: `run.sh` → `python -m locked_system.main` → `cli.main.main` → `run_interactive` → `LockedLoop.process`.
- **Single-message path**: `run.sh -m` → `cli.main.main` → `run_single` → `LockedLoop.process` → output string or JSON.
