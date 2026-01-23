"""Tests for Shaper v2 State Machine.

Covers TEST_PLAN.md:
- E. State Machine (Tests 33-38)
- F. L4 Phase Confirmation Gate (Tests 39-42)
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules" / "design_framework"))

from shaper.models import ShaperModel, SpecModel
from shaper.state_machine import ShaperStateMachine, MODES


class TestStateMachine(unittest.TestCase):
    """E. State Machine (Tests 33-38)"""

    def test_33_initial_mode_is_idle(self):
        """Test 33: Initial mode is IDLE."""
        machine = ShaperStateMachine()
        self.assertEqual(machine.mode, "IDLE")
        self.assertTrue(machine.is_idle)

    def test_34_first_ingest_transitions_to_shaping(self):
        """Test 34: First ingest transitions to SHAPING."""
        machine = ShaperStateMachine()
        machine.start_shaping("L3")
        self.assertEqual(machine.mode, "SHAPING")
        self.assertTrue(machine.is_shaping)

    def test_35_reveal_transitions_to_revealed(self):
        """Test 35: Reveal transitions to REVEALED."""
        machine = ShaperStateMachine()
        machine.start_shaping("L3")
        machine.reveal()
        self.assertEqual(machine.mode, "REVEALED")
        self.assertTrue(machine.is_revealed)

    def test_36_edit_after_reveal_forces_re_reveal(self):
        """Test 36: Edit after reveal forces re-reveal."""
        machine = ShaperStateMachine()
        machine.start_shaping("L3")
        machine.reveal()
        self.assertEqual(machine.mode, "REVEALED")

        # Edit after reveal
        machine.on_edit()
        self.assertEqual(machine.mode, "SHAPING")
        self.assertFalse(machine._revealed)

    def test_37_freeze_requires_reveal(self):
        """Test 37: Freeze requires reveal."""
        machine = ShaperStateMachine()
        machine.start_shaping("L3")

        model = ShaperModel()
        model.meta = {"ID": "WI-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L3"}
        model.objective.append("o")
        model.scope.append("s")
        model.plan.append("p")
        model.acceptance.append("a")

        # Try to freeze without reveal
        with self.assertRaises(ValueError) as ctx:
            machine.freeze(model)
        self.assertIn("Reveal required", str(ctx.exception))

    def test_38_freeze_blocked_if_required_fields_missing(self):
        """Test 38: Freeze blocked if required fields missing."""
        machine = ShaperStateMachine()
        machine.start_shaping("L3")
        machine.reveal()

        model = ShaperModel()
        # Missing all fields

        with self.assertRaises(ValueError) as ctx:
            machine.freeze(model)
        self.assertIn("Missing", str(ctx.exception))


class TestL4PhaseConfirmationGate(unittest.TestCase):
    """F. L4 Phase Confirmation Gate (Tests 39-42)"""

    def test_39_freeze_blocked_if_phases_not_confirmed(self):
        """Test 39: Freeze blocked if phases not confirmed."""
        machine = ShaperStateMachine()
        machine.start_shaping("L4")
        machine.reveal()

        model = SpecModel()
        model.meta = {"ID": "SPEC-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L4"}
        model.overview.append("o")
        model.problem.append("p")
        model.non_goals.append("n")
        model.phases.append("ph")
        model.success_criteria.append("s")
        # phases_confirmed is False

        with self.assertRaises(ValueError) as ctx:
            machine.freeze(model)
        self.assertIn("phases must be confirmed", str(ctx.exception))

    def test_40_user_confirmation_enables_phases_ingestion(self):
        """Test 40: User confirmation enables phases ingestion."""
        model = SpecModel()
        model.suggest_phase("Phase 1: Planning")
        model.suggest_phase("Phase 2: Execution")

        # Before confirmation
        self.assertEqual(model.phases, [])
        self.assertFalse(model.phases_confirmed)

        # After confirmation
        model.confirm_phases()
        self.assertTrue(model.phases_confirmed)
        self.assertEqual(model.phases, ["Phase 1: Planning", "Phase 2: Execution"])

    def test_41_confirmed_phases_allow_freeze(self):
        """Test 41: Confirmed phases allow freeze."""
        machine = ShaperStateMachine()
        machine.start_shaping("L4")
        machine.reveal()

        model = SpecModel()
        model.meta = {"ID": "SPEC-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L4"}
        model.overview.append("o")
        model.problem.append("p")
        model.non_goals.append("n")
        model.suggest_phase("Phase 1")
        model.confirm_phases()  # Confirm phases
        model.success_criteria.append("s")

        # Should not raise
        machine.freeze(model)
        self.assertEqual(machine.mode, "FROZEN")

    def test_42_unconfirmed_phases_not_included_in_output(self):
        """Test 42: Unconfirmed phases not included in output."""
        model = SpecModel()
        model.suggest_phase("Phase 1: Planning")

        # Before confirmation, phases list is empty
        self.assertEqual(model.phases, [])
        self.assertEqual(model._suggested_phases, ["Phase 1: Planning"])

        # Render would not include unconfirmed phases
        from shaper.renderers import render_spec
        model.meta = {"ID": "SPEC-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L4"}
        model.overview.append("o")
        model.problem.append("p")
        model.non_goals.append("n")
        model.success_criteria.append("s")

        output = render_spec(model)
        # Phases section exists but is empty (no numbered items)
        self.assertIn("## Phases", output)
        self.assertNotIn("1. Phase 1: Planning", output)


if __name__ == "__main__":
    unittest.main()
