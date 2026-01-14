#!/usr/bin/env python3
"""Review feedback and iterate on The Assist.

Run this to see what's working, what's not, and get AI suggestions for improvements.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from the_assist.core.feedback import get_feedback_summary, FEEDBACK_FILE


def main():
    print("\n" + "="*50)
    print("  THE ASSIST - FEEDBACK REVIEW")
    print("="*50 + "\n")

    # Load full feedback
    if not os.path.exists(FEEDBACK_FILE):
        print("No feedback yet. Use the assistant and log feedback with:")
        print("  +1 [note]  - something worked")
        print("  -1 [note]  - something didn't work")
        print("  idea [note] - suggestion for improvement")
        return

    with open(FEEDBACK_FILE, 'r') as f:
        data = json.load(f)

    feedback = data.get('feedback', [])
    if not feedback:
        print("No feedback logged yet.")
        return

    # Summary
    summary = get_feedback_summary()
    print(f"Total feedback: {summary['total']}")
    print(f"  Worked: {summary['worked']}")
    print(f"  Didn't work: {summary['didnt_work']}")
    print(f"  Ideas: {summary['suggestions']}")
    print()

    # What didn't work (most important for iteration)
    didnt_work = [f for f in feedback if f['type'] == 'didnt_work']
    if didnt_work:
        print("-" * 50)
        print("WHAT DIDN'T WORK (prioritize fixing these):")
        print("-" * 50)
        for f in didnt_work:
            print(f"\n[{f['timestamp'][:10]}] {f['note']}")
            if f.get('context'):
                print(f"  Context: {f['context'][:100]}...")
        print()

    # Ideas
    ideas = [f for f in feedback if f['type'] == 'suggestion']
    if ideas:
        print("-" * 50)
        print("IDEAS FOR IMPROVEMENT:")
        print("-" * 50)
        for f in ideas:
            print(f"\n[{f['timestamp'][:10]}] {f['note']}")
        print()

    # What worked (reinforce these patterns)
    worked = [f for f in feedback if f['type'] == 'worked']
    if worked:
        print("-" * 50)
        print("WHAT WORKED (keep doing these):")
        print("-" * 50)
        for f in worked[-5:]:  # Last 5
            print(f"\n[{f['timestamp'][:10]}] {f['note']}")
        print()

    print("-" * 50)
    print("NEXT STEPS:")
    print("-" * 50)
    print("""
1. Review 'didn't work' items - these are iteration priorities
2. Decide which to fix first (quick wins vs important)
3. Update system prompt or code as needed
4. Test and get more feedback

Files to modify:
  - the_assist/prompts/system.md  (behavior/personality)
  - the_assist/core/orchestrator.py  (logic)
  - the_assist/core/memory.py  (what it remembers)
""")


if __name__ == "__main__":
    main()
