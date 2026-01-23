# Control Plane Documentation (v2 - Audited)

This document provides a complete overview of the deterministic, gate-enforced AI execution platform. It has been audited against the production implementation in the `Control_Plane/` directory.

## 1. System Overview

### 1.1. The Problem: The Unpredictability of Agent-First Systems

Autonomous agent systems that directly interpret and execute natural language intent are inherently non-deterministic. Their behavior can change based on model version, prompt phrasing, or even subtle variations in context, leading to unpredictable outcomes. This makes them fundamentally un-auditable and unsafe for tasks requiring high reliability and correctness. Such systems often fail silently, produce plausible but incorrect work, and drift from the original user's intent without a mechanism to enforce alignment.

### 1.2. The Solution: A Deterministic, Gate-Enforced Execution Contract

This system inverts the traditional agent model. Instead of trusting an AI to interpret and act, it uses AI as a tool to help a human author a **deterministic, machine-readable execution contract**, known as a `WORK_ITEM.md`.

The core principles are:

*   **Determinism:** The `WORK_ITEM.md` is a precise specification of work. It is the sole source of truth for execution. The AI does not interpret this contract; it is executed verbatim by a simple, non-intelligent worker.
*   **Explicit Commitment:** A human must review, approve, and explicitly commit the `WORK_ITEM.md` for execution via a structured `08_commit.md` file. This action is a hard boundary, moving from a flexible "shaping" phase to a locked "execution" phase.
*   **Gate-Enforced Governance:** Before any execution occurs, the committed contract is validated by a series of deterministic, automated gates. The `G0` gate, for instance, validates the contract's schema, scope, and hash integrity. If any check fails, execution is blocked.

This architecture treats the AI as an untrusted client and the human as the accountable authority, enabling safe, auditable, and reliable automation.

## 2. System Architecture

### 2.1. Components

*   **AI Shaper:** A front-end, human-facing interface. Its only role is to assist a human in drafting a `WORK_ITEM.md`. It has no execution capabilities.
*   **Human Operator:** The engineer or lead who uses the AI Shaper, reviews the `WORK_ITEM.md`, and makes the explicit decision to commit it.
*   **Control Plane:** The deterministic core of the system. Its primary interface is the `cp.py` script. It contains no LLMs and its purpose is to manage the lifecycle of a spec-driven flow and enforce validation gates.
*   **Gates (G0-G3):** A series of non-negotiable, programmatic checkpoints within the Control Plane, implemented in `gate_runner.py`. `G0` is the primary commit-time gate that validates the execution contract's correctness and integrity.
*   **Worker Agents:** Simple, non-intelligent script runners. They are treated as untrusted and are only activated after a contract successfully passes the `G0` gate.

### 2.2. Trust Boundaries

*   **Untrusted Zone:** Contains the AI Shaper and the Worker Agents. These components are assumed to be fallible and are never given authority.
*   **Human-in-the-Loop:** The human operator is the source of authority, responsible for reviewing and committing the `WORK_ITEM.md`.
*   **Trusted Computing Base (TCB):** The Control Plane (`cp.py`, `flow_runner/`, `scripts/`) and its gate system. This is the only part of the system that is trusted to enforce rules correctly.

### 2.3. Control Flow: From Intent to Audited Execution

1.  **Shaping (Human & AI):** The **Human Operator** uses the **AI Shaper** to draft a `WORK_ITEM.md`.
2.  **Commitment (Human):** The Human Operator finalizes the `WORK_ITEM.md` and updates `08_commit.md` to set `MODE=COMMIT`.
3.  **Initiation (Human/CI):** The operator starts the execution flow using the command line: `python3 Control_Plane/cp.py flow start <SPEC_ID>`.
4.  **Enforcement (Control Plane):** The `flow start` command initializes a session. Subsequent `flow next` and `flow done` commands advance the state machine. When the flow reaches a phase requiring gates (like `Phase0A`), the `G0` gate is invoked automatically by `flow_runner.py`.
5.  **Validation (G0 Gate):** `G0` performs its checks as implemented in `gate_runner.py`.
6.  **Execution Block (Default):** If `G0` fails, the `gate_runner` returns a 'failed' status, which is recorded in `gate_results.json`. The flow is halted.
7.  **Execution Dispatch (Control Plane):** If `G0` passes, the flow proceeds. Downstream mechanisms (not detailed in the reviewed code) are responsible for dispatching the `WORK_ITEM.md` to a Worker Agent.
8.  **Auditing:** The output of the `G0` gate, including the work item's hash, is stored in `gate_results.json`, creating an immutable audit trail.

---
# CHANGE LOG (v1 to v2)

*   **Added `cp.py` as the main interface:** The original document described the concepts but omitted the primary user tool. The architecture and user guide sections were updated to reference the `cp.py` script and its `flow start/next/done` commands as the concrete implementation of the control flow.
*   **Clarified G0 Enforcement Nuance:** The original document stated that `WORK_ITEM.md` was a hard requirement. The audited code in `gate_runner.py` reveals this is only enforced if a `work_items/` directory exists within the SPEC pack. The documentation has been updated to reflect this conditional enforcement, which is a critical detail for users and auditors.
*   **Refined Control Flow:** The control flow was updated to be more precise, describing the `flow start -> next -> done` state machine that actually drives the process, rather than an abstract "commit" trigger.
*   **General Wording:** Minor changes were made to align terminology with the scripts and code files reviewed (e.g., explicitly mentioning `gate_runner.py`).

---
---

# Quick Start

This guide provides the absolute minimum commands to get the Control Plane running and see its status.

## 1. Prerequisites

*   Python 3.9+
*   Required packages installed (`pip3 install -r requirements.txt`)

## 2. Boot and Initialize

The `init.py` script validates the environment and ensures the system is ready. Run it from the repository root.

```bash
python3 Control_Plane/scripts/init.py
```
Expected output ends with `[OK] Ready to receive commands.`

## 3. List Registered Items

To see all frameworks, modules, and components the Control Plane is aware of, use the `cp.py` script.

```bash
python3 Control_Plane/cp.py list control_plane
```
This command reads the central registry and displays a table of all known items and their status.

## 4. Next Steps

You have successfully started and queried the Control Plane. To learn how to execute a task, proceed to the **Getting Started** guide.

---
---

# Getting Started

This guide walks through the end-to-end process of executing a task safely using the Control Plane.

## 1. Objective

Our goal is to execute a pre-defined task (a `SPEC Pack`) by validating it through the `G0` gate and preparing it for a worker. We will use `SPEC-003` as our example, as it is designed to test the `WORK_ITEM.md` contract.

## 2. The Execution Contract (`WORK_ITEM.md`)

Before starting, familiarize yourself with the execution contract. Open and review `Control_Plane/docs/specs/SPEC-003/work_items/WI-003-01.md`. This file tells the system exactly what to do, what files it can touch, and how to verify success.

## 3. The Commit Manifest (`08_commit.md`)

Next, review `Control_Plane/docs/specs/SPEC-003/08_commit.md`. This file acts as the human's explicit authorization to run the task. Note the line `MODE: COMMIT`, which is essential for passing the G0 gate.

## 4. Starting the Flow

All interactions with the execution flow are handled by the `cp.py` script. To begin, start a new flow session for `SPEC-003`.

```bash
python3 Control_Plane/cp.py flow start SPEC-003
```
This command creates a new session and tells you the current phase, which should be `Phase0A`.

## 5. Advancing the Flow to Trigger G0

The system moves through phases. To advance from the current phase and trigger the gate evaluation, use the `flow done` command. The `--paste` argument provides a placeholder input, as required by the state machine.

```bash
python3 Control_Plane/cp.py flow done SPEC-003 --phase Phase0A --paste "Proceeding to G0 validation."
```

This command will trigger the `G0` gate. The `gate_runner.py` script will now:
1.  Read `08_commit.md`.
2.  Verify `MODE=COMMIT`.
3.  Find the reference to `WI-003-01.md`.
4.  Execute `validate_work_item.py` on the file.
5.  Calculate the file's hash.

## 6. Checking the Results

The results of the gate run are saved to an artifact. Check the contents of the `gate_results.json` file.

```bash
cat Control_Plane/docs/specs/SPEC-003/artifacts/phase0A/gate_results.json
```

Look for `"status": "passed"` inside the JSON structure for the `G0` gate. You will also see the `evidence` block containing the `work_item_id` and `work_item_hash`, providing a full audit trail.

If the status is `failed`, the `reason` field will tell you exactly what went wrong.

You have now successfully and safely validated an execution contract through the Control Plane.

---
---

# FAQ

**Q1: What is the difference between `EXPLORE` and `COMMIT` mode?**

**A:** `EXPLORE` is a planning mode. When `08_commit.md` is set to `MODE: EXPLORE`, the `G0` gate will deterministically fail and block all execution. This is a safety feature to allow for planning and spec definition without any risk of running a task. `COMMIT` is the explicit signal that you have reviewed and approved the work item for execution.

**Q2: My execution failed at the `G0` gate. Why?**

**A:** The most common reasons for a `G0` failure are:
*   **Wrong Mode:** `08_commit.md` is not set to `MODE: COMMIT`.
*   **Invalid Work Item:** The referenced `WORK_ITEM.md` has a validation error. Check its syntax, ensure all required sections exist, and verify file paths are correct. The `reason` field in `gate_results.json` will contain the specific error from `validate_work_item.py`.
*   **Missing Work Item:** The `work_items/` directory exists for your SPEC, but `08_commit.md` does not reference a `WORK_ITEM.md` file.

**Q3: Can I run an AI agent directly?**

**A:** No. The entire system is designed to prevent this. All execution is mediated by the Control Plane. An AI can be used to *draft* a `WORK_ITEM.md`, but that contract *must* be validated by the gate system before a simple, non-intelligent worker can execute it. There is no path for an AI to gain direct execution control.

**Q4: What is a `SPEC Pack`?**

**A:** A `SPEC Pack` is a self-contained directory that defines a complete unit of functionality or work. It includes design documents, requirements, registry entries, and the execution contracts (`WORK_ITEM.md`, `08_commit.md`). The Control Plane operates on these packs, making work modular and auditable.

**Q5: How do I know the `WORK_ITEM.md` wasn't tampered with?**

**A:** The `G0` gate calculates a SHA256 hash of the `WORK_ITEM.md` file at the time of validation. This hash is stored in the `gate_results.json` audit log. The system has capabilities to compare this hash against previous runs to detect unexpected changes, providing a strong guarantee of integrity.

---
---

# LLM Integration Guide

## 1. Required Architecture: A Clean Separation of Concerns

The foundational principle of integrating an LLM with the Control Plane is maintaining a strict architectural boundary.

*   **The LLM System (Untrusted Zone):** This includes your LLM (e.g., Gemini), any prompt engineering logic, and the user-facing front-end (the "AI Shaper"). This system's **only job** is to produce a valid `WORK_ITEM.md` and `08_commit.md` as text artifacts. It must not have permissions to execute shell commands or directly access Control Plane scripts.
*   **The Filesystem (The Interface):** The LLM system interacts with the Control Plane by writing files (`WORK_ITEM.md`, `08_commit.md`) to a designated directory within a `SPEC Pack`.
*   **The Control Plane (Trusted Zone):** This system reads from the filesystem. It is triggered (e.g., by a CI/CD pipeline watching for commits, or a wrapper script) and begins its deterministic validation process, starting with the `cp.py flow start` command.

An LLM must **never** be in the trusted zone. It is a text generator, not a command executor.

## 2. Core Integration Logic

A successful integration requires the LLM front-end to perform the following steps:

1.  **Generate the Contract:** Guide the LLM to generate the full text of a `WORK_ITEM.md` that is syntactically valid and semantically correct.
2.  **Generate the Commit Manifest:** Generate a corresponding `08_commit.md` file with `MODE: COMMIT` and a reference to the newly created work item.
3.  **Write to Disk:** Place both files in the correct `SPEC Pack` directory.
4.  **Trigger the Control Plane:** The most robust method is to commit these files to git, which then triggers a CI job. The CI job's responsibility is to call the Control Plane:
    ```bash
    # Example CI job step
    python3 Control_Plane/cp.py flow start <SPEC_ID>
    python3 Control_Plane/cp.py flow done <SPEC_ID> --phase Phase0A --paste "CI trigger"
    ```
5.  **Monitor for Results:** After triggering, the integration logic must **monitor the filesystem** for the creation of `gate_results.json` in the relevant artifact directory. It must not assume success.
6.  **Parse and Report:** Parse the `gate_results.json` file. Check the `status` for the `G0` gate.
    *   If `"status": "passed"`, the integration can report success to the user.
    *   If `"status": "failed"`, the integration must parse the `reason` field and present this clear, deterministic error message to the user for correction.

## 3. Key Integration Points & APIs

Your LLM system does not call "APIs" in the traditional sense. It interacts with scripts via the filesystem and command-line interfaces.

*   **Primary Input Artifact:** `Control_Plane/docs/specs/<SPEC_ID>/work_items/<WORK_ITEM_ID>.md`
*   **Primary Trigger Artifact:** `Control_Plane/docs/specs/<SPEC_ID>/08_commit.md`
*   **Primary Control Script:** `Control_Plane/cp.py`
    *   `cp.py flow start`: Your integration's trigger mechanism must call this first.
    *   `cp.py flow done`: Must be called to advance the state machine and trigger the gates.
*   **Primary Validation Script (for pre-flight checks):** `Control_Plane/scripts/validate_work_item.py`
*   **Primary Output/Result Artifact:** `Control_Plane/docs/specs/<SPEC_ID>/artifacts/<phase>/gate_results.json`

## 4. Token Efficiency Patterns

Context windows are valuable. Do not waste tokens by showing the LLM irrelevant code.

*   **DO:** Provide the full, annotated schema of `WORK_ITEM.md` and `08_commit.md` in the system prompt. Use comments to explain what each section is for.
*   **DO:** Use two or three high-quality, valid examples of `WORK_ITEM.md` as a few-shot prompt. This is far more effective than lengthy prose explanations.
*   **DO NOT:** Show the LLM the Python code for `gate_runner.py` or `cp.py`. The LLM doesn't need to know *how* it's being validated, only *what* a valid artifact looks like.
*   **TIP:** For error correction, provide the LLM with the failed `WORK_ITEM.md` and the specific `reason` string from `gate_results.json`. Its task is then narrowly focused: "Fix this YAML file to solve the following error: 'Missing section: Acceptance Commands'".

## 5. Risks, Concerns, and Tips

*   **Risk: Malicious `WORK_ITEM.md` Generation.** A sophisticated user could use prompt injection to make the LLM generate a work item with dangerous `Acceptance Commands` (e.g., `rm -rf /`).
    *   **Mitigation:** This is precisely why the human review step (Step 3 in the Safe Operating Procedure) is non-negotiable. The system assumes the human operator is accountable for the commands they approve.
*   **Concern: Pre-flight Validation.** Waiting for the full CI/CD cycle and G0 run to get feedback on a simple syntax error is inefficient.
    *   **Tip:** Your front-end application should perform a "pre-flight" check by running `validate_work_item.py` on the generated file *before* committing. This provides instant feedback to the user and the LLM, saving time and CI resources.
*   **Risk: Scope Creep in Prompts.** Vague user prompts will lead to vague, over-scoped work items.
    *   **Tip:** Design your AI Shaper's logic to be relentlessly inquisitive. If a user says "fix the bug," the Shaper's first questions must be "Which file is the bug in? How can we write a test to prove it's fixed?". Force the user down a path of specificity.
