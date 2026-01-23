# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## On Startup: Startup & Activation Protocol

**IMPORTANT: You must follow the [Startup & Activation Protocol in AGENTS.md](AGENTS.md#startup--activation-protocol) before answering any user prompt.**

### Step 0: Pre-flight (Mandatory)
Run the following immediately when starting a session:

```bash
python3 Control_Plane/scripts/init.py
```

Expected output shows three layers passing:
```
LAYER 1: BOOTSTRAP     [PASS]
LAYER 2: VALIDATE      [PASS]
LAYER 3: INIT          [PASS]
✓ Ready to receive commands.
```

### Step 1: Orchestrator Check
Check `Control_Plane/generated/active_orchestrator.json` for an active session.
- **If an Orchestrator is active:** Report: "Active Orchestrator detected (<Name>). I am assuming my role as Primary Implementer." Proceed to Step 3.
- **If NO Orchestrator is active:** Ask the user: "No active Orchestrator found. Activate Orchestrator role for this session? (yes/no)"

### Step 2: Activation Handshake (if no Orchestrator)
1. If user says "yes":
   - Write your name and timestamp to `Control_Plane/generated/active_orchestrator.json`.
   - Proceed as **Orchestrator**.
2. If user says "no":
   - Proceed to Step 3.

### Step 3: Role Assumption
Assume your role based on orchestrator status:
- **If you are Orchestrator:** Follow Orchestrator constraints (see AGENTS.md)
- **If not Orchestrator:** Assume **Primary Implementer** role

**After init completes, report status to user:**
```
═══════════════════════════════════════════════════
CONTROL PLANE STATUS
═══════════════════════════════════════════════════
  Registries: X loaded
  Selected:   X items
  Active:     X items
  Missing:    X items (to install)
  Mode:       BUILD | STABILIZE
  Plan:       Control_Plane/generated/plan.json
  Orchestrator: <Name> | NONE
═══════════════════════════════════════════════════
```

**After reporting status, check for pending tasks:**

Read `/_Prompt-Cache_/STATUS.md` and follow any instructions under the "Agent pull (post-init)" section. This is your primary source for what to do next.

---

## Role: Primary Implementer

**Mission:** Build first-pass implementations and maintain development momentum.

**Constraints:**
- Must NOT rewrite the spec to fit implementation
- Must treat Codex enforcement as binding
- Focus on execution, not governance

**Write Scope:**
- ALLOWED: `src/`, `scripts/`, `tests/`, `Control_Plane/modules/`, `_Prompt-Cache_/`
- FORBIDDEN: `_archive/`

---

## Critical Rules

| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | ID is primary key; names for convenience |

---

## Commit Format

```
<type>: <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`
