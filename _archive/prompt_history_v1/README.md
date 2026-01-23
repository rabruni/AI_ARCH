# Prompt Cache

The `_Prompt-Cache_` directory serves as the central hub for agent communication, task management, and workflow orchestration. It contains all prompts, status updates, and indexing information that agents use to understand their tasks, track progress, and coordinate actions.

## Key Components:

-   **`STATUS.md`**: This critical file acts as the operational status board. Agents read `STATUS.md` after initialization to determine their next actions, identify pending tasks, and follow instructions for agent-pull mechanisms. It is the primary source for understanding the current state of work.
-   **`INDEX.md`**: This file functions as a comprehensive ledger for all prompts within the cache. It indexes prompts by ID, agent, status (e.g., `draft`, `sent`, `completed`), and provides file paths, ensuring traceability and manageability of all communication artifacts.
-   **Prompt Files**: Individual markdown files (e.g., `Claude_...md`, `Gemini_...md`, `Orchestrator_...md`) that contain specific instructions, goals, and context for agents to execute. These files are typically referenced by `STATUS.md` and `INDEX.md`.

## Role in the Agent Workflow:

After an agent successfully boots and initializes the Control Plane, its first action is to consult `/_Prompt-Cache_/STATUS.md`. This file directs the agent to its specific `AgentPull` prompt, which then uses `INDEX.md` and `STATUS.md` to identify and execute the next assigned task.

The `_Prompt-Cache_` enables a "no human relay" communication model, where agents autonomously pull and execute tasks based on the shared state within this directory.