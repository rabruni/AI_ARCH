---
prompt_id: P-20260122-005434-CLAUDE-PROMPTCACHE-SMOKETEST
type: prompt
target_agent: Claude
goal: Prompt-Cache smoke test (Claude can create + index response file)
status: draft
relates_to: P-20260122-004732-PROMPTCACHE-SMOKETEST
created_local: 20260122_005434
---

PROMPT ID: P-20260122-005434-CLAUDE-PROMPTCACHE-SMOKETEST
TARGET AGENT: Claude (Builder)
SINGLE RESPONSIBILITY: Prove you can use `/_Prompt-Cache_/` by creating and indexing a response artifact.

AUTHORITATIVE PROTOCOL (read)
- `docs/OPERATING_MODEL.md`
- `/_Prompt-Cache_/README.md`
- `/_Prompt-Cache_/INDEX.md`

TASK
1) Create ONE new file:
   `/_Prompt-Cache_/Claude_20260122_005434_PromptCache_SmokeTest_Response.md`
2) File MUST contain exactly this YAML header (fill nothing; use as-is) then a short body:
```yaml
---
prompt_id: F-20260122-005434-CLAUDE-PROMPTCACHE-SMOKETEST-RESPONSE
type: feedback
target_agent: Human
goal: Prompt-Cache smoke test response (Claude)
status: sent
relates_to: P-20260122-005434-CLAUDE-PROMPTCACHE-SMOKETEST
created_local: 20260122_005434
---
```
Body (4 lines max):
- `ACK: read protocol`
- `ACK: created response file`
- `ACK: updated INDEX.md`
- `NOTES: <one short friction or 'none'>`
3) Append ONE row to `/_Prompt-Cache_/INDEX.md` for the response file.

DELIVERABLE (STRICT)
Return ONLY:
1) `/_Prompt-Cache_/Claude_20260122_005434_PromptCache_SmokeTest_Response.md`
2) The exact index row you appended

