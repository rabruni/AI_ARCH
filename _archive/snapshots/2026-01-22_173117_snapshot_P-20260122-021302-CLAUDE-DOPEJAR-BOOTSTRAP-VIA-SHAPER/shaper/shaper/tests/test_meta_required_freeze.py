import unittest

from shaper.model import ShaperModel


class MetaRequiredFreezeTests(unittest.TestCase):
    def test_missing_meta_is_reported(self):
        model = ShaperModel()
        model.objective.append("Objective line")
        model.scope.append("Scope line")
        model.plan.append("Plan line")
        model.acceptance.append("Acceptance line")
        missing = model.missing_sections()
        self.assertIn("ID", missing)
        self.assertIn("Title", missing)
        self.assertIn("Status", missing)
        self.assertIn("ALTITUDE", missing)


if __name__ == "__main__":
    unittest.main()
