---
prompt_id: P-20260122-004732-PROMPTCACHE-SMOKETEST
type: prompt
target_agent: Human
goal: Verify agent can use Prompt-Cache protocol
status: draft
relates_to:
created_local: 20260122_004732
---

PROMPT ID: P-20260122-004732-PROMPTCACHE-SMOKETEST
TARGET AGENT: <Claude|Gemini|Codex>
ROLE: <Builder|Validator|Specialist>
SINGLE RESPONSIBILITY: Prove you can use `/_Prompt-Cache_/` as the handoff bus by producing an indexed response artifact.

AUTHORITATIVE PROTOCOL
- `docs/OPERATING_MODEL.md`
- `/_Prompt-Cache_/README.md`
- `/_Prompt-Cache_/INDEX.md`

TASK
1) Create ONE new response file in `/_Prompt-Cache_/` named:
   `<Target_Agent>_<YYYYMMDD_HHMMSS>_PromptCache_SmokeTest_Response.md`
2) The response file MUST start with this YAML header schema:
```yaml
---
prompt_id: F-<YYYYMMDD-HHMMSS>-PROMPTCACHE-SMOKETEST-RESPONSE
type: feedback
target_agent: <Claude|Gemini|Codex|Human>
goal: Prompt-Cache smoke test response
status: sent
relates_to: P-20260122-004732-PROMPTCACHE-SMOKETEST
created_local: <YYYYMMDD_HHMMSS>
---
```
3) After the YAML header, include:
- `ACK: read protocol`
- `ACK: created response file` (with the exact filename)
- `ACK: updated INDEX.md` (with the exact row you appended)
- `NOTES:` one line describing any friction you hit
4) Append ONE row to `/_Prompt-Cache_/INDEX.md` with the new file.

IF YOU DO NOT HAVE FILESYSTEM ACCESS
Return two things in-chat instead (so the human can apply them manually):
1) Full contents for the response file (including YAML header)
2) The exact single `INDEX.md` row to append

DELIVERABLE (STRICT)
Return ONLY:
1) The path to the response file you created (or “NO FS ACCESS”)
2) The exact `INDEX.md` row appended (or to append)

