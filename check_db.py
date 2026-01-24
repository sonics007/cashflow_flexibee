import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'data', 'cashflow.db')
if not os.path.exists(DB_FILE):
    print("DB FILE NOT FOUND")
    exit()

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(transactions)")
    cols = cursor.fetchall()
    print("Columns:", [c[1] for c in cols])
    
    cursor.execute("SELECT count(*) FROM transactions")
    print("Count:", cursor.fetchone()[0])
    
    conn.close()
except Exception as e:
    print("Error:", e)
