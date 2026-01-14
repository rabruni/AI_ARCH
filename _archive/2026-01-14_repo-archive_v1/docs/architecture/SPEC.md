# The Assist - Minimal Spec v0.1

## Vision

A cognitive anchor - not a task manager, not an assistant. External executive function support for a fast-moving, context-switching mind.

## Core Principles

### 1. AI-Native Architecture
- Trust AI to understand, organize, and adapt
- Verify outcomes, not process
- Minimal structure, maximum intelligence

### 2. Donna/Pepper Principle
- Challenge with discretion
- Know what's NEEDED vs what's WANTED
- Earn trust through competence

### 3. HRM (Hierarchical Reasoning Model)
- L1 Moment: This conversation
- L2 Operations: Today/this week
- L3 Strategy: Current priorities
- L4 Identity: North stars

### 4. Design for Wrongness
- Expect mistakes
- Repair > prevent
- Learn from corrections

## MVP Scope (This Version)

### Included
- [x] Conversational interface
- [x] System prompt with principles
- [x] Simple file-based memory
- [x] North stars storage
- [x] Context tracking
- [x] Conversation history
- [x] AI-driven memory extraction

### Deferred
- [ ] Proactive alerts
- [ ] Voice input
- [ ] Calendar/email integration
- [ ] Multi-agent architecture
- [ ] Vector search for memory
- [ ] Self-modifying memory structure

## Usage

```bash
# Setup
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"

# Run
python the_assist/main.py
```

## File Structure

```
the_assist/
├── main.py              # Entry point
├── core/
│   ├── orchestrator.py  # Main brain
│   └── memory.py        # Memory system
├── config/
│   └── settings.py      # Configuration
├── prompts/
│   └── system.md        # System prompt
├── memory/
│   └── store/           # Persistent memory
└── logs/                # Conversation logs
```

## Next Steps (Post-MVP)

1. Use it daily for 1-2 weeks
2. Note what's working / not working
3. Let patterns reveal what to build next
4. AI suggests improvements based on usage

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Model | Claude Sonnet | Balance of capability + cost |
| Memory | JSON files | Simple, inspectable, evolvable |
| Interface | Terminal | Fast to build, low friction |
| Architecture | Single orchestrator | Start simple, split when needed |
