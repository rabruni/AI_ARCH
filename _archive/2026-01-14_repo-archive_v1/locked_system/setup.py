#!/usr/bin/env python3
"""Setup script for Locked System.

This script initializes the Locked System environment:
1. Creates memory directories
2. Validates configuration
3. Optionally creates example config file
4. Tests basic imports and connectivity

Usage:
    python -m locked_system.setup              # Basic setup
    python -m locked_system.setup --config     # Create example config
    python -m locked_system.setup --test       # Run connectivity test
    python -m locked_system.setup --full       # Full setup with all options
"""
import argparse
import json
import sys
from pathlib import Path


def create_directories(memory_dir: Path) -> bool:
    """Create memory directory structure."""
    print(f"Creating memory directories at: {memory_dir}")

    try:
        memory_dir.mkdir(parents=True, exist_ok=True)
        (memory_dir / "slow").mkdir(exist_ok=True)
        (memory_dir / "fast").mkdir(exist_ok=True)
        (memory_dir / "bridge").mkdir(exist_ok=True)
        (memory_dir / "history").mkdir(exist_ok=True)
        print("  [OK] Directories created")
        return True
    except Exception as e:
        print(f"  [FAIL] Could not create directories: {e}")
        return False


def validate_imports() -> bool:
    """Validate that all imports work."""
    print("Validating imports...")

    try:
        from locked_system import LockedLoop, Config
        print("  [OK] locked_system.LockedLoop")
        print("  [OK] locked_system.Config")

        from locked_system.slow_loop import StanceMachine, CommitmentManager, GateController, Bootstrap
        print("  [OK] slow_loop components")

        from locked_system.fast_loop import HRM, Executor, ContinuousEvaluator
        print("  [OK] fast_loop components")

        from locked_system.sensing import PerceptionSensor, ContrastDetector
        print("  [OK] sensing components")

        from locked_system.memory import SlowMemory, FastMemory, BridgeMemory, History
        print("  [OK] memory components")

        from locked_system.proposals import ProposalBuffer
        print("  [OK] proposals components")

        return True
    except ImportError as e:
        print(f"  [FAIL] Import error: {e}")
        return False


def validate_config() -> bool:
    """Validate default configuration."""
    print("Validating configuration...")

    try:
        from locked_system import Config
        config = Config()
        errors = config.validate()

        if errors:
            for error in errors:
                print(f"  [WARN] {error}")
            return False
        else:
            print("  [OK] Configuration valid")
            return True
    except Exception as e:
        print(f"  [FAIL] Configuration error: {e}")
        return False


def create_example_config(path: str = "locked_system_config.yaml") -> bool:
    """Create example configuration file."""
    print(f"Creating example config at: {path}")

    config_content = """# Locked System Configuration
# See locked_system/README.md for full documentation

# Model settings
model: claude-sonnet-4-20250514
perception_model: claude-sonnet-4-20250514
max_tokens: 2000

# Memory persistence directory
memory_dir: ./memory

# Bootstrap settings
# Turns before re-offering handoff prompt in Bootstrap mode
bootstrap_soft_timeout_turns: 10

# Emergency gate settings
# Minimum turns between emergency gate uses (prevents abuse)
emergency_cooldown_turns: 3

# Proposal priority (first = highest)
proposal_priority_order:
  - user_signal      # Explicit user requests
  - decay_manager    # Commitment expiry
  - perception       # User state signals
  - continuous_eval  # Quality concerns
  - task_agent       # Child task proposals

# Commitment defaults
# How many turns before commitment expires (unless renewed)
default_lease_turns: 20
"""

    try:
        with open(path, 'w') as f:
            f.write(config_content)
        print(f"  [OK] Config created: {path}")
        return True
    except Exception as e:
        print(f"  [FAIL] Could not create config: {e}")
        return False


def test_basic_loop() -> bool:
    """Test basic loop functionality."""
    print("Testing basic loop...")

    try:
        from locked_system import LockedLoop, Config

        # Create loop with in-memory config
        config = Config(memory_dir=Path("/tmp/locked_system_test"))
        loop = LockedLoop(config)

        # Test processing
        result = loop.process("Hello, testing the system")
        print(f"  [OK] Process returned response ({len(result.response)} chars)")
        print(f"  [OK] Stance: {result.stance}")
        print(f"  [OK] Altitude: {result.altitude}")

        # Test state inspection
        state = loop.get_state()
        print(f"  [OK] State inspection works (turn {state['turn']})")

        return True
    except Exception as e:
        print(f"  [FAIL] Loop test failed: {e}")
        return False


def test_api_connectivity() -> bool:
    """Test API connectivity (requires ANTHROPIC_API_KEY)."""
    print("Testing API connectivity...")

    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  [SKIP] ANTHROPIC_API_KEY not set")
        return True  # Not a failure, just skipped

    try:
        from anthropic import Anthropic
        client = Anthropic()

        # Minimal API call
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'ok'"}]
        )
        print(f"  [OK] API connected: {response.content[0].text[:20]}...")
        return True
    except Exception as e:
        print(f"  [FAIL] API error: {e}")
        return False


def main():
    """Run setup."""
    parser = argparse.ArgumentParser(
        description="Setup script for Locked System"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Create example configuration file"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run connectivity and functionality tests"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full setup (directories + config + tests)"
    )
    parser.add_argument(
        "--memory-dir",
        type=str,
        default="./memory",
        help="Memory directory path (default: ./memory)"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Locked System Setup")
    print("=" * 50)
    print()

    results = []

    # Always validate imports
    results.append(("Imports", validate_imports()))

    # Always create directories
    results.append(("Directories", create_directories(Path(args.memory_dir))))

    # Always validate config
    results.append(("Config validation", validate_config()))

    # Optional: create example config
    if args.config or args.full:
        results.append(("Example config", create_example_config()))

    # Optional: run tests
    if args.test or args.full:
        results.append(("Basic loop test", test_basic_loop()))
        results.append(("API connectivity", test_api_connectivity()))

    # Summary
    print()
    print("=" * 50)
    print("Summary")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("Setup complete! You can now run:")
        print("  python -m locked_system.main")
        return 0
    else:
        print("Setup completed with warnings. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
