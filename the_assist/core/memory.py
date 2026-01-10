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
