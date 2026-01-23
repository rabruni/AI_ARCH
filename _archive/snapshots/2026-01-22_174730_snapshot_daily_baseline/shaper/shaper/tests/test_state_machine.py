import unittest

from shaper.state_machine import ShaperStateMachine


class StateMachineTests(unittest.TestCase):
    def test_initial_mode_idle(self):
        machine = ShaperStateMachine()
        self.assertEqual(machine.mode, "IDLE")

    def test_start_shaping_sets_mode(self):
        machine = ShaperStateMachine()
        machine.start_shaping()
        self.assertEqual(machine.mode, "SHAPING")

    def test_reveal_required_before_converge(self):
        machine = ShaperStateMachine()
        with self.assertRaises(ValueError):
            machine.converge()
        machine.reveal()
        machine.converge()
        self.assertEqual(machine.mode, "REVEALED")

    def test_freeze_requires_confirmed_phases(self):
        machine = ShaperStateMachine()
        machine.reveal()
        with self.assertRaises(ValueError):
            machine.freeze("L4")
        for phase in machine.phases:
            machine.confirm_phase(phase)
        machine.freeze("L4")
        self.assertEqual(machine.mode, "FROZEN")

    def test_unknown_phase_rejected(self):
        machine = ShaperStateMachine()
        with self.assertRaises(ValueError):
            machine.confirm_phase("nope")

    def test_non_l4_freeze_allowed_after_reveal(self):
        machine = ShaperStateMachine()
        machine.reveal()
        machine.freeze("L2")
        self.assertEqual(machine.mode, "FROZEN")


if __name__ == "__main__":
    unittest.main()
