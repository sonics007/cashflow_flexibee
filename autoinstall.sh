#!/bin/bash
#
# Cashflow Dashboard - Automatic Installation Script for Debian/Ubuntu
# This script will install and configure the entire application including systemd service
#
# Usage: sudo ./autoinstall.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo -e "${BLUE}"
echo "=========================================="
echo "  Cashflow Dashboard - Auto Installer"
echo "=========================================="
echo -e "${NC}"
echo ""
echo "This script will:"
echo "  1. Install system dependencies (Python, pip, git)"
echo "  2. Create virtual environment"
echo "  3. Install Python packages"
echo "  4. Configure systemd service"
echo "  5. Setup firewall (optional)"
echo ""

# Ask for port
echo -e "${YELLOW}Configuration:${NC}"
read -p "Enter port number for the application [default: 8887]: " PORT
PORT=${PORT:-8887}

echo -e "${GREEN}✓ Port set to: $PORT${NC}"
echo ""

# Ask for installation directory
INSTALL_DIR=$(pwd)
echo "Current directory: $INSTALL_DIR"
read -p "Install in current directory? (y/n) [default: y]: " USE_CURRENT
USE_CURRENT=${USE_CURRENT:-y}

if [[ ! $USE_CURRENT =~ ^[Yy]$ ]]; then
    read -p "Enter installation directory: " INSTALL_DIR
    INSTALL_DIR=$(eval echo $INSTALL_DIR)
fi

echo -e "${GREEN}✓ Installation directory: $INSTALL_DIR${NC}"
echo ""

# Ask for FlexiBee configuration
echo -e "${YELLOW}FlexiBee Configuration (optional):${NC}"
echo "Do you want to configure FlexiBee integration now?"
read -p "(y/n) [default: n]: " CONFIGURE_FLEXIBEE
CONFIGURE_FLEXIBEE=${CONFIGURE_FLEXIBEE:-n}

if [[ $CONFIGURE_FLEXIBEE =~ ^[Yy]$ ]]; then
    echo ""
    echo "Enter FlexiBee connection details:"
    read -p "  FlexiBee Server URL (e.g., https://demo.flexibee.eu:5434): " FB_HOST
    read -p "  Company Code (e.g., demo_sro): " FB_COMPANY
    read -p "  API Username: " FB_USER
    read -sp "  API Password: " FB_PASSWORD
    echo ""
    read -p "  Enable automatic sync every hour? (y/n) [default: n]: " FB_ENABLED
    FB_ENABLED=${FB_ENABLED:-n}
    
    if [[ $FB_ENABLED =~ ^[Yy]$ ]]; then
        FB_ENABLED_BOOL="true"
    else
        FB_ENABLED_BOOL="false"
    fi
    
    echo -e "${GREEN}✓ FlexiBee configuration saved${NC}"
else
    FB_HOST=""
    FB_COMPANY=""
    FB_USER=""
    FB_PASSWORD=""
    FB_ENABLED_BOOL="false"
    echo -e "${YELLOW}⚠ FlexiBee configuration skipped (can be configured later in Settings)${NC}"
fi
echo ""

# Confirm
echo -e "${YELLOW}Summary:${NC}"
echo "  Port: $PORT"
echo "  Directory: $INSTALL_DIR"
echo "  User: $ACTUAL_USER"
if [[ ! -z "$FB_HOST" ]]; then
    echo "  FlexiBee: Enabled ($FB_HOST)"
else
    echo "  FlexiBee: Not configured"
fi
echo ""
read -p "Continue with installation? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Installation cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}=========================================="
echo "  Step 1: Installing System Dependencies"
echo "==========================================${NC}"

# Update package list
echo "Updating package list..."
apt-get update -qq

# Install dependencies
echo "Installing Python, pip, git, and other dependencies..."
apt-get install -y python3 python3-pip python3-venv git sqlite3 curl

echo -e "${GREEN}✓ System dependencies installed${NC}"
echo ""

# Navigate to installation directory
cd "$INSTALL_DIR"

echo -e "${BLUE}=========================================="
echo "  Step 2: Creating Virtual Environment"
echo "==========================================${NC}"

# Remove old venv if exists
if [ -d "venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf venv
fi

# Create virtual environment
echo "Creating virtual environment..."
sudo -u $ACTUAL_USER python3 -m venv venv

echo -e "${GREEN}✓ Virtual environment created${NC}"
echo ""

echo -e "${BLUE}=========================================="
echo "  Step 3: Installing Python Packages"
echo "==========================================${NC}"

# Activate venv and install packages
echo "Installing Flask and dependencies..."
sudo -u $ACTUAL_USER bash -c "source venv/bin/activate && pip install --upgrade pip && pip install flask pandas openpyxl werkzeug cryptography schedule"

echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

echo -e "${BLUE}=========================================="
echo "  Step 4: Creating Data Directory"
echo "==========================================${NC}"

# Create data directory
if [ ! -d "data" ]; then
    mkdir -p data
    chown $ACTUAL_USER:$ACTUAL_USER data
    echo -e "${GREEN}✓ Data directory created${NC}"
else
    echo -e "${YELLOW}⚠ Data directory already exists${NC}"
fi

# Create FlexiBee config if provided
if [[ ! -z "$FB_HOST" ]]; then
    echo "Creating FlexiBee configuration..."
    
    # Use Python to encrypt password and create config
    sudo -u $ACTUAL_USER bash -c "cd '$INSTALL_DIR' && source venv/bin/activate && python3 << 'PYTHON_EOF'
import json
import os
from flexibee_sync import PasswordEncryption

config = {
    'host': '$FB_HOST',
    'company': '$FB_COMPANY',
    'user': '$FB_USER',
    'password': PasswordEncryption.encrypt('$FB_PASSWORD'),
    'password_encrypted': True,
    'enabled': $FB_ENABLED_BOOL,
    'last_sync': ''
}

os.makedirs('data', exist_ok=True)
with open('data/flexibee_config.json', 'w') as f:
    json.dump(config, f, indent=4)

print('FlexiBee config created')
PYTHON_EOF
"
    
    echo -e "${GREEN}✓ FlexiBee configuration file created${NC}"
fi
echo ""

echo -e "${BLUE}=========================================="
echo "  Step 5: Configuring Systemd Service"
echo "==========================================${NC}"

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/cashflow.service"

cat > $SERVICE_FILE << EOF
[Unit]
Description=Cashflow Dashboard
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
Environment="PORT=$PORT"
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd service file created${NC}"

# Update app.py to use PORT environment variable
echo "Updating app.py to use port $PORT..."
if grep -q "app.run(host='0.0.0.0', port=" app.py; then
    # Backup original
    cp app.py app.py.backup
    
    # Update port in app.py
    sed -i "s/app.run(host='0.0.0.0', port=[0-9]*/app.run(host='0.0.0.0', port=int(os.environ.get('PORT', $PORT))/" app.py
    
    # Also add import os if not present
    if ! grep -q "^import os" app.py; then
        sed -i '1i import os' app.py
    fi
    
    echo -e "${GREEN}✓ app.py updated to use port $PORT${NC}"
fi

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable cashflow

echo -e "${GREEN}✓ Service enabled (will start on boot)${NC}"
echo ""

echo -e "${BLUE}=========================================="
echo "  Step 6: Firewall Configuration"
echo "==========================================${NC}"

# Check if ufw is installed
if command -v ufw &> /dev/null; then
    read -p "Do you want to open port $PORT in firewall? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ufw allow $PORT/tcp
        echo -e "${GREEN}✓ Port $PORT opened in firewall${NC}"
    else
        echo -e "${YELLOW}⚠ Skipped firewall configuration${NC}"
    fi
else
    echo -e "${YELLOW}⚠ UFW not installed, skipping firewall configuration${NC}"
fi
echo ""

echo -e "${BLUE}=========================================="
echo "  Step 7: Starting Service"
echo "==========================================${NC}"

# Start service
systemctl start cashflow

# Wait a moment
sleep 2

# Check status
if systemctl is-active --quiet cashflow; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Checking logs..."
    journalctl -u cashflow -n 20 --no-pager
fi
echo ""

echo -e "${BLUE}=========================================="
echo "  Installation Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${GREEN}✓ Cashflow Dashboard is now installed and running!${NC}"
echo ""
echo "Access the application at:"
echo -e "${BLUE}  http://$(hostname -I | awk '{print $1}'):$PORT${NC}"
echo -e "${BLUE}  http://localhost:$PORT${NC}"
echo ""
echo "Default login credentials:"
echo -e "${YELLOW}  Username: admin${NC}"
echo -e "${YELLOW}  Password: admin${NC}"
echo -e "${RED}  ⚠ CHANGE PASSWORD AFTER FIRST LOGIN!${NC}"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status cashflow    # Check service status"
echo "  sudo systemctl restart cashflow   # Restart service"
echo "  sudo systemctl stop cashflow      # Stop service"
echo "  sudo journalctl -u cashflow -f    # View logs"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Service file: $SERVICE_FILE"
echo ""
echo -e "${GREEN}Happy cash flowing! 💰${NC}"
