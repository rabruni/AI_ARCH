# The Assist - System Pre-Flight Check

This file performs a system diagnostic to verify the integrity, access, and consistency of all critical directories before initializing The Assist runtime.

---

1# Verification Steps 

1. Verify that the following directories exist:
  - /the_assist/
    - /the_assist/system/
    - /the_assist/knowledge/
    - /the_assist/system/init.md
    - /the_assist/system/knowledge.md
    - /the_assist/system/state_check.md

2. Verify access to GitHub API via valid Pat and SSH.
3. Check existence of /state/ and /actions/ directories.
4. Verify state files:
  - agent_context.md
  - version_log.json
5. Check for governance safe mode and action logging.

6. If any critical check fails, return error state and prevent startup.

---

## Output

The results of this check should be logged in /state/preflight_log.json with full details of success or failure.

This check is to be run as a required step before any execution loop.