import unittest

from shaper.cli import (
    process_line,
    TRIGGER_CONVERGE,
    TRIGGER_FREEZE,
    TRIGGER_REVEAL,
)
from shaper.model import ShaperModel
from shaper.state_machine import ShaperStateMachine


class CliFlowTests(unittest.TestCase):
    def test_reveal_sets_machine_mode(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        outputs = []

        def capture(message):
            outputs.append(message)

        process_line(model, machine, TRIGGER_REVEAL, output_func=capture)
        self.assertEqual(machine.mode, "REVEALED")
        self.assertTrue(outputs)

    def test_converge_requires_reveal(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        outputs = []

        def capture(message):
            outputs.append(message)

        process_line(model, machine, TRIGGER_CONVERGE, output_func=capture)
        self.assertEqual(outputs[-1], "Refuse: reveal required before converge.")

    def test_freeze_requires_reveal(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        outputs = []

        def capture(message):
            outputs.append(message)

        process_line(model, machine, TRIGGER_FREEZE, output_func=capture)
        self.assertEqual(outputs[-1], "Refuse: reveal required before freeze.")

    def test_freeze_requires_missing_sections(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        outputs = []

        def capture(message):
            outputs.append(message)

        process_line(model, machine, TRIGGER_REVEAL, output_func=capture)
        process_line(model, machine, TRIGGER_FREEZE, output_func=capture)
        self.assertIn("Cannot freeze. Missing:", outputs[-1])

    def test_freeze_resets_model(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        outputs = []
        model.meta.update({"ID": "WI-1", "Title": "T", "Status": "Draft", "ALTITUDE": "L2"})
        model.objective.append("Do X")
        model.scope.append("file.txt")
        model.plan.append("Step 1")
        model.acceptance.append("echo ok")

        def capture(message):
            outputs.append(message)

        process_line(model, machine, TRIGGER_REVEAL, output_func=capture)
        process_line(model, machine, TRIGGER_FREEZE, output_func=capture)
        self.assertFalse(model.meta)
        self.assertFalse(model.objective)

    def test_ingest_confirms_objective_phase(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        process_line(model, machine, "Objective: Test objective")
        self.assertTrue(machine.phases_confirmed.get("objective"))

    def test_disallowed_request_rejected(self):
        model = ShaperModel()
        machine = ShaperStateMachine()
        outputs = []

        def capture(message):
            outputs.append(message)

        process_line(model, machine, "Please execute this", output_func=capture)
        self.assertTrue(outputs[-1].startswith("Refuse:"))


if __name__ == "__main__":
    unittest.main()
