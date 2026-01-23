"""Context Window Builder for Shaper v2.

Builds the 4-block context window for LLM interactions.

Blocks (fixed order):
1. System Core: immutable instructions and constraints
2. State Machine: mode, flags, altitude, and gating state
3. Full Artifact State: complete, unsummarized current model content
4. Conversation Buffer: last two user+assistant pairs

Block 4 keeps the last 2 pairs (user+assistant).
FIFO trim oldest pair on overflow.
No summarization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Union

from .models import ShaperModel, SpecModel
from .state_machine import ShaperStateMachine
from .renderers import render_work_item, render_spec


# Type alias for a conversation pair (user message, assistant message)
ConversationPair = Tuple[str, str]


@dataclass(frozen=True)
class ContextWindow:
    """Immutable 4-block context window.

    Attributes:
        block1: System core instructions
        block2: State machine state
        block3: Full artifact state
        block4: Conversation buffer (last 2 pairs)
    """

    block1: str
    block2: str
    block3: str
    block4: List[ConversationPair]


class ConversationBuffer:
    """Manages conversation history with FIFO trimming.

    Keeps last 2 user+assistant pairs.
    Oldest pair is trimmed when adding beyond capacity.
    """

    MAX_PAIRS = 2

    def __init__(self) -> None:
        self._pairs: List[ConversationPair] = []

    @property
    def pairs(self) -> List[ConversationPair]:
        """Return current pairs (defensive copy)."""
        return list(self._pairs)

    def add_pair(self, user: str, assistant: str) -> None:
        """Add a new conversation pair.

        FIFO trims oldest pair if at capacity.
        """
        self._pairs.append((user, assistant))
        if len(self._pairs) > self.MAX_PAIRS:
            self._pairs.pop(0)  # FIFO: remove oldest

    def clear(self) -> None:
        """Clear all conversation history."""
        self._pairs.clear()


def build_system_core() -> str:
    """Build Block 1: System Core instructions.

    Contains immutable rules and constraints for the LLM.
    """
    return """SYSTEM CORE (IMMUTABLE)

ROLE: Shaper - artifact-first, deterministic shaping system.

RULES:
- No execution of commands
- No inference of plan steps (L3) - only user-provided steps
- L4 phases require explicit user confirmation
- Reveal required before freeze
- No modifications to Control Plane
- Deterministic output: no randomness, timestamps, UUIDs

ALTITUDES:
- L3: WORK_ITEM (implementation contract)
- L4: SPEC (product/architecture spec)

TRIGGERS:
- "show me what you have" → reveal
- "turn this into a work item" → converge (L3)
- "turn this into a spec" → converge (L4)
- "freeze it" → freeze"""


def build_state_block(machine: ShaperStateMachine, altitude: str | None) -> str:
    """Build Block 2: State Machine state.

    Args:
        machine: Current state machine instance.
        altitude: Current altitude (L3/L4/None).

    Returns:
        Formatted state block.
    """
    lines = [
        "STATE MACHINE",
        f"Mode: {machine.mode}",
        f"Altitude: {altitude or 'UNDETERMINED'}",
        f"Revealed: {machine._revealed}",
        "Phases confirmed:",
    ]
    for phase, confirmed in machine.phases_confirmed.items():
        lines.append(f"  - {phase}: {confirmed}")
    return "\n".join(lines)


def build_artifact_block(model: Union[ShaperModel, SpecModel, None], altitude: str | None) -> str:
    """Build Block 3: Full Artifact State.

    Args:
        model: Current model instance.
        altitude: Current altitude.

    Returns:
        Complete artifact state or placeholder.
    """
    if model is None:
        return "ARTIFACT STATE\n(No active artifact)"

    if altitude == "L3":
        content = render_work_item(model)
    elif altitude == "L4":
        content = render_spec(model)
    else:
        content = "(Unknown altitude)"

    missing = model.missing_sections()
    missing_str = ", ".join(missing) if missing else "None"

    return f"ARTIFACT STATE\n\n{content}\nMissing sections: {missing_str}"


def build_conversation_block(buffer: ConversationBuffer) -> str:
    """Build Block 4: Conversation Buffer.

    Args:
        buffer: Conversation buffer with pairs.

    Returns:
        Formatted conversation history.
    """
    if not buffer.pairs:
        return "CONVERSATION BUFFER\n(Empty)"

    lines = ["CONVERSATION BUFFER"]
    for i, (user, assistant) in enumerate(buffer.pairs, 1):
        lines.append(f"\n[Pair {i}]")
        lines.append(f"User: {user}")
        lines.append(f"Assistant: {assistant}")
    return "\n".join(lines)


def build_context_window(
    machine: ShaperStateMachine,
    model: Union[ShaperModel, SpecModel, None],
    altitude: str | None,
    buffer: ConversationBuffer,
) -> ContextWindow:
    """Build complete 4-block context window.

    Args:
        machine: State machine instance.
        model: Active model instance.
        altitude: Current altitude.
        buffer: Conversation buffer.

    Returns:
        Immutable ContextWindow with all 4 blocks.
    """
    return ContextWindow(
        block1=build_system_core(),
        block2=build_state_block(machine, altitude),
        block3=build_artifact_block(model, altitude),
        block4=buffer.pairs,
    )


def render_context_window(window: ContextWindow) -> str:
    """Render context window as a single string for LLM.

    Args:
        window: The context window to render.

    Returns:
        Complete context string.
    """
    sections = [
        "=" * 60,
        "BLOCK 1: SYSTEM CORE",
        "=" * 60,
        window.block1,
        "",
        "=" * 60,
        "BLOCK 2: STATE",
        "=" * 60,
        window.block2,
        "",
        "=" * 60,
        "BLOCK 3: ARTIFACT",
        "=" * 60,
        window.block3,
        "",
        "=" * 60,
        "BLOCK 4: CONVERSATION",
        "=" * 60,
    ]

    if not window.block4:
        sections.append("(Empty)")
    else:
        for i, (user, assistant) in enumerate(window.block4, 1):
            sections.append(f"\n[Pair {i}]")
            sections.append(f"User: {user}")
            sections.append(f"Assistant: {assistant}")

    return "\n".join(sections)
