# Test Runbook

## Prerequisites

- Python virtual environment with pytest
- pytest is included in requirements.txt

## Quick Start

```bash
# Recommended: Use verify.sh (auto-detects venv)
bash scripts/verify.sh

# Or run pytest directly via venv
venv/bin/python -m pytest -q --tb=short
```

## Running Tests

### All Tests

```bash
# Run all tests (517+ tests, ~4 seconds)
venv/bin/python -m pytest

# With verbose output
venv/bin/python -m pytest -v

# Quick summary
venv/bin/python -m pytest -q --tb=short

# With coverage (if pytest-cov installed)
venv/bin/python -m pytest --cov=the_assist --cov=locked_system
```

### Specific Test Files

```bash
# Run locked_system tests
venv/bin/python -m pytest locked_system/tests/

# Run a specific test file
venv/bin/python -m pytest locked_system/tests/test_lanes.py

# Run altitude governance test
venv/bin/python test_l2_fastlane.py
```

### Test Selection

```bash
# Run tests matching a pattern
venv/bin/python -m pytest -k "test_lanes"

# Run tests in a specific class
venv/bin/python -m pytest locked_system/tests/test_executor.py::TestExecutor
```

## Test Output Options

```bash
# Short traceback
venv/bin/python -m pytest --tb=short

# Show print statements
venv/bin/python -m pytest -s

# Stop on first failure
venv/bin/python -m pytest -x

# Run last failed tests
venv/bin/python -m pytest --lf
```

## Verification Before PR

```bash
# Full verification (includes tests) - RECOMMENDED
bash scripts/verify.sh

# Or just tests
venv/bin/python -m pytest -q
```

## Known Test Locations

| Location | Description |
|----------|-------------|
| `locked_system/tests/` | Core locked system tests |
| `test_l2_fastlane.py` | Altitude governance test |
