"""
Script to convert app.py from JSON to SQLite
"""
import re

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add database import at the top
if 'from database import' not in content:
    content = content.replace(
        'from functools import wraps',
        'from functools import wraps\nfrom database import get_db, init_db'
    )

# Remove JSON file paths
content = re.sub(
    r"TRANSACTIONS_FILE = .*?\n",
    "",
    content
)
content = re.sub(
    r"INITIAL_BALANCE_FILE = .*?\n",
    "",
    content
)
content = re.sub(
    r"USERS_FILE = .*?\n",
    "",
    content
)
content = re.sub(
    r"AUDIT_LOG_FILE = .*?\n",
    "",
    content
)

# Add init_db() call
if 'init_db()' not in content:
    content = content.replace(
        "os.makedirs(DATA_DIR, exist_ok=True)",
        "os.makedirs(DATA_DIR, exist_ok=True)\n\n# Initialize database\ninit_db()"
    )

# Replace load_users function
old_load_users = r'''def load_users\(\):
    if os\.path\.exists\(USERS_FILE\):
        with open\(USERS_FILE, 'r', encoding='utf-8'\) as f:
            return json\.load\(f\)
    # Default admin user
    return \{
        "admin": \{"password": "admin123", "role": "admin", "name": "Administrátor"\}
    \}'''

new_load_users = '''def load_users():
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
    return users'''

content = re.sub(old_load_users, new_load_users, content, flags=re.DOTALL)

# Replace save_users function
old_save_users = r'''def save_users\(users\):
    with open\(USERS_FILE, 'w', encoding='utf-8'\) as f:
        json\.dump\(users, f, indent=4, ensure_ascii=False\)'''

new_save_users = '''def save_users(users):
    """Save users to database"""
    conn = get_db()
    cursor = conn.cursor()
    for username, data in users.items():
        cursor.execute(\'\'\'
            INSERT OR REPLACE INTO users (username, password, name, role)
            VALUES (?, ?, ?, ?)
        \'\'\', (username, data['password'], data['name'], data['role']))
    conn.commit()
    conn.close()'''

content = re.sub(old_save_users, new_save_users, content)

# Write back
with open('app_new.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Created app_new.py with database support")
print("Review the file and then rename it to app.py")
