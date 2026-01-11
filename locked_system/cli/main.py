#!/usr/bin/env python3
"""Locked System CLI - Interactive and single-message modes.

Usage:
    python -m locked_system.cli.main [--config path/to/config.yaml]
    python -m locked_system.cli.main -m "Hello" --json
"""
import argparse
import json
import os
from pathlib import Path
from typing import Callable, Tuple

# Load .env file from project root
try:
    from dotenv import load_dotenv
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # dotenv not installed, rely on environment variables

from locked_system.config import Config
from locked_system.loop import LockedLoop, LoopResult
from locked_system.cli.session_logger import SessionLogger


def create_llm(config: Config, system_prompt: str = None) -> Tuple[Callable, str]:
    """
    Create LLM callable - uses Claude if API key available, otherwise placeholder.

    Returns (llm_callable, status_message) for display.

    The LLM callable signature is:
        llm(system: str, messages: list[dict], prompt: str = None) -> str

    - system: System prompt (merged with base system prompt)
    - messages: Conversation history [{"role": "user/assistant", "content": "..."}]
    - prompt: Optional additional prompt to append
    """
    base_system_prompt = system_prompt or ""

    # Try to use Claude if API key is set
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic()

            def claude_llm(system: str = None, messages: list = None, prompt: str = None) -> str:
                """Call Claude API with proper multi-turn conversation."""
                # Use base system prompt, optionally extended
                full_system = base_system_prompt
                if system:
                    full_system = f"{base_system_prompt}\n\n{system}" if base_system_prompt else system

                # Build messages list
                msgs = list(messages) if messages else []

                # If prompt provided, add as user message
                if prompt:
                    msgs.append({"role": "user", "content": prompt})

                # Ensure we have at least one message
                if not msgs:
                    msgs = [{"role": "user", "content": "Hello"}]

                response = client.messages.create(
                    model=config.model,
                    max_tokens=config.max_tokens,
                    system=full_system,
                    messages=msgs
                )
                return response.content[0].text

            return claude_llm, f"Claude ({config.model.split('-')[1]})"

        except ImportError:
            return _create_placeholder_llm(), "Placeholder (pip install anthropic for Claude)"
        except Exception as e:
            return _create_placeholder_llm(), f"Placeholder (API error: {e})"

    # Fallback to placeholder
    return _create_placeholder_llm(), "Demo mode (set ANTHROPIC_API_KEY for real AI)"


def _create_placeholder_llm() -> Callable:
    """Create placeholder LLM for testing without API key."""

    state = {"turn": 0}

    def placeholder(system: str = None, messages: list = None, prompt: str = None) -> str:
        """Placeholder that simulates conversation."""
        state["turn"] += 1

        # Get the last user message from messages or prompt
        last_user_msg = ""
        if messages:
            for msg in reversed(messages):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break
        if prompt:
            last_user_msg = prompt

        # Check for bootstrap intro stage
        if "what would you like me to call you" in (system or "").lower():
            return "Hey! I'm your Assist - think of me as a cognitive partner. What would you like me to call you?"

        # Check for bootstrap connect stage
        if "two things you're really into" in last_user_msg.lower() or "favorite things" in (system or "").lower():
            return "Nice to meet you! What are two things you're really into right now?"

        # After bootstrap - normal conversation
        if last_user_msg:
            preview = last_user_msg[:50] + "..." if len(last_user_msg) > 50 else last_user_msg
            return f"I hear you about '{preview}'. Tell me more about what's on your mind."

        return "What's on your mind?"

    return placeholder


def run_interactive(loop: LockedLoop, llm_status: str, config: Config):
    """Run interactive REPL session."""
    # Initialize session logger
    logs_dir = config.memory_dir.parent / "logs"
    logger = SessionLogger(logs_dir)
    logger.log_system(f"AI: {llm_status}")

    print("\n=== Locked System ===")
    print(f"AI: {llm_status}")
    print("-" * 40)
    print("Commands: 'state' | 'commit <goal>' | 'quit'")
    print("")

    # Generate natural greeting using the AI
    greeting = loop.generate_greeting()
    print(f"Assistant: {greeting}")
    logger.log_assistant(greeting)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit"]:
                print("\nGoodbye!")
                logger.log_system("User quit")
                logger.close()
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
                    logger.log_system(f"Commitment created: {frame}")
                else:
                    print("\n[Cannot create commitment in current stance]")
                continue

            if user_input.lower().startswith("emergency "):
                reason = user_input[10:].strip()
                if loop.trigger_emergency(reason):
                    print(f"\n[Emergency triggered: {reason}]")
                    logger.log_system(f"Emergency triggered: {reason}")
                else:
                    print("\n[Emergency on cooldown or failed]")
                continue

            # Log user input
            logger.log_user(user_input)

            # Process normal input
            result = loop.process(user_input)

            # Display response
            print(f"\nAssistant: {result.response}")

            # Log assistant response and metadata
            logger.log_assistant(result.response)
            logger.log_result(result)

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
            logger.log_system("Session interrupted")
            logger.close()
            break
        except Exception as e:
            print(f"\nError: {e}")
            logger.log_system(f"Error: {e}")


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
    parser.add_argument(
        "--system-prompt",
        type=str,
        help="Path to system prompt file"
    )

    args = parser.parse_args()

    # Load config
    if args.config:
        config = Config.from_yaml(args.config)
    else:
        config = Config()

    # Load system prompt if provided
    system_prompt = None
    if args.system_prompt:
        system_prompt = Path(args.system_prompt).read_text()
    elif config.system_prompt:
        # Config may have system_prompt path
        prompt_path = Path(config.system_prompt) if isinstance(config.system_prompt, str) else config.system_prompt
        if prompt_path and prompt_path.exists():
            system_prompt = prompt_path.read_text()

    # Create loop with LLM
    llm, llm_status = create_llm(config, system_prompt)
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
        run_interactive(loop, llm_status, config)


if __name__ == "__main__":
    main()
