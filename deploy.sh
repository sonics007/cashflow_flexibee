#!/bin/bash
# Deploy script - copies only necessary files to server
# Usage: ./deploy.sh user@server:/path/to/destination

if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh user@server:/path/to/destination"
    exit 1
fi

DEST=$1

echo "=========================================="
echo "Deploying Cashflow to: $DEST"
echo "=========================================="
echo ""

# Create list of files to deploy
FILES=(
    "app.py"
    "database.py"
    "db_wrapper.py"
    "flexibee_sync.py"
    "flexibee_rate_limiter.py"
    "flexibee_webhooks.py"
    "reset_admin_password.py"
    "run.sh"
    "install.sh"
    "install_service.sh"
    "cashflow.service"
    "README_LINUX.md"
    "FLEXIBEE_NAPOVEDA.md"
    "FLEXIBEE_RATE_LIMITING.md"
    "FLEXIBEE_IMPORT_DATE.md"
    "INTEGRATION_INSTRUCTIONS.md"
    "PROJECT_STRUCTURE.md"
)

DIRS=(
    "templates"
    "static"
)

echo "Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  ✓ $file"
done

echo ""
echo "Directories to deploy:"
for dir in "${DIRS[@]}"; do
    echo "  ✓ $dir/"
done

echo ""
read -p "Continue with deployment? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 0
fi

# Deploy files
echo ""
echo "Deploying files..."

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        scp "$file" "$DEST/"
        echo "  ✓ Deployed: $file"
    else
        echo "  ⚠ Skipped (not found): $file"
    fi
done

# Deploy directories
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        scp -r "$dir" "$DEST/"
        echo "  ✓ Deployed: $dir/"
    else
        echo "  ⚠ Skipped (not found): $dir/"
    fi
done

echo ""
echo "=========================================="
echo "✅ Deployment completed!"
echo "=========================================="
echo ""
echo "Next steps on the server:"
echo "1. cd $DEST"
echo "2. chmod +x run.sh install.sh install_service.sh"
echo "3. ./install.sh"
echo "4. sudo ./install_service.sh"
echo ""
