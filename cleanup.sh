#!/bin/bash
# Cleanup script - removes unnecessary files for Linux deployment
# Run this script to clean up the project directory

echo "=========================================="
echo "Cashflow Cleanup Script for Linux"
echo "=========================================="
echo ""

# Files to remove
FILES_TO_REMOVE=(
    "run.bat"
    "app_old.py"
    "To"
    "find_company_code.py"
    "find_flexibee_companies.py"
    "flexibee_login.py"
    "get_companies.py"
    "simple_test.py"
    "test_connection.py"
    "test_flexibee_config.py"
    "test_new_endpoint.py"
    "convert_to_sqlite.py"
    "migrate_to_db.py"
)

# Optional files (ask user)
OPTIONAL_FILES=(
    "test_clean_company.py"
    "test_import_date.py"
    "check_db.py"
    "restore_user.py"
    "init_db_quick.py"
)

echo "The following files will be REMOVED:"
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done

echo ""
echo "The following files are OPTIONAL (utility/test scripts):"
for file in "${OPTIONAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done

echo ""
read -p "Do you want to remove the main files? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    for file in "${FILES_TO_REMOVE[@]}"; do
        if [ -f "$file" ]; then
            rm "$file"
            echo "✓ Removed: $file"
        fi
    done
    echo ""
    echo "✅ Main cleanup completed!"
else
    echo "❌ Cleanup cancelled."
    exit 0
fi

echo ""
read -p "Do you want to remove optional files too? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    for file in "${OPTIONAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            rm "$file"
            echo "✓ Removed: $file"
        fi
    done
    echo ""
    echo "✅ Optional cleanup completed!"
fi

# Clean __pycache__
if [ -d "__pycache__" ]; then
    echo ""
    read -p "Do you want to remove __pycache__? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf __pycache__
        echo "✓ Removed: __pycache__"
    fi
fi

echo ""
echo "=========================================="
echo "Cleanup finished!"
echo "=========================================="
