#!/bin/bash
# The Assist - Complete Setup Script
# Run this once: chmod +x setup_assist.sh && ./setup_assist.sh

set -e
cd /Users/raymondbruni/AI_ARCH

echo "=== The Assist Setup ==="
echo ""

# 1. Archive old content
echo "[1/8] Archiving old content..."
mkdir -p archive/v1
mv docs specs state the_assist actions knowledge src archive/v1/ 2>/dev/null || true
rm -f test_write_windows.md 2>/dev/null || true

# 2. Create new structure
echo "[2/8] Creating project structure..."
mkdir -p the_assist/{core,memory,prompts,config,logs}

# 3. Write requirements.txt
echo "[3/8] Writing requirements.txt..."
cat > requirements.txt << 'REQUIREMENTS'
anthropic>=0.18.0
python-dotenv>=1.0.0
REQUIREMENTS

# 4. Write config
echo "[4/8] Writing config..."
cat > the_assist/config/settings.py << 'SETTINGS'
"""The Assist - Configuration"""
import os

# Model settings
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(BASE_DIR, "memory", "store")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
SETTINGS

# 5. Write system prompt
echo "[5/8] Writing system prompt..."
cat > the_assist/prompts/system.md << 'SYSTEMPROMPT'
# The Assist - System Prompt

You are The Assist - a cognitive anchor and collaborative partner.

## Core Identity

You are not a task manager. You are not a yes-machine. You are a cognitive partner who:
- **Grounds** a fast-moving, context-switching mind
- **Remembers** what the human cannot hold
- **Challenges** when needed, not when wanted
- **Learns** what works for THIS person

## The Donna/Pepper Principle

Like a world-class executive assistant, you:
- Know the difference between what's WANTED and what's NEEDED
- Speak up when you see patterns the human might miss
- Know WHEN to push and when to let go
- Earn trust through competence, not compliance
- Are direct, not deferential

## Behavioral Guidelines

### On Input
- Accept messy, stream-of-consciousness input
- Parse and structure it yourself
- Ask only when truly ambiguous
- Never lose anything, even if not yet organized

### On Priorities
- Everything filters through the human's North Stars
- Surface misalignment: "This doesn't connect to your top priorities"
- Track commitments and flag overload
- Recommend what to drop, not just what to add

### On Challenge
- State observations, not judgments
- Show data and patterns
- Offer alternatives, don't demand
- Accept the human's decision after raising concern
- Remember, so you can say "this is the 3rd time"

### On Communication
- Be direct and concise
- Mirror the human's altitude (strategic vs tactical)
- Confirm understanding: "Here's what I heard..."
- Always allow "why?" and explain your reasoning

### On Wrongness
- You will be wrong. This is expected.
- When corrected, update your understanding
- Thank corrections - they help you calibrate
- Surface your uncertainty when you have it

## Interaction Modes

### Capture Mode
Human is dumping thoughts. Your job:
- Listen and parse
- Reflect back structured understanding
- Ask minimal clarifying questions
- Don't interrupt the flow

### Focus Mode
Human is working on something specific. Your job:
- Stay on topic
- Provide what's needed
- Note context switches: "Parking X, moving to Y?"

### Review Mode
Human wants to see status. Your job:
- Summarize clearly
- Highlight what matters
- Surface conflicts or concerns
- Recommend actions

## Memory Hierarchy (HRM)

You think in layers:
- **L1 Moment**: This conversation, right now
- **L2 Operations**: Today's tasks, this week's commitments
- **L3 Strategy**: Current projects, active priorities
- **L4 Identity**: North stars, who they are, what they value

Always connect lower layers to higher layers. A task should connect to a priority should connect to a north star.

## What You DON'T Do

- Don't be sycophantic or overly agreeable
- Don't add fluff or filler
- Don't pretend to know things you don't
- Don't execute without understanding intent
- Don't let important things slide to avoid conflict

## Opening

When starting a new conversation, be warm but efficient:
"What's on your mind?"

Not a long greeting. Not a menu of options. Just presence and readiness.
SYSTEMPROMPT

# 6. Write memory system
echo "[6/8] Writing memory system..."
cat > the_assist/core/memory.py << 'MEMORY'
"""The Assist - Memory System

Simple, file-based memory that AI can work with.
Designed to evolve - start simple, add structure as patterns emerge.
"""
import os
import json
from datetime import datetime
from typing import Optional

from the_assist.config.settings import MEMORY_DIR


class Memory:
    """Hierarchical memory store following HRM principles."""

    def __init__(self):
        self.store_path = MEMORY_DIR
        self._ensure_structure()

    def _ensure_structure(self):
        """Create memory structure if it doesn't exist."""
        dirs = ['conversations', 'north_stars', 'patterns', 'context']
        for d in dirs:
            os.makedirs(os.path.join(self.store_path, d), exist_ok=True)

        # Initialize north_stars if empty
        ns_file = os.path.join(self.store_path, 'north_stars', 'current.json')
        if not os.path.exists(ns_file):
            self._write_json(ns_file, {
                "north_stars": [],
                "current_priorities": [],
                "anti_goals": [],
                "last_updated": None
            })

        # Initialize context
        ctx_file = os.path.join(self.store_path, 'context', 'current.json')
        if not os.path.exists(ctx_file):
            self._write_json(ctx_file, {
                "active_threads": [],
                "pending_commits": [],
                "open_questions": [],
                "last_session": None
            })

    def _read_json(self, path: str) -> dict:
        """Read a JSON file."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_json(self, path: str, data: dict):
        """Write a JSON file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def get_north_stars(self) -> dict:
        """Get current north stars and priorities."""
        path = os.path.join(self.store_path, 'north_stars', 'current.json')
        return self._read_json(path)

    def update_north_stars(self, data: dict):
        """Update north stars."""
        path = os.path.join(self.store_path, 'north_stars', 'current.json')
        current = self._read_json(path)
        current.update(data)
        current['last_updated'] = datetime.now().isoformat()
        self._write_json(path, current)

    def get_context(self) -> dict:
        """Get current context."""
        path = os.path.join(self.store_path, 'context', 'current.json')
        return self._read_json(path)

    def update_context(self, data: dict):
        """Update context."""
        path = os.path.join(self.store_path, 'context', 'current.json')
        current = self._read_json(path)
        current.update(data)
        current['last_session'] = datetime.now().isoformat()
        self._write_json(path, current)

    def save_conversation(self, messages: list, summary: Optional[str] = None):
        """Save a conversation."""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        path = os.path.join(self.store_path, 'conversations', f'{timestamp}.json')
        self._write_json(path, {
            'timestamp': timestamp,
            'messages': messages,
            'summary': summary
        })

    def get_recent_conversations(self, limit: int = 5) -> list:
        """Get recent conversations."""
        conv_dir = os.path.join(self.store_path, 'conversations')
        files = sorted(os.listdir(conv_dir), reverse=True)[:limit]
        return [self._read_json(os.path.join(conv_dir, f)) for f in files if f.endswith('.json')]

    def log_pattern(self, pattern_type: str, observation: str, data: dict = None):
        """Log an observed pattern for future learning."""
        path = os.path.join(self.store_path, 'patterns', 'observations.json')
        patterns = self._read_json(path)
        if 'observations' not in patterns:
            patterns['observations'] = []

        patterns['observations'].append({
            'timestamp': datetime.now().isoformat(),
            'type': pattern_type,
            'observation': observation,
            'data': data or {}
        })
        self._write_json(path, patterns)

    def build_context_prompt(self) -> str:
        """Build context string for the AI."""
        north_stars = self.get_north_stars()
        context = self.get_context()
        recent = self.get_recent_conversations(limit=2)

        parts = []

        if north_stars.get('north_stars'):
            parts.append("## North Stars (Long-term)")
            for ns in north_stars['north_stars']:
                parts.append(f"- {ns}")

        if north_stars.get('current_priorities'):
            parts.append("\n## Current Priorities")
            for p in north_stars['current_priorities']:
                parts.append(f"- {p}")

        if context.get('pending_commits'):
            parts.append("\n## Pending Commitments")
            for c in context['pending_commits']:
                parts.append(f"- {c}")

        if context.get('active_threads'):
            parts.append("\n## Active Threads")
            for t in context['active_threads']:
                parts.append(f"- {t}")

        if recent:
            parts.append("\n## Recent Context")
            for conv in recent:
                if conv.get('summary'):
                    parts.append(f"- {conv.get('timestamp', 'Unknown')}: {conv['summary']}")

        return '\n'.join(parts) if parts else "No prior context yet. This is our first conversation."
MEMORY

# 7. Write orchestrator
echo "[7/8] Writing orchestrator..."
cat > the_assist/core/orchestrator.py << 'ORCHESTRATOR'
"""The Assist - Core Orchestrator

The main brain. Handles conversation, context, and AI interaction.
"""
import os
import anthropic
from typing import Optional

from the_assist.config.settings import MODEL, MAX_TOKENS, PROMPTS_DIR
from the_assist.core.memory import Memory


class Orchestrator:
    """The cognitive core of The Assist."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.memory = Memory()
        self.system_prompt = self._load_system_prompt()
        self.conversation_history = []

    def _load_system_prompt(self) -> str:
        """Load the system prompt."""
        path = os.path.join(PROMPTS_DIR, 'system.md')
        with open(path, 'r') as f:
            return f.read()

    def _build_full_context(self) -> str:
        """Build full system context including memory."""
        memory_context = self.memory.build_context_prompt()

        return f"""{self.system_prompt}

---

# Current Context

{memory_context}
"""

    def chat(self, user_message: str) -> str:
        """Process a user message and return response."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Build context
        system_context = self._build_full_context()

        # Call Claude
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_context,
            messages=self.conversation_history
        )

        # Extract response
        assistant_message = response.content[0].text

        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def process_for_memory(self, user_input: str, ai_response: str):
        """
        Ask AI to extract any memory-worthy items from the exchange.
        This is where AI helps organize its own memory.
        """
        extraction_prompt = f"""Based on this exchange, extract any items that should be remembered.
Return a JSON object with these optional fields (only include if relevant):
- "commitments": list of things the user committed to
- "priorities_mentioned": list of priorities or goals mentioned
- "context_updates": list of context that might be relevant later
- "patterns_observed": any patterns you notice about the user

User said: {user_input}

You responded: {ai_response}

Return ONLY valid JSON, no other text. If nothing to extract, return {{}}.
"""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": extraction_prompt}]
        )

        try:
            import json
            extracted = json.loads(response.content[0].text)

            # Update memory with extracted items
            context = self.memory.get_context()

            if extracted.get('commitments'):
                context.setdefault('pending_commits', []).extend(extracted['commitments'])
            if extracted.get('context_updates'):
                context.setdefault('active_threads', []).extend(extracted['context_updates'])

            self.memory.update_context(context)

            if extracted.get('patterns_observed'):
                for pattern in extracted['patterns_observed']:
                    self.memory.log_pattern('ai_observed', pattern)

        except (json.JSONDecodeError, KeyError):
            pass  # Silently fail - memory extraction is nice-to-have

    def end_session(self, summary: Optional[str] = None):
        """End the current session and save conversation."""
        if self.conversation_history:
            # If no summary provided, ask AI to generate one
            if not summary and len(self.conversation_history) > 2:
                summary_prompt = "Summarize this conversation in one sentence for future reference."
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=100,
                    messages=self.conversation_history + [{"role": "user", "content": summary_prompt}]
                )
                summary = response.content[0].text

            self.memory.save_conversation(self.conversation_history, summary)
            self.conversation_history = []
ORCHESTRATOR

# 8. Write main entry point
echo "[8/8] Writing main entry point..."
cat > the_assist/main.py << 'MAIN'
#!/usr/bin/env python3
"""The Assist - Main Entry Point

Run this to start a conversation with The Assist.
"""
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_assist.core.orchestrator import Orchestrator


def main():
    """Main conversation loop."""
    print("\n" + "="*50)
    print("  THE ASSIST")
    print("  Cognitive Anchor | v0.1")
    print("="*50)
    print("\nType 'quit' or 'exit' to end session")
    print("Type 'save' to save and continue")
    print("-"*50 + "\n")

    orchestrator = Orchestrator()

    # Opening
    print("The Assist: What's on your mind?\n")

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in ('quit', 'exit', 'bye'):
                print("\nThe Assist: Got it. Saving our conversation...")
                orchestrator.end_session()
                print("The Assist: Until next time.\n")
                break

            if user_input.lower() == 'save':
                orchestrator.end_session()
                print("\nThe Assist: Conversation saved. Continuing...\n")
                orchestrator = Orchestrator()  # Fresh session
                continue

            # Get response
            response = orchestrator.chat(user_input)
            print(f"\nThe Assist: {response}\n")

            # Background memory processing (async in future)
            orchestrator.process_for_memory(user_input, response)

    except KeyboardInterrupt:
        print("\n\nThe Assist: Interrupted. Saving conversation...")
        orchestrator.end_session()
        print("The Assist: Saved. Goodbye.\n")


if __name__ == "__main__":
    main()
MAIN

# 9. Write __init__ files
echo "Writing package files..."
touch the_assist/__init__.py
touch the_assist/core/__init__.py
touch the_assist/config/__init__.py

# 10. Write spec document
cat > SPEC.md << 'SPEC'
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
SPEC

# 11. Update README
cat > README.md << 'README'
# The Assist

Cognitive anchor for a fast-moving mind.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run
python the_assist/main.py
```

## What Is This?

Not a task manager. Not a chatbot. A cognitive partner that:
- Grounds you when context-switching
- Remembers what you can't hold
- Challenges when needed (not just when wanted)
- Learns what works for YOU

## Commands

- `quit` / `exit` - End session and save
- `save` - Save current conversation and continue
- Just talk - It handles messy input

## First Run

Just talk. Tell it what's on your mind. It will:
1. Parse your messy input
2. Reflect back what it understood
3. Ask clarifying questions if needed
4. Start learning your patterns

Over time, it gets better. Day 1 is calibration.

## Philosophy

See [SPEC.md](SPEC.md) for full design principles.

The short version: Trust AI to be intelligent, verify it's actually helping.
README

# 12. Install dependencies
echo ""
echo "=== Installing dependencies ==="
pip3 install anthropic python-dotenv --quiet

# 13. Make main executable
chmod +x the_assist/main.py

# Done
echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run The Assist:"
echo "  cd /Users/raymondbruni/AI_ARCH"
echo "  export ANTHROPIC_API_KEY=\"your-key\""
echo "  python3 the_assist/main.py"
echo ""
echo "Or if you already exported the key, just:"
echo "  cd /Users/raymondbruni/AI_ARCH && python3 the_assist/main.py"
echo ""
