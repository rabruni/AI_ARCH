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
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class SessionLogger:
    """Logs conversation to date-stamped file."""

    def __init__(self, logs_dir: Path):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create date-stamped filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.logs_dir / f"{timestamp}.log"

        # Write header
        self._write(f"=== Locked System Session ===")
        self._write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write("=" * 40 + "\n")

    def _write(self, text: str):
        """Append text to log file."""
        with open(self.log_file, "a") as f:
            f.write(text + "\n")

    def log_system(self, message: str):
        """Log system message."""
        self._write(f"[SYSTEM] {message}")

    def log_assistant(self, message: str, metadata: dict = None):
        """Log assistant message."""
        self._write(f"\nAssistant: {message}")
        if metadata:
            self._write(f"  [{metadata}]")

    def log_user(self, message: str):
        """Log user message."""
        self._write(f"\nYou: {message}")

    def log_result(self, result):
        """Log LoopResult metadata."""
        meta = f"Turn {result.turn_number} | Stance: {result.stance} | Altitude: {result.altitude} | Health: {result.quality_health}"
        self._write(f"  [{meta}]")
        if result.bootstrap_active:
            self._write("  [Bootstrap mode active]")
        if result.gate_transitions:
            self._write(f"  [Gate transitions: {', '.join(result.gate_transitions)}]")

    def close(self):
        """Write session end."""
        self._write("\n" + "=" * 40)
        self._write(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write("=== Session Complete ===")

# Load .env file from project root (same as the_assist)
try:
    from dotenv import load_dotenv
    PROJECT_ROOT = Path(__file__).parent.parent
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # dotenv not installed, rely on environment variables

from locked_system.config import Config
from locked_system.loop import LockedLoop, LoopResult


def create_llm(config: Config) -> tuple[callable, str]:
    """
    Create LLM callable - uses Claude if API key available, otherwise placeholder.

    Returns (llm_callable, status_message) for display.
    """
    # Try to use Claude if API key is set
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic()

            def claude_llm(prompt: str) -> str:
                """Call Claude API with proper message format."""
                # Split system instructions from user content if present
                if "User message:" in prompt or "What they just said:" in prompt:
                    # This is a structured prompt - use system message
                    response = client.messages.create(
                        model=config.model,
                        max_tokens=config.max_tokens,
                        system="You are a thoughtful, warm assistant. Be genuine and human.",
                        messages=[{"role": "user", "content": prompt}]
                    )
                else:
                    response = client.messages.create(
                        model=config.model,
                        max_tokens=config.max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                return response.content[0].text

            return claude_llm, f"Claude ({config.model.split('-')[1]})"

        except ImportError:
            return _create_placeholder_llm(), "Placeholder (pip install anthropic for Claude)"
        except Exception as e:
            return _create_placeholder_llm(), f"Placeholder (API error: {e})"

    # Fallback to placeholder
    return _create_placeholder_llm(), "Demo mode (set ANTHROPIC_API_KEY for real AI)"


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

        # Handle Bootstrap conversation (new format from _handle_bootstrap)
        if "What they just said:" in prompt:
            # Extract what they said
            match = re.search(r'What they just said: "([^"]+)"', prompt)
            user_said = match.group(1) if match else ""

            # Extract the question to lead into
            next_q_match = re.search(r'Question to naturally lead into: "([^"]+)"', prompt)
            next_question = next_q_match.group(1) if next_q_match else ""

            # Extract hook if present
            hook_match = re.search(r'Identity-affirming hook to incorporate: "([^"]+)"', prompt)
            hook = hook_match.group(1) if hook_match else ""

            state["turn"] += 1

            # Build natural response
            if hook:
                return f"{hook} {next_question}" if next_question else hook
            elif next_question:
                return f"I hear you. {next_question}"
            else:
                return "Thanks for sharing that. What else is on your mind?"

        # Handle regular executor prompts
        if "User message:" in prompt:
            match = re.search(r'User message: (.+?)(?:\n|$)', prompt)
            user_msg = match.group(1).strip() if match else ""
            return f"I hear what you're saying about {user_msg[:40]}. Tell me more."

        return "I'm listening. What's on your mind?"

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

    args = parser.parse_args()

    # Load config
    if args.config:
        config = Config.from_yaml(args.config)
    else:
        config = Config()

    # Create loop with LLM (Claude if API key set, otherwise placeholder)
    llm, llm_status = create_llm(config)
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
