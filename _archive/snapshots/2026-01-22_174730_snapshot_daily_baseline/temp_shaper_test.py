import unittest
import os
from pathlib import Path

# It's better to add the project root to sys.path than to use relative imports
# but for a self-contained script, this is a common pattern.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Control_Plane.modules.design_framework.shaper.cli import ShaperCli
from Control_Plane.modules.design_framework.shaper.state_machine import ShaperStateMachine, MODES

class E2EShaperTest(unittest.TestCase):
    def setUp(self):
        """Set up a temporary output directory."""
        self.output_dir = Path("./temp_shaper_output")
        self.output_dir.mkdir(exist_ok=True)
        # Provide mock input/output functions for non-interactive testing
        self.cli = ShaperCli(
            output_dir=self.output_dir,
            input_func=lambda _: "",  # Mock input, not used in this test
            output_func=lambda _: None  # Mock output, suppress printing
        )

    def tearDown(self):
        """Clean up generated files and directory."""
        for f in self.output_dir.glob("*.md"):
            f.unlink()
        self.output_dir.rmdir()

    def test_l3_to_g0_loop(self):
        """Simulates a full L3 shaping session from objective to freeze."""
        print("\n--- Starting L3 Shaping Session ---")

        # 1. Define Objective (L3 altitude is detected)
        print("Injecting Objective...")
        self.cli.process_line("Objective: Create a hello_world.py script.")
        self.assertEqual(self.cli.machine.mode, "SHAPING")
        self.assertEqual(self.cli.router.altitude, "L3")

        # 2. Define Scope
        print("Injecting Scope...")
        self.cli.process_line("Scope: hello_world.py (MODIFIABLE)")
        self.assertIn("hello_world.py (MODIFIABLE)", self.cli.model.scope)

        # 3. Define Plan
        print("Injecting Plan...")
        self.cli.process_line("plan: 1. Write print('Hello, World!') to the file.")
        self.assertIn("1. Write print('Hello, World!') to the file.", self.cli.model.plan)

        # 4. Define Acceptance
        print("Injecting Acceptance...")
        self.cli.process_line("acceptance: python3 hello_world.py exits with 0")
        self.assertIn("python3 hello_world.py exits with 0", self.cli.model.acceptance)
        
        # 5. Add Meta
        print("Injecting Meta...")
        self.cli.process_line("ID: WI-TEST-01")
        self.cli.process_line("Title: Hello World Test")

        # 6. Reveal
        print("Triggering Reveal...")
        self.cli.process_line("show me what you have")
        self.assertTrue(self.cli.model.revealed_once)

        # 7. Freeze
        print("Triggering Freeze...")
        self.cli.process_line("freeze it")
        self.assertEqual(self.cli.machine.mode, "FROZEN")

        # 8. Verify Artifact
        print("Verifying Artifact...")
        expected_file = self.output_dir / "WI-TEST-01.md"
        self.assertTrue(expected_file.exists())
        content = expected_file.read_text()
        self.assertIn("Objective", content)
        self.assertIn("hello_world.py", content)
        self.assertIn("Hello, World!", content)
        print(f"SUCCESS: Artifact '{expected_file}' created successfully.")

if __name__ == "__main__":
    # Note: This is a simple runner. In a real test suite, you'd use
    # unittest.main() or a test runner like pytest.
    suite = unittest.TestLoader().loadTestsFromTestCase(E2EShaperTest)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\nSUCCESS: End-to-End Model Test Passed")
    else:
        print("\nFAIL: End-to-End Model Test Failed")
        sys.exit(1)
