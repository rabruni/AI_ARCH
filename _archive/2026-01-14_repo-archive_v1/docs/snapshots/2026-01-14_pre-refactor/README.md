# Pre-Refactor Snapshot: 2026-01-14

## What This Is

This snapshot captures the AI_ARCH repository state before the framework refactor on 2026-01-14. It preserves the original directory structure and file organization for reference and rollback purposes.

## Git Tag

```
legacy/v2026.01.14-pre-refactor
```

## How to Restore

To restore the repository to this exact state:

```bash
# Option 1: Checkout the tag (detached HEAD)
git checkout legacy/v2026.01.14-pre-refactor

# Option 2: Create a branch from the tag
git checkout -b restore/legacy-2026-01-14 legacy/v2026.01.14-pre-refactor

# Option 3: View files without switching
git show legacy/v2026.01.14-pre-refactor:path/to/file
```

## Contents of This Snapshot

- `README.md` - This file
- `TREE.txt` - Complete file listing (393 files)
- `NOTES.md` - Inventory and pain points that motivated the refactor

## Repository State at Snapshot

- **Commit**: ae6b7cd
- **Message**: doc: Critical recovery after context compaction incident
- **Date**: 2026-01-14
- **Branch**: main

## Why This Snapshot Exists

The AI_ARCH repository evolved organically with multiple parallel efforts:
- HRM (Hierarchical Reasoning Model) implementation
- Locked System architecture
- Various documentation and spec files

This created a structure that was difficult to navigate and maintain. The refactor aims to establish a clearer framework while preserving all functionality.
