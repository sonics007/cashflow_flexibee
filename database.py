import sqlite3
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_FILE = os.path.join(DB_DIR, 'cashflow.db')
BACKUP_DIR = os.path.join(DB_DIR, 'backups')
CONFIG_FILE = os.path.join(DB_DIR, 'backup_config.json')

# Create directories
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            text TEXT,
            supplier TEXT,
            customer TEXT,
            var_symbol TEXT,
            description TEXT,
            payment_status TEXT,
            created_by TEXT,
            created_at TEXT,
            modified_at TEXT,
            original_due_date TEXT,
            source_file TEXT
        )
    ''')
    
    # Migration: Add original_due_date if missing
    try:
        cursor.execute("SELECT original_due_date FROM transactions LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE transactions ADD COLUMN original_due_date TEXT")
        print("Migrated DB: Added original_due_date column")
    
    # Migration: Add source_file if missing
    try:
        cursor.execute("SELECT source_file FROM transactions LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE transactions ADD COLUMN source_file TEXT")
        print("Migrated DB: Added source_file column")
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # Audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT
        )
    ''')
    
    # Check if admin exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # Import password hashing
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash('admin')
        cursor.execute(
            "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
            ('admin', hashed_password, 'Administrator', 'admin')
        )
    
    # Set default initial balance if not exists
    cursor.execute("SELECT * FROM settings WHERE key = 'initial_balance'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES ('initial_balance', '0')")
    
    conn.commit()
    conn.close()

def create_backup():
    """Create database backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'backup_{timestamp}.db')
    
    try:
        shutil.copy2(DB_FILE, backup_file)
        return backup_file
    except Exception as e:
        print(f"Backup error: {e}")
        return None

def restore_backup(backup_file):
    """Restore database from backup"""
    try:
        if os.path.exists(backup_file):
            # Create safety backup before restore
            safety_backup = os.path.join(BACKUP_DIR, f'before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            shutil.copy2(DB_FILE, safety_backup)
            
            # Restore
            shutil.copy2(backup_file, DB_FILE)
            return True
        return False
    except Exception as e:
        print(f"Restore error: {e}")
        return False

def get_backups():
    """Get list of available backups"""
    backups = []
    if os.path.exists(BACKUP_DIR):
        for file in os.listdir(BACKUP_DIR):
            if file.endswith('.db'):
                filepath = os.path.join(BACKUP_DIR, file)
                stat = os.stat(filepath)
                backups.append({
                    'filename': file,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    return sorted(backups, key=lambda x: x['created'], reverse=True)

def load_backup_config():
    """Load backup configuration"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'enabled': False,
        'interval_hours': 24,
        'max_backups': 30
    }

def save_backup_config(config):
    """Save backup configuration"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def cleanup_old_backups(max_backups=30):
    """Remove old backups, keep only max_backups newest"""
    backups = get_backups()
    if len(backups) > max_backups:
        for backup in backups[max_backups:]:
            try:
                os.remove(os.path.join(BACKUP_DIR, backup['filename']))
            except:
                pass

# Initialize database on import
init_db()
