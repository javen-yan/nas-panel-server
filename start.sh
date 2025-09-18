#!/bin/bash

# NAS Panel Server startup script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
print_color $BLUE "Checking Python installation..."
if ! command_exists python3; then
    print_color $RED "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_color $GREEN "Python version: $PYTHON_VERSION"

# Check if virtual environment should be used
USE_VENV=${USE_VENV:-true}
VENV_DIR="venv"

if [ "$USE_VENV" = "true" ]; then
    print_color $BLUE "Setting up virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        print_color $YELLOW "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    print_color $YELLOW "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Install dependencies
print_color $BLUE "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_color $RED "Error: requirements.txt not found"
    exit 1
fi

# Check if config file exists
CONFIG_FILE="config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    print_color $YELLOW "Config file not found, generating default config..."
    python3 main.py --generate-config "$CONFIG_FILE"
fi

# Parse command line arguments
DAEMON_MODE=false
TEST_MODE=false
VERBOSE=false
CONFIG_PATH="$CONFIG_FILE"

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        -t|--test)
            TEST_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -d, --daemon    Run in daemon mode"
            echo "  -t, --test      Test data collection and exit"
            echo "  -v, --verbose   Enable verbose logging"
            echo "  -c, --config    Specify config file path"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            print_color $RED "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build command
CMD="python3 main.py"

if [ "$TEST_MODE" = "true" ]; then
    CMD="$CMD -t"
fi

if [ "$VERBOSE" = "true" ]; then
    CMD="$CMD -v"
fi

if [ "$CONFIG_PATH" != "config.yaml" ]; then
    CMD="$CMD -c $CONFIG_PATH"
fi

# Run the application
print_color $GREEN "Starting NAS Panel Server..."
print_color $BLUE "Command: $CMD"

if [ "$DAEMON_MODE" = "true" ]; then
    print_color $YELLOW "Running in daemon mode..."
    nohup $CMD > nas_panel_server.log 2>&1 &
    PID=$!
    echo $PID > nas_panel_server.pid
    print_color $GREEN "NAS Panel Server started with PID: $PID"
    print_color $BLUE "Log file: nas_panel_server.log"
    print_color $BLUE "PID file: nas_panel_server.pid"
    print_color $YELLOW "To stop the server, run: kill $PID"
else
    print_color $YELLOW "Running in foreground mode (Ctrl+C to stop)..."
    exec $CMD
fi