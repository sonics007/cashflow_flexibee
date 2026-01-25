#!/bin/bash
#
# Cashflow Dashboard - macOS Installation Script
# 
# Usage: 
#   curl -sSL https://raw.githubusercontent.com/sonics007/cashflow_flexibee/main/install-macos.sh | bash
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
cat << "EOF"
  ____          _     __ _                 
 / ___|__ _ ___| |__ / _| | _____      __  
| |   / _` / __| '_ \| |_| |/ _ \ \ /\ / /  
| |__| (_| \__ \ | | |  _| | (_) \ V  V /   
 \____\__,_|___/_| |_|_| |_|\___/ \_/\_/    
                                            
    Dashboard with FlexiBee Integration    
         macOS Installation Script
EOF
echo -e "${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo "This script will automatically:"
echo "  ✓ Install Homebrew (if not installed)"
echo "  ✓ Install Python 3.8+"
echo "  ✓ Clone the repository from GitHub"
echo "  ✓ Setup virtual environment"
echo "  ✓ Configure LaunchAgent (auto-start)"
echo "  ✓ Setup FlexiBee integration (optional)"
echo "  ✓ Start the application"
echo ""

# Get current user
CURRENT_USER=$(whoami)

# Ask for installation directory
echo -e "${YELLOW}Installation Configuration:${NC}"
read -p "Installation directory [default: ~/cashflow]: " INSTALL_DIR < /dev/tty
INSTALL_DIR=${INSTALL_DIR:-~/cashflow}
INSTALL_DIR=$(eval echo $INSTALL_DIR)  # Expand ~

# Ask for port
read -p "Application port [default: 8887]: " PORT < /dev/tty
PORT=${PORT:-8887}

echo ""
echo -e "${YELLOW}FlexiBee Configuration (optional):${NC}"
read -p "Configure FlexiBee now? (y/n) [default: n]: " CONFIGURE_FLEXIBEE < /dev/tty
CONFIGURE_FLEXIBEE=${CONFIGURE_FLEXIBEE:-n}

if [[ $CONFIGURE_FLEXIBEE =~ ^[Yy]$ ]]; then
    echo ""
    echo "Enter FlexiBee connection details:"
    read -p "  Server URL (e.g., https://demo.flexibee.eu:5434): " FB_HOST < /dev/tty
    read -p "  Company Code (e.g., demo_sro): " FB_COMPANY < /dev/tty
    read -p "  API Username: " FB_USER < /dev/tty
    read -sp "  API Password: " FB_PASSWORD < /dev/tty
    echo ""
    read -p "  Enable automatic hourly sync? (y/n) [default: n]: " FB_ENABLED < /dev/tty
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
echo "  User: $CURRENT_USER"
if [[ ! -z "$FB_HOST" ]]; then
    echo "  FlexiBee: Enabled ($FB_HOST)"
else
    echo "  FlexiBee: Not configured"
fi
echo ""
read -p "Continue? (y/n): " -n 1 -r REPLY < /dev/tty
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Installation cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Step 1/7: Installing Homebrew${NC}"
echo -e "${BLUE}==========================================${NC}"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo -e "${GREEN}✓ Homebrew already installed${NC}"
fi

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Step 2/7: Installing Dependencies${NC}"
echo -e "${BLUE}==========================================${NC}"

# Install Python if not installed
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    brew install python3
else
    echo -e "${GREEN}✓ Python 3 already installed${NC}"
fi

# Install git if not installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    brew install git
else
    echo -e "${GREEN}✓ Git already installed${NC}"
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Step 3/7: Cloning Repository${NC}"
echo -e "${BLUE}==========================================${NC}"

# Remove old installation if exists
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠ Directory $INSTALL_DIR already exists${NC}"
    read -p "Remove and reinstall? (y/n): " -n 1 -r REPLY < /dev/tty
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

echo -e "${GREEN}✓ Repository cloned to $INSTALL_DIR${NC}"

cd "$INSTALL_DIR"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Step 4/7: Creating Virtual Environment${NC}"
echo -e "${BLUE}==========================================${NC}"

python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Step 5/7: Installing Python Packages${NC}"
echo -e "${BLUE}==========================================${NC}"

source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install flask pandas openpyxl werkzeug cryptography schedule > /dev/null 2>&1

echo -e "${GREEN}✓ Python packages installed${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Step 6/7: Creating Data Directory${NC}"
echo -e "${BLUE}==========================================${NC}"

mkdir -p data

# Create FlexiBee config if provided
if [[ ! -z "$FB_HOST" ]]; then
    echo "Creating FlexiBee configuration..."
    
    python3 << PYTHON_EOF
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
    
    echo -e "${GREEN}✓ FlexiBee configured${NC}"
fi

echo -e "${GREEN}✓ Data directory ready${NC}"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Step 7/7: Configuring LaunchAgent${NC}"
echo -e "${BLUE}==========================================${NC}"

# Create LaunchAgent plist
PLIST_FILE="$HOME/Library/LaunchAgents/com.cashflow.dashboard.plist"
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cashflow.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/venv/bin/python3</string>
        <string>$INSTALL_DIR/app.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PORT</key>
        <string>$PORT</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/cashflow.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/cashflow-error.log</string>
</dict>
</plist>
EOF

# Update app.py to use PORT from environment
if grep -q "app.run(host='0.0.0.0', port=" app.py; then
    cp app.py app.py.backup
    sed -i '' "s/app.run(host='0.0.0.0', port=[0-9]*/app.run(host='0.0.0.0', port=int(os.environ.get('PORT', $PORT))/" app.py
    
    if ! grep -q "^import os" app.py; then
        sed -i '' '1i\
import os
' app.py
    fi
fi

# Load LaunchAgent
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo -e "${GREEN}✓ LaunchAgent configured${NC}"

# Wait a moment for app to start
sleep 2

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  🎉 Installation Complete!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "${CYAN}Access your Cashflow Dashboard at:${NC}"
echo -e "${BLUE}  http://localhost:$PORT${NC}"
echo ""
echo -e "${YELLOW}Default Login:${NC}"
echo "  Username: ${GREEN}admin${NC}"
echo "  Password: ${GREEN}admin${NC}"
echo -e "${RED}  ⚠ CHANGE PASSWORD IMMEDIATELY!${NC}"
echo ""
echo -e "${CYAN}Useful Commands:${NC}"
echo "  launchctl list | grep cashflow        # Check status"
echo "  launchctl unload $PLIST_FILE          # Stop"
echo "  launchctl load $PLIST_FILE            # Start"
echo "  tail -f $INSTALL_DIR/cashflow.log     # View logs"
echo ""
echo -e "${CYAN}Installation Details:${NC}"
echo "  Directory: $INSTALL_DIR"
echo "  Port: $PORT"
echo "  LaunchAgent: $PLIST_FILE"
echo ""
if [[ ! -z "$FB_HOST" ]]; then
    echo -e "${GREEN}✓ FlexiBee is configured and ready!${NC}"
    echo ""
fi
echo -e "${GREEN}Happy cash flowing! 💰${NC}"
echo ""
