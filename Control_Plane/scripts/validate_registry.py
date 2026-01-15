#!/usr/bin/env python3
"""
validate_registry.py
Validates CSV registries and required artifact files, recursively following child registries.

Usage:
  python scripts/validate_registry.py
"""
from __future__ import annotations
import csv, sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
REG_DIR = ROOT / "registries"

STATUS_ENUM = {"missing","draft","active","deprecated"}
PRIORITY_ENUM = {"P0","P1","P2","P3",""}
SELECTED_ENUM = {"yes","no",""}

def read_csv(path: Path) -> List[Dict[str,str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)

def check_file_exists(rel_path: str, context: str) -> None:
    if not rel_path:
        return
    p = (ROOT / rel_path.lstrip("/")).resolve()
    if not p.exists():
        fail(f"{context}: Missing artifact file: {rel_path} (expected at {p})")

def infer_id_field(rows: List[Dict[str,str]]) -> str:
    if not rows:
        return ""
    for k in rows[0].keys():
        if k.endswith("_id"):
            return k
    return ""

def validate_rows(path: Path, rows: List[Dict[str,str]], id_field: str) -> None:
    # ID uniqueness
    ids = [r.get(id_field,"").strip() for r in rows]
    if any(not x for x in ids):
        fail(f"{path}: empty {id_field} value found")
    if len(set(ids)) != len(ids):
        seen=set(); dups=set()
        for x in ids:
            if x in seen: dups.add(x)
            seen.add(x)
        fail(f"{path}: duplicate IDs: {sorted(dups)}")

    idset = set(ids)

    # Dependencies present
    if "dependencies" in rows[0]:
        for i,r in enumerate(rows, start=2):
            deps = [d.strip() for d in (r.get("dependencies","") or "").split(",") if d.strip()]
            missing = [d for d in deps if d not in idset]
            if missing:
                fail(f"{path}:{i}: missing dependencies not found in registry: {missing}")

    # Enums and file existence checks
    for i,r in enumerate(rows, start=2):
        status = (r.get("status","") or "").strip()
        if status and status not in STATUS_ENUM:
            fail(f"{path}:{i}: invalid status='{status}' (allowed {sorted(STATUS_ENUM)})")
        priority = (r.get("priority","") or "").strip()
        if "priority" in r and priority not in PRIORITY_ENUM:
            fail(f"{path}:{i}: invalid priority='{priority}' (allowed {sorted(PRIORITY_ENUM)})")
        sel = (r.get("selected","") or "").strip()
        if "selected" in r and sel not in SELECTED_ENUM:
            fail(f"{path}:{i}: invalid selected='{sel}' (allowed {sorted(SELECTED_ENUM)})")

        if sel == "yes":
            check_file_exists((r.get("artifact_path","") or "").strip(), f"{path}:{i}")
            # verb prompts if present
            for pf in ("install_prompt_path","update_prompt_path","verify_prompt_path","uninstall_prompt_path","prompt_path"):
                if pf in r and (r.get(pf,"") or "").strip():
                    check_file_exists((r.get(pf,"") or "").strip(), f"{path}:{i}")

        # control-plane contract enforcement
        exposes = (r.get("exposes_control_plane","") or "").strip().lower()
        child = (r.get("child_registry_path","") or "").strip()
        if exposes in {"yes","true","1"} and not child:
            fail(f"{path}:{i}: exposes_control_plane=yes but child_registry_path is empty")

def validate_registry(path: Path) -> List[Dict[str,str]]:
    rows = read_csv(path)
    if not rows:
        print(f"WARN: {path} is empty")
        return rows
    id_field = infer_id_field(rows)
    if not id_field:
        fail(f"{path}: cannot infer id field (needs a *_id column)")
    validate_rows(path, rows, id_field)
    return rows

def recurse_from_selected(rows: List[Dict[str,str]], visited: Set[Path], queue: List[Path]) -> None:
    for r in rows:
        if (r.get("selected","") or "").strip() != "yes":
            continue
        child = (r.get("child_registry_path","") or "").strip()
        if not child:
            continue
        child_path = (ROOT / child.lstrip("/")).resolve()
        if not child_path.exists():
            fail(f"Selected row references missing child registry: {child} (expected at {child_path})")
        if child_path in visited:
            continue
        queue.append(child_path)

def main() -> None:
    # Validate root registries, then recurse into any selected child registries.
    root_regs = sorted(REG_DIR.glob("*_registry.csv"))
    if not root_regs:
        fail("No registries found in ./registries")

    visited: Set[Path] = set()
    queue: List[Path] = []

    for reg in root_regs:
        print(f"Validating {reg.relative_to(ROOT)} ...")
        rows = validate_registry(reg)
        visited.add(reg.resolve())
        recurse_from_selected(rows, visited, queue)

    # BFS over child registries
    while queue:
        reg = queue.pop(0).resolve()
        if reg in visited:
            continue
        print(f"Validating {reg.relative_to(ROOT)} ...")
        rows = validate_registry(reg)
        visited.add(reg)
        recurse_from_selected(rows, visited, queue)

    print("OK: registries valid (including child registries)")

if __name__ == "__main__":
    main()
