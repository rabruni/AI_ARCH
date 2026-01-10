#!/bin/bash
# Run The Assist
cd /Users/raymondbruni/AI_ARCH
source venv/bin/activate

# Load from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "ANTHROPIC_API_KEY not found."
    echo ""
    echo "Option 1: Create .env file"
    echo "  cp .env.example .env"
    echo "  # Then edit .env and add your key"
    echo ""
    echo "Option 2: Export directly"
    echo "  export ANTHROPIC_API_KEY=\"your-key-here\""
    echo ""
    exit 1
fi

python3 the_assist/main.py
