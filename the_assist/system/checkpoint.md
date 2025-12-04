# The Assist - Runtime Checkpoint System

This file defines the runtime snapshoting system, which creates a dated state record each time the system boots successfully.

---

## Functionality

1. When a boot succeeds (from boot.md):
   - Create a datestamped json file under /state/checkpoints/
        Example: /state/checkpoints/2025-12-04T07:10:50UT.json
   - Include full repository context: verified directories, files, timestamps, etc.
   - Update /state/version_log.json with a new checkpoint entry.

2. If boot fails, mark checkpoint as failed with error reason.

## Structure
/the_assist/system/checkpoint.md -- this file
/state/checkpoints/                -- auto-generated files (JSON)
/state/version_log.json                 -- appends checkpoint status

## Sample checkpoint entry

```json
{
  "date": "2025-12-04T07:10:50UTC",
  "status": "verified",
  "verified_directories": [
    "the_assist/",
    "the_assist/system/"
  ],
  "verified_files": [
    "the_assist/system/init.md",
    "the_assist/system/state_check.md",
    "state/preflight_log.json"
  ],
  "next_state": "ready"
}
```

## Note
If any checkpoint is missing, boot mark integrity on next start.