#!/usr/bin/env bash
# validate_repo.sh - Comprehensive repository validation
# Exits nonzero on any failure

set -e

echo "============================================"
echo "  AI_ARCH Repository Validation"
echo "============================================"
echo ""

ERRORS=0
WARNINGS=0

# Detect and use venv if available
PYTHON="python3"
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
    echo "Using venv: $PYTHON"
fi
echo ""

# 1. Check required structure
echo "[1/7] Checking required directory structure..."
REQUIRED_DIRS=(
    "docs"
    "docs/architecture"
    "docs/decisions"
    "docs/runbooks"
    "docs/snapshots"
    "scripts"
    "locked_system"
    "the_assist"
)
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  OK: $dir/"
    else
        echo "  FAIL: $dir/ missing"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# 2. Check required files
echo "[2/7] Checking required files..."
REQUIRED_FILES=(
    "README.md"
    "CLAUDE.md"
    "requirements.txt"
    "run.sh"
    "docs/README.md"
    "scripts/verify.sh"
    "scripts/validate_repo.sh"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  OK: $file"
    else
        echo "  FAIL: $file missing"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# 3. Check Python syntax
echo "[3/7] Checking Python syntax..."
SYNTAX_ERRORS=0
for pyfile in $(find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" 2>/dev/null | head -30); do
    if ! $PYTHON -m py_compile "$pyfile" 2>/dev/null; then
        echo "  FAIL: Syntax error in $pyfile"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done
if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo "  OK: No syntax errors in checked files"
else
    ERRORS=$((ERRORS + SYNTAX_ERRORS))
fi
echo ""

# 4. Run pytest
echo "[4/7] Running tests..."
if $PYTHON -c "import pytest" 2>/dev/null; then
    # Exclude archive from tests to avoid running legacy test files
    if $PYTHON -m pytest --ignore=archive/ -q --tb=line 2>&1; then
        echo "  OK: Tests passed"
    else
        echo "  FAIL: Some tests failed"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  SKIP: pytest not installed"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 5. Check for legacy tag
echo "[5/7] Checking legacy preservation..."
if git tag -l "legacy/v*" | grep -q .; then
    LEGACY_TAG=$(git tag -l "legacy/v*" | tail -1)
    echo "  OK: Legacy tag exists: $LEGACY_TAG"
else
    echo "  WARN: No legacy tag found"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 6. Check documentation
echo "[6/7] Checking documentation..."
DOC_FILES=(
    "docs/snapshots/2026-01-14_pre-refactor/README.md"
    "docs/snapshots/2026-01-14_pre-refactor/TREE.txt"
    "docs/snapshots/2026-01-14_pre-refactor/NOTES.md"
    "docs/decisions/2026-01-14_framework_refactor_ADR.md"
)
for doc in "${DOC_FILES[@]}"; do
    if [ -f "$doc" ]; then
        echo "  OK: $doc"
    else
        echo "  WARN: $doc missing"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo ""

# 7. Check entry points
echo "[7/7] Checking entry points..."
ENTRY_POINTS=(
    "run.sh"
    "the_assist/main_hrm.py"
    "locked_system/cli.py"
)
for entry in "${ENTRY_POINTS[@]}"; do
    if [ -f "$entry" ]; then
        echo "  OK: $entry exists"
    else
        echo "  WARN: $entry missing"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo ""

# Summary
echo "============================================"
if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -gt 0 ]; then
        echo "  VALIDATION PASSED (with $WARNINGS warnings)"
    else
        echo "  VALIDATION PASSED"
    fi
    echo "============================================"
    exit 0
else
    echo "  VALIDATION FAILED"
    echo "  Errors: $ERRORS"
    echo "  Warnings: $WARNINGS"
    echo "============================================"
    exit 1
fi
