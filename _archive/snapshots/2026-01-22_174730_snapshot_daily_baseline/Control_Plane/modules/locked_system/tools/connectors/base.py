"""Base Connector - Abstract interface for tool drivers."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class Connector(ABC):
    """
    Abstract base class for tool connectors (drivers).

    Connectors handle the actual execution of tool operations.
    They are invoked only by ToolRuntime after policy approval.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Connector name (matches ToolSpec.connector)."""
        pass

    @abstractmethod
    def execute(self, operation: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool operation.

        Args:
            operation: The operation to perform (e.g., "read_file", "write_file")
            args: Arguments for the operation

        Returns:
            Result dictionary with operation-specific data

        Raises:
            ConnectorError: If operation fails
        """
        pass

    @abstractmethod
    def validate_args(self, operation: str, args: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate arguments for an operation.

        Returns (valid, error_message).
        """
        pass


class ConnectorError(Exception):
    """Error from connector execution."""

    def __init__(self, message: str, operation: str = None, recoverable: bool = False):
        super().__init__(message)
        self.operation = operation
        self.recoverable = recoverable
