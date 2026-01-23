import unittest

from shaper.spec_model import SpecModel, render_spec


class SpecModelTests(unittest.TestCase):
    def test_render_spec_includes_sections(self):
        model = SpecModel()
        model.meta.update({"ID": "SPEC-1", "Title": "Spec", "Status": "Draft", "ALTITUDE": "L3"})
        model.overview.append("Overview line")
        model.requirements.append("Requirement line")
        model.design.append("Design line")
        model.tests.append("Test line")

        output = render_spec(model)

        self.assertIn("## Overview", output)
        self.assertIn("## Requirements", output)
        self.assertIn("## Design", output)
        self.assertIn("## Tests", output)

    def test_missing_sections_reports_meta(self):
        model = SpecModel()
        missing = model.missing_sections()
        self.assertIn("ID", missing)
        self.assertIn("Title", missing)
        self.assertIn("Status", missing)
        self.assertIn("ALTITUDE", missing)

    def test_missing_sections_reports_body(self):
        model = SpecModel()
        model.meta.update({"ID": "SPEC-1", "Title": "Spec", "Status": "Draft", "ALTITUDE": "L3"})
        missing = model.missing_sections()
        self.assertIn("Overview", missing)
        self.assertIn("Requirements", missing)
        self.assertIn("Design", missing)
        self.assertIn("Tests", missing)

    def test_render_spec_front_matter(self):
        model = SpecModel()
        model.meta.update({"ID": "SPEC-1", "Title": "Spec", "Status": "Draft", "ALTITUDE": "L3"})
        model.overview.append("Overview line")
        model.requirements.append("Requirement line")
        model.design.append("Design line")
        model.tests.append("Test line")
        output = render_spec(model)
        self.assertTrue(output.startswith("---"))
        self.assertIn("ID: SPEC-1", output)

    def test_requirements_are_numbered(self):
        model = SpecModel()
        model.meta.update({"ID": "SPEC-1", "Title": "Spec", "Status": "Draft", "ALTITUDE": "L3"})
        model.overview.append("Overview line")
        model.requirements.extend(["R1", "R2"])
        model.design.append("Design line")
        model.tests.append("Test line")
        output = render_spec(model)
        self.assertIn("1. R1", output)
        self.assertIn("2. R2", output)


if __name__ == "__main__":
    unittest.main()
