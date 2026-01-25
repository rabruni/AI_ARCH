# Prompt-Cache Status

Living status board for active prompt threads.

## System Status

| Component | Status |
|-----------|--------|
| Orchestrator | Claude (active) |
| Auto Loop | v4.0 RUNNING (PID 8611) |
| Boot System | boot.py v1.0 |
| Mode | IDLE |

## Agent Boot Command

All agents use the unified boot system:
```bash
python3 boot.py --agent <Name> --interactive
```

## Completed Infrastructure Work

- [x] boot.py - Unified agent boot system
- [x] auto_loop.py v4.0 - Uses boot.py for prompts
- [x] AGENTS.md - Points to boot.py
- [x] CLAUDE.md / CODEX.md / GEMINI.md - Updated
- [x] Codex Adherence Test - P-20260122-CODEX-ADHERENCE-TEST (passed)
- [x] Gemini Adherence Test - P-20260122-GEMINI-ADHERENCE-TEST (passed)
- [x] Claude Adherence Test - P-20260122-CLAUDE-ADHERENCE-TEST (passed)

## Agent Pull (post-init)

No pending tasks.

---

## How to Create a Task

1. Write prompt file: `/_Prompt-Cache_/<Agent>_<Timestamp>_<Name>.md`
2. Add entry to `INDEX.md` with status=`sent`
3. Update this file with task reference
4. auto_loop.py will dispatch automatically
