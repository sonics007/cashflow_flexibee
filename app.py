from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import pandas as pd
import os
import json
from datetime import datetime
import uuid
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import schedule
import time
import threading

# Import database wrapper - these override JSON functions below
from db_wrapper import (
    load_transactions, save_transactions, 
    get_initial_balance, set_initial_balance,
    load_users, save_users,
    log_audit, get_audit_log
)

# Optional: Import webhook handler for real-time FlexiBee sync
# Uncomment the following line to enable webhooks:
# from flexibee_webhooks import init_webhooks

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this!
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

TRANSACTIONS_FILE = os.path.join(DATA_DIR, 'transactions.json')
INITIAL_BALANCE_FILE = os.path.join(DATA_DIR, 'balance.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
AUDIT_LOG_FILE = os.path.join(DATA_DIR, 'audit_log.json')

# --- User Management ---

# --- User Management ---
# Functions load_users and save_users are imported from db_wrapper (SQLite)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Old log_audit function - now using db_wrapper version
# def log_audit(action, details, username=None):
#     """Log user actions for audit trail"""
#     if username is None:
#         username = session.get('username', 'system')
#     
#     audit_logs = []
#     if os.path.exists(AUDIT_LOG_FILE):
#         with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
#             audit_logs = json.load(f)
#     
#     audit_logs.append({
#         "timestamp": datetime.now().isoformat(),
#         "username": username,
#         "action": action,
#         "details": details
#     })
#     
#     with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
#         json.dump(audit_logs, f, indent=4, ensure_ascii=False)

def load_data():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(TRANSACTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_initial_balance():
    if os.path.exists(INITIAL_BALANCE_FILE):
        with open(INITIAL_BALANCE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get('balance', 0.0)
    return 0.0

def save_initial_balance(balance):
    with open(INITIAL_BALANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump({'balance': float(balance)}, f)

# --- Routes ---

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session.get('username'), user_name=session.get('name'))

@app.route('/flexibee/help')
def flexibee_help():
    """FlexiBee integration help page"""
    return render_template('flexibee_help.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    users = load_users()
    
    if username in users and check_password_hash(users[username]['password'], password):
        session['username'] = username
        session['name'] = users[username].get('name', username)
        session['role'] = users[username].get('role', 'user')
        log_audit("login", {"username": username})
        return jsonify({"status": "success", "name": session['name']})
    
    return jsonify({"status": "error", "message": "Nesprávné přihlašovací údaje"}), 401

@app.route('/logout')
def logout_page():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/api/logout', methods=['POST'])
def logout():
    username = session.get('username')
    log_audit("logout", {"username": username})
    session.clear()
    return jsonify({"status": "success"})

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    # Removed admin check
    
    users = load_users()
    user_list = [{"username": u, "name": users[u].get('name'), "role": users[u].get('role')} for u in users]
    return jsonify({"users": user_list})

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    # Removed admin check
    
    data = request.json
    users = load_users()
    
    username = data.get('username')
    if username in users:
        return jsonify({"status": "error", "message": "Uživatel již existuje"}), 400
    
    users[username] = {
        "password": generate_password_hash(data.get('password', 'password123')),
        "name": data.get('name', username),
        "role": data.get('role', 'user')
    }
    
    save_users(users)
    log_audit("create_user", {"username": username, "by": session.get('username')})
    return jsonify({"status": "success"})

@app.route('/api/users/<username>', methods=['PUT'])
@login_required
def update_user(username):
    # Removed admin check
    
    data = request.json
    users = load_users()
    
    if username not in users:
        return jsonify({"status": "error", "message": "Uživatel neexistuje"}), 404
    
    if 'password' in data:
        users[username]['password'] = generate_password_hash(data['password'])
    if 'name' in data:
        users[username]['name'] = data['name']
    if 'role' in data:
        users[username]['role'] = data['role']
    
    save_users(users)
    log_audit("update_user", {"username": username, "by": session.get('username')})
    return jsonify({"status": "success"})

@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def delete_user(username):
    # Removed admin check
    
    if username == 'admin':
        return jsonify({"status": "error", "message": "Nelze smazat admin účet"}), 400
    
    users = load_users()
    
    if username not in users:
        return jsonify({"status": "error", "message": "Uživatel neexistuje"}), 404
    
    del users[username]
    save_users(users)
    log_audit("delete_user", {"username": username, "by": session.get('username')})
    return jsonify({"status": "success"})


@app.route('/api/init', methods=['POST'])
@login_required
def init_data():
    """Generates sample data if none exists or resets it."""
    mock_data = [
        {"id": str(uuid.uuid4()), "date": "2026-05-10", "type": "prijem", "amount": 5000, "text": "Faktúra 101 - Klient A", "created_by": session.get('username'), "created_at": datetime.now().isoformat()},
        {"id": str(uuid.uuid4()), "date": "2026-05-12", "type": "vydaj", "amount": -1200, "text": "Nájom", "created_by": session.get('username'), "created_at": datetime.now().isoformat()},
        {"id": str(uuid.uuid4()), "date": "2026-05-15", "type": "vydaj", "amount": -4500, "text": "Mzdy", "created_by": session.get('username'), "created_at": datetime.now().isoformat()},
        {"id": str(uuid.uuid4()), "date": "2026-05-20", "type": "prijem", "amount": 3000, "text": "Faktúra 102 - Klient B", "created_by": session.get('username'), "created_at": datetime.now().isoformat()},
    ]
    save_data(mock_data)
    save_initial_balance(1000)
    log_audit("init_data", {"count": len(mock_data)})
    return jsonify({"status": "initialized"})

@app.route('/api/initial_balance', methods=['POST'])
@login_required
def initial_balance_endpoint():
    try:
        data = request.json
        amount = data.get('amount')
        if amount is None:
             return jsonify({"status": "error", "message": "Missing amount"}), 400
        
        set_initial_balance(amount)
        log_audit("update_initial_balance", {"amount": amount, "by": session.get('username')})
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    try:
        # Create vstupy directories
        vstupy_dir = os.path.join(DATA_DIR, 'vstupy')
        prijate_dir = os.path.join(vstupy_dir, 'prijate')
        vydane_dir = os.path.join(vstupy_dir, 'vydane')
        
        os.makedirs(prijate_dir, exist_ok=True)
        os.makedirs(vydane_dir, exist_ok=True)
        
        uploaded_files = []
        duplicates_summary = []
        # Load existing transactions from DATABASE
        transactions = load_transactions()
        imported_count = 0
        errors = []
        
        # Track existing VS to prevent duplicates - GLOBAL for both file types
        existing_vs = set()
        for t in transactions:
            if t.get('var_symbol'):
                existing_vs.add(str(t.get('var_symbol')).strip())
        
        duplicates = []
        
        if 'prijate' in request.files:
            file = request.files['prijate']
            if file.filename:
                # Save to vstupy/prijate
                filepath = os.path.join(prijate_dir, file.filename)
                try:
                    file.save(filepath)
                except PermissionError:
                    return jsonify({"status": "error", "message": f"Soubor '{file.filename}' nelze přepsat, protože je otevřen v jiném programu. Zavřete jej."}), 400

                uploaded_files.append(f"prijate/{file.filename}")
                
                # Parse XLSX and import data
                try:
                    df = pd.read_excel(filepath)
                    
                    # DEBUG: Log column structure
                    print(f"Prijate: Načteno {len(df)} řádků, {len(df.columns)} sloupců")
                    print(f"Hlavičky: {df.columns.tolist()}")
                    if len(df) > 0:
                        print(f"První řádek: {df.iloc[0].tolist()}")
                    
                    # existing_vs and duplicates initialized above



                    for idx, row in df.iterrows():
                        try:
                            # Column mapping based on actual Excel structure:
                            # A (0): Variabilní symbol
                            # B (1): Datum přijetí
                            # C (2): Splatnost (THIS IS THE DATE WE WANT)
                            # D (3): Název firmy nebo jméno osoby
                            # E (4): Popis
                            # F (5): Celkem [Kč]
                            # G (6): Stav úhrady dokladu
                            
                            # Try column names first, fallback to indices
                            var_symbol = ""
                            for col in ['Variabilní symbol', 'VS']:
                                if col in row.index and pd.notna(row.get(col)):
                                    var_symbol = str(row.get(col)).strip()
                                    break
                            if not var_symbol and len(row) > 0:
                                var_symbol = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                            
                            # DUPLICATE CHECK
                            if var_symbol and var_symbol in existing_vs:
                                duplicates.append(var_symbol)
                                continue 

                            # Use SPLATNOST (due date) as the main date
                            date_val = None
                            for col in ['Splatnost', 'Datum splatnosti']:
                                if col in row.index and pd.notna(row.get(col)):
                                    date_val = row.get(col)
                                    break
                            if date_val is None and len(row) > 2:
                                date_val = row.iloc[2] if pd.notna(row.iloc[2]) else None
                            
                            supplier = ""
                            for col in ['Název firmy nebo jméno osoby', 'Název firmy', 'Firma']:
                                if col in row.index and pd.notna(row.get(col)):
                                    supplier = str(row.get(col))
                                    break
                            if not supplier and len(row) > 3:
                                supplier = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""
                            
                            desc_val = ""
                            for col in ['Popis', 'Description']:
                                if col in row.index and pd.notna(row.get(col)):
                                    desc_val = str(row.get(col))
                                    break
                            if not desc_val and len(row) > 4:
                                desc_val = str(row.iloc[4]) if pd.notna(row.iloc[4]) else ""
                            
                            amount_val = None
                            for col in ['Celkem [Kč]', 'Celkem', 'Částka']:
                                if col in row.index and pd.notna(row.get(col)):
                                    amount_val = row.get(col)
                                    break
                            if amount_val is None and len(row) > 5:
                                amount_val = row.iloc[5]
                            
                            raw_st = ""
                            for col in ['Stav úhrady dokladu', 'Stav úhrady', 'Stav']:
                                if col in row.index and pd.notna(row.get(col)):
                                    raw_st = str(row.get(col))
                                    break
                            if not raw_st and len(row) > 6:
                                raw_st = str(row.iloc[6]) if pd.notna(row.iloc[6]) else ""
                            
                            payment_status = 'zaplaceno' if 'uhrazeno' in raw_st.lower() or 'zaplaceno' in raw_st.lower() else 'nezaplaceno'
                            
                            if pd.notna(date_val) and pd.notna(amount_val) and amount_val != 0:
                                try:
                                    date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d') if not isinstance(date_val, str) else date_val
                                except:
                                    if idx < 3:
                                        errors.append(f"Row {idx}: Chyba parsování data '{date_val}'")
                                    continue
                                
                                try:
                                    amount = abs(float(amount_val))  # Always positive, will be negated below
                                except:
                                    if idx < 3:
                                        errors.append(f"Row {idx}: Chyba parsování částky '{amount_val}'")
                                    continue
                                
                                # Build text from available data
                                full_text = ""
                                if supplier:
                                    full_text = supplier
                                if desc_val:
                                    full_text = f"{full_text} - {desc_val}".strip(" -")
                                if var_symbol:
                                    full_text = f"VS:{var_symbol} {full_text}".strip()
                                    existing_vs.add(var_symbol)
                                
                                # If no text, use generic description
                                if not full_text:
                                    full_text = f"Výdaj {date_str}"
                                
                            
                                transactions.append({
                                    "id": str(uuid.uuid4()),
                                    "date": date_str,
                                    "type": "Výdaj",
                                    "amount": -amount,  # Negative for expense
                                    "text": full_text,
                                    "supplier": supplier or "",
                                    "customer": "",
                                    "var_symbol": var_symbol or "",
                                    "description": desc_val or "",
                                    "payment_status": payment_status,
                                    "created_by": session.get('username'),
                                    "created_at": datetime.now().isoformat(),
                                    "modified_by": None,
                                    "modified_at": None,
                                    "original_due_date": date_str
                                })
                                imported_count += 1
                            else:
                                if idx < 3:
                                    errors.append(f"Row {idx}: Chybí datum nebo částka (datum={date_val}, částka={amount_val})")

                        except Exception as row_error:
                            if idx < 3:
                                errors.append(f"Row {idx}: {str(row_error)}")
                            continue
                            
                except Exception as e:
                    log_audit("upload_file_error", {"type": "prijate", "filename": file.filename, "error": str(e)})
                    print(f"Import Error Prijate: {e}")

                # Append info about duplicates to log or session if possible, but for now we just log
                if duplicates:
                     print(f"Skipped {len(duplicates)} duplicates: {duplicates}")
                     duplicates_summary.append(f"Přeskočeno {len(duplicates)} duplicitních faktur (VS: {', '.join(duplicates[:3])}...)")

                log_audit("upload_file", {"type": "prijate", "filename": file.filename, "imported": imported_count})
            
            # Reset duplicates for next file
            duplicates = []
            
        if 'vydane' in request.files:
            file = request.files['vydane']
            if file.filename:
                # Save to vstupy/vydane
                filepath = os.path.join(vydane_dir, file.filename)
                try:
                    file.save(filepath)
                except PermissionError:
                    return jsonify({"status": "error", "message": f"Soubor '{file.filename}' nelze přepsat, protože je otevřen v jiném programu. Zavřete jej."}), 400

                uploaded_files.append(f"vydane/{file.filename}")
                
                try:
                    df = pd.read_excel(filepath)
                    
                    # Debug logging
                    if len(df) == 0:
                        errors.append(f"Vydane: Soubor je prázdný (0 řádků)")
                    else:
                        errors.append(f"Vydane: Načteno {len(df)} řádků, {len(df.columns)} sloupců. Hlavičky: {list(df.columns)}")
                    
                    for idx, row in df.iterrows():
                        try:
                            # Actual file structure (with headers):
                            # A (0): Datum vytvoření (Date created)
                            # Column mapping for issued invoices
                            # Expected columns: Splatnost, Variabilní symbol, Název firmy nebo jméno osoby, Celkem bez záloh [Kč], Popis
                            date_val = row.get('Splatnost') or row.iloc[1] if len(row) > 1 else None
                            var_symbol = str(row.get('Variabilní symbol') or row.iloc[2]) if len(row) > 2 and pd.notna(row.get('Variabilní symbol') or row.iloc[2]) else ""
                            customer = str(row.get('Název firmy nebo jméno osoby') or row.iloc[3]) if len(row) > 3 and pd.notna(row.get('Název firmy nebo jméno osoby') or row.iloc[3]) else ""
                            amount_val = row.get('Celkem bez záloh [Kč]') or row.iloc[4] if len(row) > 4 else None
                            desc_val = str(row.get('Popis') or row.iloc[5]) if len(row) > 5 and pd.notna(row.get('Popis') or row.iloc[5]) else ""
                            
                            # DUPLICATE CHECK
                            if var_symbol and var_symbol in existing_vs:
                                duplicates.append(var_symbol)
                                continue

                            # Payment status is always 'zaplaceno' for issued invoices (income)
                            payment_status = 'zaplaceno'
                            
                            if pd.notna(date_val) and pd.notna(amount_val):
                                # Parse date
                                try:
                                    date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d') if not isinstance(date_val, str) else date_val
                                except:
                                    if idx < 3:
                                        errors.append(f"Vydane řádek {idx}: Chyba parsování data '{date_val}'")
                                    continue
                                
                                # Parse amount
                                try:
                                    amount = abs(float(amount_val))  # Always positive for income
                                except:
                                    if idx < 3:
                                        errors.append(f"Vydane řádek {idx}: Chyba parsování částky '{amount_val}'")
                                    continue
                                
                                # Construct text
                                full_text = f"{customer} - {desc_val}".strip(" -")
                                if var_symbol:
                                    full_text = f"VS:{var_symbol} {full_text}"
                                
                                transactions.append({
                                    "id": str(uuid.uuid4()),
                                    "date": date_str,
                                    "amount": amount,  # Positive for income
                                    "text": full_text,
                                    "description": desc_val,
                                    "customer": customer,
                                    "supplier": "",
                                    "var_symbol": var_symbol,
                                    "payment_status": payment_status,
                                    "type": "Příjem",
                                    "created_by": session.get('username'),
                                    "created_at": datetime.now().isoformat(),
                                    "modified_by": None,
                                    "modified_at": None,
                                    "original_due_date": date_str
                                })
                                if var_symbol:
                                    existing_vs.add(var_symbol)
                                imported_count += 1
                            else:
                                if idx < 3:  # Log first few skipped rows
                                    errors.append(f"Vydane řádek {idx}: Přeskočen (datum={date_val}, částka={amount_val})")
                        except Exception as row_error:
                            if idx < 5:  # Only log first few errors
                                errors.append(f"Row {idx} (Vydane): {str(row_error)}")
                            continue
                            
                except Exception as e:
                    log_audit("upload_file_error", {"type": "vydane", "filename": file.filename, "error": str(e)})
                    print(f"Import Error Vydane: {e}")
                
                log_audit("upload_file", {"type": "vydane", "filename": file.filename, "imported": imported_count})

                if duplicates:
                     print(f"Skipped {len(duplicates)} duplicates in Vydane: {duplicates}")
                     duplicates_summary.append(f"Vydané: Přeskočeno {len(duplicates)} duplicit (VS: {', '.join(duplicates[:3])}...)")
        
        # Save updated transactions to DATABASE
        save_transactions(transactions)
        
        final_message = f"Soubory nahrány: {', '.join(uploaded_files)}. Importováno {imported_count} transakcí."
        if duplicates_summary:
            final_message += " " + " ".join(duplicates_summary)
        if imported_count == 0 and errors:
            final_message += " Chyby: " + "; ".join(errors[:3])
            
        return jsonify({
            "status": "success", 
            "message": final_message,
            "files": uploaded_files,
            "imported": imported_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/restart_server', methods=['POST'])
@login_required
def restart_server():
    """Restart server"""
    # Removed admin check
    
    log_audit("restart_server", {"by": session.get('username')})
    
    import sys
    import os
    
    # Restart the server
    os.execv(sys.executable, ['python'] + sys.argv)
    
    return jsonify({"status": "success"})

@app.route('/api/backup/create', methods=['POST'])
@login_required
def create_backup_endpoint():
    """Create database backup"""
    # Removed admin check
    
    try:
        from database import create_backup
        backup_file = create_backup()
        if backup_file:
            log_audit("create_backup", {"by": session.get('username'), "file": os.path.basename(backup_file)})
            return jsonify({
                "status": "success",
                "message": "Záloha byla vytvořena",
                "filename": os.path.basename(backup_file)
            })
        else:
            return jsonify({"status": "error", "message": "Chyba při vytváření zálohy"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Duplicate list/download endpoints removed to avoid conflicts with later definitions

@app.route('/api/backup/restore', methods=['POST'])
@login_required
def restore_backup_endpoint():
    """Restore database from backup"""
    if session.get('role') != 'admin':
         # Allow non-admins for now if it's a single user app, or check config
         pass 
    
    try:
        from database import restore_backup, BACKUP_DIR
        
        if 'file' in request.files:
            # Upload and restore from uploaded file
            file = request.files['file']
            if not file or file.filename == '':
                return jsonify({"status": "error", "message": "Nebyl vybrán žádný soubor"}), 400
            
            if file.filename.endswith('.db'):
                temp_path = os.path.join(BACKUP_DIR, f'uploaded_{file.filename}')
                file.save(temp_path)
                
                if restore_backup(temp_path):
                    log_audit("restore_backup", {"by": session.get('username'), "source": "upload"})
                    return jsonify({"status": "success", "message": "Záloha byla úspěšně obnovena ze souboru."})
                else:
                    return jsonify({"status": "error", "message": "Obnova databáze selhala (vadný soubor?)"}), 500
            else:
                 return jsonify({"status": "error", "message": "Neplatný formát souboru (očekáváno .db)"}), 400

        elif 'filename' in request.json:
            # Restore from existing backup
            filename = request.json['filename']
            backup_path = os.path.join(BACKUP_DIR, filename)
            
            if not os.path.exists(backup_path):
                return jsonify({"status": "error", "message": "Soubor zálohy neexistuje"}), 404

            if restore_backup(backup_path):
                log_audit("restore_backup", {"by": session.get('username'), "source": filename})
                return jsonify({"status": "success", "message": "Záloha byla úspěšně obnovena."})
            else:
                return jsonify({"status": "error", "message": "Obnova databáze selhala"}), 500
        else:
            return jsonify({"status": "error", "message": "Chybí soubor nebo název zálohy"}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Kritická chyba: {str(e)}"}), 500

@app.route('/api/backup/config', methods=['GET', 'POST'])
@login_required
def backup_config():
    """Get or update backup configuration"""
    # Removed admin check
    
    try:
        from database import load_backup_config, save_backup_config
        
        if request.method == 'GET':
            config = load_backup_config()
            return jsonify(config)
        else:
            config = request.json
            save_backup_config(config)
            log_audit("update_backup_config", {"by": session.get('username'), "config": config})
            return jsonify({"status": "success", "message": "Konfigurace byla uložena"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/calendar_data', methods=['GET'])
@login_required
def calendar_data():
    transactions = load_transactions()
    initial_balance = get_initial_balance()
    
    # Sort transactions by date
    transactions.sort(key=lambda x: x['date'])
    
    # Create a map of all dates with transactions
    all_dates = sorted(list(set(t['date'] for t in transactions)))
    date_map = {d: {'income': 0, 'expense': 0, 'transactions': []} for d in all_dates}
    
    # Process transactions
    
    for i, t in enumerate(transactions):
        d = t['date']
        if d not in date_map:
             continue
        date_map[d]['transactions'].append(t)

        status = str(t.get('payment_status', '')).lower().strip()
        if status == 'archiv':
            continue
            
        if t['amount'] > 0:
            # Income: Always count (based on due date)
            date_map[d]['income'] += t['amount']
        else:
            # Expense: Always count (paid or unpaid)
            date_map[d]['expense'] += abs(t['amount'])
            
    # Calculate running balance chronologically
    running_balance = initial_balance
    response_days = {}
    
    # Determine "Current Balance" (balance as of Today)
    today_str = datetime.now().strftime('%Y-%m-%d')
    current_total_balance = initial_balance
    
    # Sort dates to be sure
    sorted_dates_list = sorted(date_map.keys())
    
    for date in sorted_dates_list:
        day_data = date_map[date]
        net_change = day_data['income'] - day_data['expense']
        running_balance += net_change
        
        # Update current_total_balance if date is today or earlier
        if date <= today_str:
            current_total_balance = running_balance
        
        response_days[date] = {
            "balance": running_balance,
            "income": day_data['income'],
            "expense": day_data['expense'],
            "transactions": day_data['transactions']
        }

    # If there are no transactions today or later, current balance is the final running balance
    if not sorted_dates_list or sorted_dates_list[-1] <= today_str:
        current_total_balance = running_balance

    return jsonify({
        "initial_balance": initial_balance,
        "current_total_balance": current_total_balance, 
        "daily_status": response_days
    })

@app.route('/api/search', methods=['GET'])
@login_required
def search_transactions():
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])
    
    transactions = load_transactions()
    results = []
    
    for t in transactions:
        vs = str(t.get('var_symbol', '')).lower()
        party = str(t.get('supplier', '') or t.get('customer', '')).lower()
        desc = str(t.get('description', '')).lower()
        
        if query in vs or query in party or query in desc:
            results.append(t)
            
    results.sort(key=lambda x: x['date'], reverse=True)
    return jsonify(results)

@app.route('/api/update_transaction', methods=['POST'])
@login_required
def update_transaction():

    try:
        data = request.json
        t_id = data.get('id')
        
        if not t_id:
            return jsonify({"status": "error", "message": "Missing ID"}), 400
            
        transactions = load_transactions()
        updated = False
        
        for t in transactions:
            if t['id'] == t_id:
                # Update fields if provided
                if 'date' in data: t['date'] = data['date']
                if 'amount' in data: t['amount'] = float(data['amount'])
                if 'description' in data: t['description'] = data['description']
                if 'supplier' in data: t['supplier'] = data['supplier']
                if 'customer' in data: t['customer'] = data['customer']
                if 'type' in data: t['type'] = data['type']
                if 'var_symbol' in data: t['var_symbol'] = data['var_symbol']
                if 'payment_status' in data: t['payment_status'] = data['payment_status']
                
                # Update text for display
                # Reconstruct full text if description changed? 
                # Keep it simple: update text if desc provided
                if 'description' in data:
                     prefix = f"VS:{t.get('var_symbol')} " if t.get('var_symbol') else ""
                     ent = t.get('supplier') or t.get('customer') or ""
                     t['text'] = f"{prefix}{ent} - {t['description']}".strip(" -")
                
                t['modified_by'] = session.get('username')
                t['modified_at'] = datetime.now().isoformat()
                updated = True
                break
        
        if updated:
            save_transactions(transactions)
            log_audit("update_transaction", {"id": t_id, "changes": data})
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Transaction not found"}), 404
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/delete_transaction', methods=['POST'])
@login_required
def delete_transaction():
    try:
        data = request.json
        t_id = data.get('id')
        
        if not t_id:
            return jsonify({"status": "error", "message": "Missing ID"}), 400
            
        transactions = load_transactions()
        
        # Filter out the transaction
        new_transactions = [t for t in transactions if t['id'] != t_id]
        
        if len(new_transactions) < len(transactions):
            save_transactions(new_transactions)
            log_audit("delete_transaction", {"id": t_id, "by": session.get('username')})
            return jsonify({"status": "success"})
        else:
             return jsonify({"status": "error", "message": "Transaction not found"}), 404
             
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/initial_balance', methods=['POST'])
@login_required
def update_initial_balance():
    try:
        data = request.json
        balance = float(data.get('balance', 0))
        set_initial_balance(balance)
        log_audit("update_initial_balance", {"balance": balance})
        return jsonify({"status": "success", "balance": balance})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint to list uploaded files
@app.route('/api/uploaded_files', methods=['GET'])
@login_required
def get_uploaded_files_endpoint():
    try:
        vstupy_dir = os.path.join(DATA_DIR, 'vstupy')
        prijate_dir = os.path.join(vstupy_dir, 'prijate')
        vydane_dir = os.path.join(vstupy_dir, 'vydane')
        
        prijate_files = sorted([f for f in os.listdir(prijate_dir) if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]) if os.path.exists(prijate_dir) else []
        vydane_files = sorted([f for f in os.listdir(vydane_dir) if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]) if os.path.exists(vydane_dir) else []
        
        return jsonify({
            "prijate": prijate_files,
            "vydane": vydane_files
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reset_db', methods=['POST'])
@login_required
def reset_db():
    # Removed admin check
        
    try:
        # Clear transactions
        save_transactions([])
        # Reset balance
        set_initial_balance(0)
        
        log_audit("reset_db", {"by": session.get('username')})
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/delete_file', methods=['POST'])
@login_required
def delete_file():
    # Removed admin check
        
    try:
        data = request.json
        file_type = data.get('type') # 'prijate' or 'vydane'
        filename = data.get('filename')
        
        if not file_type or not filename:
             return jsonify({"status": "error", "message": "Missing type or filename"}), 400
             
        vstupy_dir = os.path.join(DATA_DIR, 'vstupy')
        target_dir = os.path.join(vstupy_dir, file_type)
        
        # Security check: ensure target_dir is valid and file is within it
        if file_type not in ['prijate', 'vydane']:
            return jsonify({"status": "error", "message": "Invalid type"}), 400
            
        file_path = os.path.abspath(os.path.join(target_dir, filename))
        target_dir_abs = os.path.abspath(target_dir)
        
        # Prevent directory traversal
        if not file_path.startswith(target_dir_abs):
             return jsonify({"status": "error", "message": "Invalid path"}), 400
             
        if os.path.exists(file_path):
            try:
                # Attempt to remove read-only attribute if present
                import stat
                os.chmod(file_path, stat.S_IWRITE)
                os.remove(file_path)
            except PermissionError:
                return jsonify({"status": "error", "message": f"Soubor '{filename}' je používán jiným procesem (např. Excel). Zavřete jej a zkuste to znovu."}), 400
            except Exception as e:
                return jsonify({"status": "error", "message": f"Chyba při mazání: {str(e)}"}), 500
                
            log_audit("delete_file", {"type": file_type, "filename": filename, "by": session.get('username')})
            return jsonify({"status": "success", "message": "Soubor byl úspěšně smazán z disku."})
        else:
            return jsonify({"status": "error", "message": "Soubor na disku neexistuje"}), 404
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/audit_log', methods=['GET'])
@login_required
def get_audit_log_endpoint():
    # Removed admin check
    try:
        logs = get_audit_log(100)
        return jsonify(logs)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_local_ip():
    """Get local IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def scheduled_backup():
    try:
        from database import create_backup
        print("Running scheduled backup...")
        create_backup()
        # log_audit might fail if outside context? No, it uses get_db logic.
        from db_wrapper import log_audit
        log_audit("scheduled_backup", {"status": "success"})
    except Exception as e:
        print(f"Scheduled backup failed: {e}")
        try:
            from db_wrapper import log_audit
            log_audit("scheduled_backup", {"status": "failed", "error": str(e)})
        except: pass

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

# --- Backup Endpoints ---
@app.route('/api/backup/create', methods=['POST'])
@login_required
def api_create_backup():
    # Removed admin check
    try:
        from database import create_backup
        filename = create_backup()
        log_audit("create_backup", {"filename": filename, "by": session.get('username')})
        return jsonify({"status": "success", "filename": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Disable Caching
@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/api/backup/list', methods=['GET'])
@login_required
def api_list_backups():
    # Removed admin check
    try:
        backup_dir = os.path.join(DATA_DIR, 'backups')
        if not os.path.exists(backup_dir): os.makedirs(backup_dir)
        backups = []
        for f in os.listdir(backup_dir):
            if f.endswith('.db'):
                path = os.path.join(backup_dir, f)
                size = os.path.getsize(path) / 1024 # KB
                created = datetime.fromtimestamp(os.path.getctime(path)).strftime('%Y-%m-%d %H:%M:%S')
                backups.append({"filename": f, "size": f"{size:.1f} KB", "created": created})
        backups.sort(key=lambda x: x['created'], reverse=True)
        return jsonify({"status": "success", "backups": backups})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/backup/download/<filename>', methods=['GET'])
@login_required
def api_download_backup(filename):
    # Removed admin check
    try:
        backup_dir = os.path.join(DATA_DIR, 'backups')
        return send_file(os.path.join(backup_dir, filename), as_attachment=True)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 404

@app.route('/api/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    try:
        data = request.json
        if not data.get('date') or not data.get('amount'):
             return jsonify({"status": "error", "message": "Chybí datum nebo částka"}), 400
             
        transactions = load_transactions()
        
        # Determine Type if not provided
        amt = float(data['amount'])
        t_type = "Příjem" if amt >= 0 else "Výdaj"
        if data.get('type'): t_type = data['type']

        new_t = {
            "id": str(uuid.uuid4()),
            "date": data['date'],
            "amount": amt,
            "description": data.get('description', 'Ruční zadání'),
            "type": t_type,
            "supplier": data.get('supplier', ''),
            "customer": data.get('customer', ''),
            "var_symbol": data.get('var_symbol', ''),
            "payment_status": data.get('payment_status', ''),
            "source_file": "manual_entry",
            "created_at": datetime.now().isoformat(),
            "created_by": session.get('username'),
            "original_due_date": data['date']
        }
        
        transactions.append(new_t)
        save_transactions(transactions)
        log_audit("add_transaction", {"id": new_t['id'], "amount": new_t['amount']})
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/change_password', methods=['POST'])
@login_required
def endpoint_change_password():
    try:
        data = request.json
        old_pw = data.get('old_password')
        new_pw = data.get('new_password')
        
        if not old_pw or not new_pw:
            return jsonify({"status": "error", "message": "Missing fields"}), 400
            
        username = session.get('username')
        users = load_users()
        
        if username not in users:
            return jsonify({"status": "error", "message": "User not found"}), 404
            
        user = users[username]
        
        # Verify old
        if not check_password_hash(user['password'], old_pw):
             return jsonify({"status": "error", "message": "Staré heslo není správné"}), 400
             
        # Set new
        user['password'] = generate_password_hash(new_pw)
        save_users(users)
        
        log_audit("change_password", {"username": username})
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- FlexiBee Endpoints ---

@app.route('/api/flexibee/config', methods=['GET', 'POST'])
@login_required
def flexibee_config():
    try:
        from flexibee_sync import FlexiBeeConnector
        connector = FlexiBeeConnector()
        
        if request.method == 'GET':
            config = connector.load_config()
            # Remove encrypted password from response for security
            if 'password_encrypted' in config:
                config = config.copy()
                config.pop('password_encrypted', None)
            return jsonify(config)
        else:
            data = request.json
            connector.save_config(data)
            log_audit("update_flexibee_config", {"by": session.get('username')})
            
            # Update scheduler
            global flexibee_job
            if data.get('enabled'):
                if not flexibee_job:
                     flexibee_job = schedule.every(1).hours.do(run_flexibee_sync_job)
                     print("FlexiBee sync scheduled.")
            else:
                if flexibee_job:
                    schedule.cancel_job(flexibee_job)
                    flexibee_job = None
                    print("FlexiBee sync disabled.")
            
            return jsonify({"status": "success", "message": "Konfigurace uložena"})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"FlexiBee config error: {e}")
        print(error_details)
        return jsonify({"status": "error", "message": str(e), "details": error_details}), 500

@app.route('/api/flexibee/test', methods=['POST'])
@login_required
def flexibee_test():
    try:
        from flexibee_sync import FlexiBeeConnector
        connector = FlexiBeeConnector()
        data = request.json
        
        result = connector.test_connection(
            data.get('host'), 
            data.get('company'), 
            data.get('user'), 
            data.get('password')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/flexibee/sync', methods=['POST'])
@login_required
def flexibee_sync_endpoint():
    try:
        from flexibee_sync import FlexiBeeConnector
        connector = FlexiBeeConnector()
        result = connector.sync_invoices()
        log_audit("flexibee_sync_manual", result)
        return jsonify({"status": "success", "details": result})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500

# Scheduler job wrapper
def run_flexibee_sync_job():
    try:
        print("Running scheduled FlexiBee sync...")
        from flexibee_sync import FlexiBeeConnector
        connector = FlexiBeeConnector()
        res = connector.sync_invoices()
        print(f"FlexiBee sync finished: {res}")
    except Exception as e:
        print(f"Scheduled FlexiBee sync failed: {e}")

# Global job reference
flexibee_job = None

if __name__ == '__main__':
    # Schedule backup daily at 03:00
    schedule.every().day.at("03:00").do(scheduled_backup)
    
    # Initialize FlexiBee scheduler
    try:
        from flexibee_sync import FlexiBeeConnector
        c = FlexiBeeConnector().load_config()
        if c.get('enabled'):
             flexibee_job = schedule.every(1).hours.do(run_flexibee_sync_job)
             print("FlexiBee auto-sync initialized.")
    except Exception as e: 
        print(f"FlexiBee init error: {e}")
    
    # Optional: Initialize webhooks for real-time sync
    # Uncomment the following lines to enable:
    # try:
    #     webhook_handler = init_webhooks(app, secret_key="your_webhook_secret_key")
    #     print("FlexiBee webhooks initialized.")
    # except Exception as e:
    #     print(f"Webhook init error: {e}")

    # Start thread
    t = threading.Thread(target=run_schedule)
    t.daemon = True
    t.start()
    
    local_ip = get_local_ip()
    print(f"\n{'='*60}")
    print(f"  Cashflow Dashboard Server")
    print(f"{'='*60}")
    print(f"  Local:    http://127.0.0.1:8887")
    print(f"  Network:  http://{local_ip}:8887")
    print(f"{'='*60}\n")
    
    app.run(debug=True, port=8887, host='0.0.0.0')

