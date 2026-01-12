#!/bin/bash
#
# Locked System - Startup Script
#
# Usage:
#   ./run.sh                     # Interactive mode
#   ./run.sh -d, --debug         # Debug mode (shows system state)
#   ./run.sh -m "message"        # Single message
#   ./run.sh --setup             # Run setup/validation
#   ./run.sh --test              # Run setup with tests
#   ./run.sh --reset             # Clear all memory (fresh start)
#   ./run.sh --help              # Show help
#
# Environment:
#   ANTHROPIC_API_KEY    API key for Claude (optional for placeholder mode)
#   LOCKED_MEMORY_DIR    Override memory directory (default: ./memory)
#

set -e

# Get script directory (works even if called from elsewhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODE="interactive"
MESSAGE=""
JSON_OUTPUT=false
CONFIG_FILE=""
VERBOSE=false
DEBUG_MODE=false

usage() {
    cat << EOF
Locked System - Two-Loop Cognitive Architecture

Usage: $(basename "$0") [OPTIONS]

Modes:
  (default)              Interactive chat mode
  -d, --debug            Debug mode (shows full system state)
  -m, --message MSG      Process single message and exit
  -s, --setup            Run setup validation
  -t, --test             Run setup with full tests
  -r, --reset            Clear all memory (fresh start)

Options:
  -c, --config FILE      Use configuration file (YAML)
  -j, --json             Output as JSON (single message mode)
  -v, --verbose          Verbose output
  -h, --help             Show this help

Examples:
  $(basename "$0")                           # Start interactive session
  $(basename "$0") -d                        # Start with debug panel
  $(basename "$0") -m "Hello"                # Process single message
  $(basename "$0") -m "Hello" --json         # Get JSON response
  $(basename "$0") --setup                   # Validate installation
  $(basename "$0") --test                    # Run full tests
  $(basename "$0") -c config.yaml            # Use custom config
  $(basename "$0") --reset                   # Clear memory and start fresh

Environment Variables:
  ANTHROPIC_API_KEY      API key for Claude models
  LOCKED_MEMORY_DIR      Memory directory (default: ./memory)

EOF
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--debug)
            DEBUG_MODE=true
            shift
            ;;
        -m|--message)
            MODE="message"
            MESSAGE="$2"
            shift 2
            ;;
        -s|--setup)
            MODE="setup"
            shift
            ;;
        -t|--test)
            MODE="test"
            shift
            ;;
        -r|--reset)
            MODE="reset"
            shift
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -j|--json)
            JSON_OUTPUT=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "python3 not found. Please install Python 3.8+."
    exit 1
fi

# Check we're in the right place
if [[ ! -d "$PROJECT_DIR/locked_system" ]]; then
    log_error "locked_system package not found. Run from project root."
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [[ -d "$PROJECT_DIR/venv" ]]; then
    source "$PROJECT_DIR/venv/bin/activate"
    [[ $VERBOSE == true ]] && log_info "Activated venv"
elif [[ -d "$PROJECT_DIR/.venv" ]]; then
    source "$PROJECT_DIR/.venv/bin/activate"
    [[ $VERBOSE == true ]] && log_info "Activated .venv"
fi

# Build command based on mode
case $MODE in
    interactive)
        if [[ $VERBOSE == true ]]; then
            log_info "Starting interactive session..."
            log_info "Memory dir: ${LOCKED_MEMORY_DIR:-./memory}"
            [[ -n "$ANTHROPIC_API_KEY" ]] && log_info "API key: set" || log_warn "API key: not set (using placeholder)"
        fi

        # The chat UI handles its own header
        CMD="python3 -m locked_system.main"
        [[ -n "$CONFIG_FILE" ]] && CMD="$CMD --config $CONFIG_FILE"
        [[ $DEBUG_MODE == true ]] && CMD="$CMD --debug"
        exec $CMD
        ;;

    message)
        if [[ -z "$MESSAGE" ]]; then
            log_error "Message required with -m flag"
            exit 1
        fi

        CMD="python3 -m locked_system.main -m \"$MESSAGE\""
        [[ $JSON_OUTPUT == true ]] && CMD="$CMD --json"
        [[ -n "$CONFIG_FILE" ]] && CMD="$CMD --config $CONFIG_FILE"
        eval $CMD
        ;;

    setup)
        log_info "Running setup validation..."
        CMD="python3 -m locked_system.setup"
        [[ -n "$CONFIG_FILE" ]] && CMD="$CMD --config"
        exec $CMD
        ;;

    test)
        log_info "Running setup with full tests..."
        exec python3 -m locked_system.setup --test
        ;;

    reset)
        MEMORY_DIR="${LOCKED_MEMORY_DIR:-./memory}"
        log_warn "This will delete all memory in: $MEMORY_DIR"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [[ -d "$MEMORY_DIR" ]]; then
                rm -rf "$MEMORY_DIR"
                log_success "Memory cleared: $MEMORY_DIR"
            else
                log_info "Memory directory does not exist: $MEMORY_DIR"
            fi
            # Also clear logs if they exist
            if [[ -d "./logs" ]]; then
                rm -rf "./logs"
                log_success "Logs cleared: ./logs"
            fi
            log_success "Fresh start ready. Run ./run.sh to begin."
        else
            log_info "Reset cancelled."
        fi
        ;;
esac
