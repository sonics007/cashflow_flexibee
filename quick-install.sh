#!/bin/bash
#
# Cashflow Dashboard - One-Command Auto Installer
# 
# Usage: 
#   curl -sSL https://raw.githubusercontent.com/sonics007/cashflow_flexibee/main/quick-install.sh | sudo bash
#   OR
#   wget -qO- https://raw.githubusercontent.com/sonics007/cashflow_flexibee/main/quick-install.sh | sudo bash
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Get actual user
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

clear
echo -e "${CYAN}"
cat << "EOF"
  ____          _     __ _                 
 / ___|__ _ ___| |__ / _| | _____      __  
| |   / _` / __| '_ \| |_| |/ _ \ \ /\ / /  
| |__| (_| \__ \ | | |  _| | (_) \ V  V /   
 \____\__,_|___/_| |_|_| |_|\___/ \_/\_/    
                                            
    Dashboard with FlexiBee Integration    
EOF
echo -e "${NC}"
echo -e "${BLUE}=========================================="
echo "  Quick Installation Script"
echo "==========================================${NC}"
echo ""
echo "This script will automatically:"
echo "  ✓ Install all dependencies"
echo "  ✓ Clone the repository from GitHub"
echo "  ✓ Setup virtual environment"
echo "  ✓ Configure systemd service"
echo "  ✓ Setup FlexiBee integration (optional)"
echo "  ✓ Start the application"
echo ""

# Ask for installation directory
echo -e "${YELLOW}Installation Configuration:${NC}"
read -p "Installation directory [default: /opt/cashflow]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-/opt/cashflow}

# Ask for port
read -p "Application port [default: 8887]: " PORT
PORT=${PORT:-8887}

echo ""
echo -e "${YELLOW}FlexiBee Configuration (optional):${NC}"
read -p "Configure FlexiBee now? (y/n) [default: n]: " CONFIGURE_FLEXIBEE
CONFIGURE_FLEXIBEE=${CONFIGURE_FLEXIBEE:-n}

if [[ $CONFIGURE_FLEXIBEE =~ ^[Yy]$ ]]; then
    echo ""
    echo "Enter FlexiBee connection details:"
    read -p "  Server URL (e.g., https://demo.flexibee.eu:5434): " FB_HOST
    read -p "  Company Code (e.g., demo_sro): " FB_COMPANY
    read -p "  API Username: " FB_USER
    read -sp "  API Password: " FB_PASSWORD
    echo ""
    read -p "  Enable automatic hourly sync? (y/n) [default: n]: " FB_ENABLED
    FB_ENABLED=${FB_ENABLED:-n}
    
    if [[ $FB_ENABLED =~ ^[Yy]$ ]]; then
        FB_ENABLED_BOOL="true"
    else
        FB_ENABLED_BOOL="false"
    fi
else
    FB_HOST=""
    FB_COMPANY=""
    FB_USER=""
    FB_PASSWORD=""
    FB_ENABLED_BOOL="false"
fi

# Summary
echo ""
echo -e "${YELLOW}Installation Summary:${NC}"
echo "  Directory: $INSTALL_DIR"
echo "  Port: $PORT"
echo "  User: $ACTUAL_USER"
if [[ ! -z "$FB_HOST" ]]; then
    echo "  FlexiBee: Enabled ($FB_HOST)"
else
    echo "  FlexiBee: Not configured"
fi
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Installation cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}=========================================="
echo "  Step 1/7: Installing Dependencies"
echo "==========================================${NC}"

apt-get update -qq
apt-get install -y python3 python3-pip python3-venv git sqlite3 curl wget > /dev/null 2>&1

echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}=========================================="
echo "  Step 2/7: Cloning Repository"
echo "==========================================${NC}"

# Remove old installation if exists
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠ Directory $INSTALL_DIR already exists${NC}"
    read -p "Remove and reinstall? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}✓ Old installation removed${NC}"
    else
        echo -e "${RED}Installation cancelled.${NC}"
        exit 0
    fi
fi

# Clone repository
echo "Cloning from GitHub..."
git clone https://github.com/sonics007/cashflow_flexibee.git "$INSTALL_DIR" > /dev/null 2>&1
chown -R $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR"

echo -e "${GREEN}✓ Repository cloned to $INSTALL_DIR${NC}"

cd "$INSTALL_DIR"

echo ""
echo -e "${BLUE}=========================================="
echo "  Step 3/7: Creating Virtual Environment"
echo "==========================================${NC}"

sudo -u $ACTUAL_USER python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo ""
echo -e "${BLUE}=========================================="
echo "  Step 4/7: Installing Python Packages"
echo "==========================================${NC}"

sudo -u $ACTUAL_USER bash -c "source venv/bin/activate && pip install --upgrade pip > /dev/null 2>&1 && pip install flask pandas openpyxl werkzeug cryptography schedule > /dev/null 2>&1"

echo -e "${GREEN}✓ Python packages installed${NC}"

echo ""
echo -e "${BLUE}=========================================="
echo "  Step 5/7: Creating Data Directory"
echo "==========================================${NC}"

mkdir -p data
chown $ACTUAL_USER:$ACTUAL_USER data

# Create FlexiBee config if provided
if [[ ! -z "$FB_HOST" ]]; then
    echo "Creating FlexiBee configuration..."
    
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
    echo -e "${GREEN}✓ FlexiBee configured${NC}"
fi

echo -e "${GREEN}✓ Data directory ready${NC}"

echo ""
echo -e "${BLUE}=========================================="
echo "  Step 6/7: Configuring Systemd Service"
echo "==========================================${NC}"

# Create systemd service
cat > /etc/systemd/system/cashflow.service << EOF
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

# Update app.py to use PORT from environment
if grep -q "app.run(host='0.0.0.0', port=" app.py; then
    cp app.py app.py.backup
    sed -i "s/app.run(host='0.0.0.0', port=[0-9]*/app.run(host='0.0.0.0', port=int(os.environ.get('PORT', $PORT))/" app.py
    
    if ! grep -q "^import os" app.py; then
        sed -i '1i import os' app.py
    fi
fi

systemctl daemon-reload
systemctl enable cashflow > /dev/null 2>&1

echo -e "${GREEN}✓ Systemd service configured${NC}"

echo ""
echo -e "${BLUE}=========================================="
echo "  Step 7/7: Starting Application"
echo "==========================================${NC}"

# Configure firewall if available
if command -v ufw &> /dev/null; then
    read -p "Open port $PORT in firewall? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ufw allow $PORT/tcp > /dev/null 2>&1
        echo -e "${GREEN}✓ Firewall configured${NC}"
    fi
fi

# Start service
systemctl start cashflow
sleep 2

# Check status
if systemctl is-active --quiet cashflow; then
    echo -e "${GREEN}✓ Application started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start application${NC}"
    echo "Checking logs..."
    journalctl -u cashflow -n 20 --no-pager
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  🎉 Installation Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${CYAN}Access your Cashflow Dashboard at:${NC}"
echo -e "${BLUE}  http://$(hostname -I | awk '{print $1}'):$PORT${NC}"
echo -e "${BLUE}  http://localhost:$PORT${NC}"
echo ""
echo -e "${YELLOW}Default Login:${NC}"
echo "  Username: ${GREEN}admin${NC}"
echo "  Password: ${GREEN}admin${NC}"
echo -e "${RED}  ⚠ CHANGE PASSWORD IMMEDIATELY!${NC}"
echo ""
echo -e "${CYAN}Useful Commands:${NC}"
echo "  sudo systemctl status cashflow    # Check status"
echo "  sudo systemctl restart cashflow   # Restart"
echo "  sudo systemctl stop cashflow      # Stop"
echo "  sudo journalctl -u cashflow -f    # View logs"
echo ""
echo -e "${CYAN}Installation Details:${NC}"
echo "  Directory: $INSTALL_DIR"
echo "  Port: $PORT"
echo "  Service: /etc/systemd/system/cashflow.service"
echo ""
if [[ ! -z "$FB_HOST" ]]; then
    echo -e "${GREEN}✓ FlexiBee is configured and ready!${NC}"
    echo ""
fi
echo -e "${GREEN}Happy cash flowing! 💰${NC}"
echo ""
