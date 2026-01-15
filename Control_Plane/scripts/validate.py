#!/usr/bin/env python3
"""
Validate - Layer 2: Integrity Checks

Purpose: Is the data well-formed?
Checks: Checksums, schema, referential integrity, version compatibility.
Assumes: Bootstrap passed (environment exists).
If fails: System exists but data is corrupt/invalid.

Usage:
    python Control_Plane/scripts/validate.py

Exit codes:
    0 = Validation OK
    1 = Validation FAIL
"""

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional


def get_repo_root() -> Path:
    """Find repository root (contains .git/)."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


REPO_ROOT = get_repo_root()


class ValidationResult:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def ok(self, category: str, check: str):
        self.checks.append(("OK", category, check))
        self.passed += 1

    def fail(self, category: str, check: str):
        self.checks.append(("FAIL", category, check))
        self.failed += 1

    def warn(self, category: str, check: str):
        self.checks.append(("WARN", category, check))
        self.warnings += 1

    def report(self) -> str:
        lines = ["=" * 60, "VALIDATION REPORT", "=" * 60, ""]

        current_category = None
        for status, category, msg in self.checks:
            if category != current_category:
                if current_category is not None:
                    lines.append("")
                lines.append(f"[{category}]")
                current_category = category

            symbol = {"OK": "✓", "FAIL": "✗", "WARN": "⚠"}[status]
            lines.append(f"  [{symbol}] {msg}")

        lines.append("")
        lines.append("-" * 60)

        if self.failed == 0:
            status = "VALIDATION OK"
            if self.warnings > 0:
                status += f" (with {self.warnings} warnings)"
            lines.append(f"{status}: {self.passed} checks passed")
            lines.append("Data integrity verified. Run init next.")
        else:
            lines.append(f"VALIDATION FAIL: {self.failed} checks failed")
            lines.append("Data integrity compromised. Fix issues above.")

        lines.append("=" * 60)
        return "\n".join(lines)


def sha256_file(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_manifest() -> Optional[dict]:
    """Load MANIFEST.json."""
    manifest_path = REPO_ROOT / "Control_Plane" / "MANIFEST.json"
    if not manifest_path.is_file():
        return None
    with open(manifest_path) as f:
        return json.load(f)


def check_checksums(result: ValidationResult):
    """Verify file checksums against manifest."""
    manifest = load_manifest()

    if manifest is None:
        result.fail("Checksums", "MANIFEST.json not found")
        return

    result.ok("Checksums", f"MANIFEST.json loaded (v{manifest.get('version', 'unknown')})")

    checksums = manifest.get("checksums", {})
    verified = 0
    failed = 0

    for rel_path, info in checksums.items():
        full_path = REPO_ROOT / rel_path
        if not full_path.is_file():
            result.fail("Checksums", f"Missing: {rel_path}")
            failed += 1
            continue

        expected = info.get("sha256", "")
        actual = sha256_file(full_path)

        if actual == expected:
            verified += 1
        else:
            result.fail("Checksums", f"Mismatch: {rel_path}")
            failed += 1

    if failed == 0:
        result.ok("Checksums", f"All {verified} files verified")
    else:
        result.fail("Checksums", f"{failed} files failed checksum")


def check_registry_schema(result: ValidationResult):
    """Validate registry CSV schema."""
    registry_dir = REPO_ROOT / "Control_Plane" / "registries"

    if not registry_dir.is_dir():
        result.fail("Schema", "Registry directory not found")
        return

    csv_files = list(registry_dir.glob("*.csv"))
    if not csv_files:
        result.fail("Schema", "No registry files found")
        return

    required_columns = ["name", "status", "selected"]
    valid_status = {"missing", "draft", "active", "deprecated"}
    valid_selected = {"yes", "no", ""}

    valid_count = 0
    for csv_file in csv_files:
        rel_path = csv_file.relative_to(REPO_ROOT)
        try:
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []

                # Check for ID column (id or ends with _id)
                id_cols = [h for h in headers if h == "id" or h.endswith("_id")]
                if not id_cols:
                    result.fail("Schema", f"{rel_path}: No *_id column")
                    continue

                # Check required columns
                missing = [c for c in required_columns if c not in headers]
                if missing:
                    result.fail("Schema", f"{rel_path}: Missing columns: {missing}")
                    continue

                # Check row values
                row_errors = 0
                for i, row in enumerate(reader, start=2):
                    status = row.get("status", "").strip()
                    selected = row.get("selected", "").strip()

                    if status and status not in valid_status:
                        row_errors += 1
                    if selected and selected not in valid_selected:
                        row_errors += 1

                if row_errors > 0:
                    result.warn("Schema", f"{rel_path}: {row_errors} rows with invalid enum values")
                else:
                    valid_count += 1

        except Exception as e:
            result.fail("Schema", f"{rel_path}: Parse error: {e}")

    result.ok("Schema", f"{valid_count}/{len(csv_files)} registries valid")


def check_referential_integrity(result: ValidationResult):
    """Check that artifact_path references exist."""
    registry_dir = REPO_ROOT / "Control_Plane" / "registries"

    if not registry_dir.is_dir():
        return

    csv_files = list(registry_dir.glob("*.csv"))
    path_columns = ["artifact_path", "child_registry_path"]

    missing_refs = []
    checked = 0

    for csv_file in csv_files:
        try:
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []

                for row in reader:
                    status = row.get("status", "").strip()

                    # Skip items marked as missing - they're expected to not exist
                    if status == "missing":
                        continue

                    for col in path_columns:
                        if col not in headers:
                            continue

                        path_val = row.get(col, "").strip()
                        if not path_val:
                            continue

                        # Normalize path
                        if path_val.startswith("/"):
                            path_val = path_val[1:]

                        full_path = REPO_ROOT / path_val
                        checked += 1

                        if not full_path.exists():
                            item_id = row.get(headers[0], "unknown")
                            missing_refs.append(f"{item_id}: {path_val}")

        except Exception:
            pass

    if missing_refs:
        # Only show first 5
        for ref in missing_refs[:5]:
            result.warn("References", f"Missing: {ref}")
        if len(missing_refs) > 5:
            result.warn("References", f"...and {len(missing_refs) - 5} more")
    else:
        result.ok("References", f"{checked} path references verified")


def check_version_compatibility(result: ValidationResult):
    """Check version file exists and is valid."""
    version_file = REPO_ROOT / "VERSION"

    if not version_file.is_file():
        result.fail("Version", "VERSION file not found")
        return

    version = version_file.read_text().strip()
    if not version:
        result.fail("Version", "VERSION file is empty")
        return

    # Simple semver check
    parts = version.split(".")
    if len(parts) >= 2:
        result.ok("Version", f"System version: {version}")
    else:
        result.warn("Version", f"Non-standard version format: {version}")


def check_constitution(result: ValidationResult):
    """Check SYSTEM_CONSTITUTION.md exists and has YAML block."""
    constitution_path = REPO_ROOT / "SYSTEM_CONSTITUTION.md"

    if not constitution_path.is_file():
        result.fail("Constitution", "SYSTEM_CONSTITUTION.md not found")
        return

    content = constitution_path.read_text()

    if "```yaml" in content or "```yml" in content:
        result.ok("Constitution", "Has machine-readable YAML block")
    else:
        result.warn("Constitution", "No YAML block found")

    if "registry_schema" in content:
        result.ok("Constitution", "Defines registry schema")
    else:
        result.warn("Constitution", "No registry_schema defined")


def validate() -> bool:
    """Run all validation checks."""
    result = ValidationResult()

    print("Running validation checks...\n")

    # Layer 2 checks - integrity
    check_checksums(result)
    check_registry_schema(result)
    check_referential_integrity(result)
    check_version_compatibility(result)
    check_constitution(result)

    print(result.report())

    return result.failed == 0


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
