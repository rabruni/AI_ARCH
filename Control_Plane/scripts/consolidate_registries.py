#!/usr/bin/env python3
"""One-time script to consolidate 5 registries into 1."""
import csv
import json
import sys
from pathlib import Path

# Use canonical library
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Control_Plane.lib import REGISTRIES_DIR

REG_DIR = REGISTRIES_DIR
OUTPUT = REG_DIR / "control_plane_registry.csv"

# Unified schema
HEADERS = [
    "id", "name", "entity_type", "category", "purpose", "artifact_path",
    "status", "selected", "priority", "dependencies", "version", "config"
]

rows = []

# 1. Frameworks (28 items)
with open(REG_DIR / "frameworks_registry.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        config = {}
        if r.get("child_registry_path"):
            config["child_registry_path"] = r["child_registry_path"]
        if r.get("safety_level") and r["safety_level"] != "standard":
            config["safety_level"] = r["safety_level"]
        if r.get("ci_gate") and r["ci_gate"] != "optional":
            config["ci_gate"] = r["ci_gate"]

        rows.append({
            "id": r["framework_id"],
            "name": r["name"],
            "entity_type": r.get("entity_type", "framework"),
            "category": r["category"],
            "purpose": r["purpose"],
            "artifact_path": r["artifact_path"],
            "status": r["status"],
            "selected": r["selected"],
            "priority": r["priority"],
            "dependencies": r.get("dependencies", ""),
            "version": r.get("version_current", ""),
            "config": json.dumps(config) if config else ""
        })

# 2. Modules (4 items)
with open(REG_DIR / "modules_registry.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        config = {"slot": r["slot"], "interface": r["interface"]}
        rows.append({
            "id": r["module_id"],
            "name": r["name"],
            "entity_type": "module",
            "category": r["slot"],
            "purpose": r["description"],
            "artifact_path": r["artifact_path"],
            "status": r["status"],
            "selected": r["selected"],
            "priority": "P1",
            "dependencies": "",
            "version": r["version"],
            "config": json.dumps(config)
        })

# 3. Components (5 items)
with open(REG_DIR / "components_registry.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        config = {}
        if r.get("capability_group"):
            config["capability_group"] = r["capability_group"]
        if r.get("capability_key"):
            config["capability_key"] = r["capability_key"]

        rows.append({
            "id": r["component_id"],
            "name": r["name"],
            "entity_type": "component",
            "category": r.get("domain", ""),
            "purpose": r["purpose"],
            "artifact_path": r["artifact_path"],
            "status": r["status"],
            "selected": r["selected"],
            "priority": r["priority"],
            "dependencies": r.get("dependencies", ""),
            "version": r.get("version_current", ""),
            "config": json.dumps(config) if config else ""
        })

# 4. Prompts (7 items)
with open(REG_DIR / "prompts_registry.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append({
            "id": r["prompt_id"],
            "name": r["name"],
            "entity_type": "prompt",
            "category": r.get("domain", ""),
            "purpose": r["purpose"],
            "artifact_path": r["artifact_path"],
            "status": r["status"],
            "selected": r["selected"],
            "priority": r["priority"],
            "dependencies": r.get("dependencies", ""),
            "version": "",
            "config": ""
        })

# 5. Cloud Services (2 items)
with open(REG_DIR / "cloud_services_registry.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        config = {}
        if r.get("image"):
            config["image"] = r["image"]
        if r.get("ports"):
            config["ports"] = r["ports"]
        if r.get("command"):
            config["command"] = r["command"]
        if r.get("env_vars"):
            config["env_vars"] = r["env_vars"]

        rows.append({
            "id": r["cloud_service_id"],
            "name": r["name"],
            "entity_type": "cloud",
            "category": r.get("provider", ""),
            "purpose": r.get("description", ""),
            "artifact_path": "",
            "status": r["status"],
            "selected": r["selected"],
            "priority": "P2",
            "dependencies": r.get("depends_on", ""),
            "version": "",
            "config": json.dumps(config) if config else ""
        })

# Write consolidated registry
with open(OUTPUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(rows)

print(f"Created {OUTPUT}")
print(f"Total items: {len(rows)}")

# Count by entity type
counts = {}
for r in rows:
    t = r["entity_type"]
    counts[t] = counts.get(t, 0) + 1
for t, c in sorted(counts.items()):
    print(f"  {t}: {c}")
