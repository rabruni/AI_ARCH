import unittest

from shaper.model import ShaperModel
from shaper.work_item import render_work_item


class FreezeBehaviorTests(unittest.TestCase):
    def test_freeze_resets_model(self):
        model = ShaperModel()
        model.meta.update({"ID": "WI-1", "Title": "T", "Status": "Draft", "ALTITUDE": "L2"})
        model.objective.append("Do X")
        model.scope.append("file.txt")
        model.plan.append("Step 1")
        model.acceptance.append("echo ok")
        _ = render_work_item(model)
        model.reset()
        self.assertFalse(model.meta)
        self.assertFalse(model.objective)
        self.assertFalse(model.scope)
        self.assertFalse(model.plan)
        self.assertFalse(model.acceptance)


if __name__ == "__main__":
    unittest.main()
