#!/usr/bin/env python3
"""
apply_selection.py
Reads registries and emits an ordered execution plan for selected rows, recursively following child registries.

Usage:
  python scripts/apply_selection.py
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

# Use canonical library
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Control_Plane.lib import (
    REPO_ROOT,
    CONTROL_PLANE,
    REGISTRIES_DIR,
    GENERATED_DIR,
    read_registry as lib_read_registry,
)

ROOT = CONTROL_PLANE
REG_DIR = REGISTRIES_DIR
OUT = GENERATED_DIR
OUT.mkdir(exist_ok=True)


def compute_next_action(row: Dict[str, str], artifact_exists: bool) -> str:
    """Compute the next action for an item based on its state.

    Decision matrix:
    - status=missing, artifact missing -> "install"
    - status=missing, artifact exists  -> "verify" (then mark active)
    - status=draft,   artifact missing -> "install"
    - status=draft,   artifact exists  -> "verify"
    - status=active,  artifact missing -> "repair" (artifact was deleted?)
    - status=active,  artifact exists  -> "" (ready, no action needed)
    - status=deprecated -> "uninstall" or ""
    """
    status = (row.get("status", "") or "").strip().lower()

    if status == "missing":
        return "install" if not artifact_exists else "verify"
    elif status == "draft":
        return "install" if not artifact_exists else "verify"
    elif status == "active":
        return "repair" if not artifact_exists else ""
    elif status == "deprecated":
        return "uninstall"

    return "install"  # Default for unknown status


def read_csv(path: Path) -> List[Dict[str,str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def infer_id_field(rows: List[Dict[str,str]]) -> str:
    if not rows:
        return ""
    if "id" in rows[0].keys():
        return "id"
    for k in rows[0].keys():
        if k.endswith("_id"):
            return k
    return ""

def topo_sort(ids: List[str], deps_map: Dict[str,List[str]]) -> List[str]:
    indeg = {i:0 for i in ids}
    for i in ids:
        for d in deps_map.get(i,[]):
            if d in indeg:
                indeg[i]+=1
    q = deque([i for i in ids if indeg[i]==0])
    out=[]
    # adjacency
    adj=defaultdict(list)
    for i in ids:
        for d in deps_map.get(i,[]):
            if d in indeg:
                adj[d].append(i)
    while q:
        n=q.popleft()
        out.append(n)
        for m in adj.get(n,[]):
            indeg[m]-=1
            if indeg[m]==0:
                q.append(m)
    if len(out)!=len(ids):
        raise SystemExit("ERROR: dependency cycle detected among selected items")
    return out

def plan_registry(reg_path: Path) -> Tuple[Dict, List[Path]]:
    rows = read_csv(reg_path)
    if not rows:
        return {"registry": str(reg_path.relative_to(ROOT)), "items":[]}, []
    id_field = infer_id_field(rows)
    selected = [r for r in rows if (r.get("selected","") or "").strip()=="yes"]
    idset = {r[id_field].strip() for r in selected}
    by_id = {r[id_field].strip(): r for r in selected}
    deps_map = {}
    for rid,r in by_id.items():
        deps = [d.strip() for d in (r.get("dependencies","") or "").split(",") if d.strip()]
        deps_map[rid] = [d for d in deps if d in idset]
    order = topo_sort(list(idset), deps_map) if idset else []
    items=[]
    child_regs=[]
    for rid in order:
        r = by_id[rid]
        child = (r.get("child_registry_path","") or "").strip()
        if child:
            child_regs.append((ROOT / child.lstrip("/")).resolve())

        # Check if artifact exists to compute next_action
        artifact_path = (r.get("artifact_path", "") or "").strip()
        artifact_exists = False
        if artifact_path:
            # Resolve path relative to repo root
            check_path = REPO_ROOT / artifact_path.lstrip("/")
            artifact_exists = check_path.exists()

        next_action = compute_next_action(r, artifact_exists)

        items.append({
            "id": rid,
            "name": r.get("name",""),
            "entity_type": r.get("entity_type",""),
            "category": r.get("category", r.get("domain","")),
            "artifact_path": artifact_path,
            "status": r.get("status", ""),
            "install_prompt_path": r.get("install_prompt_path","") or r.get("prompt_path",""),
            "update_prompt_path": r.get("update_prompt_path",""),
            "verify_prompt_path": r.get("verify_prompt_path",""),
            "uninstall_prompt_path": r.get("uninstall_prompt_path",""),
            "child_registry_path": child,
            "next_action": next_action,
            "priority": r.get("priority",""),
        })
    return {"registry": str(reg_path.relative_to(ROOT)), "items":items}, child_regs

def main():
    visited: Set[Path] = set()
    queue: deque[Path] = deque()

    root_regs = sorted(REG_DIR.glob("*_registry.csv"))
    for r in root_regs:
        queue.append(r.resolve())

    plans=[]
    while queue:
        reg = queue.popleft()
        if reg in visited:
            continue
        plan, children = plan_registry(reg)
        plans.append(plan)
        visited.add(reg)
        for c in children:
            if c.exists() and c not in visited:
                queue.append(c)

    out = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "plans": plans,
    }
    (OUT / "plan.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Human report
    lines = ["# Selection Report", ""]
    for p in plans:
        lines.append(f"## {p['registry']}")
        if not p["items"]:
            lines.append("- (none selected)\n")
            continue
        for it in p["items"]:
            suffix = f" → child:{it['child_registry_path']}" if it.get("child_registry_path") else ""
            action = f" [{it['next_action']}]" if it.get("next_action") else ""
            lines.append(f"- **{it['id']}** {it['name']} ({it.get('priority','')}){action} → {it.get('artifact_path','')}{suffix}")
        lines.append("")
    (OUT / "selection_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("OK: generated/plan.json and generated/selection_report.md")

if __name__ == "__main__":
    main()
