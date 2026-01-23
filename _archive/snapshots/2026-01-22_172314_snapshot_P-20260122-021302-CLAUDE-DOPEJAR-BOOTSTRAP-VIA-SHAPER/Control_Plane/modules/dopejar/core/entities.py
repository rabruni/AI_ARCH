"""The Assist - Entity Memory

Captures details about people, projects, and things the user mentions.
Builds long-term understanding of the user's world.
"""
import os
import json
from datetime import datetime
from typing import Optional

from dopejar.config.settings import MEMORY_DIR


ENTITIES_FILE = os.path.join(MEMORY_DIR, "entities", "people.json")
BEHAVIORS_FILE = os.path.join(MEMORY_DIR, "entities", "behaviors.json")


def _ensure_dirs():
    os.makedirs(os.path.dirname(ENTITIES_FILE), exist_ok=True)
    if not os.path.exists(ENTITIES_FILE):
        with open(ENTITIES_FILE, 'w') as f:
            json.dump({"people": {}}, f)
    if not os.path.exists(BEHAVIORS_FILE):
        with open(BEHAVIORS_FILE, 'w') as f:
            json.dump({
                "observed": [],      # Short-term: things we've noticed
                "validated": [],     # Long-term: confirmed patterns
                "preferences": {}    # User preferences we've learned
            }, f)


def get_people() -> dict:
    """Get known people."""
    _ensure_dirs()
    with open(ENTITIES_FILE, 'r') as f:
        return json.load(f).get("people", {})


def add_or_update_person(name: str, details: dict):
    """Add or update a person in memory."""
    _ensure_dirs()
    with open(ENTITIES_FILE, 'r') as f:
        data = json.load(f)

    name_lower = name.lower()
    if name_lower not in data["people"]:
        data["people"][name_lower] = {
            "name": name,
            "first_mentioned": datetime.now().isoformat(),
            "details": details,
            "mentions": 1
        }
    else:
        data["people"][name_lower]["details"].update(details)
        data["people"][name_lower]["mentions"] = data["people"][name_lower].get("mentions", 0) + 1
        data["people"][name_lower]["last_mentioned"] = datetime.now().isoformat()

    with open(ENTITIES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_behaviors() -> dict:
    """Get behavioral patterns."""
    _ensure_dirs()
    with open(BEHAVIORS_FILE, 'r') as f:
        return json.load(f)


def log_behavior_observation(observation: str, category: str = "general"):
    """Log a behavioral observation (short-term)."""
    _ensure_dirs()
    with open(BEHAVIORS_FILE, 'r') as f:
        data = json.load(f)

    data["observed"].append({
        "timestamp": datetime.now().isoformat(),
        "observation": observation,
        "category": category,
        "validated": False
    })

    # Keep last 50 observations
    data["observed"] = data["observed"][-50:]

    with open(BEHAVIORS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def validate_behavior(observation: str, category: str = "general"):
    """Move an observation to validated (long-term) patterns."""
    _ensure_dirs()
    with open(BEHAVIORS_FILE, 'r') as f:
        data = json.load(f)

    data["validated"].append({
        "timestamp": datetime.now().isoformat(),
        "pattern": observation,
        "category": category
    })

    with open(BEHAVIORS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def set_preference(key: str, value: str):
    """Set a learned preference."""
    _ensure_dirs()
    with open(BEHAVIORS_FILE, 'r') as f:
        data = json.load(f)

    data["preferences"][key] = {
        "value": value,
        "learned": datetime.now().isoformat()
    }

    with open(BEHAVIORS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def build_entity_context() -> str:
    """Build context string about known entities for the AI."""
    people = get_people()
    behaviors = get_behaviors()

    parts = []

    if people:
        parts.append("## People You Know")
        for key, person in people.items():
            details = person.get("details", {})
            detail_str = ", ".join(f"{k}: {v}" for k, v in details.items())
            parts.append(f"- **{person['name']}**: {detail_str}")

    if behaviors.get("validated"):
        parts.append("\n## Validated Patterns (Long-term)")
        for b in behaviors["validated"][-10:]:
            parts.append(f"- {b['pattern']}")

    if behaviors.get("preferences"):
        parts.append("\n## Learned Preferences")
        for key, pref in behaviors["preferences"].items():
            parts.append(f"- {key}: {pref['value']}")

    return '\n'.join(parts) if parts else ""
