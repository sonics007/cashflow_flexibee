from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import os
import json
from datetime import datetime
import uuid
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this!
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

TRANSACTIONS_FILE = os.path.join(DATA_DIR, 'transactions.json')
INITIAL_BALANCE_FILE = os.path.join(DATA_DIR, 'balance.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
AUDIT_LOG_FILE = os.path.join(DATA_DIR, 'audit_log.json')

# --- User Management ---

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Default admin user
    return {
        "admin": {"password": "admin123", "role": "admin", "name": "Administrátor"}
    }

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def log_audit(action, details, username=None):
    """Log user actions for audit trail"""
    if username is None:
        username = session.get('username', 'system')
    
    audit_logs = []
    if os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            audit_logs = json.load(f)
    
    audit_logs.append({
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "action": action,
        "details": details
    })
    
    with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(audit_logs, f, indent=4, ensure_ascii=False)

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

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    users = load_users()
    
    if username in users and users[username]['password'] == password:
        session['username'] = username
        session['name'] = users[username].get('name', username)
        session['role'] = users[username].get('role', 'user')
        log_audit("login", {"username": username})
        return jsonify({"status": "success", "name": session['name']})
    
    return jsonify({"status": "error", "message": "Nesprávné přihlašovací údaje"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    username = session.get('username')
    log_audit("logout", {"username": username})
    session.clear()
    return jsonify({"status": "success"})

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    users = load_users()
    user_list = [{"username": u, "name": users[u].get('name'), "role": users[u].get('role')} for u in users]
    return jsonify({"users": user_list})

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    data = request.json
    users = load_users()
    
    username = data.get('username')
    if username in users:
        return jsonify({"status": "error", "message": "Uživatel již existuje"}), 400
    
    users[username] = {
        "password": data.get('password', 'password123'),
        "name": data.get('name', username),
        "role": data.get('role', 'user')
    }
    
    save_users(users)
    log_audit("create_user", {"username": username, "by": session.get('username')})
    return jsonify({"status": "success"})

@app.route('/api/users/<username>', methods=['PUT'])
@login_required
def update_user(username):
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    data = request.json
    users = load_users()
    
    if username not in users:
        return jsonify({"status": "error", "message": "Uživatel neexistuje"}), 404
    
    if 'password' in data:
        users[username]['password'] = data['password']
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
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
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
        transactions = load_data()
        imported_count = 0
        
        if 'prijate' in request.files:
            file = request.files['prijate']
            if file.filename:
                # Save to vstupy/prijate
                filepath = os.path.join(prijate_dir, file.filename)
                file.save(filepath)
                uploaded_files.append(f"prijate/{file.filename}")
                
                # Parse XLSX and import data
                # PRIJATE faktury = faktury ktore firma DOSTANE = VYDAJ (musi zaplatit)
                try:
                    df = pd.read_excel(filepath)
                    print(f"DEBUG PRIJATE: Columns: {df.columns.tolist()}")
                    print(f"DEBUG PRIJATE: First row: {df.iloc[0].to_dict() if len(df) > 0 else 'Empty'}")
                    
                    for idx, row in df.iterrows():
                        try:
                            # Expected columns from image:
                            # A: Název firmy nebo jméno o Splatnosti
                            # B: (date - splatnost)
                            # C: Popis
                            # D: Celkem bez záloh [Kč]
                            # E: Stav úhrady dokladu
                            
                            supplier = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                            date_val = row.iloc[1] if len(row) > 1 else None
                            description = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                            amount_val = row.iloc[3] if len(row) > 3 else None
                            payment_status = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                            
                            if pd.notna(date_val) and pd.notna(amount_val):
                                # Parse date
                                if isinstance(date_val, str):
                                    date_str = date_val
                                else:
                                    date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                                
                                # Parse amount
                                amount = float(amount_val)
                                
                                # Create full description
                                full_text = f"{supplier} - {description}".strip(" -")
                                
                                transactions.append({
                                    "id": str(uuid.uuid4()),
                                    "date": date_str,
                                    "type": "vydaj",  # PRIJATE = VYDAJ (expense)
                                    "amount": -abs(amount),  # Negative for expense
                                    "text": full_text,
                                    "supplier": supplier,
                                    "description": description,
                                    "payment_status": payment_status,
                                    "created_by": session.get('username'),
                                    "created_at": datetime.now().isoformat()
                                })
                                imported_count += 1
                                print(f"DEBUG PRIJATE: Imported {imported_count}: {date_str}, -{amount}, {full_text}")
                        except Exception as row_error:
                            print(f"DEBUG PRIJATE: Error in row {idx}: {str(row_error)}")
                            continue
                            
                except Exception as e:
                    print(f"DEBUG PRIJATE ERROR: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    log_audit("upload_file_error", {"type": "prijate", "filename": file.filename, "error": str(e)})


                
                log_audit("upload_file", {"type": "prijate", "filename": file.filename, "path": filepath, "imported": imported_count})
            
        if 'vydane' in request.files:
            file = request.files['vydane']
            if file.filename:
                # Save to vstupy/vydane
                filepath = os.path.join(vydane_dir, file.filename)
                file.save(filepath)
                uploaded_files.append(f"vydane/{file.filename}")
                
                # Parse XLSX and import data
                # VYDANE faktury = faktury ktore firma VYDAVA = PRIJEM (dostane peniaze)
                try:
                    df = pd.read_excel(filepath)
                    print(f"DEBUG VYDANE: Columns: {df.columns.tolist()}")
                    print(f"DEBUG VYDANE: First row: {df.iloc[0].to_dict() if len(df) > 0 else 'Empty'}")
                    
                    for idx, row in df.iterrows():
                        try:
                            # Expected columns from image:
                            # A: Datum příjmů
                            # B: Variabilní symbol Splatnost
                            # C: (another date field)
                            # D: Název firmy nebo jméno osoby
                            # E: Celkem [Kč]
                            # F: Stav úhrady dokladu
                            # G: Popis
                            
                            date_val = row.iloc[0] if pd.notna(row.iloc[0]) else None
                            var_symbol = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                            due_date = row.iloc[2] if len(row) > 2 else None
                            customer = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                            amount_val = row.iloc[4] if len(row) > 4 else None
                            payment_status = str(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else ""
                            description = str(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) else ""
                            
                            if pd.notna(date_val) and pd.notna(amount_val):
                                # Parse date
                                if isinstance(date_val, str):
                                    date_str = date_val
                                else:
                                    date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                                
                                # Parse amount
                                amount = float(amount_val)
                                
                                # Create full description
                                full_text = f"{customer} - {description}".strip(" -")
                                if var_symbol:
                                    full_text = f"VS:{var_symbol} {full_text}"
                                
                                transactions.append({
                                    "id": str(uuid.uuid4()),
                                    "date": date_str,
                                    "type": "prijem",  # VYDANE = PRIJEM (income)
                                    "amount": abs(amount),  # Positive for income
                                    "text": full_text,
                                    "customer": customer,
                                    "var_symbol": var_symbol,
                                    "description": description,
                                    "payment_status": payment_status,
                                    "created_by": session.get('username'),
                                    "created_at": datetime.now().isoformat()
                                })
                                imported_count += 1
                                print(f"DEBUG VYDANE: Imported {imported_count}: {date_str}, +{amount}, {full_text}")
                        except Exception as row_error:
                            print(f"DEBUG VYDANE: Error in row {idx}: {str(row_error)}")
                            continue
                            
                except Exception as e:
                    print(f"DEBUG VYDANE ERROR: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    log_audit("upload_file_error", {"type": "vydane", "filename": file.filename, "error": str(e)})


                
                log_audit("upload_file", {"type": "vydane", "filename": file.filename, "path": filepath, "imported": imported_count})
        
        # Save updated transactions
        save_data(transactions)
            
        return jsonify({
            "status": "success", 
            "message": f"Soubory nahrány: {', '.join(uploaded_files)}. Importováno {imported_count} transakcí.",
            "files": uploaded_files,
            "imported": imported_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/calendar_data', methods=['GET'])
@login_required
def get_calendar_data():
    transactions = load_data()
    initial_balance = load_initial_balance()
    
    transactions.sort(key=lambda x: x['date'])
    
    trans_by_date = {}
    for t in transactions:
        d = t['date']
        if d not in trans_by_date: trans_by_date[d] = []
        trans_by_date[d].append(t)
    
    running_balance = initial_balance
    daily_status = {}
    
    for t in transactions:
        running_balance += t['amount']
        d = t['date']
        daily_status[d] = {
            "balance": running_balance,
            "transactions": trans_by_date[d]
        }
        
    return jsonify({
        "initial_balance": initial_balance,
        "daily_status": daily_status
    })

@app.route('/api/update_transaction', methods=['POST'])
@login_required
def update_transaction():
    try:
        req = request.json
        t_id = req.get('id')
        new_date = req.get('new_date')
        
        transactions = load_data()
        for t in transactions:
            if t['id'] == t_id:
                old_date = t['date']
                t['date'] = new_date
                t['modified_by'] = session.get('username')
                t['modified_at'] = datetime.now().isoformat()
                log_audit("update_transaction", {
                    "transaction_id": t_id,
                    "old_date": old_date,
                    "new_date": new_date,
                    "text": t.get('text')
                })
                break
        
        save_data(transactions)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/set_balance', methods=['POST'])
@login_required
def set_balance():
    old_balance = load_initial_balance()
    balance = request.json.get('balance')
    save_initial_balance(balance)
    log_audit("set_balance", {"old": old_balance, "new": balance})
    return jsonify({"status": "success"})

@app.route('/api/audit_log', methods=['GET'])
@login_required
def get_audit_log():
    if os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            return jsonify({"logs": logs[-100:]})  # Last 100 entries
    return jsonify({"logs": []})

@app.route('/api/uploaded_files', methods=['GET'])
@login_required
def get_uploaded_files():
    """Get list of uploaded XLSX files"""
    vstupy_dir = os.path.join(DATA_DIR, 'vstupy')
    prijate_dir = os.path.join(vstupy_dir, 'prijate')
    vydane_dir = os.path.join(vstupy_dir, 'vydane')
    
    prijate_files = []
    vydane_files = []
    
    if os.path.exists(prijate_dir):
        prijate_files = [f for f in os.listdir(prijate_dir) if f.endswith(('.xlsx', '.xls'))]
    
    if os.path.exists(vydane_dir):
        vydane_files = [f for f in os.listdir(vydane_dir) if f.endswith(('.xlsx', '.xls'))]
    
    return jsonify({
        "prijate": prijate_files,
        "vydane": vydane_files
    })

@app.route('/api/reset_db', methods=['POST'])
@login_required
def reset_db():
    """Reset database - delete all transactions and balance"""
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        if os.path.exists(TRANSACTIONS_FILE):
            os.remove(TRANSACTIONS_FILE)
        if os.path.exists(INITIAL_BALANCE_FILE):
            os.remove(INITIAL_BALANCE_FILE)
        
        log_audit("reset_db", {"by": session.get('username')})
        return jsonify({"status": "success", "message": "Databáze byla vymazána"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/restart_server', methods=['POST'])
@login_required
def restart_server():
    """Restart server"""
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
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
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
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

@app.route('/api/backup/list', methods=['GET'])
@login_required
def list_backups():
    """List available backups"""
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        from database import get_backups
        backups = get_backups()
        return jsonify({"backups": backups})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/backup/download/<filename>', methods=['GET'])
@login_required
def download_backup(filename):
    """Download backup file"""
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        from database import BACKUP_DIR
        from flask import send_file
        backup_path = os.path.join(BACKUP_DIR, filename)
        if os.path.exists(backup_path) and filename.endswith('.db'):
            return send_file(backup_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({"status": "error", "message": "Soubor nenalezen"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/backup/restore', methods=['POST'])
@login_required
def restore_backup_endpoint():
    """Restore database from backup"""
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        from database import restore_backup, BACKUP_DIR
        
        if 'file' in request.files:
            # Upload and restore from uploaded file
            file = request.files['file']
            if file.filename.endswith('.db'):
                temp_path = os.path.join(BACKUP_DIR, f'uploaded_{file.filename}')
                file.save(temp_path)
                
                if restore_backup(temp_path):
                    log_audit("restore_backup", {"by": session.get('username'), "source": "upload"})
                    return jsonify({"status": "success", "message": "Záloha byla obnovena"})
                else:
                    return jsonify({"status": "error", "message": "Chyba při obnově"}), 500
        elif 'filename' in request.json:
            # Restore from existing backup
            filename = request.json['filename']
            backup_path = os.path.join(BACKUP_DIR, filename)
            
            if restore_backup(backup_path):
                log_audit("restore_backup", {"by": session.get('username'), "source": filename})
                return jsonify({"status": "success", "message": "Záloha byla obnovena"})
            else:
                return jsonify({"status": "error", "message": "Chyba při obnově"}), 500
        else:
            return jsonify({"status": "error", "message": "Chybí soubor nebo název zálohy"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/backup/config', methods=['GET', 'POST'])
@login_required
def backup_config():
    """Get or update backup configuration"""
    if session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
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

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"\n{'='*60}")
    print(f"  Cashflow Dashboard Server")
    print(f"{'='*60}")
    print(f"  Local:    http://127.0.0.1:8888")
    print(f"  Network:  http://{local_ip}:8888")
    print(f"{'='*60}\n")
    
    app.run(debug=True, port=8888, host='0.0.0.0')

