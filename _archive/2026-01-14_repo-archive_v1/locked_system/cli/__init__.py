"""CLI module for locked_system.

This module contains application-specific code for running locked_system
as a standalone CLI tool. The core library functionality is in the parent
package.

Usage:
    python -m locked_system.cli.main
"""
from locked_system.cli.session_logger import SessionLogger

__all__ = ["SessionLogger"]
