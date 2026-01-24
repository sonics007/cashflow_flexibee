"""
Migration script to convert JSON data to SQLite database
Run this once to migrate existing data
"""
import json
import os
from database import get_db

DATA_DIR = 'data'
TRANSACTIONS_FILE = os.path.join(DATA_DIR, 'transactions.json')
BALANCE_FILE = os.path.join(DATA_DIR, 'balance.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
AUDIT_FILE = os.path.join(DATA_DIR, 'audit_log.json')

def migrate():
    conn = get_db()
    cursor = conn.cursor()
    
    print("Starting migration...")
    
    # Migrate transactions
    if os.path.exists(TRANSACTIONS_FILE):
        print("Migrating transactions...")
        with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
            transactions = json.load(f)
            for t in transactions:
                cursor.execute('''
                    INSERT OR REPLACE INTO transactions 
                    (id, date, type, amount, text, supplier, customer, var_symbol, 
                     description, payment_status, created_by, created_at, modified_by, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    t.get('id'),
                    t.get('date'),
                    t.get('type'),
                    t.get('amount'),
                    t.get('text'),
                    t.get('supplier'),
                    t.get('customer'),
                    t.get('var_symbol'),
                    t.get('description'),
                    t.get('payment_status'),
                    t.get('created_by'),
                    t.get('created_at'),
                    t.get('modified_by'),
                    t.get('modified_at')
                ))
        print(f"✓ Migrated {len(transactions)} transactions")
    
    # Migrate balance
    if os.path.exists(BALANCE_FILE):
        print("Migrating balance...")
        with open(BALANCE_FILE, 'r', encoding='utf-8') as f:
            balance = json.load(f)
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES ('initial_balance', ?)",
                (str(balance.get('initial_balance', 0)),)
            )
        print("✓ Migrated balance")
    
    # Migrate users
    if os.path.exists(USERS_FILE):
        print("Migrating users...")
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            for username, data in users.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO users (username, password, name, role)
                    VALUES (?, ?, ?, ?)
                ''', (username, data['password'], data['name'], data['role']))
        print(f"✓ Migrated {len(users)} users")
    
    # Migrate audit log
    if os.path.exists(AUDIT_FILE):
        print("Migrating audit log...")
        with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            for log in logs:
                cursor.execute('''
                    INSERT INTO audit_log (timestamp, username, action, details)
                    VALUES (?, ?, ?, ?)
                ''', (
                    log.get('timestamp'),
                    log.get('username'),
                    log.get('action'),
                    json.dumps(log.get('details', {}))
                ))
        print(f"✓ Migrated {len(logs)} audit log entries")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    print("\nOld JSON files are still in data/ folder.")
    print("You can delete them manually after verifying the migration.")

if __name__ == '__main__':
    migrate()
