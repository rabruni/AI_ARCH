# Control Plane Governance

**This repo is governed by a Control Plane.** Read this before doing work.

---

## Always Follow (Even Without /init)

1. **ID is primary key** - Look up items by ID (e.g., FMWK-001), not name
2. **Registries are truth** - CSVs in `Control_Plane/registries/` define what exists
3. **Archive, never delete** - Move to `_archive/`, don't delete files

---

## Commands

| Command | Action |
|---------|--------|
| `/init` | Boot full Control Plane governance |
| `/plan` | Show pending work from plan.json |
| `/validate` | Run integrity checks |

---

## /init Procedure

When user says `/init`, execute these steps and report PASS/FAIL for each:

### Step 1: Bootstrap (Environmental)
```bash
python3 Control_Plane/scripts/bootstrap.py
```
- **PASS**: "BOOTSTRAP OK" in output
- **FAIL**: Fix environmental issues before continuing

### Step 2: Validate (Integrity)
```bash
python3 Control_Plane/scripts/validate.py
```
- **PASS**: "VALIDATION OK" in output
- **FAIL**: Data integrity compromised, fix before continuing

### Step 3: Generate Plan (Semantic)
```bash
python3 Control_Plane/scripts/apply_selection.py
```
- **PASS**: Creates `Control_Plane/generated/plan.json`
- **FAIL**: Registry semantic error, check CSV content

### Step 4: Load Governance Rules
```
READ: Control_Plane/init/init.md
READ: Control_Plane/CLAUDE.md
```
- **PASS**: Files exist and are readable
- **FAIL**: Critical governance files missing

### Step 5: Report Status
```
Report to user:
  ════════════════════════════════════════
  CONTROL PLANE INITIALIZED
  ════════════════════════════════════════
  Step 1 Bootstrap:  [PASS/FAIL]
  Step 2 Validate:   [PASS/FAIL]
  Step 3 Plan:       [PASS/FAIL]
  Step 4 Governance: [PASS/FAIL]
  ────────────────────────────────────────
  Mode: [BUILD/STABILIZE]
  Pending: [N] items to install
  Plan: Control_Plane/generated/plan.json
  ════════════════════════════════════════
```

---

## /plan Procedure

When user says `/plan`:
```
READ: Control_Plane/generated/plan.json
DISPLAY: List of items with status and action needed
```

---

## /validate Procedure

When user says `/validate`:
```bash
python3 Control_Plane/scripts/validate.py
```
Report PASS/FAIL with details.

---

## After /init

Once initialized, you are governed:

- **To create**: Use `Control_Plane/control_plane/prompts/install.md`
- **To update**: Use `Control_Plane/control_plane/prompts/update.md`
- **To verify**: Use `Control_Plane/control_plane/prompts/verify.md`
- **To remove**: Use `Control_Plane/control_plane/prompts/uninstall.md`

Always update registries when modifying artifacts.

---

## Quick Reference

| File | Purpose |
|------|---------|
| `Control_Plane/scripts/init.py` | Run all 3 layers at once |
| `Control_Plane/init/init.md` | Full boot documentation |
| `Control_Plane/CLAUDE.md` | Behavioral rules |
| `Control_Plane/generated/plan.json` | Current work plan |
| `Control_Plane/registries/*.csv` | Source of truth |
