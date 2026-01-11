"""Notes - Captures user and developer notes via natural language.

Triggered by phrases like:
- Developer: "note that for dev", "remember this for development", "dev note"
- Personal: "write that down", "remember this for me", "make a note"
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal
import re


class NoteType:
    DEVELOPER = "developer"
    PERSONAL = "personal"


# Patterns that suggest note-taking intent
DEVELOPER_PATTERNS = [
    r"note.*(for|to).*(dev|developer|development)",
    r"dev(eloper)?\s*note",
    r"remember.*(for|to).*(dev|development)",
    r"write.*(for|to).*(dev|developer)",
    r"log.*(for|to).*(dev|development)",
    r"(add|put).*(to|in).*dev.*note",
]

PERSONAL_PATTERNS = [
    r"(write|note|jot).*(that|this).*(down|for me)",
    r"remember.*(that|this).*(for me)?$",
    r"make.*(a )?(note|reminder)",
    r"(save|keep|store).*(that|this)",
    r"don'?t (let me )?forget",
    r"(add|put).*(to|in).*my.*note",
]


class Notes:
    """
    Note-taking manager.

    Detects note-taking intent from user input and saves to appropriate file.
    """

    def __init__(self, notes_dir: Path):
        self.notes_dir = notes_dir
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        self.developer_file = self.notes_dir / "developer.md"
        self.personal_file = self.notes_dir / "personal.md"

        # Initialize files with headers if they don't exist
        self._init_file(self.developer_file, "Developer Notes")
        self._init_file(self.personal_file, "Personal Notes")

    def _init_file(self, path: Path, title: str):
        """Initialize note file with header if it doesn't exist."""
        if not path.exists():
            path.write_text(f"# {title}\n\n")

    def detect_note_intent(self, user_input: str) -> Optional[str]:
        """
        Detect if user wants to make a note.

        Returns NoteType.DEVELOPER, NoteType.PERSONAL, or None.
        """
        lower = user_input.lower()

        # Check developer patterns first (more specific)
        for pattern in DEVELOPER_PATTERNS:
            if re.search(pattern, lower):
                return NoteType.DEVELOPER

        # Check personal patterns
        for pattern in PERSONAL_PATTERNS:
            if re.search(pattern, lower):
                return NoteType.PERSONAL

        return None

    def extract_note_content(self, user_input: str, context: str = "") -> str:
        """
        Extract the actual note content from the user's message.

        The context is the previous assistant message or conversation context
        that the user might be referring to with "that".
        """
        lower = user_input.lower()

        # If they said "note that" or "remember this", the content is in context
        if re.search(r"(note|remember|write|save).*(that|this)", lower):
            if context:
                return context

        # Otherwise, try to extract content after the intent phrase
        # Remove the intent phrase and use the rest
        cleaned = user_input
        for pattern in DEVELOPER_PATTERNS + PERSONAL_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.strip(" :-,.")

        # If we got content, use it; otherwise use context
        return cleaned if cleaned else context

    def add_note(
        self,
        note_type: str,
        content: str,
        source: str = "conversation"
    ) -> str:
        """
        Add a note to the appropriate file.

        Returns confirmation message.
        """
        if not content.strip():
            return "I didn't catch what to note. Could you say that again?"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        if note_type == NoteType.DEVELOPER:
            file_path = self.developer_file
            label = "developer notes"
        else:
            file_path = self.personal_file
            label = "personal notes"

        # Format the note entry
        entry = f"\n## {timestamp}\n{content}\n"

        # Append to file
        with open(file_path, "a") as f:
            f.write(entry)

        return f"Got it - added to your {label}."

    def get_recent_notes(self, note_type: str, n: int = 5) -> list[str]:
        """Get the most recent notes of a type."""
        if note_type == NoteType.DEVELOPER:
            file_path = self.developer_file
        else:
            file_path = self.personal_file

        if not file_path.exists():
            return []

        content = file_path.read_text()
        # Split by ## headers (each note entry)
        entries = re.split(r'\n## ', content)[1:]  # Skip the title
        return entries[-n:] if entries else []

    def get_notes_path(self, note_type: str) -> Path:
        """Get the path to a notes file."""
        if note_type == NoteType.DEVELOPER:
            return self.developer_file
        return self.personal_file
