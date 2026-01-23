import unittest

from shaper.router import detect_altitude


class RouterAltitudeTests(unittest.TestCase):
    def test_detects_known_altitudes(self):
        self.assertEqual(detect_altitude("Vision for the product").altitude, "L4")
        self.assertEqual(detect_altitude("Architecture approach").altitude, "L3")
        self.assertEqual(detect_altitude("Plan the steps").altitude, "L2")
        self.assertEqual(detect_altitude("Implement the fix").altitude, "L1")

    def test_requires_clarification_for_unknown(self):
        route = detect_altitude("Hello there")
        self.assertEqual(route.altitude, "UNCLEAR")
        self.assertIsNotNone(route.clarification)

    def test_empty_input_is_unclear(self):
        route = detect_altitude("   ")
        self.assertEqual(route.altitude, "UNCLEAR")
        self.assertIsNotNone(route.clarification)

    def test_detects_keywords_case_insensitive(self):
        self.assertEqual(detect_altitude("STRATEGY overview").altitude, "L4")
        self.assertEqual(detect_altitude("ARCHITECTURE notes").altitude, "L3")


if __name__ == "__main__":
    unittest.main()
