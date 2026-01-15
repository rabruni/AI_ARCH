# Control Plane Contract (Registry-Driven)

## Intent
The registry is the top-level control plane. Rows represent installable/activatable modules.

## Core Operations
- **Select**: set `selected=yes` (optionally within a `profile`).
- **Install/Update/Verify/Uninstall**: execute the corresponding prompt templates, passing the row as context.
- **Dependencies**: install dependencies first; verify in dependency order.

## Nested Control Planes
Modules may expose a `child_registry_path` that becomes a subordinate control plane.

## Extension to Application Architecture
Use `entity_type=architecture_module` for swappable components (memory bus, reasoning model, etc.).
Each architecture module should specify `params_schema_path`, `package_source`, and `provides_capabilities`.

## Required packs for Repo OS module
The Repo OS module registry (`/modules/repo_os/registries/repo_os_registry.csv`) MUST include these packs as selected=yes:
- Prompts
- Created Items
- Scripts
- Workflows
- Templates
- Docs
- Profiles
- Runbooks Library
- Init System

If any are missing, Repo OS is considered misconfigured.
