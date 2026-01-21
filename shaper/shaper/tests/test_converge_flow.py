import unittest

from shaper.shaper.cli import converge
from shaper.shaper.model import ShaperModel


class ConvergeFlowTests(unittest.TestCase):
    def test_converge_fills_missing_sections(self):
        model = ShaperModel()
        prompts = []
        responses = iter(
            [
                "WI-1",
                "Title text",
                "Draft",
                "L2",
                "Objective line",
                "Scope line",
                "Plan line",
                "Acceptance line",
            ]
        )

        def fake_input(_prompt):
            return next(responses)

        def fake_output(message):
            prompts.append(message)

        converge(model, input_func=fake_input, output_func=fake_output)

        self.assertEqual(model.meta["ID"], "WI-1")
        self.assertEqual(model.meta["Title"], "Title text")
        self.assertEqual(model.meta["Status"], "Draft")
        self.assertEqual(model.meta["ALTITUDE"], "L2")
        self.assertEqual(model.objective, ["Objective line"])
        self.assertEqual(model.scope, ["Scope line"])
        self.assertEqual(model.plan, ["Plan line"])
        self.assertEqual(model.acceptance, ["Acceptance line"])
        self.assertEqual(len(prompts), 8)


if __name__ == "__main__":
    unittest.main()
