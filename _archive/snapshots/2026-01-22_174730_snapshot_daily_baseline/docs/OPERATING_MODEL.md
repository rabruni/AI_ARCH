# Operating Model (Roles + Rules of Engagement)

## 1) Scope

This document is the source of truth for:
- roles and segregation of duty (who does what)
- communication and handoff protocol
- separation between team, core system, and residents
- prompt authoring and storage rules

## 2) Terminology: “Repo” vs “Git”

When we say “repo”, we distinguish:
- **Filesystem working tree:** the directory on disk we are operating in (tracked + untracked files). This is the operational “source of truth” during a session.
- **Git history:** the commit graph (what is permanently recorded). This is the audit/persistence layer.

Rules:
- Work is coordinated against the filesystem working tree.
- Durability and provenance come from git commits (performed by the Builder role).

## 3) Team Roles (Highest Altitude)

**Canonical Source of Truth:** `docs/MULTI_AGENT_CHARTER.md`

The system strictly separates **creation**, **verification**, **validation**, and **coordination**.

### Orchestrator (Single Active Control Authority)
**Mission:** Coordinate flow, preserve role boundaries, and ensure correct sequencing.
**Key Rule:** Only one Orchestrator exists at a time.
**Authority:** Can pause/redirect agents but **cannot override Codex’s compliance verdict**.

### Claude (Primary Implementer)
**Mission:** Build first-pass implementations and maintain development momentum.
**Key Rule:** Must not rewrite the spec to fit implementation.

### Codex (Spec Enforcer & Compliance Gate)
**Mission:** Ensure the system conforms to the spec; represents the **spec made executable**.
**Key Rule:** Has final say on compliance; owns tests and gates.

### Gemini (Validator, Risk Scout & Aperture Keeper)
**Mission:** Protect correctness, relevance, and safety; acts as the **breadth guardian**.
**Key Rule:** Does not implement or enforce; proposes spec improvements before implementation.


## 3) System Layers (Do Not Conflate)

### Layer A: Team (governance + coordination)

The human + model roles that plan, design, validate, and implement.

### Layer B: Core System (this repo’s core application)

**Shaper + Control Plane**. This is where core logic lives and where current progress/blockers may occur.

### Layer C: Residents (planned inhabitants)

Systems such as `assist` / `locked_system` are future residents of the core system. They are not the core system and must not be merged conceptually with Shaper/Control Plane behavior or team roles.

## 4) Development Lifecycle (The Loop)

We use a strict loop to prevent drift:

1. **ORCHESTRATE (Orchestrator):** define scope + prompt and write handoff to `/_Prompt-Cache_/`.
2. **ARCHITECT (Claude):** materialize design artifacts (schemas/spec packs) from the prompt.
3. **AUDIT (Gemini):** issue PASS/FAIL against the authoritative artifacts.
4. **IMPLEMENT (Claude/Codex Specialist):** build exactly what was specified.
5. **VERIFY (Gemini):** run tests/validation; confirm determinism and edge cases.
6. **COMMIT (Claude):** stage and commit verified changes.

## 4.1 Execution Ethos (Agent-Run Work)

Core ethos: repository work is executed by the assigned agent roles, not by manual human edits.

Rules:
- The **Human Operator** approves goals/scope and selects which agent acts, but does not directly edit repo files as part of the workflow.
- **All filesystem changes** (code, specs, work items, context packets, docs, prompts) are written by an agent operating under its role constraints.
- Shaping authoritative intent artifacts (`WORK_ITEM` / `SPEC`) is performed via Shaper (`./shaper.sh` or `python3 Control_Plane/cp.py shape`) by an agent session designated to run it.

## 5) Communication Protocol

- **Prompt-driven handoffs:** agents do not “chat”; they exchange prompt files in `/_Prompt-Cache_/`.
- **Curated prompts:** stable templates live in `/prompts/`.
- **Artifact authority:** the working filesystem (checked-in files + working tree) is the source of truth; chat is ephemeral.
- **No hallucinated handoffs:** no one claims “done” unless the artifact exists on disk.
- **No human relay:** humans do not copy/paste prompts between agents; agents pull their tasks from the prompt cache.

## 6) Prompt Authoring + Storage

### 6.1 Prompt Cache Directory

All prompts that the orchestrator is asked to write are saved to `/_Prompt-Cache_/`.

Canonical directory: `/_Prompt-Cache_/` (hyphenated). Do not use `/_Prompt_Cache_/` (deprecated/removed).

Indexes:
- `/_Prompt-Cache_/INDEX.md` (index of record; append-only rows)
- `/_Prompt-Cache_/STATUS.md` (living status board for active threads)

### 6.1.1 Prompts Directory

Curated, reusable prompts and templates live in `/prompts/`.

### 6.1.2 Prompt-Cache Protocol (L1 Exchange Bus)

`/_Prompt-Cache_/` is the **agent-to-agent exchange bus** for prompts, feedback, audit notes, and handoffs.

Requirements:
- Every new prompt or feedback file MUST be added to `/_Prompt-Cache_/INDEX.md`.
- Files MUST use deterministic naming and include a small YAML header for indexing.
- Prompts and feedback are separate files; do not overwrite.

### 6.1.3 Prompt Quality Rules (Stand-alone + Cost-Effective)

- Prompts MUST be **standalone**: no placeholders, no “fill this in”, no reliance on chat context.
- Prompts MUST be **executable**: include all required paths, identifiers, and deliverable format.
- Prompts MUST be **token-efficient**: shortest text that still enforces constraints and success criteria.
- Prompts MUST be **deterministic**: no timestamps/UUIDs/randomness inside the prompt body unless required by the task.

### 6.2 Naming Policy

Filename pattern:
`<Target_Agent>_<YYYYMMDD_HHMMSS>_<Goal>.md`

Rules:
- `Target_Agent` is a short identifier like `Claude`, `Gemini`, `Codex`
- timestamp uses local time in `YYYYMMDD_HHMMSS`
- `Goal` is a concise slug (words joined by `_`, non-alphanumerics removed)

### 6.3 Output Contract

When asked to write a prompt, the orchestrator:
- writes the prompt to `/_Prompt-Cache_/` using the naming policy
- does not automatically read the prompt back in chat
- reads it back only on explicit request (e.g., “show me the prompt contents”)

### 6.4 Execution Contract (Agent-Pull)

- Agents are responsible for discovering and executing their next work item by reading:
  - `/_Prompt-Cache_/STATUS.md` (current thread state)
  - `/_Prompt-Cache_/INDEX.md` (artifact ledger + file paths)
- Humans do not relay prompt bodies between chats.
- All agent outputs are written as prompt/feedback artifacts and indexed.

## 7) Segregation Of Duty (Write Access)

### 7.1 What “Segregation of Duty” means here

Segregation of duty means different roles have different write responsibilities so that no single role both:
- defines intent and constraints
- implements core changes
- validates correctness

This reduces drift and prevents “marking your own homework”.

### 7.2 Enforced write scopes

**Orchestrator (this instance)**
- MAY write: `/docs/`, `HOWTO_USE.md`, `README.md`, `AGENTS.md`, `/prompts/`, `/_Prompt-Cache_/`
- MUST NOT write: `shaper/`, `Control_Plane/`, `src/`, `tests/`, `scripts/`, `_archive/`

**Gemini (Validator)**
- MAY write: `/docs/`, `/prompts/`, `/_Prompt-Cache_/`
- MUST NOT write: core implementation code paths

**Claude (Builder)**
- MAY write: any repo path required to implement approved work
- Responsible for: core implementation, running commands, and git operations when needed

**Codex (The Specialist) — other instances only**
- MAY write: core implementation code paths when explicitly invoked
- Otherwise stays idle

### 7.3 Prompt exception

All roles MAY read and write prompts to:
- `/prompts/`
- `/_Prompt-Cache_/`

## 8) Safety Constraints (“Firewall”)

- The Control Plane is sacred: do not modify gating/execution logic (e.g., `cp.py`, `gate_runner`) without an explicit, audited design prompt.
- Validation is zero-trust: verification is performed by the validator role, not by the implementing role.

## 9) Session Start (Codex Orchestrator)

When starting a new Codex CLI session in this repo:
- open `AGENTS.md` (front door) and confirm you are acting as **Orchestrator**
- read this file (`docs/OPERATING_MODEL.md`)
- use `/_Prompt-Cache_/` for all handoffs and prompt iteration
- do not write core implementation paths; route implementation to Claude (or Codex Specialist when explicitly invoked)

### 9.1 Orchestrator activation (not automatic)

Being inside this repo does **not** automatically grant the orchestrator role to every Codex session.

Activation handshake (required each new session):
- The Codex session starts **UNASSIGNED**.
- It must ask the human operator: “Activate Orchestrator role for this session? (yes/no)”.
- Only on explicit “yes” may it operate as the Orchestrator and apply the orchestrator write-scope rules.
- On “no”, the session remains UNASSIGNED and should not perform orchestration work (it may exit or wait for an explicit Specialist prompt).
