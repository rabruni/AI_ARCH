# Design Framework Module Standard

## Purpose
This standard defines the structural invariants for the Design Framework module, ensuring it remains a lightweight, declarative, and deterministic system for anchoring agent development.

## Structural Invariants
1.  **Declarative Assets:** All components (templates, scripts) must be declarative. No hidden behavior.
2.  **Registry-Driven:** The module and its assets are registered in `control_plane_registry.csv` and its own child registry.
3.  **Deterministic Application:** The `apply_spec_pack.py` script must be deterministic, copying files predictably.

## Prohibited
1.  **Complex Logic:** The apply script must not contain complex logic; it is for file copying only.
2.  **External Dependencies:** The script must use only the Python standard library.
3.  **Novel Frameworks:** Templates must be minimal and not introduce new, complex methodologies.
