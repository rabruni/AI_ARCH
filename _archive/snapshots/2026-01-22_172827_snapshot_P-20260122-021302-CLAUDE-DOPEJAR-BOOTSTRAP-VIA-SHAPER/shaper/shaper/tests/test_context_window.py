import unittest

from shaper.context_window import build_context_window


class ContextWindowTests(unittest.TestCase):
    def test_trims_to_two_pairs(self):
        history = [
            ("user-1", "assistant-1"),
            ("user-2", "assistant-2"),
            ("user-3", "assistant-3"),
        ]
        window = build_context_window("b1", "b2", "b3", history)
        self.assertEqual(len(window.block4), 2)
        self.assertEqual(window.block4[0], ("user-2", "assistant-2"))
        self.assertEqual(window.block4[1], ("user-3", "assistant-3"))

    def test_keeps_pairs_when_two(self):
        history = [("user-1", "assistant-1"), ("user-2", "assistant-2")]
        window = build_context_window("b1", "b2", "b3", history)
        self.assertEqual(window.block4, history)

    def test_empty_history(self):
        window = build_context_window("b1", "b2", "b3", [])
        self.assertEqual(window.block4, [])

    def test_blocks_preserved(self):
        window = build_context_window("one", "two", "three", [])
        self.assertEqual(window.block1, "one")
        self.assertEqual(window.block2, "two")
        self.assertEqual(window.block3, "three")


if __name__ == "__main__":
    unittest.main()
