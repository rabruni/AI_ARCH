#!/usr/bin/env python3
"""The Assist - HRM Entry Point

True Hierarchical Reasoning Model implementation.

Four layers, clean separation:
- L1 Intent: Define success, hold authority
- L2 Planner: Choose approach, manage tradeoffs
- L3 Executor: Do the work, report state
- L4 Evaluator: Compare to intent, trigger revision
"""
import sys
import os
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_assist.hrm import HRMLoop
from the_assist.core.formatter import (
    format_header, format_assist_message,
    format_system_message, format_divider, get_simple_prompt
)


def print_help():
    """Print available commands."""
    print("""
Commands:
  quit, exit     - Save and exit
  intent         - Show current intent (L1)
  plan           - Show current plan (L2)
  eval           - Show last evaluation (L4)
  patterns       - Show evaluation patterns
  stance [x]     - Set stance (partner|support|challenge)
  nongoal [x]    - Add a non-goal
  success [x]    - Set success criteria
  unblock [x]    - Remove topic from blocked list
  help           - Show this message

Otherwise, just talk naturally.
""")


def main():
    """Main conversation loop with HRM architecture."""
    print()
    print(format_header("THE ASSIST", "HRM Architecture | v0.3"))
    print()
    print("Type 'help' for commands, or just talk.")
    print(format_divider())
    print()

    # Initialize HRM loop
    hrm = HRMLoop()

    # Show current intent
    intent = hrm.get_intent_summary()
    print(format_system_message(f"Stance: {intent['stance']} | North stars: {', '.join(intent['north_stars'][:2])}", "info"))
    print()

    # Opening
    opening = hrm.get_opening()
    print(format_assist_message(opening))

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
                hrm.end_session()
                print(format_assist_message("Until next time."))
                break

            if user_input.lower() == 'help':
                print_help()
                continue

            if user_input.lower() == 'intent':
                intent = hrm.get_intent_summary()
                print(f"\n[Intent (L1)]")
                print(f"  North stars: {', '.join(intent['north_stars'])}")
                print(f"  Success: {intent['success']}")
                print(f"  Stance: {intent['stance']}")
                print(f"  Non-goals: {', '.join(intent['non_goals'])}")
                print()
                continue

            if user_input.lower() == 'plan':
                plan = hrm.get_current_plan()
                if plan:
                    print(f"\n[Current Plan (L2)]")
                    print(f"  Approach: {plan.approach}")
                    print(f"  Altitude: {plan.altitude}")
                    print(f"  Stance: {plan.stance}")
                    print(f"  Focus: {', '.join(plan.focus)}")
                    print(f"  Constraints: {', '.join(plan.constraints)}")
                    print(f"  Blocked: {', '.join(plan.blocked_topics) if plan.blocked_topics else 'none'}")
                    if plan.revision_reason:
                        print(f"  Revision reason: {plan.revision_reason}")
                else:
                    print("\n[No plan yet]")
                print()
                continue

            if user_input.lower() == 'eval':
                evaluation = hrm.get_last_evaluation()
                if evaluation:
                    print(f"\n[Last Evaluation (L4)]")
                    print(f"  Matched intent: {evaluation.matched_intent}")
                    print(f"  Severity: {evaluation.severity}")
                    print(f"  Issue: {evaluation.issue or 'none'}")
                    print(f"  Revision needed: {evaluation.revision_needed}")
                    print(f"  Recommendation: {evaluation.recommendation}")
                else:
                    print("\n[No evaluation yet]")
                print()
                continue

            if user_input.lower() == 'patterns':
                patterns = hrm.get_evaluation_patterns()
                print(f"\n[Evaluation Patterns]")
                print(f"  Repeated issues: {patterns.get('repeated_issues', [])[-3:]}")
                print(f"  Successful approaches: {patterns.get('successful_approaches', [])[-3:]}")
                print()
                continue

            if user_input.lower().startswith('stance '):
                stance = user_input[7:].strip()
                try:
                    hrm.set_stance(stance)
                    print(f"\n[Stance set to: {stance}]\n")
                except ValueError as e:
                    print(f"\n[Error: {e}]\n")
                continue

            if user_input.lower().startswith('nongoal '):
                nongoal = user_input[8:].strip()
                hrm.add_non_goal(nongoal)
                print(f"\n[Added non-goal: {nongoal}]\n")
                continue

            if user_input.lower().startswith('success '):
                success = user_input[8:].strip()
                hrm.set_success(success)
                print(f"\n[Success criteria updated]\n")
                continue

            if user_input.lower().startswith('unblock '):
                topic = user_input[8:].strip()
                hrm.clear_blocked_topic(topic)
                print(f"\n[Unblocked: {topic}]\n")
                continue

            # Process through HRM loop
            response = hrm.process(user_input)
            print()
            print(format_assist_message(response))

    except KeyboardInterrupt:
        print("\n")
        print(format_system_message("Interrupted. Saving...", "warn"))
        hrm.end_session()
        print(format_assist_message("Saved. Goodbye."))


if __name__ == "__main__":
    main()
