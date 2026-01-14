# Contributing to Locked System

Thank you for your interest in contributing to Locked System! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/raymondbruni/locked_system.git
cd locked_system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Set up your API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Running Tests

Run the full test suite:
```bash
pytest locked_system/tests/ -v
```

Run tests with coverage:
```bash
pytest locked_system/tests/ -v --cov=locked_system --cov-report=html
```

Run specific test files:
```bash
pytest locked_system/tests/test_lanes.py -v
pytest locked_system/tests/test_executor.py -v
```

## Code Style

This project uses:
- **ruff** for linting and formatting
- **mypy** for type checking

Run linting:
```bash
ruff check locked_system/
```

Run type checking:
```bash
mypy locked_system/ --ignore-missing-imports
```

## Architecture Principles

When contributing, please follow these core principles:

### 1. Agents are Proposers
Agents can only propose actions via `AgentPacket`. They cannot execute tools directly or make state changes.

### 2. Default-Deny Security
All operations are denied by default. Explicit grants are required for any capability.

### 3. All Writes Require Approval
Any operation with side effects (file writes, external calls) must go through `WriteApprovalGate`.

### 4. Deterministic Behavior
Outcomes must be reproducible given the same inputs. Avoid randomness in decision logic.

### 5. Single Active Lane
Only one lane can be active at a time. Lane switching requires explicit gate approval.

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation if needed
5. Submit a pull request with a clear description

## Commit Messages

Use clear, descriptive commit messages:
- `feat: Add lane budget enforcement`
- `fix: Correct firewall validation for nested proposals`
- `test: Add integration tests for executor pipeline`
- `docs: Update architecture documentation`

## Project Structure

```
locked_system/
├── lanes/          # Workstream scheduler
├── tools/          # Tool system (specs, connectors, runtime)
├── agents/         # Agent definitions and runtime
├── executor/       # Execution pipeline
├── front_door/     # Cognitive router agent
├── memory/         # Memory subsystems
├── tests/          # Test suite
└── ...
```

## Questions?

Open an issue for questions or discussion about potential contributions.
