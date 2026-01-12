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

        # Respond based on user message
        if last_user_msg:
            preview = last_user_msg[:50] + "..." if len(last_user_msg) > 50 else last_user_msg
            return f"I hear you about '{preview}'. Tell me more about what's on your mind."

        return "What's on your mind?"

    return placeholder


def run_interactive(loop: LockedLoop, llm_status: str, config: Config, debug_mode: bool = False):
    """Run interactive REPL session with iMessage-style chat UI."""
    from locked_system.cli.chat_ui import ChatUI
    from locked_system.memory.consent import format_consent_prompt, format_consent_status

    # Initialize session logger
    logs_dir = config.memory_dir.parent / "logs"
    logger = SessionLogger(logs_dir)
    logger.log_system(f"AI: {llm_status}")

    # Initialize chat UI
    history_file = config.memory_dir / ".chat_history"
    ui = ChatUI(history_file)

    # Show header
    subtitle = f"{llm_status} | DEBUG MODE" if debug_mode else llm_status
    ui.print_header("Locked System", subtitle)

    # Check for consent on first run
    if loop.needs_consent():
        print(format_consent_prompt())
        choice = input(" > ").strip().lower()

        if choice == 'none':
            loop.grant_consent(False, False, False)
            ui.print_system_message("Memory disabled. Nothing will be saved.")
        elif choice == 'all':
            loop.grant_consent(True, True, True)
            ui.print_system_message("All memory enabled.")
        else:
            # Parse individual choices
            conv = '1' in choice
            signals = '2' in choice
            prefs = '3' in choice
            loop.grant_consent(conv, signals, prefs)
            enabled = []
            if conv: enabled.append("conversation")
            if signals: enabled.append("signals")
            if prefs: enabled.append("preferences")
            if enabled:
                ui.print_system_message(f"Enabled: {', '.join(enabled)}")
            else:
                ui.print_system_message("Memory disabled.")
        print()

    ui.print_help()

    # Show initial state in debug mode
    if debug_mode:
        ui.print_debug_panel(loop.get_state())

    while True:
        try:
            user_input = ui.get_input()

            if not user_input:
                continue

            # Vim-style commands (start with :)
            if user_input.startswith(":"):
                cmd = user_input[1:].strip().lower()  # Remove : prefix

                if cmd in ["q", "quit", "exit"]:
                    # Clear the input line
                    print(f"\033[A\033[K", end="")
                    ui.print_system_message("Goodbye!")
                    logger.log_system("User quit")
                    logger.close()
                    ui.cleanup()
                    break

                if cmd in ["h", "help"]:
                    print(f"\033[A\033[K", end="")
                    ui.print_help()
                    continue

                if cmd in ["c", "clear"]:
                    ui.clear_screen()
                    header_subtitle = f"{llm_status} | DEBUG MODE" if debug_mode else llm_status
                    ui.print_header("Locked System", header_subtitle)
                    continue

                if cmd in ["s", "state"]:
                    print(f"\033[A\033[K", end="")
                    state = loop.get_state()
                    ui.print_system_message("Current State")
                    print(json.dumps(state, indent=2, default=str))
                    continue

                if cmd.startswith("commit "):
                    print(f"\033[A\033[K", end="")
                    frame = cmd[7:].strip()
                    if loop.create_commitment(frame):
                        ui.print_success(f"Commitment created: {frame}")
                        logger.log_system(f"Commitment created: {frame}")
                    else:
                        ui.print_error("Cannot create commitment in current stance")
                    continue

                if cmd.startswith("e ") or cmd.startswith("emergency "):
                    print(f"\033[A\033[K", end="")
                    reason = cmd.split(" ", 1)[1].strip() if " " in cmd else ""
                    if reason and loop.trigger_emergency(reason):
                        ui.print_system_message(f"Emergency triggered: {reason}")
                        logger.log_system(f"Emergency triggered: {reason}")
                    else:
                        ui.print_error("Emergency failed or no reason given")
                    continue

                # Notes commands
                if cmd in ["n", "notes"]:
                    print(f"\033[A\033[K", end="")
                    notes = loop.note_capture.get_notes_formatted(n=10)
                    ui.print_notes(notes, "Recent Notes (all)")
                    continue

                if cmd in ["nd", "notes dev", "notes developer"]:
                    print(f"\033[A\033[K", end="")
                    from locked_system.capabilities.note_capture import NoteType
                    notes = loop.note_capture.get_notes_formatted(NoteType.DEVELOPER, n=10)
                    ui.print_notes(notes, "Developer Notes")
                    continue

                if cmd in ["np", "notes personal"]:
                    print(f"\033[A\033[K", end="")
                    from locked_system.capabilities.note_capture import NoteType
                    notes = loop.note_capture.get_notes_formatted(NoteType.PERSONAL, n=10)
                    ui.print_notes(notes, "Personal Notes")
                    continue

                if cmd in ["t", "trust"]:
                    print(f"\033[A\033[K", end="")
                    print(loop.get_trust_panel())
                    continue

                if cmd in ["l", "learn", "learning"]:
                    print(f"\033[A\033[K", end="")
                    print(loop.get_learning_panel())
                    continue

                if cmd in ["sig", "signals"]:
                    print(f"\033[A\033[K", end="")
                    print(loop.get_signals_panel())
                    continue

                if cmd in ["m", "memory"]:
                    print(f"\033[A\033[K", end="")
                    consent = loop.get_consent_summary()
                    print("\nMEMORY CONSENT STATUS\n")
                    if consent.get('status') == 'configured':
                        print(f"  Conversation history:  {'✓ enabled' if consent.get('conversation_history') else '✗ disabled'}")
                        print(f"  Interaction signals:   {'✓ enabled' if consent.get('interaction_signals') else '✗ disabled'}")
                        print(f"  Learned preferences:   {'✓ enabled' if consent.get('learned_preferences') else '✗ disabled'}")
                        if consent.get('first_consent_at'):
                            print(f"\n  First consent: {consent['first_consent_at'][:10]}")
                    else:
                        print("  No consent preferences configured")
                    print("\n  Use :memory clear to clear all stored data")
                    print("  Use :memory reset to reconfigure consent")
                    continue

                if cmd == "memory clear":
                    print(f"\033[A\033[K", end="")
                    loop.clear_conversation()
                    ui.print_success("Cleared conversation history")
                    logger.log_system("Memory cleared by user")
                    continue

                if cmd == "memory reset":
                    print(f"\033[A\033[K", end="")
                    loop.revoke_consent()
                    ui.print_system_message("Consent reset. Restart to reconfigure.")
                    logger.log_system("Consent reset by user")
                    continue

                # Unknown command
                print(f"\033[A\033[K", end="")
                ui.print_error(f"Unknown command: {cmd}")
                continue

            # Display user message
            ui.print_user_message(user_input)

            # Log user input
            logger.log_user(user_input)

            # Process normal input
            result = loop.process(user_input)

            # Display assistant response with signal status strip
            signal_strip = loop.get_signal_display(compact=True)
            ui.print_assistant_message(result.response, signal_strip=signal_strip)

            # Show gate transitions if any
            if result.gate_transitions:
                ui.print_gate_transition(result.gate_transitions)

            # Show debug panel after each response
            if debug_mode:
                ui.print_debug_panel(loop.get_state())

            # Log assistant response and metadata
            logger.log_assistant(result.response)
            logger.log_result(result)

        except KeyboardInterrupt:
            print()
            ui.print_system_message("Interrupted. Goodbye!")
            logger.log_system("Session interrupted")
            logger.close()
            ui.cleanup()
            break
        except Exception as e:
            ui.print_error(str(e))
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
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode (shows full system state)"
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
                "gate_transitions": result.gate_transitions
            }
            print(json.dumps(output, indent=2))
        else:
            print(result.response)
    else:
        run_interactive(loop, llm_status, config, debug_mode=args.debug)


if __name__ == "__main__":
    main()
