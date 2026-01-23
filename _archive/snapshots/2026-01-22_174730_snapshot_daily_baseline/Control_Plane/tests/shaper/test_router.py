"""Tests for Shaper v2 Altitude Router.

Covers TEST_PLAN.md:
- D. Altitude Router (Tests 27-32)
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules" / "design_framework"))

from shaper.router import detect_altitude, AltitudeRouter, CLARIFICATION_PROMPT


class TestAltitudeRouter(unittest.TestCase):
    """D. Altitude Router (Tests 27-32)"""

    def test_27_l3_classification_for_work_item_cues(self):
        """Test 27: L3 classification for work item cues."""
        route = detect_altitude("I need to implement a fix for the bug")
        self.assertEqual(route.altitude, "L3")

        route = detect_altitude("Create a work item for this task")
        self.assertEqual(route.altitude, "L3")

        route = detect_altitude("Steps to patch the code")
        self.assertEqual(route.altitude, "L3")

    def test_28_l4_classification_for_spec_cues(self):
        """Test 28: L4 classification for spec cues."""
        route = detect_altitude("Define the architecture for this system")
        self.assertEqual(route.altitude, "L4")

        route = detect_altitude("Create a spec for the product vision")
        self.assertEqual(route.altitude, "L4")

        route = detect_altitude("Write an RFC with non-goals and success criteria")
        self.assertEqual(route.altitude, "L4")

    def test_29_unclear_when_ambiguous_input(self):
        """Test 29: UNCLEAR when ambiguous input."""
        route = detect_altitude("Hello world")
        self.assertEqual(route.altitude, "UNCLEAR")

        route = detect_altitude("Let's do something")
        self.assertEqual(route.altitude, "UNCLEAR")

    def test_30_clarification_prompt_required_on_unclear(self):
        """Test 30: Clarification prompt required on UNCLEAR."""
        route = detect_altitude("Hello world")
        self.assertEqual(route.altitude, "UNCLEAR")
        self.assertIsNotNone(route.clarification)
        self.assertEqual(route.clarification, CLARIFICATION_PROMPT)

    def test_31_altitude_immutable_after_first_ingest(self):
        """Test 31: Altitude immutable after first ingest."""
        router = AltitudeRouter()

        # First detection - not locked yet
        route = router.detect("implement the feature")
        self.assertEqual(route.altitude, "L3")
        self.assertFalse(router.is_locked)

        # Lock it
        router.lock("L3")
        self.assertTrue(router.is_locked)
        self.assertEqual(router.altitude, "L3")

        # After locking, detect returns locked altitude regardless of input
        route = router.detect("architecture overview")  # Would be L4
        self.assertEqual(route.altitude, "L3")  # But returns locked L3

    def test_32_altitude_change_requires_reset(self):
        """Test 32: Altitude change requires reset."""
        router = AltitudeRouter()
        router.lock("L3")

        # Attempting to lock different altitude should raise
        with self.assertRaises(ValueError) as ctx:
            router.lock("L4")
        self.assertIn("Cannot change", str(ctx.exception))

        # After reset, can lock to different altitude
        router.reset()
        self.assertFalse(router.is_locked)
        router.lock("L4")
        self.assertEqual(router.altitude, "L4")


if __name__ == "__main__":
    unittest.main()
