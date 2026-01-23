#!/usr/bin/env bash
set -euo pipefail

REGISTRY_XLSX="Control_Plane/registries/Prompt Map.xlsx"
REGISTRY_JSON="Control_Plane/registries/compiled/registry.json"
SPEC_ID="SPEC-001"

RUN_PHASE2="1"
for arg in "$@"; do
  case "$arg" in
    --spec=*)
      SPEC_ID="${arg#*=}"
      ;;
    --phase1)
      RUN_PHASE2="1"
      ;;
  esac
done

ARTIFACTS_DIR="Control_Plane/docs/specs/${SPEC_ID}/artifacts"
LOG_PATH="${ARTIFACTS_DIR}/flow_smoke_check.log"
mkdir -p "${ARTIFACTS_DIR}"

: > "${LOG_PATH}"

log() {
  echo "$*" | tee -a "${LOG_PATH}"
}

run_step() {
  local label="$1"
  shift
  if "$@" 2>&1 | tee -a "${LOG_PATH}"; then
    log "PASS: ${label}"
  else
    log "FAIL: ${label}"
    exit 1
  fi
}

run_step "Step 1 Compile Registry" \
  python3 Control_Plane/cp.py compile-registry "${REGISTRY_XLSX}" --output "${REGISTRY_JSON}"

run_step "Step 2 Start Flow Session" \
  python3 Control_Plane/cp.py flow start "${SPEC_ID}" --registry "${REGISTRY_JSON}"

run_step "Step 3 Phase0A Next" \
  python3 Control_Plane/cp.py flow next "${SPEC_ID}"
run_step "Step 3b Phase0A Done" \
  python3 Control_Plane/cp.py flow done "${SPEC_ID}" --phase Phase0A --paste "ok"

run_step "Step 4 Phase1 Next" \
  python3 Control_Plane/cp.py flow next "${SPEC_ID}"
run_step "Step 4b Phase1 Done" \
  python3 Control_Plane/cp.py flow done "${SPEC_ID}" --phase Phase1 --paste "ok"

if [[ "${RUN_PHASE2}" == "1" ]]; then
  run_step "Step 5 Phase2 Next" \
    python3 Control_Plane/cp.py flow next "${SPEC_ID}"
  run_step "Step 5b Phase2 Done" \
    python3 Control_Plane/cp.py flow done "${SPEC_ID}" --phase Phase2 --paste "ok"
fi

GATE_RESULTS="${ARTIFACTS_DIR}/phase2/gate_results.json"
G3_LOG="${ARTIFACTS_DIR}/phase2/gate_logs/G3.log"

run_step "Step 6 Verify gate_results.json" test -f "${GATE_RESULTS}"
run_step "Step 7 Verify G3.log" test -f "${G3_LOG}"

if [[ "${SPEC_ID}" == "SPEC-002" ]]; then
  run_step "Step 8 Verify G0 gate present" \
    python3 - <<'PY'
import json
from pathlib import Path
artifact_root = Path("Control_Plane/docs/specs/SPEC-002/artifacts")
found = False
for path in artifact_root.rglob("gate_results.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    if any(item.get("gate_id") == "G0" for item in data):
        found = True
        break
if not found:
    raise SystemExit("Missing G0 entry in any gate_results.json under SPEC-002")
PY
fi

if [[ "${SPEC_ID}" == "SPEC-003" ]]; then
  run_step "Step 8 Verify G0 with valid WORK_ITEM (path, id, hash)" \
    python3 - <<'PY'
import json
from pathlib import Path
artifact_root = Path("Control_Plane/docs/specs/SPEC-003/artifacts")
found_g0_pass = False
for path in artifact_root.rglob("gate_results.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data:
        if item.get("gate_id") == "G0" and item.get("status") == "passed":
            evidence = item.get("evidence") or {}
            # Check all required evidence fields
            if not evidence.get("work_item_path"):
                raise SystemExit("G0 evidence missing work_item_path")
            if not evidence.get("work_item_id"):
                raise SystemExit("G0 evidence missing work_item_id")
            if not evidence.get("work_item_hash"):
                raise SystemExit("G0 evidence missing work_item_hash")
            if evidence.get("work_item_validated") is not True:
                raise SystemExit("G0 evidence work_item_validated is not True")
            found_g0_pass = True
            print(f"G0 evidence verified: id={evidence['work_item_id']}, hash={evidence['work_item_hash'][:16]}...")
            break
    if found_g0_pass:
        break
if not found_g0_pass:
    raise SystemExit("G0 did not pass with complete evidence for SPEC-003")
PY

  log "Testing G0 failure with invalid work item..."
  # Temporarily swap to invalid work item
  COMMIT_MD="Control_Plane/docs/specs/SPEC-003/08_commit.md"
  BACKUP=$(cat "${COMMIT_MD}")
  sed -i.bak 's|WI-003-01.md|WI-003-02-invalid.md|' "${COMMIT_MD}"

  # Run G0 and expect failure
  run_step "Step 9 Verify G0 fails with invalid WORK_ITEM" \
    python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from pathlib import Path
from Control_Plane.flow_runner.gate_runner import GateRunner
runner = GateRunner(Path.cwd())
result = runner.run_gate("G0", "SPEC-003", "Phase0A")
if result["status"] != "failed":
    raise SystemExit(f"Expected G0 to fail with invalid work item, got: {result['status']}")
if "validation failed" not in result.get("reason", "").lower():
    raise SystemExit(f"Expected validation failure message, got: {result.get('reason')}")
print("G0 correctly failed for invalid work item")
PY

  # Restore original
  echo "${BACKUP}" > "${COMMIT_MD}"
  rm -f "${COMMIT_MD}.bak"

  log "Testing G0 failure with tampered work item (hash mismatch)..."
  # Tamper with the valid work item file
  WORK_ITEM="Control_Plane/docs/specs/SPEC-003/work_items/WI-003-01.md"
  WORK_ITEM_BACKUP=$(cat "${WORK_ITEM}")
  echo "# TAMPERED CONTENT" >> "${WORK_ITEM}"

  # Run G0 and expect hash mismatch failure
  run_step "Step 10 Verify G0 fails with tampered WORK_ITEM (hash mismatch)" \
    python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from pathlib import Path
from Control_Plane.flow_runner.gate_runner import GateRunner
runner = GateRunner(Path.cwd())
result = runner.run_gate("G0", "SPEC-003", "Phase0A")
if result["status"] != "failed":
    raise SystemExit(f"Expected G0 to fail with tampered work item, got: {result['status']}")
if "hash mismatch" not in result.get("reason", "").lower():
    raise SystemExit(f"Expected hash mismatch message, got: {result.get('reason')}")
evidence = result.get("evidence") or {}
if not evidence.get("expected_hash") or not evidence.get("actual_hash"):
    raise SystemExit("Expected hash evidence in failure result")
print(f"G0 correctly detected tampering: expected={evidence['expected_hash'][:16]}..., actual={evidence['actual_hash'][:16]}...")
PY

  # Restore original work item
  echo "${WORK_ITEM_BACKUP}" > "${WORK_ITEM}"
fi
