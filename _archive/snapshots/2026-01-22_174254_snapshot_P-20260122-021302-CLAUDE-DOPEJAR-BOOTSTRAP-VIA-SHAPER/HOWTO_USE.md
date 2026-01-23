# How to Use This Repository

## Bootstrap the Project

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rabruni/AI_ARCH.git
   cd AI_ARCH
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: `requirements.txt` will be created as the project develops)*

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

## Running Tests

```bash
# Run all tests (when available)
pytest tests/

# Run with coverage
pytest tests/ --cov=src
```

*Tests are not yet implemented. This will be updated as the project develops.*

## For New Contributors

### Operating Model (Roles + Layers)

This repo is run as a multi-agent system with strict separation between:
- **The team** (human + LLM roles coordinating work)
- **The core system** (Shaper + Control Plane)
- **Residents** (future/planned systems housed by the core system)

Source of truth: `docs/OPERATING_MODEL.md`.

### Directory Conventions

| Directory | Purpose |
|-----------|---------|
| `/src` | All source code |
| `/tests` | Test files mirroring `/src` structure |
| `/docs` | Design documents, specs, ADRs |
| `/prompts` | LLM prompts and templates |
| `/_Prompt-Cache_` | Generated prompts saved for reproducibility |
| `/scripts` | One-off utilities and helpers |
| `/config` | Configuration files |

### Workflow

1. Read `REPO_MANIFEST.json` to understand current project state
2. Check `/docs` for architectural decisions and design specs
3. Check `/prompts` for any LLM interaction patterns
4. Create feature branches from `main`
5. Write tests alongside code
6. Update documentation when changing behavior

### Decision Records

Design decisions are stored in `/docs/decisions/` as ADR (Architecture Decision Records) files.

### Prompts

LLM prompts and conversation templates are stored in `/prompts/` with version control for reproducibility.

### Prompt Cache

Operational prompt drafts generated during work are saved to `/_Prompt-Cache_/` to keep an audit trail for reviews and reuse.
Naming policy: `/_Prompt-Cache_/README.md`.

Note: `/_Prompt_Cache_/` is deprecated/removed. Use `/_Prompt-Cache_/`.

Index: `/_Prompt-Cache_/INDEX.md`.

## Archive Reference

The previous codebase is preserved in `/_archive/2026-01-14_repo-archive_v1/`. This archive is **read-only** and exists for:
- Historical reference
- Code recovery if needed
- Understanding prior design decisions

Do not modify files in the archive. Copy to active directories if reusing code.
