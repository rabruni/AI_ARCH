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
