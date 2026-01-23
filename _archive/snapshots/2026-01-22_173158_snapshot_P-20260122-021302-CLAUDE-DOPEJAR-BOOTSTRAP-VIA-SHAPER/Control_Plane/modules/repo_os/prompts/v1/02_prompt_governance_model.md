# Repo OS — Prompt Governance Model (v1)

Purpose:
Establish prompts as first-class, governed artifacts.

Rules:
- All prompts are versioned (P###_name_vN.md)
- v1 prompts are immutable
- prompts/index.csv is the source of truth
- New intent = new prompt or new version

Required Artifacts:
- prompts/index.csv
- P000_repo_prompting_rules_v1.md
- P001_archive_and_clean_init_v1.md

Validation:
- CI fails if index.csv missing
- CI fails if v1 prompt modified
