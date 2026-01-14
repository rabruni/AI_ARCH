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

## Architecture Evolution

The current `the_assist/hrm/` is being replaced by the **Locked System** architecture:
- See `the_assist/docs/LOCKED_SYSTEM.md` for the canonical design
- Two loops: Slow (authority) + Fast (execution)
- Four components: Commitment, Stance, HRM, Memory
- Key invariant: Evaluators propose only, never decide

## Session Continuity

- Read `SESSION_HANDOFF.md` for current project state and next steps
- Update `the_assist/docs/LEARNINGS.md` with session patterns
- Commitment persists via leases; conversation is ephemeral

## CRITICAL: Context Compaction Recovery

If you see "This session is being continued from a previous conversation":

**STOP. DO NOT PROCEED BASED ON SUMMARY ALONE.**

1. **READ THESE FILES FIRST:**
   - `DECISIONS.md` - All design decisions
   - `BUILD_PROCESS.md` - Build instructions and file locations
   - `capabilities_v2.csv` - Component inventory with EXACT locations

2. **VERIFY WITH USER:**
   - "What milestone are we on?"
   - "What was the last completed work?"

3. **CHECK FILE LOCATIONS:**
   - Reasoning HRM goes in `the_assist/reasoning/` NOT `locked_system/core/`
   - Learning HRM goes in `the_assist/learning/` NOT `locked_system/core/`
   - Memory Bus goes in `shared/memory/` NOT `locked_system/core/`

**Background:** 12 hours of work was nearly lost because an agent after context compaction built modules in wrong locations without reading the specs. Don't repeat this mistake.

## Canonical Spec Files

| File | Purpose | Authority |
|------|---------|-----------|
| `DECISIONS.md` | All design decisions | HIGHEST - read first |
| `BUILD_PROCESS.md` | Build instructions | Required before implementation |
| `DOPEJAR_ARCHITECTURE.md` | System architecture | Design reference |
| `capabilities_v2.csv` | File locations | EXACT paths for all files |
| `HRM_INTERFACE_SPECS.md` | API contracts | Interface definitions |
| `IMPLEMENTATION_ORDER.md` | Build sequence | Milestone order |

## Conventions

### run.sh Files (ALWAYS DO THIS)

Every runnable application MUST have a `run.sh` at its root. When creating or modifying entry points:

1. **Always update `run.sh`** - User starts apps via `./run.sh`, never raw python commands
2. **Root run.sh** (`/run.sh`) - Master launcher with options for all apps
3. **Package run.sh** (`/locked_system/run.sh`, etc.) - Package-specific launcher

```bash
# User always runs:
./run.sh              # Default (frontdoor demo)
./run.sh assist       # The Assist HRM
./run.sh locked       # Locked System CLI
./run.sh test         # Run tests
```

When adding a new entry point:
- Add option to root `run.sh`
- Create package-level `run.sh` if needed
- Update help text in both
