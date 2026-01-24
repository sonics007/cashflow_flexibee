from database import get_db

conn = get_db()
cursor = conn.cursor()

# Check and add admin user if not exists
cursor.execute("SELECT * FROM users WHERE username = 'admin'")
if not cursor.fetchone():
    cursor.execute('''
        INSERT INTO users (username, password, name, role)
        VALUES ('admin', 'admin123', 'Administrátor', 'admin')
    ''')
    print("✓ Admin user created")
else:
    print("✓ Admin user exists")

# Check initial balance
cursor.execute("SELECT * FROM settings WHERE key = 'initial_balance'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO settings (key, value) VALUES ('initial_balance', '0')")
    print("✓ Initial balance set to 0")
else:
    print("✓ Initial balance exists")

# Check transactions
cursor.execute("SELECT COUNT(*) FROM transactions")
count = cursor.fetchone()[0]
print(f"✓ Transactions in DB: {count}")

conn.commit()
conn.close()

print("\n✅ Database initialized successfully!")
