# Repo OS — CI Guardrails (v1)

Purpose:
Automated enforcement of Repo OS rules.

Installs GitHub Actions workflow enforcing:
- prompts/index.csv existence
- prompt filename format
- clean-init requires _archive
- v1 prompt immutability

Failure of any rule fails the PR.
