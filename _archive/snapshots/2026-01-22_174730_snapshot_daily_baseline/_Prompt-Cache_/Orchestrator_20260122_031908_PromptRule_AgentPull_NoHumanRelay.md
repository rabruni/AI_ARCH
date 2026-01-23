---
prompt_id: P-20260122-031908-PROMPTRULE-AGENT-PULL-NO-HUMAN-RELAY
type: prompt
target_agent: Human
goal: Update workflow: agents pull and execute prompts from Prompt-Cache; human does not relay/copy-paste between agents
status: sent
relates_to: P-20260122-030812-PROMPTRULE-NO-AUTO-READBACK
created_local: 20260122_031908
---

Rule update (effective immediately):
- All actions and IO flow through the prompt system (`/_Prompt-Cache_/`), not through human copy/paste between agent chats.
- Agents are responsible for pulling their next assigned prompt from `/_Prompt-Cache_/STATUS.md` + `/_Prompt-Cache_/INDEX.md` and executing it.
- Human interaction is limited to approvals by referencing prompt/feedback artifacts (no manual file inspection; no relaying prompt bodies).
