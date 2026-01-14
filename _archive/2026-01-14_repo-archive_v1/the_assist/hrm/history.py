"""HRM Session History

Lightweight session memory for continuity.

Stores session summaries with timestamps and indexes.
Only loaded when user asks continuity questions.
"""
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import re


HRM_DIR = Path(__file__).parent / "memory"


@dataclass
class SessionRecord:
    """A single session record."""
    index: int
    date: str                    # ISO date
    time: str                    # ISO time
    summary: str                 # 1-2 sentence summary
    topics: list[str]            # Key topics discussed
    duration_exchanges: int      # How many exchanges


class SessionHistory:
    """
    Session history manager.

    Cheap: Only loads when needed.
    Indexed: Can retrieve specific sessions.
    Time-bounded: Keeps last N sessions.
    """

    MAX_SESSIONS = 20  # Keep last 20 sessions

    def __init__(self):
        self.history_file = HRM_DIR / "session_history.json"
        self._ensure_exists()
        self._current_session_start: Optional[datetime] = None
        self._current_topics: list[str] = []
        self._exchange_count: int = 0

    def _ensure_exists(self):
        HRM_DIR.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            self._save({"sessions": [], "next_index": 1})

    def _load(self) -> dict:
        with open(self.history_file, 'r') as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def start_session(self):
        """Mark session start."""
        self._current_session_start = datetime.now()
        self._current_topics = []
        self._exchange_count = 0

    def record_exchange(self, topics: list[str]):
        """Record an exchange. Called after each user interaction."""
        self._exchange_count += 1
        for topic in topics:
            if topic and topic not in self._current_topics:
                self._current_topics.append(topic)
        # Keep topics bounded
        self._current_topics = self._current_topics[-10:]

    def end_session(self, summary: str):
        """
        End session and save record.

        Args:
            summary: 1-2 sentence summary of what was discussed
        """
        if not self._current_session_start:
            return

        data = self._load()

        record = SessionRecord(
            index=data["next_index"],
            date=self._current_session_start.strftime("%Y-%m-%d"),
            time=self._current_session_start.strftime("%H:%M"),
            summary=summary,
            topics=self._current_topics,
            duration_exchanges=self._exchange_count
        )

        data["sessions"].append(asdict(record))
        data["next_index"] += 1

        # Keep only last N sessions
        data["sessions"] = data["sessions"][-self.MAX_SESSIONS:]

        self._save(data)

        # Reset
        self._current_session_start = None
        self._current_topics = []
        self._exchange_count = 0

    def get_last_session(self) -> Optional[SessionRecord]:
        """Get the most recent session."""
        data = self._load()
        if data["sessions"]:
            return SessionRecord(**data["sessions"][-1])
        return None

    def get_session(self, index: int) -> Optional[SessionRecord]:
        """Get session by index."""
        data = self._load()
        for s in data["sessions"]:
            if s["index"] == index:
                return SessionRecord(**s)
        return None

    def get_sessions_by_date(self, date: str) -> list[SessionRecord]:
        """Get all sessions from a specific date (YYYY-MM-DD)."""
        data = self._load()
        return [SessionRecord(**s) for s in data["sessions"] if s["date"] == date]

    def get_recent_sessions(self, n: int = 5) -> list[SessionRecord]:
        """Get last N sessions."""
        data = self._load()
        return [SessionRecord(**s) for s in data["sessions"][-n:]]

    def get_all_sessions(self) -> list[SessionRecord]:
        """Get all sessions."""
        data = self._load()
        return [SessionRecord(**s) for s in data["sessions"]]

    def search_sessions(self, keyword: str) -> list[SessionRecord]:
        """Search sessions by keyword in summary or topics."""
        data = self._load()
        keyword = keyword.lower()
        results = []
        for s in data["sessions"]:
            if (keyword in s["summary"].lower() or
                any(keyword in t.lower() for t in s["topics"])):
                results.append(SessionRecord(**s))
        return results

    def format_session(self, session: SessionRecord) -> str:
        """Format a session for display."""
        return (
            f"[Session #{session.index}] {session.date} {session.time}\n"
            f"  Summary: {session.summary}\n"
            f"  Topics: {', '.join(session.topics) if session.topics else 'none'}\n"
            f"  Exchanges: {session.duration_exchanges}"
        )

    def format_sessions_brief(self, sessions: list[SessionRecord]) -> str:
        """Format multiple sessions briefly."""
        if not sessions:
            return "No sessions found."
        lines = []
        for s in sessions:
            lines.append(f"#{s.index} [{s.date}] {s.summary[:60]}{'...' if len(s.summary) > 60 else ''}")
        return "\n".join(lines)

    def build_context_for_continuity(self, n: int = 3) -> str:
        """
        Build context for continuity questions.

        Only called when user asks about previous sessions.
        Returns context string to inject into prompt.
        """
        sessions = self.get_recent_sessions(n)
        if not sessions:
            return "No previous sessions recorded."

        lines = ["PREVIOUS SESSIONS:"]
        for s in sessions:
            lines.append(f"- Session #{s.index} ({s.date}): {s.summary}")
            if s.topics:
                lines.append(f"  Topics: {', '.join(s.topics)}")
        return "\n".join(lines)

    @staticmethod
    def is_continuity_question(user_input: str) -> bool:
        """
        Detect if user is asking about previous sessions.

        Returns True if we should load session history.
        """
        patterns = [
            r"\bwhat were we\b",
            r"\bwhere were we\b",
            r"\blast (time|session)\b",
            r"\bprevious(ly)?\b",
            r"\bcontinue from\b",
            r"\bpick up\b",
            r"\bbefore (the )?(crash|session)\b",
            r"\bremember when\b",
            r"\bwe (talked|discussed|worked on)\b",
            r"\bwhat did we\b",
            r"\bsession (#|\d|history)\b",
        ]
        input_lower = user_input.lower()
        return any(re.search(p, input_lower) for p in patterns)
