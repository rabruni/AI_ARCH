# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**The Assist** is a cognitive anchor system implementing HRM (Hierarchical Reasoning Model) - a framework for AI agents that separates intent, planning, execution, and evaluation into distinct layers with stable interfaces.

The project has two entry points:
- `the_assist/main_hrm.py` - **Current**: True HRM implementation with four-layer architecture
- `the_assist/main.py` - **Legacy**: Multi-agent orchestrator (kept for comparison)

## Commands

```bash
# Setup
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"

# Run HRM (primary)
python the_assist/main_hrm.py

# Run legacy orchestrator
python the_assist/main.py

# Test altitude governance
python test_l2_fastlane.py
```

## HRM Architecture

The HRM framework enforces separation of reasoning at different altitudes. Located in `the_assist/hrm/`:

```
L1 Intent (intent.py)     → Tiny, stable, HIGH AUTHORITY. Defines success, non-goals, stop conditions.
L2 Planner (planner.py)   → Fresh context (Chinese wall). Takes intent + situation → outputs plan.
L3 Executor (executor.py) → Conversation context (ephemeral). Does work, reports STATE not meaning.
L4 Evaluator (evaluator.py) → Fresh context. Compares outcome to intent, triggers revision UP.
```

**Key principle**: State flows UP, meaning flows DOWN.

### Memory Types by Layer

| Layer | File | Characteristics |
|-------|------|-----------------|
| Intent | `intent.json` | <50 lines, stable, rarely changes, high authority |
| Planner | `plans.json` | Semi-stable, rewritable per session |
| Executor | conversation | Ephemeral, cleared after session |
| Evaluator | `evaluations.json` | Delta-based, time-bounded |

### Altitude Governance

Reusable component (`altitude.py`) enforcing reasoning levels:
- L4 (Identity) - Always accessible
- L3 (Strategy) - Requires L4 connection
- L2 (Operations) - Requires L3 established
- Cannot skip levels

```python
from hrm.altitude import AltitudeGovernor
gov = AltitudeGovernor()
gov.detect_level("What are my tasks?")  # -> L2
gov.can_descend("L3", "L2")             # -> ValidationResult
```

## Design Principles

1. **Intent has authority** - If any layer conflicts with intent, intent wins
2. **Layers don't leak** - Executor never modifies intent, Evaluator never executes
3. **Revision is cheap** - Changing plan doesn't require changing intent
4. **Each layer has isolated context** - Fresh API calls for Planner and Evaluator (Chinese walls)
5. **Design for wrongness** - Expect mistakes, repair > prevent, learn from corrections

## Session Continuity

- Read `SESSION_HANDOFF.md` for current project state and next steps
- Update `the_assist/docs/LEARNINGS.md` with session patterns
- Intent (L1) persists across sessions; conversation is ephemeral
