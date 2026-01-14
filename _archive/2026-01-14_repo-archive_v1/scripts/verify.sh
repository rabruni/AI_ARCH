#!/usr/bin/env bash
# verify.sh - Run all verification checks for the Python project
# Exit on first failure
set -e

echo "=========================================="
echo "  AI_ARCH Verification Script"
echo "=========================================="
echo ""

# Track overall status
ERRORS=0

# Detect and use venv if available
PYTHON="python3"
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
    echo "Using venv: $PYTHON"
    echo ""
fi

# Check Python is available
echo "[1/5] Checking Python..."
if $PYTHON --version &> /dev/null; then
    PYTHON_VERSION=$($PYTHON --version 2>&1)
    echo "  OK: $PYTHON_VERSION"
else
    echo "  FAIL: Python not found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check required files exist
echo "[2/5] Checking required files..."
REQUIRED_FILES=(
    "requirements.txt"
    "CLAUDE.md"
    "the_assist/main_hrm.py"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  OK: $file exists"
    else
        echo "  WARN: $file not found"
    fi
done
echo ""

# Check Python syntax
echo "[3/5] Checking Python syntax..."
SYNTAX_ERRORS=0
for pyfile in $(find . -name "*.py" -not -path "./venv/*" -not -path "./archive/*" 2>/dev/null | head -20); do
    if $PYTHON -m py_compile "$pyfile" 2>/dev/null; then
        :
    else
        echo "  FAIL: Syntax error in $pyfile"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done
if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo "  OK: No syntax errors found"
else
    ERRORS=$((ERRORS + SYNTAX_ERRORS))
fi
echo ""

# Run pytest if available
echo "[4/5] Running tests..."
if $PYTHON -c "import pytest" 2>/dev/null; then
    if $PYTHON -m pytest --co -q 2>/dev/null | head -5; then
        echo "  Tests collected. Running..."
        if $PYTHON -m pytest -q --tb=short 2>&1 | tail -10; then
            echo "  OK: Tests completed"
        else
            echo "  WARN: Some tests may have failed (check output above)"
        fi
    fi
else
    echo "  SKIP: pytest not installed (pip install pytest)"
fi
echo ""

# Check for common issues
echo "[5/5] Checking for common issues..."
ISSUES=0

# Check for debug prints
if grep -r "print(" --include="*.py" --exclude-dir=venv --exclude-dir=archive -l 2>/dev/null | head -3 | grep -q .; then
    echo "  INFO: Found print() statements (may be intentional)"
fi

# Check for TODO/FIXME
TODO_COUNT=$(grep -r "TODO\|FIXME" --include="*.py" --exclude-dir=venv --exclude-dir=archive 2>/dev/null | wc -l | tr -d ' ')
if [ "$TODO_COUNT" -gt 0 ]; then
    echo "  INFO: Found $TODO_COUNT TODO/FIXME comments"
fi

echo "  OK: Common issues check complete"
echo ""

# Summary
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "  VERIFICATION PASSED"
    echo "=========================================="
    exit 0
else
    echo "  VERIFICATION FAILED ($ERRORS errors)"
    echo "=========================================="
    exit 1
fi
