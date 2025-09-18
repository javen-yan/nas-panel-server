#!/bin/bash

# NAS Panel Server stop script

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

PID_FILE="nas_panel_server.pid"

if [ ! -f "$PID_FILE" ]; then
    print_color $YELLOW "PID file not found. Trying to find running processes..."
    
    # Try to find running processes
    PIDS=$(pgrep -f "python.*main.py" || true)
    
    if [ -z "$PIDS" ]; then
        print_color $RED "No running NAS Panel Server processes found"
        exit 1
    fi
    
    print_color $BLUE "Found running processes: $PIDS"
    for PID in $PIDS; do
        print_color $YELLOW "Stopping process $PID..."
        kill $PID
        sleep 2
        
        # Check if process is still running
        if kill -0 $PID 2>/dev/null; then
            print_color $YELLOW "Process $PID still running, sending SIGKILL..."
            kill -9 $PID
        fi
        
        print_color $GREEN "Process $PID stopped"
    done
else
    PID=$(cat "$PID_FILE")
    
    if kill -0 $PID 2>/dev/null; then
        print_color $BLUE "Stopping NAS Panel Server (PID: $PID)..."
        kill $PID
        
        # Wait for process to stop
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Check if process is still running
        if kill -0 $PID 2>/dev/null; then
            print_color $YELLOW "Process still running, sending SIGKILL..."
            kill -9 $PID
        fi
        
        print_color $GREEN "NAS Panel Server stopped successfully"
    else
        print_color $YELLOW "Process $PID is not running"
    fi
    
    # Remove PID file
    rm -f "$PID_FILE"
fi

print_color $GREEN "Stop script completed"