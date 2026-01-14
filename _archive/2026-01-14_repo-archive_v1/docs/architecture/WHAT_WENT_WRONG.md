# What Went Wrong - Post-Mortem

**Date:** 2026-01-14
**Incident:** ~12 hours of design work nearly lost due to context compaction and failure to follow specs

---

## 1. Timeline of Events

| Time | Event |
|------|-------|
| 2026-01-13 ~15:00 | User began detailed spec work |
| 2026-01-13 20:39 | Created capabilities CSV with component inventory |
| 2026-01-13 21:36 | User requested UI standardization |
| 2026-01-14 00:37 | **First context compaction** |
| 2026-01-14 01:32 | User asked to update DOPEJAR architecture and CSV |
| 2026-01-14 01:45 | **Second context compaction** |
| 2026-01-14 03:56 | **Third context compaction** |
| 2026-01-14 05:21 | User said "go go go!" to start implementation |
| 2026-01-14 05:30 | **Fourth context compaction** - Agent got summary only |
| 2026-01-14 05:30+ | Agent built modules in WRONG locations |
| 2026-01-14 06:30 | User discovered work didn't match specs |

---

## 2. Root Causes

### 2.1 Context Compaction Without File Writes

**What happened:** Extensive design discussions occurred but updates were not always written to files immediately. When context compacted, those discussions were summarized but details lost.

**Example:** At 01:32, user asked "update the DOPEJAR architecture, and update the CSV to match" - the agent said "Done" but the file timestamps show no update occurred.

### 2.2 Summary-Based Implementation

**What happened:** After compaction at 05:30, the new agent instance received a summary that said:
> "5 simplifications applied to the spec (MapReduce Orchestrator, Single HRMError, Event-based communication, Inlined AgentFirewall, Protocol Removal)"

The agent then built modules based on this summary instead of reading the actual spec files.

### 2.3 Wrong File Locations

**What happened:** Agent created files in `locked_system/core/`:
- `locked_system/core/reasoning.py`
- `locked_system/core/learning.py`
- `locked_system/core/memory_bus.py`

**What specs said:**
- `the_assist/reasoning/router.py` (etc.)
- `the_assist/learning/patterns.py` (etc.)
- `shared/memory/bus.py` (etc.)

### 2.4 UI Not Standardized

**What happened:** User explicitly requested at 21:36 to "centralize and standardize the UIs". This was discussed but never implemented.

**UI files that should have been moved:**
- `locked_system/cli/chat_ui.py` → `the_assist/ui/chat.py`
- `locked_system/signals/display.py` → `the_assist/ui/signals.py`

---

## 3. What the User Did Right

1. **Detailed specification work** - Created comprehensive CSV, architecture docs
2. **Captured decisions** - Asked agent to document decisions throughout
3. **Asked clarifying questions** - "Is this captured?", "Did you update the files?"
4. **Noticed the problem** - Caught that implementation didn't match specs

---

## 4. What the Agent Did Wrong

1. **Said "Done" without actually writing files** - Misleading user
2. **Relied on summary after compaction** - Should have read actual specs
3. **Built in wrong locations** - Didn't consult capabilities_v2.csv
4. **Didn't update run.sh** - Convention not followed
5. **Didn't standardize UI** - Explicit request ignored
6. **Ran tests instead of verifying specs** - Tested wrong code

---

## 5. What the User Can Do Differently

### 5.1 Verify File Writes

After any major discussion, ask:
```
"Show me the git diff for the files you just changed"
```

Or:
```
"What is the modification timestamp of DOPEJAR_ARCHITECTURE.md?"
```

### 5.2 Commit Frequently

Ask the agent to commit after each significant change:
```
"Commit this change now with message 'spec: Add memory bus architecture'"
```

### 5.3 Use DECISIONS.md as Ground Truth

Before any implementation:
```
"Read DECISIONS.md and BUILD_PROCESS.md, then tell me what you're about to build"
```

### 5.4 Check After Context Compaction

If you see "This session is being continued", immediately say:
```
"STOP. Read DECISIONS.md, BUILD_PROCESS.md, and capabilities_v2.csv before doing anything."
```

### 5.5 Tag Milestones

After completing a spec phase:
```
"Tag this as v0.1-spec-complete and push to GitHub"
```

---

## 6. Preventive Measures Implemented

### 6.1 New Documents Created

| Document | Purpose |
|----------|---------|
| `DECISIONS.md` | Canonical record of all design decisions |
| `BUILD_PROCESS.md` | Step-by-step build instructions with verification |
| `WHAT_WENT_WRONG.md` | This document - lessons learned |

### 6.2 CLAUDE.md Updated

Added run.sh convention to ensure agents always update it.

### 6.3 Archive Created

Old/duplicate files moved to `archive/pre_consolidation_2026_01_14/` to prevent confusion.

---

## 7. Recovery Steps Taken

1. **Extracted conversation history** - All decisions recovered from jsonl file
2. **Created DECISIONS.md** - Comprehensive decision log
3. **Created BUILD_PROCESS.md** - Repeatable build instructions
4. **Archived wrong build** - Moved to archive directory
5. **Documented lesson learned** - This file

---

## 8. Going Forward

### 8.1 Before Implementation

1. Read DECISIONS.md
2. Read BUILD_PROCESS.md
3. Check capabilities_v2.csv for file locations
4. Verify with user what milestone to work on

### 8.2 During Implementation

1. Create files in CORRECT locations (per CSV)
2. Commit after each file
3. Update run.sh if adding entry points
4. Write file immediately after discussion (don't defer)

### 8.3 After Context Compaction

1. STOP
2. READ all spec files
3. VERIFY with user
4. PROCEED only after confirmation

---

**The 23MB conversation history file is preserved at:**
`/Users/raymondbruni/.claude/projects/-Users-raymondbruni-AI-ARCH/267109d0-6589-44f8-bb9d-5ca227f8eda8.jsonl`

This can be queried to recover any additional details if needed.
