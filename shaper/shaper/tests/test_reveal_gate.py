import unittest

from shaper.cli import process_line, reveal
from shaper.model import ShaperModel
from shaper.state_machine import ShaperStateMachine


class RevealGateTests(unittest.TestCase):
    def test_reveal_includes_meta_keys(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        output = reveal(model, machine)
        self.assertIn("- ID:", output)
        self.assertIn("- Title:", output)
        self.assertIn("- Status:", output)
        self.assertIn("- ALTITUDE:", output)

    def test_reveal_sets_flag(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        self.assertFalse(model.revealed_once)
        _ = reveal(model, machine)
        self.assertTrue(model.revealed_once)

    def test_converge_requires_reveal(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        outputs = []

        def capture(message):
            outputs.append(message)

        process_line(model, machine, "turn this into a work item", output_func=capture)
        self.assertEqual(outputs[-1], "Refuse: reveal required before converge.")


if __name__ == "__main__":
    unittest.main()
