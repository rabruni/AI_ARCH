#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/control_plane_reconcile.sh observe [-r <repo_root>]
  ./scripts/control_plane_reconcile.sh check-drift [-r <repo_root>]
  ./scripts/control_plane_reconcile.sh auto-reconcile [-r <repo_root>] [--apply] [--no-validate]

Notes:
  - Defaults repo_root to current directory.
  - auto-reconcile is conservative: only flips status between missing <-> active
    based on artifact_path existence.
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

cmd="$1"
shift

rootdir="$(pwd)"
apply="no"
validate="yes"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--root)
      rootdir="$2"
      shift 2
      ;;
    --apply)
      apply="yes"
      shift
      ;;
    --no-validate)
      validate="no"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown арг: $1" >&2
      usage
      exit 1
      ;;
  esac
done

case "$cmd" in
  observe)
    python3 - <<'PY' "$rootdir"
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))

from Control_Plane.lib.registry import find_all_registries, read_registry, get_id_column

observations = []
for reg in find_all_registries():
    headers, rows = read_registry(reg)
    id_col = get_id_column(headers)
    for r in rows:
        ap = (r.get("artifact_path") or r.get("path") or "").strip()
        resolved = None
        exists = None
        if ap:
            rel = ap[1:] if ap.startswith("/") else ap
            resolved = str((root / rel).resolve())
            exists = (root / rel).exists()
        observations.append({
            "registry": str(reg),
            "id": r.get(id_col, "") if id_col else "",
            "name": r.get("name", ""),
            "status": r.get("status", ""),
            "selected": r.get("selected", ""),
            "artifact_path": ap,
            "resolved_path": resolved,
            "exists": exists,
        })

out_path = root / "Control_Plane" / "generated" / "registry_observed.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps({"root": str(root), "observations": observations}, indent=2))
print(f"OK: wrote {out_path}")
PY
    ;;
  check-drift)
    python3 - <<'PY' "$rootdir"
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))

from Control_Plane.lib.registry import find_all_registries, read_registry, get_id_column

drift = []
for reg in find_all_registries():
    headers, rows = read_registry(reg)
    id_col = get_id_column(headers)
    for r in rows:
        status = (r.get("status") or "").strip().lower()
        ap = (r.get("artifact_path") or r.get("path") or "").strip()
        if not ap:
            continue
        rel = ap[1:] if ap.startswith("/") else ap
        exists = (root / rel).exists()
        if status == "active" and not exists:
            drift.append((reg, r.get(id_col, "") if id_col else "", r.get("name", ""), status, ap, exists))
        if status == "missing" and exists:
            drift.append((reg, r.get(id_col, "") if id_col else "", r.get("name", ""), status, ap, exists))

if not drift:
    print("OK: no drift found")
    raise SystemExit(0)

print(f"DRIFT: {len(drift)} items")
for reg, rid, name, status, ap, exists in drift:
    print(f"{reg}: {rid} {name} status={status} path={ap} exists={exists}")
raise SystemExit(1)
PY
    ;;
  auto-reconcile)
    python3 - <<'PY' "$rootdir" "$apply"
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
apply = sys.argv[2] == "yes"

sys.path.insert(0, str(root))

from Control_Plane.lib.registry import find_all_registries, read_registry, write_registry, get_id_column

changes = []
for reg in find_all_registries():
    headers, rows = read_registry(reg)
    id_col = get_id_column(headers)
    updated = False
    for r in rows:
        status = (r.get("status") or "").strip().lower()
        ap = (r.get("artifact_path") or r.get("path") or "").strip()
        if not ap:
            continue
        rel = ap[1:] if ap.startswith("/") else ap
        exists = (root / rel).exists()
        if status == "active" and not exists:
            changes.append((reg, r.get(id_col, "") if id_col else "", r.get("name", ""), "active", "missing", ap))
            if apply:
                r["status"] = "missing"
                updated = True
        elif status == "missing" and exists:
            changes.append((reg, r.get(id_col, "") if id_col else "", r.get("name", ""), "missing", "active", ap))
            if apply:
                r["status"] = "active"
                updated = True
    if apply and updated:
        write_registry(reg, headers, rows)

if not changes:
    print("OK: no changes needed")
    raise SystemExit(0)

for reg, rid, name, old, new, ap in changes:
    print(f"{reg}: {rid} {name} {old} -> {new} ({ap})")

if apply:
    print("Applied changes to registries")
else:
    print("Dry-run only; re-run with --apply to write changes")
PY
    if [[ "$apply" == "yes" ]]; then
      if [[ "$validate" == "yes" ]]; then
        python3 "$rootdir/Control_Plane/scripts/generate_manifest.py"
        python3 "$rootdir/Control_Plane/scripts/validate.py"
      fi
    fi
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage
    exit 1
    ;;
esac
