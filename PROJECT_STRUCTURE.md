# 📁 Cashflow Project Structure - Linux Deployment

## ✅ Essential Files (KEEP)

### Core Application
- `app.py` - Main Flask application
- `database.py` - Database schema and initialization
- `db_wrapper.py` - Database abstraction layer

### FlexiBee Integration
- `flexibee_sync.py` - FlexiBee synchronization logic
- `flexibee_rate_limiter.py` - Rate limiting for FlexiBee API
- `flexibee_webhooks.py` - Webhook handler (optional)

### Linux Deployment
- `run.sh` - Start script for Linux
- `install.sh` - Installation script
- `install_service.sh` - Systemd service installer
- `cashflow.service` - Systemd service configuration

### Utilities
- `reset_admin_password.py` - Reset admin password if locked out

### Documentation
- `README_LINUX.md` - Linux deployment guide
- `FLEXIBEE_NAPOVEDA.md` - FlexiBee help (Czech)
- `FLEXIBEE_RATE_LIMITING.md` - Rate limiting documentation
- `FLEXIBEE_IMPORT_DATE.md` - Import date feature docs
- `INTEGRATION_INSTRUCTIONS.md` - Integration guide

### Directories
- `templates/` - HTML templates
- `static/` - CSS, JS, images
- `data/` - Database and config files (created at runtime)

---

## ❌ Files to REMOVE (Windows/Debug/Obsolete)

### Windows-specific
- `run.bat` - Windows batch script

### Obsolete
- `app_old.py` - Old version of app
- `To` - Unknown file

### Debug/Test Scripts (not needed in production)
- `find_company_code.py`
- `find_flexibee_companies.py`
- `flexibee_login.py`
- `get_companies.py`
- `simple_test.py`
- `test_connection.py`
- `test_flexibee_config.py`
- `test_new_endpoint.py`

### Migration Scripts (already migrated)
- `convert_to_sqlite.py`
- `migrate_to_db.py`

### Optional (can remove if not needed)
- `test_clean_company.py` - Test for company name cleaning
- `test_import_date.py` - Test for import date feature
- `check_db.py` - Database checker
- `restore_user.py` - User restore utility
- `init_db_quick.py` - Quick DB init

---

## 🚀 How to Clean Up

### Option 1: Automated (Recommended)
```bash
chmod +x cleanup.sh
./cleanup.sh
```

### Option 2: Manual
```bash
# Remove Windows files
rm run.bat

# Remove obsolete files
rm app_old.py To

# Remove debug scripts
rm find_company_code.py find_flexibee_companies.py flexibee_login.py
rm get_companies.py simple_test.py test_connection.py
rm test_flexibee_config.py test_new_endpoint.py

# Remove migration scripts
rm convert_to_sqlite.py migrate_to_db.py

# Optional: Remove test files
rm test_clean_company.py test_import_date.py

# Optional: Remove utility scripts
rm check_db.py restore_user.py init_db_quick.py

# Clean Python cache
rm -rf __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## 📦 Minimal Production Setup

After cleanup, your directory should contain:

```
cashflow_app_v2/
├── app.py                          # Main app
├── database.py                     # DB schema
├── db_wrapper.py                   # DB wrapper
├── flexibee_sync.py                # FlexiBee sync
├── flexibee_rate_limiter.py        # Rate limiter
├── flexibee_webhooks.py            # Webhooks
├── reset_admin_password.py         # Admin reset
├── run.sh                          # Start script
├── install.sh                      # Install script
├── install_service.sh              # Service installer
├── cashflow.service                # Systemd config
├── README_LINUX.md                 # Docs
├── FLEXIBEE_*.md                   # FlexiBee docs
├── INTEGRATION_INSTRUCTIONS.md     # Integration docs
├── templates/                      # HTML templates
│   ├── index.html
│   ├── login.html
│   ├── settings_modal.html
│   └── flexibee_help.html
├── static/                         # Static files
│   ├── style.css
│   ├── script.js
│   ├── flexibee.js
│   └── favicon.ico
└── data/                           # Runtime data (auto-created)
    ├── cashflow.db
    ├── flexibee_config.json
    └── backups/
```

---

## 🔧 After Cleanup

1. **Test the application:**
   ```bash
   python3 app.py
   ```

2. **Login with default credentials:**
   - Username: `admin`
   - Password: `admin`
   - ⚠️ Change password immediately after first login!

3. **Install as service:**
   ```bash
   sudo ./install_service.sh
   ```

4. **Check service status:**
   ```bash
   sudo systemctl status cashflow
   ```

---

## 📊 Disk Space Saved

Approximate space saved after cleanup:
- Debug scripts: ~20 KB
- Migration scripts: ~6 KB
- Windows files: ~1 KB
- Python cache: varies
- **Total: ~30-50 KB**

Not much, but keeps the project clean and organized! 🧹
