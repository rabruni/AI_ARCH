"""Note Capture Capability - Gated file writes for notes.

This capability requires explicit delegation to use.
Writes are logged and validated.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
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


class NoteCaptureCapability:
    """
    Gated note-taking capability.

    Key invariants:
    - Requires explicit delegation to write
    - All writes are logged
    - Writes are validated after completion
    - Cannot self-authorize
    """

    CAPABILITY_ID = "note_capture"
    SIDE_EFFECTS = ["file_write"]

    def __init__(
        self,
        notes_dir: Path,
        authorization_check: Optional[Callable[[str, str], bool]] = None
    ):
        """
        Initialize note capture.

        Args:
            notes_dir: Directory to store notes
            authorization_check: Callback to check authorization (grantee, capability) -> bool
        """
        self.notes_dir = notes_dir
        self._auth_check = authorization_check
        self._write_log: list[dict] = []

        # Ensure directory exists
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

    def set_authorization_check(self, check: Callable[[str, str], bool]):
        """Set the authorization check callback."""
        self._auth_check = check

    def is_authorized(self, grantee: str = "agent") -> bool:
        """Check if note capture is authorized for the given grantee."""
        if self._auth_check is None:
            # No auth check configured - deny by default for safety
            return False
        return self._auth_check(grantee, self.CAPABILITY_ID)

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
        cleaned = user_input
        for pattern in DEVELOPER_PATTERNS + PERSONAL_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.strip(" :-,.")

        # If we got content, use it; otherwise use context
        return cleaned if cleaned else context

    def capture(
        self,
        note_type: str,
        content: str,
        grantee: str = "agent",
        source: str = "conversation"
    ) -> dict:
        """
        Capture a note (gated operation).

        Returns result dict with success status and message.
        """
        # Authorization check FIRST
        if not self.is_authorized(grantee):
            self._log_attempt(note_type, content, grantee, authorized=False)
            return {
                "success": False,
                "authorized": False,
                "message": "Note capture not authorized. Request delegation first.",
                "suggested_action": "Propose note_capture delegation via gate"
            }

        if not content.strip():
            return {
                "success": False,
                "authorized": True,
                "message": "No content to capture."
            }

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        if note_type == NoteType.DEVELOPER:
            file_path = self.developer_file
            label = "developer notes"
        else:
            file_path = self.personal_file
            label = "personal notes"

        # Format the note entry
        entry = f"\n## {timestamp}\n{content}\n"

        # Write to file
        with open(file_path, "a") as f:
            f.write(entry)

        # Validate by reading back
        verified = self._verify_write(file_path, timestamp, content)

        # Log the write
        self._log_attempt(
            note_type, content, grantee,
            authorized=True,
            success=verified,
            file_path=str(file_path)
        )

        if verified:
            display_content = content[:100] + "..." if len(content) > 100 else content
            return {
                "success": True,
                "authorized": True,
                "verified": True,
                "message": f"Captured to {label}",
                "file": file_path.name,
                "content_preview": display_content
            }
        else:
            return {
                "success": False,
                "authorized": True,
                "verified": False,
                "message": f"Write may have failed to {label}",
                "file": str(file_path)
            }

    def _verify_write(self, file_path: Path, timestamp: str, content: str) -> bool:
        """Verify that a note was written correctly."""
        try:
            if not file_path.exists():
                return False

            file_content = file_path.read_text()
            return timestamp in file_content and content in file_content
        except Exception:
            return False

    def _log_attempt(
        self,
        note_type: str,
        content: str,
        grantee: str,
        authorized: bool,
        success: bool = False,
        file_path: str = None
    ):
        """Log a capture attempt for auditing."""
        self._write_log.append({
            "timestamp": datetime.now().isoformat(),
            "note_type": note_type,
            "grantee": grantee,
            "authorized": authorized,
            "success": success,
            "file_path": file_path,
            "content_length": len(content) if content else 0
        })

    def get_recent_notes(self, note_type: str, n: int = 5) -> list[str]:
        """Get the most recent notes of a type (raw entries)."""
        if note_type == NoteType.DEVELOPER:
            file_path = self.developer_file
        else:
            file_path = self.personal_file

        if not file_path.exists():
            return []

        content = file_path.read_text()
        entries = re.split(r'\n## ', content)[1:]
        return entries[-n:] if entries else []

    def get_notes_formatted(self, note_type: str = None, n: int = 10) -> list[dict]:
        """
        Get notes in a structured format with parsed timestamps.

        Returns list of dicts with: timestamp, content, type, datetime
        """
        notes = []

        types_to_read = [note_type] if note_type else [NoteType.DEVELOPER, NoteType.PERSONAL]

        for ntype in types_to_read:
            if ntype == NoteType.DEVELOPER:
                file_path = self.developer_file
            else:
                file_path = self.personal_file

            if not file_path.exists():
                continue

            content = file_path.read_text()
            entries = re.split(r'\n## ', content)[1:]

            for entry in entries:
                lines = entry.strip().split('\n')
                if lines:
                    # First line is timestamp
                    timestamp_str = lines[0].strip()
                    note_content = '\n'.join(lines[1:]).strip()

                    # Parse timestamp
                    try:
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                    except ValueError:
                        dt = None

                    notes.append({
                        'timestamp': timestamp_str,
                        'datetime': dt,
                        'content': note_content,
                        'type': ntype,
                        'file': file_path.name
                    })

        # Sort by datetime (most recent first)
        notes.sort(key=lambda x: x['datetime'] or datetime.min, reverse=True)

        return notes[:n]

    def get_all_notes_summary(self) -> dict:
        """Get a summary of all notes."""
        dev_notes = self.get_notes_formatted(NoteType.DEVELOPER, n=100)
        personal_notes = self.get_notes_formatted(NoteType.PERSONAL, n=100)

        return {
            'developer': {
                'count': len(dev_notes),
                'file': str(self.developer_file),
                'recent': dev_notes[:3]
            },
            'personal': {
                'count': len(personal_notes),
                'file': str(self.personal_file),
                'recent': personal_notes[:3]
            },
            'total': len(dev_notes) + len(personal_notes)
        }

    def get_notes_path(self, note_type: str) -> Path:
        """Get the path to a notes file."""
        if note_type == NoteType.DEVELOPER:
            return self.developer_file
        return self.personal_file

    def get_write_log(self, n: int = 10) -> list[dict]:
        """Get recent write log entries."""
        return self._write_log[-n:]

    def get_capability_info(self) -> dict:
        """Get capability info for registry."""
        return {
            "id": self.CAPABILITY_ID,
            "side_effects": self.SIDE_EFFECTS,
            "requires_delegation": True,
            "description": "Captures notes to files",
            "files": {
                "developer": str(self.developer_file),
                "personal": str(self.personal_file)
            }
        }
