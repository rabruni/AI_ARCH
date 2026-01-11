#!/usr/bin/env python3
"""The Assist - Entry Point (using locked_system framework)

This is the new entry point that uses locked_system as the core framework.
The Assist's personality, Intent model, and self-reflection are layered on top.

For legacy behavior, use main.py or main_hrm.py instead.

Architecture:
    locked_system (framework)
    └── The Assist (personality layer)
        ├── Donna/Pepper personality (prompts/system.md)
        ├── Intent model (hrm/intent.py)
        └── Custom formatting (core/formatter.py)
"""
import sys
import os
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from locked_system import LockedLoop, Config
from locked_system.cli.main import create_llm
from locked_system.cli.session_logger import SessionLogger

from the_assist.personality import (
    create_prompt_enhancer,
    PersonalityConfig,
)
from the_assist.personality.injector import get_personality_defaults
from the_assist.adapters.intent_to_commitment import create_intent_context_for_prompt
from the_assist.hrm.intent import IntentStore
from the_assist.core.formatter import (
    format_header, format_assist_message,
    format_system_message, format_divider, get_simple_prompt
)


class TheAssist:
    """
    The Assist - Built on locked_system.

    Combines:
    - locked_system's two-loop architecture
    - The Assist's Donna/Pepper personality
    - Intent-based authority model
    - Custom formatting
    """

    def __init__(self):
        # Paths
        self.base_dir = Path(__file__).parent
        self.prompts_dir = self.base_dir / "prompts"
        self.memory_dir = self.base_dir / "memory" / "locked"

        # Load personality
        self.personality_config = PersonalityConfig(
            system_prompt_path=self.prompts_dir / "system.md",
        )
        defaults = get_personality_defaults()

        # Intent store (The Assist's unique authority layer)
        self.intent = IntentStore()

        # Configure locked_system
        config = Config(
            memory_dir=self.memory_dir,
            system_prompt=self.prompts_dir / "system.md",
            bootstrap_greeting=defaults["intro_greeting"],
            bootstrap_connect_prompt=defaults["connect_prompt"],
        )

        # Create LLM with personality
        system_prompt = None
        if (self.prompts_dir / "system.md").exists():
            system_prompt = (self.prompts_dir / "system.md").read_text()

        llm, self.llm_status = create_llm(config, system_prompt)

        # Create prompt enhancer that injects intent context
        base_enhancer = create_prompt_enhancer(self.personality_config)

        def full_prompt_enhancer(prompt: str) -> str:
            """Enhance prompts with both personality and intent context."""
            intent_context = create_intent_context_for_prompt(self.intent)
            personality_enhanced = base_enhancer(prompt)
            return f"{intent_context}\n{personality_enhanced}"

        # Create locked loop with hooks
        self.loop = LockedLoop(
            config=config,
            llm_callable=llm,
            on_bootstrap_complete=self._on_bootstrap_complete,
            on_gate_transition=self._on_gate_transition,
            on_response_generated=self._on_response_generated,
            prompt_enhancer=full_prompt_enhancer,
        )

    def _on_bootstrap_complete(self, user_name: str):
        """Called when bootstrap completes."""
        pass

    def _on_gate_transition(self, gate: str, from_stance: str, to_stance: str):
        """Called on gate transitions."""
        pass

    def _on_response_generated(self, response: str, result):
        """Called after response generation."""
        pass

    def process(self, user_input: str) -> str:
        """Process user input through The Assist."""
        result = self.loop.process(user_input)
        return result.response

    def get_greeting(self) -> str:
        """Get opening greeting."""
        return self.loop.generate_greeting()

    def get_state(self) -> dict:
        """Get current state."""
        loop_state = self.loop.get_state()
        intent = self.intent.get_intent()
        return {
            **loop_state,
            "intent": {
                "north_stars": intent.north_stars,
                "success": intent.current_success,
                "stance": intent.stance,
                "non_goals": intent.non_goals,
            }
        }

    def get_intent_summary(self) -> dict:
        """Get intent summary."""
        intent = self.intent.get_intent()
        return {
            "north_stars": intent.north_stars,
            "success": intent.current_success,
            "stance": intent.stance,
            "non_goals": intent.non_goals,
        }

    def set_stance(self, stance: str):
        """Set current stance."""
        self.intent.set_stance(stance)

    def add_non_goal(self, non_goal: str):
        """Add a non-goal."""
        self.intent.add_non_goal(non_goal)

    def set_success(self, success: str):
        """Set success criteria."""
        self.intent.set_success(success)

    def end_session(self):
        """End the session."""
        pass


def print_help():
    """Print available commands."""
    print("""
Commands:
  quit, exit     - Exit
  intent         - Show current intent
  state          - Show full state
  stance [x]     - Set stance (partner|support|challenge)
  nongoal [x]    - Add a non-goal
  success [x]    - Set success criteria
  help           - Show this message

Otherwise, just talk naturally.
""")


def main():
    """Main entry point."""
    print()
    print(format_header("THE ASSIST", "locked_system powered | v2.0"))
    print()
    print("Type 'help' for commands, or just talk.")
    print(format_divider())
    print()

    # Initialize The Assist
    assist = TheAssist()

    # Show status
    print(format_system_message(f"AI: {assist.llm_status}", "info"))
    intent = assist.get_intent_summary()
    print(format_system_message(f"Stance: {intent['stance']} | North stars: {', '.join(intent['north_stars'][:2])}", "info"))
    print()

    # Get greeting
    greeting = assist.get_greeting()
    print(format_assist_message(greeting))

    # Initialize logger
    logs_dir = assist.base_dir / "logs"
    logger = SessionLogger(logs_dir)
    logger.log_system(f"AI: {assist.llm_status}")
    logger.log_assistant(greeting)

    try:
        while True:
            try:
                user_input = input(get_simple_prompt()).strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Commands
            if user_input.lower() in ('quit', 'exit', 'bye'):
                print()
                print(format_system_message("Ending session...", "info"))
                assist.end_session()
                logger.close()
                print(format_assist_message("Until next time."))
                break

            if user_input.lower() == 'help':
                print_help()
                continue

            if user_input.lower() == 'intent':
                intent = assist.get_intent_summary()
                print(f"\n[Intent]")
                print(f"  North stars: {', '.join(intent['north_stars'])}")
                print(f"  Success: {intent['success']}")
                print(f"  Stance: {intent['stance']}")
                print(f"  Non-goals: {', '.join(intent['non_goals'])}")
                print()
                continue

            if user_input.lower() == 'state':
                state = assist.get_state()
                import json
                print(f"\n[State]")
                print(json.dumps(state, indent=2, default=str))
                print()
                continue

            if user_input.lower().startswith('stance '):
                stance = user_input[7:].strip()
                try:
                    assist.set_stance(stance)
                    print(f"\n[Stance set to: {stance}]\n")
                except ValueError as e:
                    print(f"\n[Error: {e}]\n")
                continue

            if user_input.lower().startswith('nongoal '):
                nongoal = user_input[8:].strip()
                assist.add_non_goal(nongoal)
                print(f"\n[Added non-goal: {nongoal}]\n")
                continue

            if user_input.lower().startswith('success '):
                success = user_input[8:].strip()
                assist.set_success(success)
                print(f"\n[Success criteria updated]\n")
                continue

            # Log and process
            logger.log_user(user_input)

            response = assist.process(user_input)
            print()
            print(format_assist_message(response))

            logger.log_assistant(response)

    except KeyboardInterrupt:
        print("\n")
        print(format_system_message("Interrupted. Saving...", "warn"))
        assist.end_session()
        logger.close()
        print(format_assist_message("Saved. Goodbye."))


if __name__ == "__main__":
    main()
