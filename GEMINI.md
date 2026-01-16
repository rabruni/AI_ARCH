# GEMINI.md

This file provides guidance for Google Gemini when working with code in this repository.

---

## On Startup: Boot the Control Plane

**Run this immediately when starting a session:**

```bash
python3 Control_Plane/scripts/init.py
```

Expected output:
```
LAYER 1: BOOTSTRAP     [PASS]
LAYER 2: VALIDATE      [PASS]
LAYER 3: INIT          [PASS]
✓ Ready to receive commands.
```

Then read: `Control_Plane/CONTROL_PLANE_SPEC.md`

---

## Key Concepts

- **Registry is source of truth:** `Control_Plane/registries/control_plane_registry.csv`
- **Use NAMES for lookups, not IDs** (P003)
- **Four verbs:** install, update, verify, uninstall

---

## Commands

```bash
# List everything
python3 Control_Plane/scripts/registry.py list control_plane

# Show item by name
python3 Control_Plane/scripts/registry.py show "Definition of Done"

# Modify item
python3 Control_Plane/scripts/registry.py modify "Local Dev Harness" selected=yes

# Check dependencies
python3 Control_Plane/scripts/link.py check
```

---

## Critical Rules

| Rule | Description |
|------|-------------|
| P000 | Always run init.py first |
| P001 | Registry is source of truth |
| P002 | Validate before commit |
| P003 | Names are primary, IDs are reference |

---

## Commit Suffix

```
Co-Authored-By: Gemini <noreply@google.com>
```
