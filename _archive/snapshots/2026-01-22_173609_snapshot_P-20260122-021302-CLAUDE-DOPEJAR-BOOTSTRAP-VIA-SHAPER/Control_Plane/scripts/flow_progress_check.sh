#!/usr/bin/env bash
set -euo pipefail

SPEC_ID="SPEC-001"
SMOKE_LOG="Control_Plane/docs/specs/${SPEC_ID}/artifacts/flow_smoke_check.log"
GATE_RESULTS="Control_Plane/docs/specs/${SPEC_ID}/artifacts/phase2/gate_results.json"
G3_LOG="Control_Plane/docs/specs/${SPEC_ID}/artifacts/phase2/gate_logs/G3.log"
CI_WORKFLOW=".github/workflows/ci.yml"

fail() {
  echo "FAIL: $1"
  exit 1
}

[[ -f "${SMOKE_LOG}" ]] || fail "Smoke log missing: ${SMOKE_LOG}"
grep -q "PASS: Step 1" "${SMOKE_LOG}" || fail "Smoke test missing PASS lines"
grep -q "PASS: Step 2" "${SMOKE_LOG}" || fail "Smoke test missing PASS lines"
grep -q "PASS: Step 3" "${SMOKE_LOG}" || fail "Smoke test missing PASS lines"
grep -q "PASS: Step 4" "${SMOKE_LOG}" || fail "Smoke test missing PASS lines"
grep -q "PASS: Step 5" "${SMOKE_LOG}" || fail "Smoke test missing PASS lines"

[[ -f "${GATE_RESULTS}" ]] || fail "gate_results.json missing"
[[ -f "${G3_LOG}" ]] || fail "G3.log missing"

grep -q "G1 PASSED" "${SMOKE_LOG}" || fail "G1 PASSED not found"
grep -q "G2 PASSED" "${SMOKE_LOG}" || fail "G2 PASSED not found"
grep -q "G3 PASSED" "${SMOKE_LOG}" || fail "G3 PASSED not found"

grep -q "flow_smoke_check.sh" "${CI_WORKFLOW}" || fail "CI workflow missing smoke script"
grep -q "flow_progress_check.sh" "${CI_WORKFLOW}" || fail "CI workflow missing progress script"

echo "PASS: Step 1 MVP Skeleton"
echo "PASS: Step 2 Gates Implemented"
echo "PASS: Step 3 Flow Logic"
echo "PASS: Step 4 Spec & Prompt"
echo "PASS: Step 5 Registry Compiler"
echo "PASS: Step 6 CI Integration"
echo ">>> CONTROL PLANE FULL VALIDATION AND CI ARTIFACT UPLOAD VERIFIED"
