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
