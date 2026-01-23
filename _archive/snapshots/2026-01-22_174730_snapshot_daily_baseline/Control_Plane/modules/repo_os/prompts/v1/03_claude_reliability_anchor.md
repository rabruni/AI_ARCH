# Repo OS — Claude Reliability Anchor (v1)

Purpose:
Pin Claude behavior to repository rules across sessions.

Creates/repairs CLAUDE.md enforcing:
- Always read P000 first
- Never edit v1 prompts
- Always update prompts/index.csv
- Always run verify before final output
- Never delete /_archive

Outcome:
Claude behaves deterministically and safely.
