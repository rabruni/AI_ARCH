You are an AI agent working in this repository. Follow these instructions to generate a code-derived documentation set (no README/MD intent docs). Do not edit repository documentation unless explicitly asked. Use only the code to derive behavior and structure.

Goal
- Produce the following artifacts from code-only inspection:
  1) Code-Derived Design Doc (Behavioral Overview)
  2) Interface & Prompt Construction (Code-Derived)
  3) Example: Prompt Construction for a Normal Turn
  4) Directory & Module Structure (code-observed)
  5) Startup & Entry Paths

Constraints
- Ignore README.md and any other .md design/intent notes for the analysis. Only read code files.
- Document what the system does (behavioral reality), not what it intends to do.
- Use direct evidence from code: include fully-qualified file paths and key function/class names.
- Store outputs in a new or existing folder at repo root named: code_derived_docs/
- Each artifact should be a separate markdown file with a clear title.

How to Run (code inspection only)
1) List code structure:
   - ls -a locked_system
   - ls -a locked_system/{cli,fast_loop,slow_loop,sensing,memory,proposals}
2) Read the core modules (non-.md only):
   - locked_system/loop.py
   - locked_system/config.py
   - locked_system/main.py
   - locked_system/notes.py
   - locked_system/run.sh
   - locked_system/setup.py
3) Read CLI modules:
   - locked_system/cli/main.py
   - locked_system/cli/session_logger.py
4) Read slow loop modules:
   - locked_system/slow_loop/stance.py
   - locked_system/slow_loop/commitment.py
   - locked_system/slow_loop/gates.py
   - locked_system/slow_loop/bootstrap.py
5) Read fast loop modules:
   - locked_system/fast_loop/hrm.py
   - locked_system/fast_loop/executor.py
   - locked_system/fast_loop/continuous_eval.py
6) Read sensing modules:
   - locked_system/sensing/perception.py
   - locked_system/sensing/contrast.py
7) Read memory modules:
   - locked_system/memory/slow.py
   - locked_system/memory/fast.py
   - locked_system/memory/bridge.py
   - locked_system/memory/history.py
8) Read proposals:
   - locked_system/proposals/buffer.py
9) Read package __init__ modules for exports:
   - locked_system/__init__.py
   - locked_system/cli/__init__.py
   - locked_system/slow_loop/__init__.py
   - locked_system/fast_loop/__init__.py
   - locked_system/sensing/__init__.py
   - locked_system/memory/__init__.py
   - locked_system/proposals/__init__.py

Output Files (write to code_derived_docs/)
- code_derived_docs/behavioral_overview.md
- code_derived_docs/interface_prompt_construction.md
- code_derived_docs/example_prompt_construction.md
- code_derived_docs/directory_module_structure.md
- code_derived_docs/startup_entry_paths.md

Content Guidelines
- Each file should include:
  - Purpose
  - Inputs
  - Outputs
  - Key call paths or data flow (as applicable)
- For the example prompt construction, provide a concrete, annotated example of the system prompt and message list formation using the executor path (no README references).
- Keep language factual and tied to code evidence.

