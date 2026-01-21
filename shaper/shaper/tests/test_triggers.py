import unittest

from shaper.shaper.cli import is_trigger, TRIGGER_CONVERGE, TRIGGER_FREEZE, TRIGGER_REVEAL


class TriggerTests(unittest.TestCase):
    def test_exact_trigger_match(self):
        self.assertTrue(is_trigger("show me what you have", TRIGGER_REVEAL))
        self.assertTrue(is_trigger("SHOW ME WHAT YOU HAVE", TRIGGER_REVEAL))
        self.assertFalse(is_trigger("show me", TRIGGER_REVEAL))

    def test_other_triggers(self):
        self.assertTrue(is_trigger("turn this into a work item", TRIGGER_CONVERGE))
        self.assertTrue(is_trigger("freeze it", TRIGGER_FREEZE))
        self.assertFalse(is_trigger("freeze it now", TRIGGER_FREEZE))


if __name__ == "__main__":
    unittest.main()
