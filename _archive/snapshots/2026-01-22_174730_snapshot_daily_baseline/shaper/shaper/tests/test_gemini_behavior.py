import unittest

from shaper.gemini import GeminiLlmConnection, GeminiModel


class GeminiBehaviorTests(unittest.TestCase):
    def test_resolve_region_explicit(self):
        model = GeminiModel(regions=["r1", "r2"], distribute_requests=True)
        self.assertEqual(model.resolve_region("r2"), "r2")

    def test_resolve_region_first_region(self):
        model = GeminiModel(regions=["r1", "r2"], distribute_requests=True)
        self.assertEqual(model.resolve_region(), "r1")

    def test_resolve_region_none_without_regions(self):
        model = GeminiModel(regions=[], distribute_requests=True)
        self.assertIsNone(model.resolve_region())

    def test_send_history_text_only(self):
        model = GeminiModel()
        conn = GeminiLlmConnection(model=model)
        conn.send_history([{"parts": [{"type": "text", "text": "hello"}]}])

    def test_send_history_rejects_non_text(self):
        model = GeminiModel()
        conn = GeminiLlmConnection(model=model)
        with self.assertRaises(ValueError):
            conn.send_history([{"parts": [{"type": "image", "data": "x"}]}])


if __name__ == "__main__":
    unittest.main()
