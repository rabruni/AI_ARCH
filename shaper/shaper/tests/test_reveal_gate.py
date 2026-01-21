import unittest

from shaper.shaper.cli import process_line, reveal
from shaper.shaper.model import ShaperModel


class RevealGateTests(unittest.TestCase):
    def test_reveal_includes_meta_keys(self):
        model = ShaperModel()
        output = reveal(model)
        self.assertIn("- ID:", output)
        self.assertIn("- Title:", output)
        self.assertIn("- Status:", output)
        self.assertIn("- ALTITUDE:", output)

    def test_reveal_sets_flag(self):
        model = ShaperModel()
        self.assertFalse(model.revealed_once)
        _ = reveal(model)
        self.assertTrue(model.revealed_once)

    def test_converge_requires_reveal(self):
        model = ShaperModel()
        outputs = []

        def capture(message):
            outputs.append(message)

        process_line(model, "turn this into a work item", output_func=capture)
        self.assertEqual(outputs[-1], "Refuse: reveal required before converge.")


if __name__ == "__main__":
    unittest.main()
