#!/bin/bash
# Run The Assist / Locked System
cd /Users/raymondbruni/AI_ARCH
source venv/bin/activate

# Load from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Show help
show_help() {
    echo "Usage: ./run.sh [option]"
    echo ""
    echo "Options:"
    echo "  (none)        Run Front-Door Agent demo (default)"
    echo "  frontdoor     Run Front-Door Agent demo"
    echo "  assist, hrm   Run The Assist (HRM 4-layer architecture)"
    echo "  assist-legacy Run The Assist (legacy orchestrator)"
    echo "  locked        Run Locked System CLI"
    echo "  test          Run all tests"
    echo "  help          Show this help"
    echo ""
}

# Check if key is set (not needed for tests or frontdoor demo)
check_api_key() {
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
}

case "${1:-frontdoor}" in
    assist|hrm)
        check_api_key
        python3 the_assist/main_hrm.py
        ;;
    assist-legacy)
        check_api_key
        python3 the_assist/main.py
        ;;
    locked)
        check_api_key
        python3 -m locked_system.cli.main "${@:2}"
        ;;
    frontdoor)
        python3 locked_system/demo_front_door.py
        ;;
    test)
        pytest locked_system/tests/ -v "${@:2}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
