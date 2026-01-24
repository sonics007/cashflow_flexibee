#!/bin/bash

# Cashflow Dashboard - Installation Script for Linux (Ubuntu/Debian)

set -e  # Exit on error

echo "=========================================="
echo "   Cashflow Dashboard Installer"
echo "=========================================="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 could not be found. Please install it first."
    echo "   sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip"
    exit 1
fi

echo "✅ Python3 found."

# 2. Create Virtual Environment
if [ -d "venv" ]; then
    # Check if this is a valid Linux venv
    if [ ! -f "venv/bin/activate" ]; then
        echo "⚠️  Found 'venv' folder but 'bin/activate' is missing."
        echo "    (If you copied this from Windows, the venv is incompatible.)"
        echo ">>> Removing invalid venv..."
        rm -rf venv
    else
        echo ">>> Virtual environment already exists."
    fi
fi

if [ ! -d "venv" ]; then
    echo ">>> Creating virtual environment (venv)..."
    # Try to create venv
    if ! python3 -m venv venv; then
         echo "❌ Failed to create venv. You might need to install python3-venv:"
         echo "   sudo apt-get install python3-venv"
         exit 1
    fi
fi

# 3. Install Dependencies
echo ">>> Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found! Installing default packages..."
    pip install flask pandas openpyxl schedule werkzeug
fi

# 4. Create Directories
echo ">>> Setting up directory structure..."
mkdir -p data/vstupy/prijate
mkdir -p data/vstupy/vydane
mkdir -p data/backups

# 5. Create Run Script
echo ">>> Creating startup script (run.sh)..."
cat > run.sh << 'EOL'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_ENV=production
python3 app.py
EOL

chmod +x run.sh

# 6. Initialize Database (if needed)
# If database.db doesn't exist, app.py creates it on run, or we can run init_db_quick.py
if [ ! -f "data/cashflow.db" ]; then
    echo ">>> Initializing database..."
    # We can run a small snippet to init DB if needed, but app.py handles it normally via get_db?
    # app.py has lazy loading.
    pass
fi

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "To start the application manually:"
echo "   ./run.sh"
echo ""
echo "To set up as a system service (auto-start), look at 'cashflow.service' template."
