"""
Reset admin password in database
Použitie: python reset_admin_password.py
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_FILE = os.path.join(DB_DIR, 'cashflow.db')

def reset_admin_password(new_password='admin123'):
    """Reset admin password to default"""
    
    if not os.path.exists(DB_FILE):
        print(f"❌ Databáza neexistuje: {DB_FILE}")
        return False
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if not admin:
            print("❌ Admin užívateľ neexistuje v databáze!")
            print("Vytváram nového admin užívateľa...")
            
            # Create admin user with hashed password
            hashed_password = generate_password_hash(new_password)
            cursor.execute(
                "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
                ('admin', hashed_password, 'Administrator', 'admin')
            )
            conn.commit()
            print(f"✅ Admin užívateľ vytvorený!")
            print(f"   Užívateľské meno: admin")
            print(f"   Heslo: {new_password}")
        else:
            print(f"✅ Admin užívateľ nájdený")
            print(f"   Aktuálne heslo v DB: {admin[1][:50]}...")
            
            # Check if password is already hashed
            if admin[1].startswith('pbkdf2:') or admin[1].startswith('scrypt:'):
                print("   ℹ️  Heslo je už hashované")
                response = input("   Chcete ho resetovať? (y/n): ")
                if response.lower() != 'y':
                    print("   Zrušené.")
                    conn.close()
                    return False
            else:
                print("   ⚠️  Heslo NIE JE hashované (plain text)!")
            
            # Update password with hash
            hashed_password = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password = ? WHERE username = 'admin'",
                (hashed_password,)
            )
            conn.commit()
            print(f"✅ Heslo resetované!")
            print(f"   Užívateľské meno: admin")
            print(f"   Nové heslo: {new_password}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("  RESET ADMIN HESLA")
    print("="*60)
    print()
    
    # Možnosť zadať vlastné heslo
    custom_password = input("Zadajte nové heslo (Enter = 'admin123'): ").strip()
    if not custom_password:
        custom_password = 'admin123'
    
    print()
    success = reset_admin_password(custom_password)
    
    print()
    print("="*60)
    if success:
        print("✅ HOTOVO!")
        print()
        print("Teraz sa môžete prihlásiť:")
        print(f"  Užívateľské meno: admin")
        print(f"  Heslo: {custom_password}")
    else:
        print("❌ ZLYHALO!")
    print("="*60)
