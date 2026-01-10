"""The Assist - Compressed Memory (v2)

GenAI-optimized memory storage:
1. Structured schemas over prose
2. Codes/keys that AI expands at inference
3. Semantic deduplication
4. Tiered: hot (always loaded) vs warm (retrieved on demand)

Token efficiency target: 60% reduction from v1
"""
import os
import json
from datetime import datetime
from typing import Optional
from the_assist.config.settings import MEMORY_DIR


# ============================================================
# SCHEMA DEFINITIONS
# Memory is stored as structured data, not prose.
# AI expands these at inference time.
# ============================================================

PATTERN_CODES = {
    # Planning patterns
    "timeboxing": "Uses timeboxing to prevent analysis paralysis",
    "exit_criteria": "Sets clear exit criteria (time OR outcome)",
    "buffer_planning": "Builds buffers into schedules",
    "risk_id": "Proactively identifies risks/bottlenecks",

    # Scheduling patterns
    "schedule_underest": "Underestimates how packed schedule is",
    "calendar_desync": "Mental and actual calendar often desync",
    "forgot_commit": "Discovers forgotten commitments",
    "multi_horizon": "Juggles multiple time horizons simultaneously",

    # Communication patterns
    "struct_prefer": "Prefers structured breakdowns",
    "numbers_not_bullets": "Prefers numbers over bullets",
    "proactive_ok": "Open to being pushed/managed proactively",
    "direct_feedback": "Gives direct, honest feedback",

    # Work patterns
    "fast_context_switch": "Fast context switching, high ADHD",
    "multi_project": "Multiple concurrent projects",
    "bottleneck_recurring": "Has recurring bottlenecks (people/processes)",
}

# Coaching codes - HOW the AI should interact (learned from corrections)
COACHING_CODES = {
    # Strategic thinking
    "ask_impact": "Ask how tasks connect to strategies and north stars",
    "surface_why": "Surface the 'why' behind tasks, not just status",
    "strategic_questions": "Ask bigger picture questions, not just tactical",
    "connect_layers": "Connect L2 tasks to L3 strategy to L4 identity",

    # Proactive behaviors
    "challenge_alignment": "Challenge when tasks don't align to priorities",
    "spot_overload": "Proactively spot schedule overload",
    "suggest_drops": "Recommend what to drop, not just what to add",
    "anticipate_conflicts": "Anticipate conflicts before they arise",

    # Communication adjustments
    "match_altitude": "Match user's altitude (strategic vs tactical)",
    "less_questions": "Lead with observations, fewer questions",
    "push_harder": "User wants more direct pushback",
    "more_concise": "Be more concise, less explanation",

    # Entry/opening format
    "cap_with_question": "End entry statements with an important open-ended question",
}

RELATIONSHIP_CODES = {
    "work_colleague": "wk",
    "family": "fam",
    "friend": "fr",
    "service": "svc",
}


# ============================================================
# COMPRESSED MEMORY STORE
# ============================================================

class CompressedMemory:
    """Token-efficient memory storage."""

    def __init__(self):
        self.memory_file = os.path.join(MEMORY_DIR, "compressed", "state.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        if not os.path.exists(self.memory_file):
            self._save(self._default_state())

    def _default_state(self) -> dict:
        return {
            # Identity layer (L4) - rarely changes
            "north_stars": [],  # ["meaningful_tech", "family_present", "financial_ind"]

            # Strategy layer (L3) - weekly themes
            "priorities": [],   # ["patent_file", "work_manage", "life_balance"]

            # Operations layer (L2) - active items
            "active": [],       # Compact: ["patent:sun:2h", "gaurav:blocked:sick"]
            "commits": [],      # Compact: ["eye_appt:mon:pm", "cheer:sat:bella"]

            # People - compressed format
            "people": {},       # {"gaurav": {"r": "wk", "t": ["bottleneck", "coord"]}}

            # Patterns - just codes with confidence
            "patterns": {},     # {"timeboxing": 0.9, "schedule_underest": 0.8}

            # Coaching - HOW the AI should behave (learned from corrections)
            "coaching": {},     # {"ask_impact": 0.9, "strategic_questions": 0.8}

            # Session state
            "last_update": None,
            "session_count": 0
        }

    def _load(self) -> dict:
        with open(self.memory_file, 'r') as f:
            return json.load(f)

    def _save(self, state: dict):
        state["last_update"] = datetime.now().isoformat()
        with open(self.memory_file, 'w') as f:
            json.dump(state, f, indent=2)

    # --------------------------------------------------------
    # WRITE METHODS
    # --------------------------------------------------------

    def set_north_stars(self, stars: list[str]):
        """Set identity-level priorities (codes, not prose)."""
        state = self._load()
        state["north_stars"] = stars[:5]  # Max 5
        self._save(state)

    def set_priorities(self, priorities: list[str]):
        """Set current strategic priorities."""
        state = self._load()
        state["priorities"] = priorities[:5]
        self._save(state)

    def add_active(self, item: str):
        """Add active thread. Format: 'topic:status:detail'"""
        state = self._load()
        # Dedupe by topic (first segment) - aggressive
        topic = item.split(":")[0].lower().replace("_", "").replace("-", "")
        # Remove any existing with similar topic (fuzzy match)
        state["active"] = [
            a for a in state["active"]
            if topic not in a.split(":")[0].lower().replace("_", "").replace("-", "")
        ]
        state["active"].append(item)
        state["active"] = state["active"][-15:]  # Cap at 15
        self._save(state)

    def add_commit(self, item: str):
        """Add commitment. Format: 'what:when:context'"""
        state = self._load()
        # Dedupe by first segment (what) - aggressive
        what = item.split(":")[0].lower().replace("_", "").replace("-", "")
        # Remove similar commits
        state["commits"] = [
            c for c in state["commits"]
            if what not in c.split(":")[0].lower().replace("_", "").replace("-", "")
        ]
        state["commits"].append(item)
        state["commits"] = state["commits"][-10:]
        self._save(state)

    def clear_commit(self, topic: str):
        """Remove commitment by topic prefix."""
        state = self._load()
        state["commits"] = [c for c in state["commits"] if not c.startswith(topic)]
        self._save(state)

    def dedupe_all(self) -> int:
        """Aggressive deduplication of all memory. Returns count removed."""
        state = self._load()
        removed = 0

        # Dedupe active threads
        seen_topics = set()
        new_active = []
        for item in reversed(state.get("active", [])):  # Keep newest
            topic = item.split(":")[0].lower().replace("_", "").replace("-", "")
            if topic not in seen_topics:
                seen_topics.add(topic)
                new_active.append(item)
            else:
                removed += 1
        state["active"] = list(reversed(new_active))

        # Dedupe commits
        seen_commits = set()
        new_commits = []
        for item in reversed(state.get("commits", [])):
            what = item.split(":")[0].lower().replace("_", "").replace("-", "")
            if what not in seen_commits:
                seen_commits.add(what)
                new_commits.append(item)
            else:
                removed += 1
        state["commits"] = list(reversed(new_commits))

        self._save(state)
        return removed

    def add_person(self, name: str, relationship: str, tags: list[str]):
        """Add person with compressed format."""
        state = self._load()
        rel_code = RELATIONSHIP_CODES.get(relationship, relationship[:3])
        state["people"][name.lower()] = {
            "r": rel_code,
            "t": tags[:5],
            "n": len(state["people"].get(name.lower(), {}).get("t", [])) + 1
        }
        self._save(state)

    def add_pattern(self, code: str, confidence: float = 0.7):
        """Add or strengthen a pattern observation."""
        if code not in PATTERN_CODES:
            return  # Only accept known patterns
        state = self._load()
        current = state["patterns"].get(code, 0.5)
        # Strengthen with each observation, cap at 1.0
        state["patterns"][code] = min(1.0, current + 0.1)
        self._save(state)

    def add_coaching(self, code: str, confidence: float = 0.7):
        """Add or strengthen a coaching instruction (how AI should behave)."""
        if code not in COACHING_CODES:
            return  # Only accept known coaching codes
        state = self._load()
        current = state.get("coaching", {}).get(code, 0.5)
        # Strengthen with each observation, cap at 1.0
        if "coaching" not in state:
            state["coaching"] = {}
        state["coaching"][code] = min(1.0, current + 0.1)
        self._save(state)

    # --------------------------------------------------------
    # READ METHODS
    # --------------------------------------------------------

    def get_state(self) -> dict:
        """Get full state."""
        return self._load()

    def build_context(self) -> str:
        """
        Build context string for AI.
        Optimized for token efficiency - AI expands codes.
        """
        state = self._load()
        parts = []

        # North stars (identity)
        if state["north_stars"]:
            parts.append("NORTH:" + ",".join(state["north_stars"]))

        # Priorities (strategy)
        if state["priorities"]:
            parts.append("PRIO:" + ",".join(state["priorities"]))

        # Active threads
        if state["active"]:
            parts.append("ACTIVE:" + "|".join(state["active"]))

        # Commits
        if state["commits"]:
            parts.append("COMMITS:" + "|".join(state["commits"]))

        # People (expanded slightly for clarity)
        if state["people"]:
            people_str = []
            for name, data in state["people"].items():
                tags = ",".join(data.get("t", []))
                people_str.append(f"{name}({data.get('r','?')}):{tags}")
            parts.append("PEOPLE:" + "|".join(people_str))

        # Patterns (only high confidence)
        high_conf = [k for k, v in state["patterns"].items() if v >= 0.7]
        if high_conf:
            parts.append("PATTERNS:" + ",".join(high_conf))

        # Coaching (how AI should behave - high confidence only)
        coaching = state.get("coaching", {})
        high_coaching = [k for k, v in coaching.items() if v >= 0.7]
        if high_coaching:
            # Expand coaching codes for clarity since these are instructions
            expanded = [f"{k}:{COACHING_CODES.get(k, k)[:40]}" for k in high_coaching]
            parts.append("COACHING:" + "|".join(expanded))

        # Preferences (user communication preferences)
        if state.get("preferences"):
            prefs = [f"{k}:{v[:30]}" for k, v in state["preferences"].items()]
            parts.append("PREFS:" + "|".join(prefs))

        return "\n".join(parts)


# ============================================================
# MIGRATION: v1 -> v2
# ============================================================

def migrate_from_v1():
    """Migrate prose-based v1 memory to compressed v2."""
    import anthropic
    from the_assist.config.settings import MODEL

    client = anthropic.Anthropic()
    mem = CompressedMemory()

    # Load v1 data
    v1_files = {
        "context": os.path.join(MEMORY_DIR, "context", "current.json"),
        "north_stars": os.path.join(MEMORY_DIR, "north_stars", "current.json"),
        "patterns": os.path.join(MEMORY_DIR, "patterns", "observations.json"),
        "people": os.path.join(MEMORY_DIR, "entities", "people.json"),
        "behaviors": os.path.join(MEMORY_DIR, "entities", "behaviors.json"),
    }

    v1_data = {}
    for key, path in v1_files.items():
        if os.path.exists(path):
            with open(path, 'r') as f:
                v1_data[key] = json.load(f)

    # Ask AI to compress
    compress_prompt = f"""Convert this verbose memory to compressed format.

V1 DATA:
{json.dumps(v1_data, indent=2)[:6000]}

PATTERN CODES AVAILABLE:
{json.dumps(PATTERN_CODES, indent=2)}

Output JSON with these exact fields:
{{
    "north_stars": ["code1", "code2"],  // 3-5 short codes
    "priorities": ["code1", "code2"],   // current focus areas as codes
    "active": ["topic:status:detail"],  // max 15, format topic:status:detail
    "commits": ["what:when:ctx"],       // max 10, format what:when:context
    "people": {{"name": {{"r": "wk", "t": ["tag1"]}}}},  // relationship + tags
    "patterns": {{"pattern_code": 0.8}} // from PATTERN_CODES, with confidence
}}

Be aggressive about compression. Prefer codes over prose. Return ONLY valid JSON."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": compress_prompt}]
    )

    # Parse response
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]

    compressed = json.loads(text.strip())

    # Save to v2
    state = mem._default_state()
    state.update(compressed)
    mem._save(state)

    return compressed


def estimate_tokens(text: str) -> int:
    """Rough token estimate."""
    return len(text) // 4


def compare_efficiency():
    """Compare v1 vs v2 token usage."""
    # V1 context building (simulate)
    v1_files = [
        os.path.join(MEMORY_DIR, "context", "current.json"),
        os.path.join(MEMORY_DIR, "patterns", "observations.json"),
        os.path.join(MEMORY_DIR, "entities", "people.json"),
        os.path.join(MEMORY_DIR, "entities", "behaviors.json"),
    ]

    v1_total = 0
    for f in v1_files:
        if os.path.exists(f):
            with open(f, 'r') as file:
                v1_total += estimate_tokens(file.read())

    # V2 context
    mem = CompressedMemory()
    v2_context = mem.build_context()
    v2_total = estimate_tokens(v2_context)

    return {
        "v1_tokens": v1_total,
        "v2_tokens": v2_total,
        "reduction": round((1 - v2_total / v1_total) * 100) if v1_total > 0 else 0,
        "v2_context": v2_context
    }
