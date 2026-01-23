"""Capabilities - Gated tools.

All capabilities:
- Require explicit delegation to use
- Are logged when invoked
- Can be revoked at any time
- Have defined side effects

Available capabilities:
- note_capture: Write notes to files
- memory_write: Write to slow memory
"""
from locked_system.capabilities.registry import (
    CAPABILITIES,
    check_capability,
    get_capability_info,
    list_capabilities,
    register_capability,
)
from locked_system.capabilities.note_capture import NoteCaptureCapability, NoteType

__all__ = [
    'CAPABILITIES',
    'check_capability',
    'get_capability_info',
    'list_capabilities',
    'register_capability',
    'NoteCaptureCapability',
    'NoteType',
]
