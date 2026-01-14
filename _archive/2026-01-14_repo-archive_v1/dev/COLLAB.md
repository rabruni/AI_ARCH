# The Assist - Collaboration Memory

This file is read by Claude Code at session start to understand where we are.

## Current State

**Phase**: Early Prototype (Working)
**Last Session**: 2026-01-09

### What's Built
- [x] Core orchestrator with Claude API integration
- [x] Hierarchical memory system (north stars, context, conversations, patterns)
- [x] Entity memory (people, validated behaviors, preferences)
- [x] Feedback capture system (+1, -1, idea commands)
- [x] System prompt with Donna/Pepper principles
- [x] Date/time awareness in context
- [x] Memory curator agent (daily/weekly cleanup)
- [x] **Compressed memory v2** - 91% token reduction
- [x] **Proactive engine** - intuition-first interaction with reaction tracking
- [x] **Integrity system** - boot/shutdown checkpoints, hash verification, multi-agent ready
- [x] **Console formatter** - hierarchical numbering (1, 1.1, 1.1.1), chat-style output
- [x] **Session retrospective** - MBTI/Big 5 behavioral analysis at shutdown
- [x] **AI self-reflection** - performance analysis, outcome attribution (the mirror)

### Key Decisions Made
1. **AI-native architecture** - trust AI, verify outcomes, minimal scaffolding
2. **HRM layers** - L1 Moment → L2 Operations → L3 Strategy → L4 Identity
3. **Design for wrongness** - repair > prevent, learn from corrections
4. **Middle-out + evolutionary** - start with core loop, grow organically
5. **Donna Principle** - challenge with discretion, needed vs wanted
6. **Numbers over bullets** - user preference for structured lists
7. **Intuition-first interaction** - lead with what AI thinks, not questions
8. **No AI self-awareness meta-commentary** - don't explain AI limitations/behavior
9. **Dual analysis at shutdown** - user behavior + AI behavior = outcomes

### User Context
- ENTP baseline (see baseline.json)
- Has ADHD patterns, fast context-switching
- Tends to underestimate schedule, mental/actual calendar desync
- Responds well to structured breakdowns
- Open to being pushed/managed proactively
- Three main use cases: work management, patent filing, life balance

### Known People
- **Gaurav**: work colleague, recurring bottleneck for coordination
- **Stewart**: work colleague, dataset handoff
- **Bella**: daughter, cheer competitions

## Architecture Notes

```
the_assist/
├── main.py              # Entry point, all commands
├── config/
│   └── settings.py      # Config with dotenv loading
├── core/
│   ├── orchestrator.py  # Main brain, uses v2 memory
│   ├── memory.py        # v1 memory (conversation archival only)
│   ├── memory_v2.py     # v2 compressed memory (91% smaller)
│   ├── proactive.py     # Intuition-first interaction
│   ├── integrity.py     # Boot/shutdown, checkpoints, hashes
│   ├── formatter.py     # Console formatting, bullet→number
│   ├── retrospective.py # User behavioral analysis (MBTI, Big 5)
│   ├── ai_reflection.py # AI self-assessment (the mirror)
│   ├── entities.py      # People/behavior (legacy)
│   ├── feedback.py      # Feedback capture
│   └── curator.py       # Memory maintenance
├── prompts/
│   └── system.md        # System prompt
└── memory/
    └── store/
        ├── compressed/     # v2 state.json (primary)
        ├── curator/        # Curator state
        ├── retrospectives/ # User behavioral trends + baseline
        ├── ai_reflection/  # AI performance trends
        ├── integrity/      # Boot/shutdown state, version log
        ├── conversations/  # Archived conversations
        └── (legacy v1 dirs)
```

## Commands Available
- `quit/exit` - Save and exit (runs retrospective + AI reflection)
- `save` - Save conversation and continue
- `+1/-1 [note]` - Log what worked/didn't
- `idea [note]` - Log suggestion
- `feedback` - Show feedback summary
- `memory` - Show current memory state
- `clear [topic]` - Remove from active memory
- `status` - Show system integrity status
- `trends` - Show user behavioral trends
- `reflect` - Show AI performance trends
- `help` - Show commands

## Shutdown Analysis

At shutdown, two analyses run:

1. **User Retrospective** (`retrospective.py`)
   - Session quality (productive/moderate/scattered/stuck)
   - MBTI signals and shifts from baseline
   - Big 5 signals
   - Behavioral patterns (energy, focus, decision style)
   - Learnings for future sessions

2. **AI Self-Reflection** (`ai_reflection.py`)
   - Quality scores (conciseness, accuracy, actionability, tone_match, intuition_quality, memory_relevance, value_add, trust_building)
   - Outcome analysis (effectiveness, friction points, smooth moments)
   - Self-critique (what worked, what failed, missed opportunities)
   - Pattern detection (trust trajectory)
   - Improvement actions

Combined analysis enables: "User state + AI behavior = Outcome" pattern learning.

## Token Budget Awareness
- **V2 compressed memory**: ~338 tokens (was ~3,882 in v1 = 91% reduction)
- **Full context**: ~1,110 tokens (system prompt + memory)
- Memory format: `NORTH:|PRIO:|ACTIVE:|COMMITS:|PEOPLE:|PATTERNS:|COACHING:|PREFS:`
- AI expands codes at inference time
- Curator maintains via topic-prefix removal

## Interaction Learning (Coaching)

Coaching captures HOW the AI should behave (learned from user corrections):

| Code | Meaning |
|------|---------|
| ask_impact | Ask how tasks connect to strategies and north stars |
| strategic_questions | Ask bigger picture questions, not just tactical |
| connect_layers | Connect L2 tasks to L3 strategy to L4 identity |
| surface_why | Surface the 'why' behind tasks, not just status |
| challenge_alignment | Challenge when tasks don't align to priorities |
| push_harder | User wants more direct pushback |
| more_concise | Be more concise, less explanation |

Coaching is extracted from conversations when user teaches AI how to interact better.
Example context: `COACHING:ask_impact:Ask how tasks connect to strategies|strategic_questions:Ask bigger picture questions`

## Next Steps (Priority Order)
1. Test full shutdown analysis with real usage
2. Add combined insights command (`insights`?)
3. Consider calendar integration for schedule sync
4. Clean up legacy v1 files once v2 proven stable
5. Plan multi-agent architecture (curator, retrospective, reflection as agents)

---
*Updated by Claude Code - 2026-01-09*
