"""
File Memory Bus (MOD-MEM-001)

Simple file-based memory storage implementation.
Stores data as JSON files in a directory structure.

Usage:
    from memory_bus_file import FileMemoryBus

    bus = FileMemoryBus("/path/to/storage")
    bus.set("user:123", {"name": "Alice"})
    data = bus.get("user:123")
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .interfaces import MemoryBusInterface, MemoryEntry


class FileMemoryBus(MemoryBusInterface):
    """
    File-based memory bus implementation.

    Stores each key as a JSON file. Keys with colons (e.g., "user:123")
    are converted to directory paths (e.g., "user/123.json").
    """

    def __init__(self, base_path: str | Path):
        """
        Initialize file memory bus.

        Args:
            base_path: Directory to store memory files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self.base_path / "_metadata.json"

    def _key_to_path(self, key: str) -> Path:
        """Convert a key to a file path."""
        # Replace colons with directory separators
        parts = key.replace(":", "/").split("/")
        # Last part is the filename
        filename = parts[-1] + ".json"
        # Build path
        if len(parts) > 1:
            dir_path = self.base_path / "/".join(parts[:-1])
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path / filename
        return self.base_path / filename

    def _read_entry(self, path: Path) -> Optional[dict]:
        """Read entry from file."""
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Check TTL
            if data.get("ttl") and data.get("created_at"):
                created = datetime.fromisoformat(data["created_at"])
                elapsed = (datetime.now(timezone.utc) - created).total_seconds()
                if elapsed > data["ttl"]:
                    # Expired - delete and return None
                    path.unlink()
                    return None
            return data
        except (json.JSONDecodeError, OSError):
            return None

    def _write_entry(self, path: Path, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Write entry to file."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            data = {
                "key": key,
                "value": value,
                "created_at": now,
                "updated_at": now,
                "ttl": ttl,
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except OSError:
            return False

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        path = self._key_to_path(key)
        entry = self._read_entry(path)
        if entry:
            return entry.get("value")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value."""
        path = self._key_to_path(key)
        return self._write_entry(path, key, value, ttl)

    def delete(self, key: str) -> bool:
        """Delete a key."""
        path = self._key_to_path(key)
        if path.is_file():
            try:
                path.unlink()
                return True
            except OSError:
                return False
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        path = self._key_to_path(key)
        entry = self._read_entry(path)
        return entry is not None

    def keys(self, pattern: str = "*") -> list[str]:
        """List keys matching pattern."""
        import fnmatch

        all_keys = []
        for path in self.base_path.rglob("*.json"):
            if path.name.startswith("_"):
                continue
            # Convert path back to key
            rel_path = path.relative_to(self.base_path)
            key = str(rel_path.with_suffix("")).replace("/", ":")
            all_keys.append(key)

        if pattern == "*":
            return sorted(all_keys)
        return sorted(k for k in all_keys if fnmatch.fnmatch(k, pattern))

    def clear(self) -> int:
        """Clear all entries."""
        count = 0
        for path in self.base_path.rglob("*.json"):
            if path.name.startswith("_"):
                continue
            try:
                path.unlink()
                count += 1
            except OSError:
                pass
        return count

    def get_entry(self, key: str) -> Optional[MemoryEntry]:
        """Get full entry with metadata."""
        path = self._key_to_path(key)
        data = self._read_entry(path)
        if not data:
            return None
        return MemoryEntry(
            key=data.get("key", key),
            value=data.get("value"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            ttl=data.get("ttl"),
            tags=data.get("tags"),
        )

    def stats(self) -> dict:
        """Return storage statistics."""
        total_files = 0
        total_bytes = 0
        for path in self.base_path.rglob("*.json"):
            if path.name.startswith("_"):
                continue
            total_files += 1
            total_bytes += path.stat().st_size
        return {
            "type": "file",
            "base_path": str(self.base_path),
            "total_entries": total_files,
            "total_bytes": total_bytes,
        }


# Factory function for module loading
def create_memory_bus(config: dict) -> FileMemoryBus:
    """Create a FileMemoryBus instance from config."""
    base_path = config.get("base_path", "memory/data")
    return FileMemoryBus(base_path)
