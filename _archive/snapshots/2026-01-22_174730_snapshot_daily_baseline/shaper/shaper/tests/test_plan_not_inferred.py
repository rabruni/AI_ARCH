import unittest

from shaper.model import ShaperModel


class PlanInferenceTests(unittest.TestCase):
    def test_plan_not_inferred(self):
        model = ShaperModel()
        model.ingest("We should consider options for rollout.")
        self.assertEqual(model.objective, ["We should consider options for rollout."])
        self.assertEqual(model.plan, [])


if __name__ == "__main__":
    unittest.main()
