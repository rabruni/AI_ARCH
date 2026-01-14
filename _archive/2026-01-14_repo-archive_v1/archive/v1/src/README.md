# The Assist - System Manifest

This directory defines the core architecture and runtime structure for *The Assist* - the intelligent layer of the AI Arch project.

---

## Architecture Overview

/The Assist/
    System-level directory.
    Holds active components, runtime logic, and knowledge rules.

//the_assist/system/
    Here lives the system configuration, interpreter rules, and initialization logic.
    - *knowledge.md* : Command interpreter mappings and default context.
    - *.keep* : Placeholder to keep directory visible in Git.
    - *manifest.md* : System manifest and build-in

//the_assist/knowledge/
    Static and procedural documentation.

//the_assist/state/
    Runtime state, memory, and temporary files.
    Example:
    - agent_context.md: Stores the current cognitive context.
    - version_log.json: long-term version and history log

/actions/
    Contains GitHub Actions and other external operational scripts.

## Purpose
* This defines the intelligence and cognitive infrastructure of the AI Arch system.
* It serves as the bootstrap for all fairly operating agents.

## Structure
- **system**/ - Runtime and configuration files for The Assist.
- **knowledge**/ - Static and procedural documentation.
- **state**/ - Context and memory files.
*- *actions**/ - Automated scripts and Action definitions.

## Governance
Safe mode enabled:
and logged through /state/action_log.json
