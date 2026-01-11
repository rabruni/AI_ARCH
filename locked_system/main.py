#!/usr/bin/env python3
"""Locked System - Entry Point.

Usage:
    python -m locked_system.main [--config path/to/config.yaml]

Or import and use directly:
    from locked_system import LockedLoop, Config
    loop = LockedLoop(Config())
    result = loop.process("Hello")

CLI functionality is in locked_system.cli.main
"""
from locked_system.cli.main import main, create_llm, run_interactive, run_single

if __name__ == "__main__":
    main()
