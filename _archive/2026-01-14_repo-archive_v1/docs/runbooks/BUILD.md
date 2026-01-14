# Build Runbook

## Prerequisites

- Python 3.10+
- pip (Python package manager)
- Anthropic API key

## Environment Setup

```bash
# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-key-here"
```

## Build Verification

```bash
# Run verification script (auto-detects venv if present)
bash scripts/verify.sh

# The script will:
# 1. Use venv/bin/python if venv exists
# 2. Check Python version
# 3. Verify required files exist
# 4. Check Python syntax (first 20 .py files)
# 5. Run pytest (517+ tests)
# 6. Report common issues (print statements, TODOs)

# Or manually check syntax
venv/bin/python -m py_compile the_assist/main_hrm.py
```

## Running the Application

```bash
# Primary entry point (HRM)
python the_assist/main_hrm.py

# Or use run.sh
./run.sh
```

## Common Issues

### ModuleNotFoundError

```bash
# Ensure you're in the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### API Key Missing

```bash
# Set the environment variable
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Permission Denied on Scripts

```bash
chmod +x scripts/verify.sh scripts/capture.sh run.sh
```
