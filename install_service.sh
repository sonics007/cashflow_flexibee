#!/bin/bash
# Automatický instalační skript pro Cashflow Dashboard jako systemd service
# Pro Debian/Ubuntu/Raspberry Pi (spuštění jako root)

set -e  # Ukončit při chybě

echo "================================================"
echo "  Cashflow Dashboard - Instalace systemd služby"
echo "================================================"
echo ""

# Zjištění aktuálního adresáře
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "📁 Adresář aplikace: $SCRIPT_DIR"

# Zjištění uživatele a skupiny
if [ "$EUID" -eq 0 ]; then
    # Běží jako root - zeptáme se na uživatele
    echo "⚠️  Běžíte jako root."
    echo "Pod jakým uživatelem má služba běžet?"
    read -r -p "Uživatel (výchozí: root): " ACTUAL_USER
    ACTUAL_USER="${ACTUAL_USER:-root}"
    
    if [ "$ACTUAL_USER" = "root" ]; then
        ACTUAL_GROUP="root"
    else
        ACTUAL_GROUP=$(id -gn "$ACTUAL_USER" 2>/dev/null || echo "$ACTUAL_USER")
    fi
else
    ACTUAL_USER="$USER"
    ACTUAL_GROUP=$(id -gn)
fi

echo "👤 Uživatel: $ACTUAL_USER"
echo "👥 Skupina: $ACTUAL_GROUP"

# Kontrola existence app.py
if [ ! -f "$SCRIPT_DIR/app.py" ]; then
    echo "❌ Soubor app.py nebyl nalezen v $SCRIPT_DIR"
    exit 1
fi

# Kontrola/vytvoření virtuálního prostředí
VENV_PATH="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "⚠️  Virtuální prostředí neexistuje, vytvářím..."
    if [ "$ACTUAL_USER" = "root" ]; then
        python3 -m venv "$VENV_PATH"
    else
        su - "$ACTUAL_USER" -c "python3 -m venv $VENV_PATH"
    fi
    echo "✅ Virtuální prostředí vytvořeno"
fi

# Kontrola Python interpretu
PYTHON_BIN="$VENV_PATH/bin/python3"
if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ Python interpreter nebyl nalezen: $PYTHON_BIN"
    exit 1
fi

# Instalace závislostí (pokud existuje requirements.txt)
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "📦 Instaluji závislosti..."
    if [ "$ACTUAL_USER" = "root" ]; then
        "$VENV_PATH/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
    else
        su - "$ACTUAL_USER" -c "$VENV_PATH/bin/pip install -r $SCRIPT_DIR/requirements.txt --quiet"
    fi
    echo "✅ Závislosti nainstalovány"
fi

# Vytvoření systemd service souboru
SERVICE_FILE="/etc/systemd/system/cashflow.service"
echo "📝 Vytvářím systemd service: $SERVICE_FILE"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Cashflow Dashboard Web App
After=network.target

[Service]
User=$ACTUAL_USER
Group=$ACTUAL_GROUP

WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$VENV_PATH/bin"
ExecStart=$PYTHON_BIN app.py

# Restart při pádu
Restart=always
RestartSec=5

# Logování
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cashflow

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service soubor vytvořen"

# Nastavení oprávnění
echo "🔒 Nastavuji oprávnění..."
chown -R "$ACTUAL_USER:$ACTUAL_GROUP" "$SCRIPT_DIR"
chmod 644 "$SERVICE_FILE"

# Reload systemd
echo "🔄 Reload systemd daemon..."
systemctl daemon-reload

# Povolení služby při startu
echo ""
echo "⚙️  Povolit službu při startu systému? (y/n)"
read -r -p "Odpověď: " enable_service
if [[ "$enable_service" =~ ^[Yy]$ ]]; then
    systemctl enable cashflow.service
    echo "✅ Služba povolena při startu"
fi

# Spuštění služby
echo ""
echo "🚀 Spustit službu nyní? (y/n)"
read -r -p "Odpověď: " start_service
if [[ "$start_service" =~ ^[Yy]$ ]]; then
    systemctl start cashflow.service
    echo "✅ Služba spuštěna"
    sleep 2
    systemctl status cashflow.service --no-pager
fi

echo ""
echo "================================================"
echo "  ✅ Instalace dokončena!"
echo "================================================"
echo ""
echo "📋 Užitečné příkazy:"
echo "  • Spustit službu:     systemctl start cashflow"
echo "  • Zastavit službu:    systemctl stop cashflow"
echo "  • Restart služby:     systemctl restart cashflow"
echo "  • Status služby:      systemctl status cashflow"
echo "  • Logy služby:        journalctl -u cashflow -f"
echo "  • Povolit při startu: systemctl enable cashflow"
echo "  • Zakázat při startu: systemctl disable cashflow"
echo ""
echo "🌐 Aplikace běží na: http://$(hostname -I | awk '{print $1}'):8888"
echo ""
