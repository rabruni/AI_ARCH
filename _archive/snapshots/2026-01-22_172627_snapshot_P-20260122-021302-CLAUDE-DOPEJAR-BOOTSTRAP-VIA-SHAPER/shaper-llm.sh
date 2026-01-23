#!/bin/bash
# LLM-Powered Shaper CLI
# Uses Claude API for natural language artifact shaping

cd "$(dirname "$0")"

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

python3 -c "
import sys
sys.path.insert(0, '.')
from Control_Plane.modules.design_framework.shaper.llm_shaper import main
sys.exit(main())
" "$@"
