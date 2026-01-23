# Control Plane

The `Control_Plane` directory houses the core governance and operational framework for the AI agent system. It is designed to be the central nervous system, orchestrating agent behavior, managing system state, and ensuring adherence to defined protocols.

## Key Components:

-   **`scripts/`**: Contains essential Python scripts, including `init.py`, which performs system bootstrapping and validation, and `registry.py` for managing registry entries.
-   **`registries/`**: This subdirectory holds the system's registries in CSV format. These registries are the **source of truth** for all managed items, components, and their associated metadata.
-   **`generated/`**: Stores dynamically generated files, such as `plan.json`, `selection_report.md`, and compiled registry outputs, which reflect the current operational state and task planning.
-   **`control_plane/`**: Contains internal definitions and prompts specific to the Control Plane's operations.

## Role in the Boot Process:

During system startup, `Control_Plane/scripts/init.py` is executed to:
1.  Validate the environment and core file structures.
2.  Read and compile the registries from `registries/`.
3.  Establish the initial operational mode (e.g., BUILD, STABILIZE).

The Control Plane acts as the foundational layer, ensuring the system is in a consistent and validated state before agents proceed with specific tasks.