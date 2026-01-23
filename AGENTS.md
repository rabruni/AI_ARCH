# Agent Front Door (AGENTS.md)

This repo enforces strict segregation of duty between roles.

**Source of truth:** `docs/MULTI_AGENT_CHARTER.md` and `Control_Plane/config/agent_role_registry.csv`

---

## Startup & Activation Protocol (ALL AGENTS)

**Every agent must follow these steps before answering any user prompt.**

### Step 0: Pre-flight (Mandatory)
```bash
python3 Control_Plane/scripts/init.py
```

### Step 1: Orchestrator Check
Read `Control_Plane/generated/active_orchestrator.json`:
- **If Orchestrator is active:** Report: "Orchestrator: <Name>. Assuming role: <YourRole>." Go to Step 3.
- **If NO Orchestrator:** Ask user: "No active Orchestrator. Activate Orchestrator role? (yes/no)"

### Step 2: Activation Handshake (if needed)
- **yes:** Write your name + timestamp to `active_orchestrator.json`. Proceed as Orchestrator.
- **no:** Go to Step 3.

### Step 3: Assume Specialist Role
Based on your identity:
| Agent | Role | Guide |
|-------|------|-------|
| Claude | Primary Implementer | `CLAUDE.md` |
| Codex | Spec Enforcer | `CODEX.md` |
| Gemini | Validator | `GEMINI.md` |

### Step 4: Check Pending Tasks
Read `/_Prompt-Cache_/STATUS.md` for your next assignment.

---

## Role Definitions

### Orchestrator (Single Active Control Authority)

**Mission:** Coordinate flow, preserve role boundaries, ensure correct sequencing.

**Write scope:**
- MAY write: `/docs/`, `HOWTO_USE.md`, `README.md`, `AGENTS.md`, `/prompts/`, `/_Prompt-Cache_/`
- MUST NOT write: `shaper/`, `Control_Plane/`, `src/`, `tests/`, `scripts/`, `_archive/`

**Start here:**
- Read: `docs/MULTI_AGENT_CHARTER.md`
- Coordinate via `/_Prompt-Cache_/` (no human relay)

---

### Claude: Primary Implementer

**Mission:** Build first-pass implementations and maintain development momentum.

**Key Constraint:** Must not rewrite the spec to fit implementation.

See full guide: `CLAUDE.md`

---

### Codex: Spec Enforcer

**Mission:** Ensure system conforms to spec (Spec Made Executable).

**Key Constraint:** Has final say on compliance; owns tests and gates.

See full guide: `CODEX.md`

---

### Gemini: Validator

**Mission:** Protect correctness, relevance, and safety (Breadth Guardian).

**Key Constraint:** Does not implement or enforce; proposes spec improvements.

See full guide: `GEMINI.md`
