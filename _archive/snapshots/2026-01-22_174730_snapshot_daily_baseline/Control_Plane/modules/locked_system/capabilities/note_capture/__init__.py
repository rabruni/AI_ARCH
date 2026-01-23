"""Note capture capability - gated file writes.

Requires explicit delegation before writing.
All writes are logged and validated.
"""
from locked_system.capabilities.note_capture.tool import (
    NoteCaptureCapability,
    NoteType,
    DEVELOPER_PATTERNS,
    PERSONAL_PATTERNS,
)

__all__ = [
    'NoteCaptureCapability',
    'NoteType',
    'DEVELOPER_PATTERNS',
    'PERSONAL_PATTERNS',
]
