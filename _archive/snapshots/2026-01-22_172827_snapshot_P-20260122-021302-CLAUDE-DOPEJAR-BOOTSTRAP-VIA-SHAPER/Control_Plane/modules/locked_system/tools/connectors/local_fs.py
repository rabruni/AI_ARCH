"""Local Filesystem Connector - Sandboxed file operations.

Provides file read/write/list operations within allowed directories.
Enforces Developer Workspace sandboxing.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import fnmatch

from locked_system.tools.connectors.base import Connector, ConnectorError


class LocalFSConnector(Connector):
    """
    Local filesystem connector with sandboxing.

    Security features:
    - Allowlisted root directories only
    - Blocklisted personal data paths
    - Path escape prevention (.., symlinks)
    - No absolute paths outside roots
    """

    # Default workspace roots
    DEFAULT_ALLOWED_ROOTS = [
        "./",  # Current directory
        "./docs/",
        "./core/",
        "./agents/",
        "./capabilities/",
    ]

    # Personal data blocklist (never accessible)
    PERSONAL_DATA_BLOCKLIST = [
        "~/",
        "/Users/*/Documents/",
        "/Users/*/Desktop/",
        "/Users/*/Downloads/",
        "/home/*/Documents/",
        "/home/*/Desktop/",
        "/home/*/Downloads/",
        "**/.ssh/",
        "**/credentials*",
        "**/.env",
        "**/secrets*",
        "**/passwords*",
        "**/.aws/",
        "**/.gcloud/",
    ]

    def __init__(
        self,
        allowed_roots: List[str] = None,
        blocklist: List[str] = None,
        base_path: str = None,
    ):
        """
        Initialize the connector.

        Args:
            allowed_roots: List of allowed root directories
            blocklist: Additional paths to block
            base_path: Base path to resolve relative roots against
        """
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._allowed_roots = self._resolve_roots(allowed_roots or self.DEFAULT_ALLOWED_ROOTS)
        self._blocklist = (blocklist or []) + self.PERSONAL_DATA_BLOCKLIST

    @property
    def name(self) -> str:
        return "local_fs"

    def _resolve_roots(self, roots: List[str]) -> List[Path]:
        """Resolve root paths to absolute paths."""
        resolved = []
        for root in roots:
            if root.startswith("./"):
                resolved.append((self._base_path / root[2:]).resolve())
            else:
                resolved.append(Path(root).resolve())
        return resolved

    def _validate_path(self, path_str: str) -> tuple[bool, str, Optional[Path]]:
        """
        Validate a path against security constraints.

        Returns (valid, error_message, resolved_path).
        """
        try:
            # Resolve the path
            path = Path(path_str)
            if not path.is_absolute():
                path = (self._base_path / path).resolve()
            else:
                path = path.resolve()

            # Check for path traversal
            path_str_resolved = str(path)
            if ".." in path_str:
                return False, "Path traversal (..) not allowed", None

            # Check against blocklist
            for blocked in self._blocklist:
                if fnmatch.fnmatch(path_str_resolved, blocked):
                    return False, f"Path matches blocklist: {blocked}", None
                if fnmatch.fnmatch(path_str, blocked):
                    return False, f"Path matches blocklist: {blocked}", None

            # Check symlinks point to allowed locations
            if path.is_symlink():
                real_path = path.resolve()
                if not self._is_under_allowed_root(real_path):
                    return False, "Symlink target outside allowed roots", None

            # Check if under allowed root
            if not self._is_under_allowed_root(path):
                return False, f"Path outside allowed roots: {path}", None

            return True, "", path

        except Exception as e:
            return False, f"Path validation error: {str(e)}", None

    def _is_under_allowed_root(self, path: Path) -> bool:
        """Check if path is under any allowed root."""
        for root in self._allowed_roots:
            try:
                path.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def validate_args(self, operation: str, args: Dict[str, Any]) -> tuple[bool, str]:
        """Validate arguments for an operation."""
        if operation in ("read_file", "write_file", "file_info"):
            if "path" not in args:
                return False, "Missing required 'path' argument"
            valid, error, _ = self._validate_path(args["path"])
            return valid, error

        if operation == "list_directory":
            if "path" not in args:
                return False, "Missing required 'path' argument"
            valid, error, _ = self._validate_path(args["path"])
            return valid, error

        return False, f"Unknown operation: {operation}"

    def execute(self, operation: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a filesystem operation."""
        # Validate first
        valid, error = self.validate_args(operation, args)
        if not valid:
            raise ConnectorError(error, operation=operation)

        if operation == "read_file":
            return self._read_file(args)
        elif operation == "write_file":
            return self._write_file(args)
        elif operation == "list_directory":
            return self._list_directory(args)
        elif operation == "file_info":
            return self._file_info(args)
        else:
            raise ConnectorError(f"Unknown operation: {operation}", operation=operation)

    def _read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents."""
        _, _, path = self._validate_path(args["path"])

        if not path.exists():
            raise ConnectorError(f"File not found: {path}", operation="read_file")

        if not path.is_file():
            raise ConnectorError(f"Not a file: {path}", operation="read_file")

        try:
            content = path.read_text(encoding="utf-8")
            return {
                "content": content,
                "size": len(content),
                "path": str(path),
            }
        except UnicodeDecodeError:
            # Try binary
            content = path.read_bytes()
            return {
                "content": f"<binary file, {len(content)} bytes>",
                "size": len(content),
                "path": str(path),
                "is_binary": True,
            }
        except Exception as e:
            raise ConnectorError(f"Read error: {str(e)}", operation="read_file")

    def _write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Write file contents."""
        _, _, path = self._validate_path(args["path"])
        content = args.get("content", "")
        mode = args.get("mode", "overwrite")

        try:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            if mode == "append":
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
            else:
                path.write_text(content, encoding="utf-8")

            return {
                "bytes_written": len(content.encode("utf-8")),
                "path": str(path),
            }
        except Exception as e:
            raise ConnectorError(f"Write error: {str(e)}", operation="write_file")

    def _list_directory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents."""
        _, _, path = self._validate_path(args["path"])
        pattern = args.get("pattern", "*")

        if not path.exists():
            raise ConnectorError(f"Directory not found: {path}", operation="list_directory")

        if not path.is_dir():
            raise ConnectorError(f"Not a directory: {path}", operation="list_directory")

        try:
            entries = []
            for entry in path.glob(pattern):
                # Validate each entry is still in allowed space
                if self._is_under_allowed_root(entry):
                    entries.append(str(entry.relative_to(path)))

            return {
                "entries": sorted(entries),
                "count": len(entries),
                "path": str(path),
            }
        except Exception as e:
            raise ConnectorError(f"List error: {str(e)}", operation="list_directory")

    def _file_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get file metadata."""
        _, _, path = self._validate_path(args["path"])

        exists = path.exists()
        result = {
            "exists": exists,
            "path": str(path),
        }

        if exists:
            stat = path.stat()
            result.update({
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        return result

    def add_allowed_root(self, root: str) -> None:
        """Add an allowed root directory."""
        if root.startswith("./"):
            resolved = (self._base_path / root[2:]).resolve()
        else:
            resolved = Path(root).resolve()
        self._allowed_roots.append(resolved)

    def add_to_blocklist(self, pattern: str) -> None:
        """Add a pattern to the blocklist."""
        self._blocklist.append(pattern)
