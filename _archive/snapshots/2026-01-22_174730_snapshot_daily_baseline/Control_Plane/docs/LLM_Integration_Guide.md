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
