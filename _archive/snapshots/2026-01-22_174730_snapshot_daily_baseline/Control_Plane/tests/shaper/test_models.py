"""Tests for Shaper v2 Models and Renderers.

Covers TEST_PLAN.md:
- A. L3 Work Item Model (Tests 1-10)
- B. L4 Spec Model (Tests 11-20)
- C. Deterministic Rendering (Tests 21-26)
"""

import unittest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules" / "design_framework"))

from shaper.models import ShaperModel, SpecModel
from shaper.renderers import render_work_item, render_spec


class TestL3WorkItemModel(unittest.TestCase):
    """A. L3 Work Item Model (Tests 1-10)"""

    def test_01_ingest_objective_line_populates_objective_list(self):
        """Test 1: Ingest objective line populates objective list."""
        model = ShaperModel()
        model.ingest("objective: Build the feature")
        self.assertEqual(model.objective, ["Build the feature"])

    def test_02_ingest_scope_line_populates_scope_list(self):
        """Test 2: Ingest scope line populates scope list."""
        model = ShaperModel()
        model.ingest("scope: src/main.py")
        self.assertEqual(model.scope, ["src/main.py"])

    def test_03_ingest_plan_line_populates_plan_list(self):
        """Test 3: Ingest plan line populates plan list."""
        model = ShaperModel()
        model.ingest("plan: Step one")
        self.assertEqual(model.plan, ["Step one"])

    def test_04_ingest_acceptance_line_populates_acceptance_list(self):
        """Test 4: Ingest acceptance line populates acceptance list."""
        model = ShaperModel()
        model.ingest("acceptance: pytest tests/")
        self.assertEqual(model.acceptance, ["pytest tests/"])

    def test_05_meta_fields_captured_when_prefixed(self):
        """Test 5: Meta fields captured when prefixed."""
        model = ShaperModel()
        model.ingest("ID: WI-001")
        model.ingest("Title: Test Work Item")
        model.ingest("Status: Draft")
        model.ingest("ALTITUDE: L3")
        self.assertEqual(model.meta["ID"], "WI-001")
        self.assertEqual(model.meta["Title"], "Test Work Item")
        self.assertEqual(model.meta["Status"], "Draft")
        self.assertEqual(model.meta["ALTITUDE"], "L3")

    def test_06_missing_sections_include_all_meta_fields_when_empty(self):
        """Test 6: Missing sections include all meta fields when empty."""
        model = ShaperModel()
        missing = model.missing_sections()
        self.assertIn("ID", missing)
        self.assertIn("Title", missing)
        self.assertIn("Status", missing)
        self.assertIn("ALTITUDE", missing)

    def test_07_missing_sections_include_body_sections_when_empty(self):
        """Test 7: Missing sections include Objective/Scope/Plan/Acceptance when empty."""
        model = ShaperModel()
        model.meta = {"ID": "WI-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L3"}
        missing = model.missing_sections()
        self.assertIn("Objective", missing)
        self.assertIn("Scope", missing)
        self.assertIn("Implementation Plan", missing)
        self.assertIn("Acceptance Commands", missing)

    def test_08_no_inference_generic_line_does_not_populate_plan(self):
        """Test 8: No-inference: generic line does not populate plan."""
        model = ShaperModel()
        model.ingest("We should consider options for rollout.")
        self.assertEqual(model.objective, ["We should consider options for rollout."])
        self.assertEqual(model.plan, [])

    def test_09_reset_clears_all_lists_and_meta(self):
        """Test 9: Reset clears all lists and meta."""
        model = ShaperModel()
        model.objective.append("test")
        model.scope.append("test")
        model.plan.append("test")
        model.acceptance.append("test")
        model.meta["ID"] = "WI-001"
        model.revealed_once = True
        model.reset()
        self.assertEqual(model.objective, [])
        self.assertEqual(model.scope, [])
        self.assertEqual(model.plan, [])
        self.assertEqual(model.acceptance, [])
        self.assertEqual(model.meta, {})
        self.assertFalse(model.revealed_once)

    def test_10_reveal_flag_resets_on_reset(self):
        """Test 10: Reveal flag resets on reset."""
        model = ShaperModel()
        model.revealed_once = True
        model.reset()
        self.assertFalse(model.revealed_once)


class TestL4SpecModel(unittest.TestCase):
    """B. L4 Spec Model (Tests 11-20)"""

    def test_11_ingest_overview_line_populates_overview(self):
        """Test 11: Ingest overview line populates overview."""
        model = SpecModel()
        model.ingest("overview: System architecture")
        self.assertEqual(model.overview, ["System architecture"])

    def test_12_ingest_problem_line_populates_problem(self):
        """Test 12: Ingest problem line populates problem."""
        model = SpecModel()
        model.ingest("problem: Current system is slow")
        self.assertEqual(model.problem, ["Current system is slow"])

    def test_13_ingest_non_goals_line_populates_non_goals(self):
        """Test 13: Ingest non-goals line populates non_goals."""
        model = SpecModel()
        model.ingest("non-goal: Mobile support")
        self.assertEqual(model.non_goals, ["Mobile support"])

    def test_14_ingest_success_criteria_line_populates_success_criteria(self):
        """Test 14: Ingest success criteria line populates success_criteria."""
        model = SpecModel()
        model.ingest("success: Response time < 100ms")
        self.assertEqual(model.success_criteria, ["Response time < 100ms"])

    def test_15_phases_suggested_do_not_mark_confirmed(self):
        """Test 15: Phases suggested do not mark confirmed."""
        model = SpecModel()
        model.suggest_phase("Phase 1: Planning")
        self.assertFalse(model.phases_confirmed)
        self.assertEqual(model._suggested_phases, ["Phase 1: Planning"])
        self.assertEqual(model.phases, [])

    def test_16_missing_sections_ignore_work_items(self):
        """Test 16: Missing sections ignore work_items."""
        model = SpecModel()
        model.meta = {"ID": "SPEC-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L4"}
        model.overview.append("o")
        model.problem.append("p")
        model.non_goals.append("n")
        model.phases.append("ph")
        model.success_criteria.append("s")
        # work_items is empty but should not be in missing
        missing = model.missing_sections()
        self.assertNotIn("Work Items", missing)
        self.assertEqual(missing, [])

    def test_17_missing_sections_include_required_fields_when_empty(self):
        """Test 17: Missing sections include required fields when empty."""
        model = SpecModel()
        missing = model.missing_sections()
        self.assertIn("ID", missing)
        self.assertIn("Overview", missing)
        self.assertIn("Problem", missing)
        self.assertIn("Non-Goals", missing)
        self.assertIn("Phases", missing)
        self.assertIn("Success Criteria", missing)

    def test_18_reset_clears_all_lists_meta_flags(self):
        """Test 18: Reset clears all lists, meta, flags."""
        model = SpecModel()
        model.overview.append("o")
        model.problem.append("p")
        model.non_goals.append("n")
        model.phases.append("ph")
        model.work_items.append("w")
        model.success_criteria.append("s")
        model.meta["ID"] = "SPEC-001"
        model.revealed_once = True
        model.phases_confirmed = True
        model.reset()
        self.assertEqual(model.overview, [])
        self.assertEqual(model.problem, [])
        self.assertEqual(model.non_goals, [])
        self.assertEqual(model.phases, [])
        self.assertEqual(model.work_items, [])
        self.assertEqual(model.success_criteria, [])
        self.assertEqual(model.meta, {})
        self.assertFalse(model.revealed_once)
        self.assertFalse(model.phases_confirmed)

    def test_19_reveal_flag_defaults_false(self):
        """Test 19: Reveal flag defaults false."""
        model = SpecModel()
        self.assertFalse(model.revealed_once)

    def test_20_phases_confirmed_defaults_false(self):
        """Test 20: Phases_confirmed defaults false."""
        model = SpecModel()
        self.assertFalse(model.phases_confirmed)


class TestDeterministicRendering(unittest.TestCase):
    """C. Deterministic Rendering (Tests 21-26)"""

    def test_21_work_item_render_ordering_matches_schema(self):
        """Test 21: Work item render ordering matches schema."""
        model = ShaperModel()
        model.meta = {"ID": "WI-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L3"}
        model.objective.append("o")
        model.scope.append("s")
        model.plan.append("p")
        model.acceptance.append("a")
        output = render_work_item(model)
        # Check ordering: front matter, then sections in order
        self.assertIn("---", output)
        objective_pos = output.find("## Objective")
        scope_pos = output.find("## Scope: File Permissions")
        plan_pos = output.find("## Implementation Plan")
        acceptance_pos = output.find("## Acceptance Commands")
        self.assertLess(objective_pos, scope_pos)
        self.assertLess(scope_pos, plan_pos)
        self.assertLess(plan_pos, acceptance_pos)

    def test_22_spec_render_ordering_matches_schema(self):
        """Test 22: Spec render ordering matches schema."""
        model = SpecModel()
        model.meta = {"ID": "SPEC-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L4"}
        model.overview.append("o")
        model.problem.append("p")
        model.non_goals.append("n")
        model.phases.append("ph")
        model.success_criteria.append("s")
        output = render_spec(model)
        # Check ordering
        overview_pos = output.find("## Overview")
        problem_pos = output.find("## Problem")
        non_goals_pos = output.find("## Non-Goals")
        phases_pos = output.find("## Phases")
        success_pos = output.find("## Success Criteria")
        self.assertLess(overview_pos, problem_pos)
        self.assertLess(problem_pos, non_goals_pos)
        self.assertLess(non_goals_pos, phases_pos)
        self.assertLess(phases_pos, success_pos)

    def test_23_rendering_uses_lf_and_single_trailing_newline(self):
        """Test 23: Rendering uses LF and single trailing newline."""
        model = ShaperModel()
        model.meta = {"ID": "WI-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L3"}
        model.objective.append("o")
        model.scope.append("s")
        model.plan.append("p")
        model.acceptance.append("a")
        output = render_work_item(model)
        # Should end with single newline
        self.assertTrue(output.endswith("\n"))
        self.assertFalse(output.endswith("\n\n"))
        # Should use LF only (no CRLF)
        self.assertNotIn("\r", output)

    def test_24_identical_state_produces_identical_output_work_item(self):
        """Test 24: Identical state produces identical output (work item)."""
        model1 = ShaperModel()
        model1.meta = {"ID": "WI-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L3"}
        model1.objective.append("o")
        model1.scope.append("s")
        model1.plan.append("p")
        model1.acceptance.append("a")

        model2 = ShaperModel()
        model2.meta = {"ID": "WI-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L3"}
        model2.objective.append("o")
        model2.scope.append("s")
        model2.plan.append("p")
        model2.acceptance.append("a")

        output1 = render_work_item(model1)
        output2 = render_work_item(model2)
        self.assertEqual(output1, output2)

    def test_25_identical_state_produces_identical_output_spec(self):
        """Test 25: Identical state produces identical output (spec)."""
        model1 = SpecModel()
        model1.meta = {"ID": "SPEC-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L4"}
        model1.overview.append("o")
        model1.problem.append("p")
        model1.non_goals.append("n")
        model1.phases.append("ph")
        model1.success_criteria.append("s")

        model2 = SpecModel()
        model2.meta = {"ID": "SPEC-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L4"}
        model2.overview.append("o")
        model2.problem.append("p")
        model2.non_goals.append("n")
        model2.phases.append("ph")
        model2.success_criteria.append("s")

        output1 = render_spec(model1)
        output2 = render_spec(model2)
        self.assertEqual(output1, output2)

    def test_26_no_timestamps_random_content_present(self):
        """Test 26: No timestamps/random content present."""
        model = ShaperModel()
        model.meta = {"ID": "WI-001", "Title": "T", "Status": "Draft", "ALTITUDE": "L3"}
        model.objective.append("o")
        model.scope.append("s")
        model.plan.append("p")
        model.acceptance.append("a")
        output = render_work_item(model)
        # Check no common timestamp patterns
        import re
        # ISO timestamp pattern
        self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", output))
        # UUID pattern
        self.assertIsNone(re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", output))


if __name__ == "__main__":
    unittest.main()
