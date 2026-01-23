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
