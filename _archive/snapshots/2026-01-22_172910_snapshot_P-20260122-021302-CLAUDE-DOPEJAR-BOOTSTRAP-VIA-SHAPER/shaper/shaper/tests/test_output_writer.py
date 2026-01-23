import tempfile
import unittest
from pathlib import Path

from shaper.output_writer import write_output


class OutputWriterTests(unittest.TestCase):
    def test_writes_new_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_ITEM.md"
            result = write_output(path, "content")
            self.assertTrue(result.exists())

    def test_increments_sequence_when_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_ITEM.md"
            path.write_text("first", encoding="utf-8")
            result = write_output(path, "second")
            self.assertEqual(result.name, "WORK_ITEM_1.md")

    def test_increments_sequence_multiple(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "WORK_ITEM.md"
            base.write_text("first", encoding="utf-8")
            (Path(tmp) / "WORK_ITEM_1.md").write_text("second", encoding="utf-8")
            result = write_output(base, "third")
            self.assertEqual(result.name, "WORK_ITEM_2.md")

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_ITEM.md"
            path.write_text("first", encoding="utf-8")
            result = write_output(path, "second")
            self.assertEqual(path.read_text(encoding="utf-8"), "first")
            self.assertEqual(result.read_text(encoding="utf-8"), "second")

    def test_handles_no_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "WORK_ITEM"
            path.write_text("first", encoding="utf-8")
            result = write_output(path, "second")
            self.assertEqual(result.name, "WORK_ITEM_1")


if __name__ == "__main__":
    unittest.main()
