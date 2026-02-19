"""
Database wrapper - provides same interface as JSON functions but uses SQLite
Import this instead of using JSON files directly
"""
from database import get_db
import json

def load_transactions():
    """Load transactions from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY date")
    transactions = []
    for row in cursor.fetchall():
        # Use dict-style access (row_factory = sqlite3.Row)
        t = dict(row)
        transactions.append({
            "id": t.get("id"),
            "date": t.get("date"),
            "type": t.get("type"),
            "amount": t.get("amount"),
            "text": t.get("text") or "",
            "supplier": t.get("supplier") or "",
            "customer": t.get("customer") or "",
            "var_symbol": t.get("var_symbol") or "",
            "description": t.get("description") or "",
            "payment_status": t.get("payment_status") or "",
            "created_by": t.get("created_by"),
            "created_at": t.get("created_at"),
            "modified_at": t.get("modified_at"),
            "original_due_date": t.get("original_due_date") or t.get("date"),
            "source_file": t.get("source_file") or ""
        })
    conn.close()
    return transactions

def save_transactions(transactions):
    """Save transactions to database"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Clear existing
    cursor.execute("DELETE FROM transactions")
    
    # Insert all
    for t in transactions:
        cursor.execute('''
            INSERT INTO transactions 
            (id, date, type, amount, text, supplier, customer, var_symbol, 
             description, payment_status, created_by, created_at, modified_at, original_due_date, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            t.get('modified_at'),
            t.get('original_due_date'),
            t.get('source_file', '')
        ))
    
    conn.commit()
    conn.close()

def get_initial_balance():
    """Get initial balance from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'initial_balance'")
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row else 0.0

def set_initial_balance(balance):
    """Set initial balance in database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value)
        VALUES ('initial_balance', ?)
    ''', (str(balance),))
    conn.commit()
    conn.close()

def load_users():
    """Load users from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, name, role FROM users")
    users = {}
    for row in cursor.fetchall():
        users[row[0]] = {
            "password": row[1],
            "name": row[2],
            "role": row[3]
        }
    conn.close()
    return users if users else {"admin": {"password": "scrypt:32768:8:1$uI1Jw4eAQ0oPbCtA$73dbc7b20585f583a37fba6427cd61bb3093edab90c8fc102dfbb39f02fdc22745fce4cc1187a31113394c8079f5134da47c531cafcb741dad6fd08f9f85af9b", "role": "admin", "name": "Administrátor"}}

def save_users(users):
    """Save users to database"""
    conn = get_db()
    cursor = conn.cursor()
    for username, data in users.items():
        cursor.execute('''
            INSERT OR REPLACE INTO users (username, password, name, role)
            VALUES (?, ?, ?, ?)
        ''', (username, data['password'], data['name'], data['role']))
    conn.commit()
    conn.close()

def log_audit(action, details, username='system'):
    """Log audit entry to database"""
    from datetime import datetime
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_log (timestamp, username, action, details)
        VALUES (?, ?, ?, ?)
    ''', (datetime.now().isoformat(), username, action, json.dumps(details)))
    conn.commit()
    conn.close()

def get_audit_log(limit=50):
    """Retrieve audit logs from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, username, action, details FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
    logs = []
    for row in cursor.fetchall():
        logs.append({
            "timestamp": row[0],
            "username": row[1],
            "action": row[2],
            "details": json.loads(row[3]) if row[3] else {}
        })
    conn.close()
    return logs
