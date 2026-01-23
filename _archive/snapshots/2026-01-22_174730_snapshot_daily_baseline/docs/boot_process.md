# AI Agent System Boot Process

This document outlines the critical path for an AI agent (e.g., Claude, Gemini) to boot, initialize the Control Plane, and autonomously identify its first task within the AI_ARCH repository. This process ensures a consistent and self-serving operational state.

## 1. Agent Startup and Initial Instruction

The boot process begins when an agent starts a new session. Its first action is dictated by its primary role guide:

*   **`CLAUDE.md` / `GEMINI.md` (Root Directory)**: These files serve as the initial entry points for their respective agents. They contain the foundational instruction to kickstart the Control Plane.

    *   **Critical Action**: Execute `python3 Control_Plane/scripts/init.py`.

## 2. Control Plane Initialization (`init.py`)

The `init.py` script, located within the `Control_Plane/scripts/` directory, is the central orchestrator of the initial system setup.

*   **`Control_Plane/scripts/init.py`**:
    *   **Layer 1: BOOTSTRAP**: Verifies the existence of all essential directories, critical files (e.g., `SYSTEM_CONSTITUTION.md`), and required tools (e.g., `python3`, `git`).
    *   **Layer 2: VALIDATE**: Ensures data integrity by validating `MANIFEST.json` checksums, registry schemas, and path references.
    *   **Layer 3: INIT (Semantic)**: Processes and compiles the system's registries to establish the current operational mode (e.g., BUILD, STABILIZE) and generates an initial `plan.json`.

*   **`Control_Plane/registries/*.csv`**: These registry files are the **source of truth** for all managed items, modules, and governance protocols. They are read by `init.py` during validation and initialization.

## 3. Post-Initialization Task Discovery

Immediately after `init.py` successfully completes all three layers, the agent proceeds to identify its next task autonomously, leveraging the `_Prompt-Cache_`.

*   **`/_Prompt-Cache_/STATUS.md`**: This file acts as the primary **status board and hand-off point**.
    *   **Critical Action**: The agent reads `STATUS.md` (specifically the "Agent pull (post-init)" section) to find instructions on how to proceed. It directs the agent to its dedicated `AgentPull` runner prompt.

*   **`/_Prompt-Cache_/INDEX.md`**: This file serves as the **comprehensive ledger** of all prompts within the cache.
    *   **Critical Action**: The `AgentPull` runner consults `INDEX.md` to locate the correct prompt file (e.g., `Claude_..._AgentPull_RunPending.md`) based on its unique ID and status.

*   **Agent-Specific `AgentPull` Prompt (e.g., `Claude_20260122_032208_AgentPull_RunPending.md`)**:
    *   **Role**: This is the agent's **self-serving mechanism**. It contains the logic for the agent to systematically identify, pull, and execute its next pending task based on the current state in `STATUS.md` and `INDEX.md`.

## Summary of Critical Path

The critical path for boot and init ensures that an agent:
1.  Is properly initialized and validated against the system's configuration.
2.  Transitions smoothly from setup to task execution.
3.  Operates autonomously by discovering its next actions from the `_Prompt-Cache_` without requiring human intervention (the "no human relay" principle).

This structured approach guarantees that the system is always in a known good state and that agents can efficiently proceed with their assigned workflows.
