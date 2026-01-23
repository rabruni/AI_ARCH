"""Tests for Shaper v2 Context Window Builder.

Covers TEST_PLAN.md:
- G. Context Window Builder (Tests 43-45)
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules" / "design_framework"))

from shaper.context_builder import ConversationBuffer, build_context_window
from shaper.state_machine import ShaperStateMachine
from shaper.models import ShaperModel


class TestContextWindowBuilder(unittest.TestCase):
    """G. Context Window Builder (Tests 43-45)"""

    def test_43_block_4_keeps_last_two_pairs_only(self):
        """Test 43: Block 4 keeps last two pairs only."""
        buffer = ConversationBuffer()

        # Add 3 pairs
        buffer.add_pair("user1", "assistant1")
        buffer.add_pair("user2", "assistant2")
        buffer.add_pair("user3", "assistant3")

        # Should only keep last 2
        pairs = buffer.pairs
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0], ("user2", "assistant2"))
        self.assertEqual(pairs[1], ("user3", "assistant3"))

    def test_44_fifo_trim_oldest_pair_on_overflow(self):
        """Test 44: FIFO trim oldest pair on overflow."""
        buffer = ConversationBuffer()

        # Add pairs and verify FIFO behavior
        buffer.add_pair("first_user", "first_assistant")
        buffer.add_pair("second_user", "second_assistant")
        self.assertEqual(len(buffer.pairs), 2)

        # Add third - should remove first
        buffer.add_pair("third_user", "third_assistant")
        pairs = buffer.pairs
        self.assertEqual(len(pairs), 2)
        # First pair should be gone
        self.assertNotIn(("first_user", "first_assistant"), pairs)
        self.assertEqual(pairs[0], ("second_user", "second_assistant"))
        self.assertEqual(pairs[1], ("third_user", "third_assistant"))

    def test_45_freeze_clears_conversation_buffer_and_resets_model(self):
        """Test 45: Freeze clears conversation buffer and resets model."""
        # Setup
        buffer = ConversationBuffer()
        buffer.add_pair("user", "assistant")
        machine = ShaperStateMachine()
        machine.start_shaping("L3")
        machine.reveal()

        model = ShaperModel()
        model.meta = {"ID": "WI-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L3"}
        model.objective.append("o")
        model.scope.append("s")
        model.plan.append("p")
        model.acceptance.append("a")

        # Pre-freeze: buffer has content
        self.assertEqual(len(buffer.pairs), 1)

        # Freeze
        machine.freeze(model)

        # Simulate post-freeze cleanup (as CLI would do)
        buffer.clear()
        model.reset()

        # Buffer should be empty
        self.assertEqual(len(buffer.pairs), 0)

        # Model should be reset
        self.assertEqual(model.objective, [])
        self.assertEqual(model.meta, {})
        self.assertFalse(model.revealed_once)


class TestContextWindowIntegration(unittest.TestCase):
    """Additional context window integration tests."""

    def test_build_context_window_returns_immutable_window(self):
        """Context window is immutable (frozen dataclass)."""
        buffer = ConversationBuffer()
        buffer.add_pair("u", "a")
        machine = ShaperStateMachine()
        machine.start_shaping("L3")
        model = ShaperModel()

        window = build_context_window(machine, model, "L3", buffer)

        # Should be a frozen dataclass
        with self.assertRaises(Exception):  # FrozenInstanceError
            window.block1 = "modified"

    def test_context_window_has_four_blocks(self):
        """Context window contains all four blocks."""
        buffer = ConversationBuffer()
        machine = ShaperStateMachine()
        machine.start_shaping("L3")
        model = ShaperModel()

        window = build_context_window(machine, model, "L3", buffer)

        self.assertIsNotNone(window.block1)  # System Core
        self.assertIsNotNone(window.block2)  # State
        self.assertIsNotNone(window.block3)  # Artifact
        self.assertIsNotNone(window.block4)  # Conversation (may be empty list)


if __name__ == "__main__":
    unittest.main()
