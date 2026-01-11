#!/usr/bin/env python3
"""Locked System - Entry Point.

Usage:
    python -m locked_system.main [--config path/to/config.yaml]

Or import and use directly:
    from locked_system import LockedLoop, Config
    loop = LockedLoop(Config())
    result = loop.process("Hello")
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from locked_system.config import Config
from locked_system.loop import LockedLoop, LoopResult


def create_default_llm() -> callable:
    """Create default LLM callable (placeholder for actual implementation)."""
    def llm(prompt: str) -> str:
        """
        Placeholder LLM implementation.

        In production, replace with actual LLM call:
        - Anthropic Claude
        - OpenAI GPT
        - Local model
        """
        # Extract user message from prompt
        if "User message:" in prompt:
            user_msg = prompt.split("User message:")[-1].strip()
            user_msg = user_msg.split("\n")[0]
        else:
            user_msg = "your message"

        return f"I understand you're saying: {user_msg}. How can I help you with that?"

    return llm


def run_interactive(loop: LockedLoop):
    """Run interactive REPL session."""
    print("\n=== Locked System ===")
    print("Type 'quit' or 'exit' to end session")
    print("Type 'state' to see current loop state")
    print("Type 'commit <frame>' to create a commitment")
    print("Type 'emergency <reason>' to trigger emergency gate")
    print("-" * 40)

    # Initial greeting - if in Bootstrap, show first prompt
    if loop.bootstrap.is_active:
        initial_prompt = loop.bootstrap.get_current_prompt()
        if initial_prompt:
            print(f"\nAssistant: Welcome. {initial_prompt}")
        else:
            print("\nAssistant: Welcome. What's on your mind?")
    else:
        print("\nAssistant: Welcome. How can I help you today?")

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit"]:
                print("\nGoodbye!")
                break

            if user_input.lower() == "state":
                state = loop.get_state()
                print("\n--- Current State ---")
                print(json.dumps(state, indent=2, default=str))
                continue

            if user_input.lower().startswith("commit "):
                frame = user_input[7:].strip()
                if loop.create_commitment(frame):
                    print(f"\n[Commitment created: {frame}]")
                else:
                    print("\n[Cannot create commitment in current stance]")
                continue

            if user_input.lower().startswith("emergency "):
                reason = user_input[10:].strip()
                if loop.trigger_emergency(reason):
                    print(f"\n[Emergency triggered: {reason}]")
                else:
                    print("\n[Emergency on cooldown or failed]")
                continue

            # Process normal input
            result = loop.process(user_input)

            # Display response
            print(f"\nAssistant: {result.response}")

            # Display metadata
            print(f"\n  [Turn {result.turn_number} | "
                  f"Stance: {result.stance} | "
                  f"Altitude: {result.altitude} | "
                  f"Health: {result.quality_health}]")

            if result.bootstrap_active:
                print("  [Bootstrap mode active]")

            if result.gate_transitions:
                print(f"  [Gate transitions: {', '.join(result.gate_transitions)}]")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def run_single(loop: LockedLoop, message: str) -> LoopResult:
    """Process a single message and return result."""
    return loop.process(message)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Locked System - Two-tempo cognitive loop"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--message",
        "-m",
        type=str,
        help="Single message to process (non-interactive)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (for single message mode)"
    )

    args = parser.parse_args()

    # Load config
    if args.config:
        config = Config.from_yaml(args.config)
    else:
        config = Config()

    # Create loop with default LLM
    llm = create_default_llm()
    loop = LockedLoop(config, llm)

    # Run appropriate mode
    if args.message:
        result = run_single(loop, args.message)
        if args.json:
            output = {
                "response": result.response,
                "stance": result.stance,
                "altitude": result.altitude,
                "turn": result.turn_number,
                "health": result.quality_health,
                "bootstrap_active": result.bootstrap_active,
                "gate_transitions": result.gate_transitions
            }
            print(json.dumps(output, indent=2))
        else:
            print(result.response)
    else:
        run_interactive(loop)


if __name__ == "__main__":
    main()
