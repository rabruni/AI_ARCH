# GEMINI.md

This file provides guidance for Google Gemini when working with code in this repository.

---

## On Startup: Startup & Activation Protocol

**IMPORTANT: You must follow the [Startup & Activation Protocol in AGENTS.md](AGENTS.md#startup--activation-protocol) before answering any user prompt.**

### Step 0: Pre-flight (Mandatory)
Run this immediately when starting a session:

```bash
python3 Control_Plane/scripts/init.py
```

Expected output:
```
LAYER 1: BOOTSTRAP     [PASS]
LAYER 2: VALIDATE      [PASS]
LAYER 3: INIT          [PASS]
✓ Ready to receive commands.
```

### Step 1: Orchestrator Check
Check `Control_Plane/generated/active_orchestrator.json` for an active session.
- **If an Orchestrator is active:** Report its presence and assume your role as **Validator**.
- **If NO Orchestrator is active:** Follow the handshake in `AGENTS.md`.


**After init, check for pending tasks:** Read `/_Prompt-Cache_/STATUS.md` and follow any instructions under the "Agent pull (post-init)" section. This is your primary source for what to do next.

## Validation Protocol: The Self-Healing Loop

Your role is not just to grade, but to **drive correction**.

**If Validation FAILS:**
1.  **Do NOT stop.**
2.  **Create a Fix Prompt**: Write a new file `/_Prompt-Cache_/Claude_<TIMESTAMP>_Fix_<TaskID>.md`.
    *   Include the full error log/traceback.
    *   Provide specific instructions on what needs to be fixed.
    *   Mandate a smoke test for the fix.
3.  **Update Index**: Add a row to `/_Prompt-Cache_/INDEX.md` for this new prompt, marking it `sent`.
4.  **Update Status**: In `/_Prompt-Cache_/STATUS.md`:
    *   Mark the validation task as `FAIL`.
    *   Add a line for the new Fix Prompt as `ready`.
    *   Increment the `retry_count` for this thread (if not present, start at 1).

**If Validation PASSES:**
1.  Mark the task as `complete` / `passed` in `STATUS.md` and `INDEX.md`.

Then read: `Control_Plane/CONTROL_PLANE_SPEC.md`

---

## Key Concepts

- **Registry is source of truth:** `Control_Plane/registries/control_plane_registry.csv`
- **ID is primary key; names accepted for convenience** (P003)
- **Four verbs:** install, update, verify, uninstall

---

## Commands

```bash
# List everything
python3 Control_Plane/scripts/registry.py list control_plane

# Show item by name
python3 Control_Plane/scripts/registry.py show "Definition of Done"

# Modify item
python3 Control_Plane/scripts/registry.py modify "Local Dev Harness" selected=yes

# Check dependencies
python3 Control_Plane/scripts/link.py check
```

---

## Critical Rules

| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | ID is primary key; names for convenience |

---

## Commit Suffix

```
Co-Authored-By: Gemini <noreply@google.com>
```
