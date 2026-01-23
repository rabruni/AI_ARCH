"""Tool Registry - ToolSpec loader and registry.

Manages tool specifications, validates schemas, and provides lookup.
"""

from typing import Dict, Optional, List
from pathlib import Path
import yaml
import os

from locked_system.tools.models import ToolSpec, SideEffect


class ToolRegistry:
    """
    Registry for tool specifications.

    Loads ToolSpecs from YAML files and provides lookup/validation.
    """

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}
        self._initialized = False

    def register(self, spec: ToolSpec) -> None:
        """Register a tool specification."""
        if spec.id in self._tools:
            existing = self._tools[spec.id]
            # Allow version upgrade, reject duplicates
            if existing.version == spec.version:
                raise ValueError(f"Tool {spec.id} v{spec.version} already registered")
        self._tools[spec.id] = spec

    def get(self, tool_id: str) -> Optional[ToolSpec]:
        """Get a tool specification by ID."""
        return self._tools.get(tool_id)

    def exists(self, tool_id: str) -> bool:
        """Check if a tool is registered."""
        return tool_id in self._tools

    def list_all(self) -> List[ToolSpec]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_by_connector(self, connector: str) -> List[ToolSpec]:
        """List tools using a specific connector."""
        return [t for t in self._tools.values() if t.connector == connector]

    def list_by_side_effect(self, side_effect: SideEffect) -> List[ToolSpec]:
        """List tools with a specific side effect type."""
        return [t for t in self._tools.values() if t.side_effect == side_effect]

    def load_from_yaml(self, yaml_path: str) -> None:
        """
        Load tool specifications from a YAML file.

        Expected format:
        ```yaml
        tools:
          - id: "fs.read_file"
            version: "1.0"
            side_effect: "read"
            ...
        ```
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            return

        tools = data.get('tools', [])
        for tool_data in tools:
            spec = ToolSpec.from_dict(tool_data)
            self.register(spec)

    def load_from_directory(self, dir_path: str) -> None:
        """Load all YAML tool specs from a directory."""
        path = Path(dir_path)
        if not path.exists():
            return

        for yaml_file in path.glob("*.yaml"):
            self.load_from_yaml(str(yaml_file))

        for yaml_file in path.glob("*.yml"):
            self.load_from_yaml(str(yaml_file))

    def initialize_defaults(self) -> None:
        """Register built-in default tools."""
        if self._initialized:
            return

        # fs.read_file - Read file contents
        self.register(ToolSpec(
            id="fs.read_file",
            version="1.0",
            side_effect=SideEffect.READ,
            required_scopes=["fs.read"],
            connector="local_fs",
            description="Read contents of a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "size": {"type": "integer"},
                }
            }
        ))

        # fs.write_file - Write file contents (requires approval)
        self.register(ToolSpec(
            id="fs.write_file",
            version="1.0",
            side_effect=SideEffect.WRITE,
            required_scopes=["fs.write"],
            connector="local_fs",
            description="Write contents to a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"},
                    "mode": {"type": "string", "enum": ["overwrite", "append"], "default": "overwrite"}
                },
                "required": ["path", "content"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "bytes_written": {"type": "integer"},
                }
            }
        ))

        # fs.list_directory - List directory contents
        self.register(ToolSpec(
            id="fs.list_directory",
            version="1.0",
            side_effect=SideEffect.READ,
            required_scopes=["fs.read"],
            connector="local_fs",
            description="List contents of a directory",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                    "pattern": {"type": "string", "description": "Optional glob pattern"}
                },
                "required": ["path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "entries": {"type": "array", "items": {"type": "string"}},
                }
            }
        ))

        # fs.file_info - Get file metadata
        self.register(ToolSpec(
            id="fs.file_info",
            version="1.0",
            side_effect=SideEffect.READ,
            required_scopes=["fs.read"],
            connector="local_fs",
            description="Get file metadata",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "exists": {"type": "boolean"},
                    "is_file": {"type": "boolean"},
                    "is_dir": {"type": "boolean"},
                    "size": {"type": "integer"},
                    "modified": {"type": "string"},
                }
            }
        ))

        self._initialized = True

    def validate_request(self, tool_id: str, args: dict) -> tuple[bool, str]:
        """
        Validate a tool invocation request.

        Returns (valid, error_message).
        """
        spec = self.get(tool_id)
        if not spec:
            return False, f"Unknown tool: {tool_id}"

        # Basic schema validation (check required fields)
        schema = spec.input_schema
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for field in required:
            if field not in args:
                return False, f"Missing required field: {field}"

        # Type validation (basic)
        for key, value in args.items():
            if key in properties:
                prop_schema = properties[key]
                expected_type = prop_schema.get("type")

                if expected_type == "string" and not isinstance(value, str):
                    return False, f"Field {key} must be string"
                elif expected_type == "integer" and not isinstance(value, int):
                    return False, f"Field {key} must be integer"
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False, f"Field {key} must be boolean"

        return True, ""
