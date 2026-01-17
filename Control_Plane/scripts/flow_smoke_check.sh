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
