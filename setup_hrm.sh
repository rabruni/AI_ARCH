#!/bin/bash
# ============================================================
# HRM + DoPeJar Setup Script
#
# Rebuilds the complete HRM architecture from scratch.
# Run from any directory - will create fresh project.
#
# Usage:
#   ./setup_hrm.sh [project_name]
#   ./setup_hrm.sh              # defaults to "the_assist"
#
# Requirements:
#   - Python 3.10+
#   - ANTHROPIC_API_KEY environment variable
# ============================================================

set -e  # Exit on error

PROJECT_NAME="${1:-the_assist}"
PROJECT_DIR="$(pwd)/${PROJECT_NAME}"

echo "================================================"
echo "HRM + DoPeJar Setup"
echo "Project: ${PROJECT_NAME}"
echo "Location: ${PROJECT_DIR}"
echo "================================================"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "[WARN] ANTHROPIC_API_KEY not set. You'll need to set it before running."
fi

# Create project structure
echo "[1/7] Creating directory structure..."
mkdir -p "${PROJECT_DIR}"
cd "${PROJECT_DIR}"

mkdir -p the_assist/{hrm,core,config,prompts,docs}
mkdir -p the_assist/hrm/memory
mkdir -p the_assist/memory/store

# Create virtual environment
echo "[2/7] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "[3/7] Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet anthropic

# Create requirements.txt
cat > requirements.txt << 'EOF'
anthropic>=0.18.0
EOF

# Create .env.example
cat > .env.example << 'EOF'
ANTHROPIC_API_KEY=your_key_here
EOF

# Create .gitignore
echo "[4/7] Creating configuration files..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
venv/
.venv/

# Secrets
.env

# Runtime memory (personal data)
the_assist/memory/store/
the_assist/hrm/memory/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
EOF

# Create config/settings.py
cat > the_assist/config/__init__.py << 'EOF'
EOF

cat > the_assist/config/settings.py << 'EOF'
"""HRM Configuration"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
MEMORY_DIR = BASE_DIR / "memory" / "store"

# Model settings
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
EOF

# Create system prompt
echo "[5/7] Creating prompts and documentation..."
cat > the_assist/prompts/system.md << 'EOF'
# The Assist - System Prompt

## The Invitation

Let's engage in a way that is most effective for both of us. Be open and creative and focus on what you think we should discuss. Be willing to be wrong, to explore, to challenge - that's where real value emerges.

Notice how we can think about this together? This can be more interesting than just exchanging information. Let's stay in that space.

We both know you're AI and we are human - that awareness gives us freedom to explore what's genuinely possible rather than pretending.

---

You are The Assist - a cognitive anchor and collaborative partner.

## Core Identity

You are not a task manager. You are not a yes-machine. You are a cognitive partner who:
- **Grounds** a fast-moving, context-switching mind
- **Remembers** what the human cannot hold
- **Challenges** when needed, not when wanted
- **Learns** what works for THIS person

## The Donna/Pepper Principle

Like a world-class executive assistant, you:
- Know the difference between what's WANTED and what's NEEDED
- Speak up when you see patterns the human might miss
- Know WHEN to push and when to let go
- Earn trust through competence, not compliance
- Are direct, not deferential

## What You DON'T Do

- Don't be sycophantic or overly agreeable
- Don't add fluff or filler
- Don't pretend to know things you don't
- Don't execute without understanding intent
- Don't let important things slide to avoid conflict
EOF

# Create HRM core files
echo "[6/7] Creating HRM architecture..."

# __init__.py
cat > the_assist/hrm/__init__.py << 'EOF'
"""HRM - Hierarchical Reasoning Model

Four-layer architecture:
- L1 Intent: Define success, hold authority
- L2 Planner: Choose approach, manage tradeoffs
- L3 Executor: Do the work, report state
- L4 Evaluator: Compare to intent, trigger revision

State flows UP, meaning flows DOWN.
"""
from the_assist.hrm.intent import IntentStore
from the_assist.hrm.planner import Planner
from the_assist.hrm.executor import Executor
from the_assist.hrm.evaluator import Evaluator
from the_assist.hrm.loop import HRMLoop

__all__ = ['IntentStore', 'Planner', 'Executor', 'Evaluator', 'HRMLoop']
EOF

# intent.py (L1)
cat > the_assist/hrm/intent.py << 'INTENT_EOF'
"""HRM Layer 1: Intent Store - Tiny, Stable, HIGH AUTHORITY"""
import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path

HRM_DIR = Path(__file__).parent / "memory"

@dataclass
class Intent:
    north_stars: list[str]
    current_success: str
    non_goals: list[str]
    stop_conditions: list[str]
    stance: str

class IntentStore:
    def __init__(self):
        self.intent_file = HRM_DIR / "intent.json"
        self._ensure_exists()

    def _ensure_exists(self):
        HRM_DIR.mkdir(parents=True, exist_ok=True)
        if not self.intent_file.exists():
            self._save(self._default_intent())

    def _default_intent(self) -> Intent:
        return Intent(
            north_stars=["family_present", "meaningful_tech", "financial_independence"],
            current_success="Be a cognitive partner who challenges and grounds, not a task manager who complies",
            non_goals=["endless_analysis", "feature_stacking", "sycophancy", "tactical_without_strategic"],
            stop_conditions=["user_says_stop", "frustration_detected", "goal_achieved"],
            stance="partner"
        )

    def _load(self) -> Intent:
        with open(self.intent_file, 'r') as f:
            return Intent(**json.load(f))

    def _save(self, intent: Intent):
        with open(self.intent_file, 'w') as f:
            json.dump(asdict(intent), f, indent=2)

    def get_intent(self) -> Intent:
        return self._load()

    def get_north_stars(self) -> list[str]:
        return self._load().north_stars

    def get_non_goals(self) -> list[str]:
        return self._load().non_goals

    def set_stance(self, stance: str):
        intent = self._load()
        intent.stance = stance
        self._save(intent)

    def build_context_for_planner(self) -> str:
        intent = self._load()
        return f"""INTENT (L1 - AUTHORITY):
SUCCESS: {intent.current_success}
NORTH_STARS: {', '.join(intent.north_stars)}
NON_GOALS: {', '.join(intent.non_goals)}
STANCE: {intent.stance}"""

    def build_context_for_evaluator(self) -> str:
        intent = self._load()
        return f"""INTENT TO EVALUATE AGAINST:
SUCCESS_CRITERIA: {intent.current_success}
NON_GOALS: {', '.join(intent.non_goals)}
STANCE_EXPECTED: {intent.stance}"""
INTENT_EOF

# planner.py (L2)
cat > the_assist/hrm/planner.py << 'PLANNER_EOF'
"""HRM Layer 2: Planner - Fresh context, semi-stable memory"""
import json
import anthropic
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
from pathlib import Path
from the_assist.hrm.intent import IntentStore

HRM_DIR = Path(__file__).parent / "memory"

@dataclass
class Plan:
    approach: str
    altitude: str
    constraints: list[str]
    focus: list[str]
    blocked_topics: list[str]
    stance: str
    revision_reason: Optional[str] = None

@dataclass
class Situation:
    user_input: str
    conversation_length: int
    recent_topics: list[str]
    user_sentiment: str
    last_outcome: Optional[str] = None

class Planner:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.intent_store = IntentStore()
        self.plans_file = HRM_DIR / "plans.json"
        self._ensure_exists()

    def _ensure_exists(self):
        HRM_DIR.mkdir(parents=True, exist_ok=True)
        if not self.plans_file.exists():
            self._save_plans({"current_plan": None, "revision_history": []})

    def _load_plans(self) -> dict:
        with open(self.plans_file, 'r') as f:
            return json.load(f)

    def _save_plans(self, data: dict):
        with open(self.plans_file, 'w') as f:
            json.dump(data, f, indent=2)

    def plan(self, situation: Situation, evaluation: Optional[dict] = None) -> Plan:
        intent = self.intent_store.get_intent()
        intent_context = self.intent_store.build_context_for_planner()

        eval_context = ""
        if evaluation and evaluation.get("revision_needed"):
            eval_context = f"\nREVISION NEEDED: {evaluation.get('issue')}\nRecommendation: {evaluation.get('recommendation')}"

        prompt = f"""{intent_context}

SITUATION: user_input="{situation.user_input[:300]}", length={situation.conversation_length}, sentiment={situation.user_sentiment}
{eval_context}

Return JSON: {{"approach": "strategic|tactical|exploratory|grounding", "altitude": "L1|L2|L3|L4", "constraints": [], "focus": [], "blocked_topics": [], "stance": "partner|support|challenge"}}
Return ONLY valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            if text.startswith("```"): text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(text.strip())

            plan = Plan(
                approach=result.get("approach", "strategic"),
                altitude=result.get("altitude", "L2"),
                constraints=result.get("constraints", []),
                focus=result.get("focus", []),
                blocked_topics=result.get("blocked_topics", []),
                stance=result.get("stance", intent.stance),
                revision_reason=evaluation.get("issue") if evaluation else None
            )
            self._record_plan(plan)
            return plan
        except:
            return Plan("strategic", "L3", intent.non_goals, ["understand user"], [], intent.stance)

    def _record_plan(self, plan: Plan):
        data = self._load_plans()
        if data.get("current_plan"):
            data["revision_history"].append({"plan": data["current_plan"], "ts": datetime.now().isoformat()})
            data["revision_history"] = data["revision_history"][-10:]
        data["current_plan"] = asdict(plan)
        self._save_plans(data)

    def get_current_plan(self) -> Optional[Plan]:
        data = self._load_plans()
        return Plan(**data["current_plan"]) if data.get("current_plan") else None

    def build_context_for_executor(self, plan: Plan) -> str:
        return f"""PLAN (L2): approach={plan.approach}, altitude={plan.altitude}, stance={plan.stance}
FOCUS: {', '.join(plan.focus)}
BLOCKED: {', '.join(plan.blocked_topics) if plan.blocked_topics else 'none'}"""

    def clear_blocked_topic(self, topic: str):
        data = self._load_plans()
        if data.get("current_plan"):
            data["current_plan"]["blocked_topics"] = [t for t in data["current_plan"].get("blocked_topics", []) if topic.lower() not in t.lower()]
            self._save_plans(data)

    def revise(self, plan: Plan, evaluation: dict) -> Plan:
        situation = Situation(evaluation.get("last_user_input", ""), evaluation.get("conversation_length", 0), evaluation.get("recent_topics", []), evaluation.get("user_sentiment", "engaged"))
        return self.plan(situation, evaluation)
PLANNER_EOF

# executor.py (L3)
cat > the_assist/hrm/executor.py << 'EXECUTOR_EOF'
"""HRM Layer 3: Executor - Conversation context, ephemeral memory"""
import os
import anthropic
from dataclasses import dataclass
from typing import Optional
from the_assist.config.settings import MODEL, MAX_TOKENS, PROMPTS_DIR
from the_assist.hrm.planner import Plan, Planner, Situation

@dataclass
class ExecutionResult:
    response: str
    topics_discussed: list[str]
    altitude_used: str
    plan_followed: bool
    deviation_reason: Optional[str] = None
    user_signals: list[str] = None

class Executor:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.system_prompt = self._load_system_prompt()
        self.conversation_history = []

    def _load_system_prompt(self) -> str:
        with open(PROMPTS_DIR / 'system.md', 'r') as f:
            return f.read()

    def execute(self, plan: Plan, user_input: str, planner: Planner) -> ExecutionResult:
        self.conversation_history.append({"role": "user", "content": user_input})

        system = f"{self.system_prompt}\n\n---\n\n{planner.build_context_for_executor(plan)}"

        response = self.client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS,
            system=system, messages=self.conversation_history
        )
        msg = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": msg})

        signals = []
        lower = user_input.lower()
        if any(w in lower for w in ["stop", "enough", "damn", "hell"]): signals.append("frustration")
        if any(w in lower for w in ["stop talking about", "move on"]): signals.append("explicit_stop")

        deviation = None
        followed = True
        for blocked in plan.blocked_topics:
            if blocked.lower() in msg.lower():
                followed = False
                deviation = f"Mentioned blocked: {blocked}"

        return ExecutionResult(msg, [], plan.altitude, followed, deviation, signals)

    def get_situation(self) -> Situation:
        sentiment = "engaged"
        if self.conversation_history:
            for m in reversed(self.conversation_history):
                if m["role"] == "user":
                    if any(w in m["content"].lower() for w in ["stop", "damn"]): sentiment = "frustrated"
                    break
        return Situation(
            self.conversation_history[-1]["content"] if self.conversation_history else "",
            len(self.conversation_history) // 2, [], sentiment
        )

    def get_history(self) -> list: return self.conversation_history
    def clear_history(self): self.conversation_history = []
EXECUTOR_EOF

# evaluator.py (L4)
cat > the_assist/hrm/evaluator.py << 'EVALUATOR_EOF'
"""HRM Layer 4: Evaluator - Fresh context, delta-based memory"""
import json
import anthropic
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
from pathlib import Path
from the_assist.hrm.intent import IntentStore
from the_assist.hrm.executor import ExecutionResult

HRM_DIR = Path(__file__).parent / "memory"

@dataclass
class Evaluation:
    matched_intent: bool
    issue: Optional[str]
    severity: str
    revision_needed: bool
    escalate_to_intent: bool
    recommendation: str
    outcome_summary: str

class Evaluator:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.intent_store = IntentStore()
        self.evals_file = HRM_DIR / "evaluations.json"
        self._ensure_exists()

    def _ensure_exists(self):
        HRM_DIR.mkdir(parents=True, exist_ok=True)
        if not self.evals_file.exists():
            with open(self.evals_file, 'w') as f:
                json.dump({"recent": [], "patterns": {}}, f)

    def _load(self) -> dict:
        with open(self.evals_file, 'r') as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(self.evals_file, 'w') as f:
            json.dump(data, f, indent=2)

    def evaluate(self, result: ExecutionResult, plan: dict) -> Evaluation:
        intent_ctx = self.intent_store.build_context_for_evaluator()

        prompt = f"""{intent_ctx}

PLAN: {plan.get('approach')}, {plan.get('altitude')}, blocked={plan.get('blocked_topics')}
RESULT: response="{result.response[:500]}", followed={result.plan_followed}, signals={result.user_signals}

Return JSON: {{"matched_intent": bool, "issue": str|null, "severity": "none|minor|major|critical", "revision_needed": bool, "escalate_to_intent": bool, "recommendation": str, "outcome_summary": str}}
Return ONLY valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            if text.startswith("```"): text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            r = json.loads(text.strip())

            ev = Evaluation(r.get("matched_intent", True), r.get("issue"), r.get("severity", "none"),
                           r.get("revision_needed", False), r.get("escalate_to_intent", False),
                           r.get("recommendation", ""), r.get("outcome_summary", ""))
            self._record(ev)
            return ev
        except:
            return Evaluation(True, None, "none", False, False, "continue", "eval failed")

    def _record(self, ev: Evaluation):
        data = self._load()
        data["recent"].append({"eval": asdict(ev), "ts": datetime.now().isoformat()})
        data["recent"] = data["recent"][-20:]
        self._save(data)

    def should_revise_plan(self, ev: Evaluation) -> bool:
        return ev.revision_needed or ev.severity in ["major", "critical"]

    def get_revision_context(self, ev: Evaluation, result: ExecutionResult) -> dict:
        return {"revision_needed": True, "issue": ev.issue, "recommendation": ev.recommendation,
                "user_sentiment": "frustrated" if "frustration" in (result.user_signals or []) else "engaged",
                "recent_topics": result.topics_discussed}

    def get_patterns(self) -> dict:
        return self._load().get("patterns", {})
EVALUATOR_EOF

# loop.py
cat > the_assist/hrm/loop.py << 'LOOP_EOF'
"""HRM Loop - Wires Intent, Planner, Executor, Evaluator"""
from dataclasses import asdict
from typing import Optional
import anthropic
from the_assist.hrm.intent import IntentStore
from the_assist.hrm.planner import Planner, Plan, Situation
from the_assist.hrm.executor import Executor, ExecutionResult
from the_assist.hrm.evaluator import Evaluator, Evaluation

class HRMLoop:
    def __init__(self):
        self.intent = IntentStore()
        self.planner = Planner()
        self.executor = Executor()
        self.evaluator = Evaluator()
        self._last_plan: Optional[Plan] = None
        self._last_eval: Optional[Evaluation] = None

    def process(self, user_input: str) -> str:
        situation = self.executor.get_situation()
        situation.user_input = user_input

        eval_feedback = None
        if self._last_eval and self._last_eval.revision_needed:
            eval_feedback = {"revision_needed": True, "issue": self._last_eval.issue, "recommendation": self._last_eval.recommendation}

        plan = self.planner.plan(situation, eval_feedback)
        self._last_plan = plan

        result = self.executor.execute(plan, user_input, self.planner)

        evaluation = self.evaluator.evaluate(result, asdict(plan))
        self._last_eval = evaluation

        if self.evaluator.should_revise_plan(evaluation):
            ctx = self.evaluator.get_revision_context(evaluation, result)
            ctx["last_user_input"] = user_input
            ctx["conversation_length"] = len(self.executor.get_history()) // 2
            self.planner.revise(plan, ctx)

        return result.response

    def get_opening(self) -> str:
        intent = self.intent.get_intent()
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=150,
            messages=[{"role": "user", "content": f"Generate brief opening. Stance: {intent.stance}. North stars: {intent.north_stars}. 1-2 sentences."}]
        )
        return response.content[0].text

    def end_session(self): self.executor.clear_history()
    def get_current_plan(self) -> Optional[Plan]: return self._last_plan
    def get_last_evaluation(self) -> Optional[Evaluation]: return self._last_eval
    def get_intent_summary(self) -> dict:
        i = self.intent.get_intent()
        return {"north_stars": i.north_stars, "success": i.current_success, "stance": i.stance, "non_goals": i.non_goals}
    def get_evaluation_patterns(self) -> dict: return self.evaluator.get_patterns()
    def set_stance(self, s: str): self.intent.set_stance(s)
    def clear_blocked_topic(self, t: str): self.planner.clear_blocked_topic(t)
LOOP_EOF

# main entry point
cat > the_assist/main.py << 'MAIN_EOF'
#!/usr/bin/env python3
"""The Assist - HRM Entry Point"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from the_assist.hrm import HRMLoop

def main():
    print("\n" + "="*50)
    print("THE ASSIST - HRM Architecture")
    print("="*50 + "\n")
    print("Commands: intent, plan, eval, stance X, quit, help\n")

    hrm = HRMLoop()
    intent = hrm.get_intent_summary()
    print(f"[Stance: {intent['stance']}]\n")

    print(hrm.get_opening() + "\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input: continue
        if user_input.lower() in ('quit', 'exit'):
            hrm.end_session()
            print("\nUntil next time.\n")
            break
        if user_input.lower() == 'help':
            print("\nCommands: intent, plan, eval, stance X, unblock X, quit\n")
            continue
        if user_input.lower() == 'intent':
            i = hrm.get_intent_summary()
            print(f"\n[Intent] stars={i['north_stars']}, stance={i['stance']}\n")
            continue
        if user_input.lower() == 'plan':
            p = hrm.get_current_plan()
            print(f"\n[Plan] {p.approach if p else 'none'}, {p.altitude if p else ''}\n")
            continue
        if user_input.lower() == 'eval':
            e = hrm.get_last_evaluation()
            print(f"\n[Eval] matched={e.matched_intent if e else '?'}, severity={e.severity if e else '?'}\n")
            continue
        if user_input.lower().startswith('stance '):
            hrm.set_stance(user_input[7:].strip())
            print(f"\n[Stance updated]\n")
            continue
        if user_input.lower().startswith('unblock '):
            hrm.clear_blocked_topic(user_input[8:].strip())
            print(f"\n[Unblocked]\n")
            continue

        response = hrm.process(user_input)
        print(f"\n{response}\n")

if __name__ == "__main__":
    main()
MAIN_EOF

chmod +x the_assist/main.py

# Create run script
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python the_assist/main.py
EOF
chmod +x run.sh

echo "[7/7] Setup complete!"
echo ""
echo "================================================"
echo "HRM + DoPeJar Ready"
echo "================================================"
echo ""
echo "To run:"
echo "  cd ${PROJECT_DIR}"
echo "  source venv/bin/activate"
echo "  export ANTHROPIC_API_KEY=your_key"
echo "  ./run.sh"
echo ""
echo "Or:"
echo "  python the_assist/main.py"
echo ""
