#!/usr/bin/env python3
"""
Snapshot - Create a Safe Backup of Repository State

Purpose: Creates a timestamped copy of the current repository state into `_archive/snapshots/`.
Usage: python3 scripts/snapshot.py [label]

This is a 'Panic Button' safety net. Run this before starting automated loops.
"""

import os
import sys
import shutil
import datetime
from pathlib import Path

# Config
IGNORE_DIRS = {
    '.git',
    'venv',
    '__pycache__',
    '.pytest_cache',
    'node_modules',
    '_archive',  # Crucial: do not recurse into archives
    '.DS_Store'
}

IGNORE_FILES = {
    '.DS_Store'
}

def create_snapshot(label=None):
    repo_root = Path.cwd()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    
    snapshot_name = f"{timestamp}_snapshot"
    if label:
        snapshot_name += f"_{label}"
        
    archive_dir = repo_root / "_archive" / "snapshots"
    dest_dir = archive_dir / snapshot_name

    print(f"Creating snapshot at: {dest_dir}")

    # Create destination
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Walk and copy
    file_count = 0
    dir_count = 0

    for root, dirs, files in os.walk(repo_root):
        # Filter directories in-place to prevent recursion
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        
        rel_path = Path(root).relative_to(repo_root)
        
        # Create corresponding dir in snapshot
        target_dir = dest_dir / rel_path
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            dir_count += 1

        for file in files:
            if file in IGNORE_FILES or file.startswith('.'):
                continue
                
            src_file = Path(root) / file
            dst_file = target_dir / file
            
            shutil.copy2(src_file, dst_file)
            file_count += 1

    # Write Manifest
    manifest_path = dest_dir / "SNAPSHOT_MANIFEST.txt"
    with open(manifest_path, "w") as f:
        f.write(f"Snapshot created: {timestamp}\n")
        f.write(f"Label: {label or 'manual'}\n")
        f.write(f"Source: {repo_root}\n")
        f.write(f"Files: {file_count}\n")
        f.write(f"Directories: {dir_count}\n")

    print(f"[OK] Snapshot complete. Files: {file_count}, Dirs: {dir_count}")
    return str(dest_dir)

if __name__ == "__main__":
    label_arg = sys.argv[1] if len(sys.argv) > 1 else None
    create_snapshot(label_arg)
