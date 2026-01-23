"""The Assist - Feedback System

Captures what works and what doesn't for iteration.
"""
import os
import json
from datetime import datetime
from typing import Optional

from dopejar.config.settings import BASE_DIR


FEEDBACK_FILE = os.path.join(BASE_DIR, "feedback", "log.json")


def _ensure_feedback_dir():
    """Ensure feedback directory exists."""
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump({"feedback": []}, f)


def log_feedback(
    feedback_type: str,  # 'worked', 'didnt_work', 'suggestion', 'observation'
    note: str,
    context: Optional[str] = None,
    tags: Optional[list] = None
):
    """Log a piece of feedback."""
    _ensure_feedback_dir()

    with open(FEEDBACK_FILE, 'r') as f:
        data = json.load(f)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": feedback_type,
        "note": note,
        "context": context,
        "tags": tags or []
    }

    data["feedback"].append(entry)

    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    return entry


def get_feedback_summary() -> dict:
    """Get summary of feedback for review."""
    _ensure_feedback_dir()

    with open(FEEDBACK_FILE, 'r') as f:
        data = json.load(f)

    feedback = data.get("feedback", [])

    summary = {
        "total": len(feedback),
        "worked": len([f for f in feedback if f["type"] == "worked"]),
        "didnt_work": len([f for f in feedback if f["type"] == "didnt_work"]),
        "suggestions": len([f for f in feedback if f["type"] == "suggestion"]),
        "recent": feedback[-10:] if feedback else []
    }

    return summary


def get_session_feedback(session_start: datetime) -> dict:
    """Get feedback logged since session start."""
    _ensure_feedback_dir()

    with open(FEEDBACK_FILE, 'r') as f:
        data = json.load(f)

    feedback = data.get("feedback", [])

    # Filter to feedback since session start
    session_feedback = []
    for f in feedback:
        try:
            ts = datetime.fromisoformat(f["timestamp"])
            if ts >= session_start:
                session_feedback.append(f)
        except (ValueError, KeyError):
            continue

    return {
        "worked": [f for f in session_feedback if f["type"] == "worked"],
        "didnt_work": [f for f in session_feedback if f["type"] == "didnt_work"],
        "suggestions": [f for f in session_feedback if f["type"] == "suggestion"],
        "positive_count": len([f for f in session_feedback if f["type"] == "worked"]),
        "negative_count": len([f for f in session_feedback if f["type"] == "didnt_work"]),
    }
