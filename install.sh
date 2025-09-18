#!/bin/bash

# NAS Panel Server Installation Script

set -e

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_color $YELLOW "Running as root. This script will install system-wide."
    INSTALL_DIR="/opt/nas-panel-server"
    CONFIG_DIR="/etc/nas-panel-server"
    LOG_DIR="/var/log/nas-panel-server"
    DATA_DIR="/var/lib/nas-panel-server"
    SYSTEMD_INSTALL=true
else
    print_color $YELLOW "Running as regular user. This script will install to home directory."
    INSTALL_DIR="$HOME/.local/share/nas-panel-server"
    CONFIG_DIR="$HOME/.config/nas-panel-server"
    LOG_DIR="$HOME/.local/share/nas-panel-server/logs"
    DATA_DIR="$HOME/.local/share/nas-panel-server/data"
    SYSTEMD_INSTALL=false
fi

print_color $BLUE "NAS Panel Server Installation"
print_color $BLUE "============================="
echo "Install directory: $INSTALL_DIR"
echo "Config directory: $CONFIG_DIR"
echo "Log directory: $LOG_DIR"
echo "Data directory: $DATA_DIR"
echo ""

# Create directories
print_color $YELLOW "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"

# Copy files
print_color $YELLOW "Copying application files..."
cp -r nas_panel_server "$INSTALL_DIR/"
cp main.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp setup.py "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/"
cp USAGE.md "$INSTALL_DIR/"
cp start.sh "$INSTALL_DIR/"
cp stop.sh "$INSTALL_DIR/"

# Make scripts executable
chmod +x "$INSTALL_DIR/start.sh"
chmod +x "$INSTALL_DIR/stop.sh"

# Copy configuration
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    print_color $YELLOW "Installing default configuration..."
    cp config.yaml "$CONFIG_DIR/"
    cp config_example.yaml "$CONFIG_DIR/"
else
    print_color $BLUE "Configuration file already exists, skipping..."
fi

# Create virtual environment and install dependencies
print_color $YELLOW "Setting up Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install systemd service (if root)
if [ "$SYSTEMD_INSTALL" = true ]; then
    print_color $YELLOW "Installing systemd service..."
    
    # Create user and group
    if ! id "nas-panel" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" nas-panel
    fi
    
    # Set ownership
    chown -R nas-panel:nas-panel "$INSTALL_DIR"
    chown -R nas-panel:nas-panel "$CONFIG_DIR"
    chown -R nas-panel:nas-panel "$LOG_DIR"
    chown -R nas-panel:nas-panel "$DATA_DIR"
    
    # Install service file
    sed "s|/opt/nas-panel-server|$INSTALL_DIR|g" nas-panel-server.service > /etc/systemd/system/nas-panel-server.service
    sed -i "s|/etc/nas-panel-server|$CONFIG_DIR|g" /etc/systemd/system/nas-panel-server.service
    
    systemctl daemon-reload
    systemctl enable nas-panel-server
    
    print_color $GREEN "Systemd service installed and enabled."
    print_color $BLUE "To start the service: systemctl start nas-panel-server"
    print_color $BLUE "To check status: systemctl status nas-panel-server"
    print_color $BLUE "To view logs: journalctl -u nas-panel-server -f"
fi

# Create desktop entry (if not root)
if [ "$SYSTEMD_INSTALL" = false ]; then
    DESKTOP_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"
    
    cat > "$DESKTOP_DIR/nas-panel-server.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NAS Panel Server
Comment=System monitoring with MQTT publishing
Exec=$INSTALL_DIR/start.sh
Icon=computer
Terminal=false
Categories=System;Monitor;
EOF
    
    print_color $GREEN "Desktop entry created."
fi

# Create command line shortcuts
BIN_DIR="$HOME/.local/bin"
if [ "$SYSTEMD_INSTALL" = true ]; then
    BIN_DIR="/usr/local/bin"
fi

mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/nas-panel-server" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
source venv/bin/activate
python main.py "\$@"
EOF

chmod +x "$BIN_DIR/nas-panel-server"

print_color $GREEN "Installation completed successfully!"
print_color $BLUE ""
print_color $BLUE "Usage:"
print_color $BLUE "  nas-panel-server                 # Start server"
print_color $BLUE "  nas-panel-server -t              # Test collection"
print_color $BLUE "  nas-panel-server -c config.yaml  # Use custom config"
print_color $BLUE ""
print_color $BLUE "Configuration file: $CONFIG_DIR/config.yaml"
print_color $BLUE "Log files: $LOG_DIR/"
print_color $BLUE ""

if [ "$SYSTEMD_INSTALL" = true ]; then
    print_color $YELLOW "To start as system service:"
    print_color $BLUE "  systemctl start nas-panel-server"
else
    print_color $YELLOW "To start manually:"
    print_color $BLUE "  $INSTALL_DIR/start.sh"
fi