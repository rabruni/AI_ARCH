# Selection Report

## registries/components_registry.csv
- (none selected)

## registries/frameworks_registry.csv
- **FMWK-900** Repo OS Module (P0) → /modules/repo_os/README.md → child:/modules/repo_os/registries/repo_os_registry.csv

## registries/prompts_registry.csv
- **PRMPT-001** Control Plane Install (P0) → /control_plane/prompts/install.md
- **PRMPT-002** Control Plane Update (P0) → /control_plane/prompts/update.md
- **PRMPT-003** Control Plane Verify (P0) → /control_plane/prompts/verify.md
- **PRMPT-004** Control Plane Uninstall (P1) → /control_plane/prompts/uninstall.md

## modules/repo_os/registries/repo_os_registry.csv
- **ROS-M001** Repo OS Prompts () →  → child:/modules/repo_os/registries/prompts_registry.csv
- **ROS-M012** Repo OS Templates () →  → child:/modules/repo_os/registries/templates_registry.csv
- **ROS-M030** Init System () → /init/init.md → child:/init/init_registry.csv
- **ROS-M020** Runbooks Library () → /runbooks → child:/modules/repo_os/registries/runbooks_registry.csv
- **ROS-M010** Repo OS Scripts () →  → child:/modules/repo_os/registries/scripts_registry.csv
- **ROS-M013** Repo OS Docs () →  → child:/modules/repo_os/registries/docs_registry.csv
- **ROS-M014** Repo OS Profiles () →  → child:/modules/repo_os/registries/profiles_registry.csv
- **ROS-M002** Repo OS Created Items () →  → child:/modules/repo_os/registries/repo_os_created_items_registry.csv
- **ROS-M011** Repo OS Workflows () →  → child:/modules/repo_os/registries/workflows_registry.csv

## modules/repo_os/registries/prompts_registry.csv
- **ROS-P007** 07 Missing Items Tracker (P0) → /modules/repo_os/prompts/v1/07_missing_items_tracker.md
- **ROS-P001** 01 Archive Clean Init Meta Prompt (P0) → /modules/repo_os/prompts/v1/01_archive_clean_init_meta_prompt.md
- **ROS-P002** 02 Prompt Governance Model (P0) → /modules/repo_os/prompts/v1/02_prompt_governance_model.md
- **ROS-P004** 04 Ci Guardrails Prompt (P0) → /modules/repo_os/prompts/v1/04_ci_guardrails_prompt.md
- **ROS-P005** 05 Local Hooks Prompt (P0) → /modules/repo_os/prompts/v1/05_local_hooks_prompt.md
- **ROS-P003** 03 Claude Reliability Anchor (P0) → /modules/repo_os/prompts/v1/03_claude_reliability_anchor.md
- **ROS-P006** 06 Prompt Tracking Csv (P0) → /modules/repo_os/prompts/v1/06_prompt_tracking_csv.md

## modules/repo_os/registries/templates_registry.csv
- **ROS-T001** ADR Template () → /templates/adr/0000-template.md
- **ROS-T002** PR Template () → /templates/pr/PULL_REQUEST_TEMPLATE.md

## init/init_registry.csv
- **INIT-005** CLAUDE.md Schema (P1) → /init/CLAUDE_md_schema.json
- **INIT-006** Coverage Report (P2) → /init/init_instruction_coverage_report.md
- **INIT-002** State Initialization (P0) → /init/state_initialization_procedure.md
- **INIT-003** Governance Mode (P0) → /init/governance_mode_specification.md
- **INIT-007** Coverage JSON (P2) → /init/init_command_instruction_coverage.json
- **INIT-004** Verb Prompts Loader (P0) → /init/actions_loader_spec.md
- **INIT-001** Init Entry Point (P0) → /init/init.md

## modules/repo_os/registries/runbooks_registry.csv
- **ROS-RB001** Runbooks Library () → /runbooks

## modules/repo_os/registries/scripts_registry.csv
- **ROS-S001** Registry Validator () → /scripts/validate_registry.py
- **ROS-S002** Selection Planner () → /scripts/apply_selection.py

## modules/repo_os/registries/docs_registry.csv
- **ROS-D010** Control Plane Contract () → /control_plane/CONTROL_PLANE_CONTRACT.md
- **ROS-D001** Repo Root README () → /README.md
- **ROS-D020** Repo OS Module README () → /modules/repo_os/README.md
- **ROS-D002** Repo Root HOWTO () → /HOWTO_USE.md

## modules/repo_os/registries/profiles_registry.csv
- **ROS-PROF001** Personal Minimal () → /modules/repo_os/profiles/personal_minimal.json

## modules/repo_os/registries/repo_os_created_items_registry.csv
- **ROS-006** Prompt tracking CSV (starter) () → /generated/prompts_index.csv
- **ROS-007** Missing items tracker CSV () → /generated/repo_os_missing_items.csv
- **ROS-001** Archive + Clean Init meta-prompt (idempotent) () → /modules/repo_os/prompts/v1/01_archive_clean_init_meta_prompt.md
- **ROS-005** Local hooks concept () → /scripts/install-hooks.sh
- **ROS-004** CI guardrails concept () → /.github/workflows/repo_guardrails.yml
- **ROS-003** Claude reliability anchor concept (CLAUDE.md) () → /CLAUDE.md
- **ROS-002** Prompt governance model (P000/P001 + index.csv concept) () → 

## modules/repo_os/registries/workflows_registry.csv
- **ROS-W001** Repo OS Validation Workflow () → /.github/workflows/repo_os_validation.yml
