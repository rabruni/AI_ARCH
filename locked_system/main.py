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


def create_llm(config: Config) -> callable:
    """
    Create LLM callable - uses Claude if API key available, otherwise placeholder.

    Same approach as the_assist - uses anthropic.Anthropic() with claude-sonnet.
    """
    import os

    # Try to use Claude if API key is set
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic()

            def claude_llm(prompt: str) -> str:
                """Call Claude API."""
                response = client.messages.create(
                    model=config.model,
                    max_tokens=config.max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

            print("[Using Claude API]")
            return claude_llm

        except ImportError:
            print("[Warning: anthropic package not installed, using placeholder]")
        except Exception as e:
            print(f"[Warning: Claude API error ({e}), using placeholder]")

    # Fallback to placeholder
    print("[Using placeholder LLM - set ANTHROPIC_API_KEY for real responses]")
    return _create_placeholder_llm()


def _create_placeholder_llm() -> callable:
    """Create placeholder LLM for testing without API key."""

    state = {"turn": 0}

    def placeholder(prompt: str) -> str:
        import re

        # Handle greeting generation
        if "Generate a warm, natural welcome" in prompt:
            if "Bootstrap" in prompt and "Stage prompt to incorporate" in prompt:
                match = re.search(r'Stage prompt to incorporate: "([^"]+)"', prompt)
                if match:
                    stage_prompt = match.group(1)
                    return f"Hey there. Before we dive in - {stage_prompt.lower()}"
            elif "Active commitment" in prompt:
                return "Good to see you again. Ready to pick up where we left off?"
            else:
                return "Hey. What's on your mind today?"

        # Bootstrap-aware responses
        prompt_lower = prompt.lower()
        if "sensemaking" in prompt_lower:
            state["turn"] += 1
            if state["turn"] == 1:
                return "I hear you. What's helping you stay where you are right now?"
            elif state["turn"] == 2:
                return "Those are real anchors. If you moved one step up, what would be different?"
            elif state["turn"] == 3:
                return "That sounds meaningful. What's one small thing that would help?"
            elif state["turn"] == 4:
                return "Would you like me to keep listening, or start offering structure?"
            else:
                return "Let's work on this together. Where should we start?"

        # Default
        if "User message:" in prompt:
            user_msg = prompt.split("User message:")[-1].strip().split("\n")[0]
            return f"I'm with you. Tell me more about '{user_msg[:30]}'."

        return "I'm listening. What's on your mind?"

    return placeholder


def run_interactive(loop: LockedLoop):
    """Run interactive REPL session."""
    print("\n=== Locked System ===")
    print("Type 'quit' or 'exit' to end session")
    print("Type 'state' to see current loop state")
    print("Type 'commit <frame>' to create a commitment")
    print("Type 'emergency <reason>' to trigger emergency gate")
    print("-" * 40)

    # Generate natural greeting using the AI
    greeting = loop.generate_greeting()
    print(f"\nAssistant: {greeting}")

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

    # Create loop with LLM (Claude if API key set, otherwise placeholder)
    llm = create_llm(config)
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
