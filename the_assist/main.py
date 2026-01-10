#!/usr/bin/env python3
"""The Assist - Main Entry Point

Run this to start a conversation with The Assist.
"""
import sys
import os
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_assist.core.orchestrator import Orchestrator
from the_assist.core.feedback import log_feedback, get_feedback_summary, get_session_feedback
from the_assist.core.curator import MemoryCurator
from the_assist.core.memory_v2 import CompressedMemory
from the_assist.core.integrity import boot_or_warn, shutdown_safe, get_status, boot_or_warn_with_context, get_boot_context_for_ai
from the_assist.core.retrospective import run_retrospective, get_behavioral_summary
from the_assist.core.ai_reflection import AIReflection, analyze_session_complete
from the_assist.core.formatter import (
    format_header, format_user_message, format_assist_message,
    format_system_message, format_divider, get_simple_prompt,
    bullets_to_numbers
)


def print_help():
    """Print available commands."""
    print("""
Commands:
  quit, exit     - Save and exit
  save           - Save conversation and continue
  +1 [note]      - Log something that worked
  -1 [note]      - Log something that didn't work
  idea [note]    - Log a suggestion/idea
  feedback       - Show feedback summary
  memory         - Show current memory state
  clear [topic]  - Remove item from active memory
  status         - Show system integrity status
  trends         - Show behavioral trends (user)
  reflect        - Show AI performance trends
  help           - Show this message

Otherwise, just talk naturally.
""")


def handle_feedback_command(user_input: str, last_exchange: tuple) -> bool:
    """Handle feedback commands. Returns True if handled."""
    user_msg, ai_msg = last_exchange if last_exchange else (None, None)
    context = f"User: {user_msg}\nAssist: {ai_msg}" if user_msg else None

    if user_input.startswith('+1'):
        note = user_input[2:].strip() or "This worked well"
        log_feedback('worked', note, context)
        print("\n[Logged: worked] " + note + "\n")
        return True

    elif user_input.startswith('-1'):
        note = user_input[2:].strip() or "This didn't work"
        log_feedback('didnt_work', note, context)
        print("\n[Logged: didn't work] " + note + "\n")
        return True

    elif user_input.lower().startswith('idea '):
        note = user_input[5:].strip()
        log_feedback('suggestion', note, context)
        print("\n[Logged: idea] " + note + "\n")
        return True

    elif user_input.lower() == 'feedback':
        summary = get_feedback_summary()
        print(f"""
Feedback Summary:
  Total: {summary['total']}
  Worked: {summary['worked']}
  Didn't work: {summary['didnt_work']}
  Suggestions: {summary['suggestions']}

Recent:""")
        for f in summary['recent'][-5:]:
            print(f"  [{f['type']}] {f['note'][:50]}...")
        print()
        return True

    return False


def main():
    """Main conversation loop."""
    print()
    print(format_header("THE ASSIST", "Cognitive Anchor | v0.2"))

    # Boot sequence with integrity checks
    boot_success, boot_ctx = boot_or_warn_with_context()
    if not boot_success:
        print(format_system_message("Boot failed. Check errors above.", "error"))
        return

    status = get_status()
    print(format_system_message(f"Session #{status['session_count']}", "info"))
    print()
    print("Type 'help' for commands, or just talk.")
    print(format_divider())
    print()

    # Run memory curation on startup
    curator = MemoryCurator()
    insights = curator.run_if_needed()

    orchestrator = Orchestrator()
    session_start = datetime.now()  # Track for feedback correlation
    last_exchange = (None, None)
    exchange_count = 0  # Track for mid-session checkpoints

    # Surface any curator insights (brief, not intrusive)
    if insights:
        for insight in insights:
            print(format_system_message(insight, "info"))
        print()

    # Proactive opening - intuition-based, not generic
    opening = orchestrator.get_opening()
    print(format_assist_message(opening))

    try:
        while True:
            try:
                user_input = input(get_simple_prompt()).strip()
            except EOFError:
                break

            if not user_input:
                continue

            # Echo user input in formatted style (optional - comment out if too verbose)
            # print(format_user_message(user_input))

            # Check for commands
            if user_input.lower() in ('quit', 'exit', 'bye'):
                print()
                print(format_system_message("Saving and analyzing session...", "info"))

                # Run retrospective before ending session
                status = get_status()
                if len(orchestrator.conversation_history) >= 2:
                    retro = run_retrospective(
                        orchestrator.conversation_history,
                        status['session_count']
                    )
                    if not retro.get("skipped"):
                        quality = retro.get("session_quality", "unknown")
                        learnings = retro.get("learnings", [])
                        print(format_system_message(f"Session quality: {quality}", "info"))
                        if learnings:
                            print(format_system_message(f"Learned: {learnings[0][:50]}...", "info"))

                    # Run AI self-reflection (the mirror)
                    # Include explicit user feedback from this session
                    session_feedback = get_session_feedback(session_start)
                    reflector = AIReflection()
                    ai_retro = reflector.reflect_on_session(
                        orchestrator.conversation_history,
                        status['session_count'],
                        retro,
                        session_feedback
                    )
                    if not ai_retro.get("skipped"):
                        effectiveness = ai_retro.get("outcome_analysis", {}).get("overall_effectiveness", "unknown")
                        trust = ai_retro.get("pattern_detection", {}).get("trust_trajectory", "unknown")
                        print(format_system_message(f"AI effectiveness: {effectiveness} | Trust: {trust}", "info"))

                orchestrator.end_session()
                shutdown_safe()
                print(format_assist_message("Until next time."))
                break

            if user_input.lower() == 'save':
                orchestrator.end_session()
                print(format_system_message("Conversation saved. Continuing...", "success"))
                orchestrator = Orchestrator()
                continue

            if user_input.lower() == 'help':
                print_help()
                continue

            # Memory commands
            if user_input.lower() == 'memory':
                mem = CompressedMemory()
                state = mem.get_state()
                print("\n[Memory State]")
                print(f"Active ({len(state.get('active', []))}):")
                for a in state.get('active', [])[:8]:
                    print(f"  {a}")
                if len(state.get('active', [])) > 8:
                    print(f"  ...and {len(state.get('active', [])) - 8} more")
                print(f"\nCommits ({len(state.get('commits', []))}):")
                for c in state.get('commits', [])[:5]:
                    print(f"  {c}")
                print()
                continue

            if user_input.lower().startswith('clear '):
                topic = user_input[6:].strip()
                if topic:
                    mem = CompressedMemory()
                    state = mem.get_state()
                    before = len(state.get('active', []))
                    state['active'] = [a for a in state.get('active', []) if not a.startswith(topic)]
                    state['commits'] = [c for c in state.get('commits', []) if not c.startswith(topic)]
                    after = len(state.get('active', []))
                    mem._save(state)
                    print(f"\n[Cleared '{topic}' - removed {before - after} items]\n")
                continue

            if user_input.lower() == 'status':
                s = get_status()
                print(f"\n[System Status]")
                print(f"  Session: #{s['session_count']}")
                print(f"  Last boot: {s['last_boot']}")
                print(f"  Last shutdown: {s['last_shutdown']}")
                print(f"  Clean shutdown: {s['clean_shutdown']}")
                print(f"  Hash match: {s['hash_match']}")
                print()
                continue

            if user_input.lower() == 'trends':
                t = get_behavioral_summary()
                print(f"\n[Behavioral Trends]")
                print(f"  Sessions analyzed: {t['sessions_analyzed']}")
                print(f"  MBTI baseline: {t['mbti_baseline']}")
                print(f"  Avg corrections/session: {t['avg_corrections_per_session']}")
                print(f"  Correction trend: {t['correction_trend']}")
                if t['top_topics']:
                    print(f"  Top topics: {', '.join([x[0] for x in t['top_topics'][:3]])}")
                if t['recent_learnings']:
                    print(f"  Recent learnings:")
                    for l in t['recent_learnings'][:3]:
                        print(f"    - {l[:50]}...")
                print()
                continue

            if user_input.lower() == 'reflect':
                r = AIReflection().get_ai_performance_summary()
                print(f"\n[AI Performance]")
                print(f"  Sessions reflected: {r['sessions_reflected']}")
                print(f"  Overall avg quality: {r['overall_avg']}")
                print(f"  Trend: {r['trend_direction']}")
                if r['avg_quality_scores']:
                    print(f"  Quality scores:")
                    for dim, score in r['avg_quality_scores'].items():
                        if score is not None:
                            print(f"    {dim}: {score}")
                if r['recent_failures']:
                    print(f"  Recent failures:")
                    for f in r['recent_failures']:
                        print(f"    - {f[:50]}...")
                if r['recent_strengths']:
                    print(f"  Recent strengths:")
                    for s in r['recent_strengths']:
                        print(f"    - {s[:50]}...")
                if r['outcome_patterns']:
                    print(f"  Outcome patterns: {r['outcome_patterns']}")
                print()
                continue

            # Handle feedback commands
            if handle_feedback_command(user_input, last_exchange):
                continue

            # Get response
            response = orchestrator.chat(user_input)
            print()
            print(format_assist_message(response))

            # Track for feedback context
            last_exchange = (user_input, response)
            exchange_count += 1

            # Mid-session checkpoint every 10 exchanges
            if exchange_count > 0 and exchange_count % 10 == 0:
                # Run lightweight reflection
                mem = CompressedMemory()
                removed = mem.dedupe_all()
                if removed > 0:
                    print(format_system_message(f"Memory cleaned: {removed} duplicates removed", "info"))

                # Check session health
                if len(orchestrator.conversation_history) >= 10:
                    print(format_system_message(f"Checkpoint: {exchange_count} exchanges", "info"))

            # Background memory processing
            orchestrator.process_for_memory(user_input, response)

    except KeyboardInterrupt:
        print("\n")
        print(format_system_message("Interrupted. Saving...", "warn"))

        # Still run retrospective on interrupt if we have conversation
        status = get_status()
        if len(orchestrator.conversation_history) >= 2:
            retro = run_retrospective(
                orchestrator.conversation_history,
                status['session_count']
            )
            # Run AI reflection too
            if not retro.get("skipped"):
                reflector = AIReflection()
                reflector.reflect_on_session(
                    orchestrator.conversation_history,
                    status['session_count'],
                    retro
                )

        orchestrator.end_session()
        shutdown_safe()
        print(format_assist_message("Saved. Goodbye."))


if __name__ == "__main__":
    main()
