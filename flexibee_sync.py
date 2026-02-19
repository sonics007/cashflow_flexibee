import requests
import json
import os
import uuid
from datetime import datetime, timedelta
import urllib3
import time
from cryptography.fernet import Fernet
import base64
import hashlib
from flexibee_rate_limiter import flexibee_rate_limiter, flexibee_adaptive_delay

# Suppress insecure request warnings if user uses self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CONFIG_FILE = os.path.join(DATA_DIR, 'flexibee_config.json')
KEY_FILE = os.path.join(DATA_DIR, '.flexibee_key')

class PasswordEncryption:
    """Handle password encryption/decryption using Fernet (symmetric encryption)"""
    
    @staticmethod
    def _get_or_create_key():
        """Get existing key or create new one"""
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'rb') as f:
                return f.read()
        else:
            # Generate key from machine-specific data for consistency
            # This allows decryption even after restart
            key = Fernet.generate_key()
            with open(KEY_FILE, 'wb') as f:
                f.write(key)
            # Hide the key file on Windows
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(KEY_FILE, 2)  # FILE_ATTRIBUTE_HIDDEN
            except:
                pass
            return key
    
    @staticmethod
    def encrypt(password):
        """Encrypt password"""
        if not password:
            return ""
        key = PasswordEncryption._get_or_create_key()
        f = Fernet(key)
        encrypted = f.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt(encrypted_password):
        """Decrypt password"""
        if not encrypted_password:
            return ""
        try:
            key = PasswordEncryption._get_or_create_key()
            f = Fernet(key)
            decoded = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted = f.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""

class RetryHandler:
    """Handle retry logic for API requests"""
    
    @staticmethod
    def retry_request(func, max_retries=3, backoff_factor=2, timeout=30):
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for wait time between retries
            timeout: Request timeout in seconds
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func(timeout=timeout)
            except requests.exceptions.Timeout as e:
                last_exception = e
                wait_time = backoff_factor ** attempt
                print(f"Timeout on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                wait_time = backoff_factor ** attempt
                print(f"Connection error on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            except requests.exceptions.HTTPError as e:
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    raise e
                last_exception = e
                wait_time = backoff_factor ** attempt
                print(f"HTTP error {e.response.status_code} on attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            except Exception as e:
                # Unknown error, don't retry
                raise e
        
        # All retries failed
        raise last_exception

class FlexiBeeConnector:
    def __init__(self):
        self.config = self.load_config()
        self.page_size = 100  # Default page size for pagination
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
             try:
                 with open(CONFIG_FILE, 'r') as f:
                     config = json.load(f)
                     # Decrypt password if encrypted
                     if config.get('password_encrypted'):
                         config['password'] = PasswordEncryption.decrypt(config.get('password', ''))
                     return config
             except:
                 return {}
        return {}
    
    def save_config(self, config):
        # Preserve last_sync if not provided in new config
        old_config = self.load_config()
        if 'last_sync' in old_config and 'last_sync' not in config:
            config['last_sync'] = old_config['last_sync']
        
        # Encrypt password before saving
        config_to_save = config.copy()
        if config_to_save.get('password'):
            config_to_save['password'] = PasswordEncryption.encrypt(config_to_save['password'])
            config_to_save['password_encrypted'] = True
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_to_save, f, indent=4)
        self.config = config

    def get_url(self, path):
        host = self.config.get('host', '').rstrip('/')
        company = self.config.get('company', '')
        # FlexiBee API format: https://server:port/c/company/resource.json
        if not host.startswith('http'):
            host = 'https://' + host
        return f"{host}/c/{company}/{path}"

    def get_auth(self):
        return (self.config.get('user', ''), self.config.get('password', ''))

    def test_connection(self, host, company, user, password):
        """Test connection and return server info with detailed logging"""
        print("\n" + "="*70)
        print("FLEXIBEE CONNECTION TEST")
        print("="*70)
        
        # Temporary config for testing
        test_url = host.rstrip('/')
        if not test_url.startswith('http'): 
            test_url = 'https://' + test_url
            print(f"⚠️  Added HTTPS protocol: {test_url}")
        
        # Use faktura-vydana endpoint instead of status.json (which doesn't work for company-specific URLs)
        url = f"{test_url}/c/{company}/faktura-vydana.json?limit=1"
        
        print(f"🔗 URL:      {url}")
        print(f"👤 User:     {user}")
        print(f"🔑 Password: {'*' * len(password) if password else '(empty)'}")
        print(f"🏢 Company:  {company}")
        print("-"*70)
        
        def make_request(timeout=10):
            print(f"Sending request (timeout: {timeout}s)...")
            # Rate limiting
            flexibee_rate_limiter.acquire()
            flexibee_adaptive_delay.wait()
            
            try:
                response = requests.get(url, auth=(user, password), verify=False, timeout=timeout)
                print(f"Response status: {response.status_code}")
                response.raise_for_status()
                flexibee_adaptive_delay.on_success()
                return response
            except Exception as e:
                flexibee_adaptive_delay.on_error()
                raise e
        
        try:
            response = RetryHandler.retry_request(make_request, max_retries=3, timeout=10)
            data = response.json()
            
            print(f"✅ Connection successful!")
            print(f"📊 Response data keys: {list(data.keys())}")
            
            # Try to get version info
            if 'winstrom' in data:
                winstrom = data['winstrom']
                print(f"📦 Winstrom data: {list(winstrom.keys())}")
                version = winstrom.get('version', 'Unknown')
                print(f"🔢 FlexiBee version: {version}")
                print("="*70 + "\n")
                return {"status": "success", "version": version, "server": test_url}
            else:
                print(f"⚠️  Unexpected response format: {data}")
                print("="*70 + "\n")
                return {"status": "success", "message": "Connected but unexpected format", "data": data}
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 'Unknown'
            
            # Try to get response text
            response_text = 'No response'
            if e.response:
                try:
                    response_text = e.response.text
                    # Try to parse as JSON for better error message
                    try:
                        error_data = e.response.json()
                        if 'winstrom' in error_data:
                            message = error_data['winstrom'].get('message', '')
                            if message:
                                response_text = f"FlexiBee: {message}"
                    except:
                        pass
                except:
                    response_text = 'Could not read response'
            
            print(f"❌ HTTP Error: {status_code}")
            print(f"📄 Response: {response_text[:500]}")
            print("="*70 + "\n")
            
            error_msg = f"HTTP {status_code}"
            if status_code == 401:
                error_msg += " - Nesprávné meno alebo heslo"
            elif status_code == 403:
                error_msg += " - Prístup zamietnutý (API možno nie je aktivované)"
            elif status_code == 404:
                error_msg += f" - {response_text}"
            
            return {"status": "error", "message": error_msg, "details": response_text}
            
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            print("="*70 + "\n")
            return {"status": "error", "message": f"Nepodarilo sa pripojiť k serveru: {test_url}"}
            
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout: {e}")
            print("="*70 + "\n")
            return {"status": "error", "message": "Server neodpovedá (timeout)"}
            
        except Exception as e:
            print(f"❌ Unexpected error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            print("="*70 + "\n")
            return {"status": "error", "message": str(e)}

    def _fetch_paginated_data(self, resource, filter_str, params, max_retries=3):
        """
        Fetch data with pagination support
        
        Args:
            resource: API resource (e.g., 'faktura-vydana')
            filter_str: Filter string for the query (empty string = no filter)
            params: Query parameters
            max_retries: Maximum retry attempts per request
        
        Returns:
            List of all records
        """
        all_data = []
        start = 0
        
        while True:
            # Update params with pagination
            paginated_params = params.copy()
            paginated_params['start'] = start
            paginated_params['limit'] = self.page_size
            
            if filter_str:
                url = self.get_url(f'{resource}/{filter_str}.json')
            else:
                url = self.get_url(f'{resource}.json')
            
            print(f"  Fetching: {url} (start={start})")
            
            def make_request(timeout=30):
                # Rate limiting
                flexibee_rate_limiter.acquire()
                flexibee_adaptive_delay.wait()
                
                try:
                    resp = requests.get(
                        url, 
                        params=paginated_params, 
                        auth=self.get_auth(), 
                        verify=False,
                        timeout=timeout
                    )
                    print(f"  HTTP {resp.status_code} - {len(resp.content)} bytes")
                    resp.raise_for_status()
                    flexibee_adaptive_delay.on_success()
                    return resp
                except Exception as e:
                    flexibee_adaptive_delay.on_error()
                    raise e
            
            try:
                resp = RetryHandler.retry_request(make_request, max_retries=max_retries, timeout=30)
                data = resp.json().get('winstrom', {}).get(resource, [])
                print(f"  Got {len(data)} records from {resource}")
                
                if not data:
                    # No more data
                    break
                
                all_data.extend(data)
                
                # Check if we got less than page_size, meaning we're done
                if len(data) < self.page_size:
                    break
                
                start += self.page_size
                print(f"Fetched {len(all_data)} records from {resource}...")
                
            except Exception as e:
                print(f"Error fetching page {start // self.page_size} from {resource}: {e}")
                raise e
        
        return all_data


    def sync_invoices(self):
        """
        Synchronize issued and received invoices.
        Smart Sync: Only fetches records changed since last_sync.
        Features:
        - Pagination for large datasets
        - Retry mechanism with exponential backoff
        - Encrypted password storage
        """
        def parse_flexibee_date(date_str):
            """
            Ultra-robust date parsing for FlexiBee.
            Handles: '2024-05-11+02:00', '11+02:00.05.2024', '2024-11-08T00:00:00'
            """
            if not date_str:
                return ''
            import re
            try:
                # 1. Remove timezone offset like +02:00 or +01:00 wherever it is
                cleaned = re.sub(r'\+\d{2}:\d{2}', '', str(date_str))
                
                # 2. Handle T separator (ISO)
                if 'T' in cleaned:
                    cleaned = cleaned.split('T')[0]
                
                # 3. Handle DD.MM.YYYY (after timezone removal it might look like 11.05.2024)
                if '.' in cleaned and '-' not in cleaned:
                    parts = [p for p in cleaned.split('.') if p.strip().isdigit()]
                    if len(parts) >= 3:
                        # Extract day, month, year (taking only digits to be safe)
                        d = parts[0].strip()[-2:]
                        m = parts[1].strip()[-2:]
                        y = parts[2].strip()[:4]
                        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                
                # 4. Final attempt: Extract YYYY-MM-DD using regex
                match = re.search(r'(\d{4}-\d{2}-\d{2})', cleaned)
                if match:
                    return match.group(1)
                
                return cleaned.strip()[:10]
            except:
                return str(date_str)[:10] if date_str else ''
        
        def clean_company_name(company_str):
            """
            Remove 'code:' prefix from FlexiBee company name.
            FlexiBee returns: 'code:Company Name' -> we want: 'Company Name'
            """
            if not company_str:
                return ''
            company_str = str(company_str).strip()
            # Remove 'code:' prefix if present
            if company_str.startswith('code:'):
                return company_str[5:].strip()
            return company_str
        
        if not self.config.get('enabled') and not self.config.get('manual_run'):
            # If not explicitly enabled, do nothing (unless forced manually)
            pass

        last_sync = self.config.get('last_sync', '')
        import_from_date = self.config.get('import_from_date', '')
        now = datetime.now()

        from db_wrapper import save_transactions, load_transactions
        import uuid

        existing_transactions = load_transactions()

        # Check how many FlexiBee records we already have
        flexibee_count = sum(1 for t in existing_transactions if t.get('source_file', '').startswith('flexibee:'))
        print(f"Existing FlexiBee records in DB: {flexibee_count}")

        # Force full sync if no FlexiBee records exist in DB (regardless of last_sync)
        is_initial_sync = (not last_sync) or (flexibee_count == 0)
        if flexibee_count == 0 and last_sync:
            print("DB has no FlexiBee records despite last_sync being set — forcing full sync")

        params = {
            'detail': 'custom:id,code,datSplat,sumCelkem,firma,varSym,popis,lastUpdate,uhrazeno',
        }

        # NOTE: FlexiBee WQL only supports 'gt' and 'lt' (NOT 'ge'/'gte'/'le'/'lte')
        # For import_from_date filtering we use datSplat (invoice due date) NOT lastUpdate,
        # because an old 2024 invoice can have a recent lastUpdate (e.g. payment status changed).
        # datSplat gt '2025-12-31' correctly returns only invoices due from 2026-01-01 onwards.
        if is_initial_sync:
            if import_from_date:
                try:
                    # Subtract 1 day so 'gt' behaves like '>=' for the given date
                    from_dt = datetime.strptime(import_from_date, '%Y-%m-%d') - timedelta(days=1)
                    filter_date = from_dt.strftime('%Y-%m-%d')
                    filter_str = f"(datSplat gt '{filter_date}')"
                    print(f"Initial sync filter by datSplat: {filter_str}")
                except Exception:
                    filter_str = ""
                    print("Initial sync: no filter (import all)")
            else:
                # No date restriction — import ALL invoices from FlexiBee
                filter_str = ""
                print("Initial sync: no filter (import all invoices)")
        else:
            filter_str = f"(lastUpdate gt '{last_sync}')"
            print(f"Incremental sync filter: {filter_str}")

        new_invoices_issued = 0
        new_invoices_received = 0

        # Create a map of existing FlexiBee transactions by remote code
        existing_map = {}
        for t in existing_transactions:
            src = t.get('source_file', '')
            if src.startswith('flexibee:'):
                code = src.split(':', 1)[1]
                existing_map[code] = t

        updated_transactions = []

        # 1. Issued Invoices (Faktura Vydaná) -> Income
        try:
            print("Syncing issued invoices...")
            data = self._fetch_paginated_data('faktura-vydana', filter_str, params)
            
            for inv in data:
                code = inv.get('code')
                remote_id = f"flexibee:{code}"
                
                # Check if exists
                t = existing_map.get(remote_id)
                if not t:
                    t = {'id': str(uuid.uuid4()), 'created_at': now.isoformat()}
                    new_invoices_issued += 1
                
                # Map fields
                t['date'] = parse_flexibee_date(inv.get('datSplat', ''))  # Due date
                t['amount'] = float(inv.get('sumCelkem', 0)) # Positive for income
                t['type'] = 'Příjem'
                firma_raw = inv.get('firma', {}).get('showAs', '') if isinstance(inv.get('firma'), dict) else str(inv.get('firma', ''))
                t['customer'] = clean_company_name(firma_raw)
                t['supplier'] = '' # My company
                t['var_symbol'] = inv.get('varSym', '')
                t['description'] = inv.get('popis', f"Faktura {code}")
                t['payment_status'] = 'zaplaceno' if inv.get('uhrazeno', 0) else 'nezaplaceno'
                t['source_file'] = remote_id
                
                updated_transactions.append(t)
                
        except Exception as e:
            print(f"Error syncing issued invoices: {e}")
            raise e

        # 2. Received Invoices (Faktura Přijatá) -> Expense
        try:
            print("Syncing received invoices...")
            data = self._fetch_paginated_data('faktura-prijata', filter_str, params)
            
            for inv in data:
                code = inv.get('code')
                remote_id = f"flexibee:{code}"
                
                t = existing_map.get(remote_id)
                if not t:
                    t = {'id': str(uuid.uuid4()), 'created_at': now.isoformat()}
                    new_invoices_received += 1
                
                # Map fields
                t['date'] = parse_flexibee_date(inv.get('datSplat', ''))
                amount = float(inv.get('sumCelkem', 0))
                t['amount'] = -abs(amount)
                
                t['type'] = 'Výdaj'
                t['customer'] = ''
                firma_raw = inv.get('firma', {}).get('showAs', '') if isinstance(inv.get('firma'), dict) else str(inv.get('firma', ''))
                t['supplier'] = clean_company_name(firma_raw)
                t['var_symbol'] = inv.get('varSym', '')
                t['description'] = inv.get('popis', f"Faktura {code}")
                t['payment_status'] = 'zaplaceno' if inv.get('uhrazeno', 0) else 'nezaplaceno'
                t['source_file'] = remote_id
                
                updated_transactions.append(t)
                
        except Exception as e:
            print(f"Error syncing received invoices: {e}")
            raise e

        # Save changes
        if updated_transactions:
            if is_initial_sync:
                # Initial sync: keep non-FlexiBee records (manual entries, Excel imports)
                # and replace ALL FlexiBee records with the fresh data
                non_flexibee = [t for t in existing_transactions
                                if not t.get('source_file', '').startswith('flexibee:')]
                final_list = non_flexibee + updated_transactions
                print(f"Initial sync: kept {len(non_flexibee)} non-FlexiBee records, added {len(updated_transactions)} FlexiBee records")
            else:
                # Incremental sync: merge — keep all existing, update/add changed records
                updated_ids = {t['id'] for t in updated_transactions}
                final_list = [t for t in existing_transactions if t['id'] not in updated_ids]
                final_list.extend(updated_transactions)

            save_transactions(final_list)

            # Update last_sync only if successful
            self.config['last_sync'] = now.strftime('%Y-%m-%dT%H:%M:%S')
            self.save_config(self.config)

        return {
            "status": "success",
            "invoices_issued": new_invoices_issued,
            "invoices_received": new_invoices_received,
            "total_synced": len(updated_transactions)
        }

    def register_webhook(self, webhook_url, events=None):
        """
        Register webhook for real-time notifications
        
        Args:
            webhook_url: URL to receive webhook notifications
            events: List of events to subscribe to (e.g., ['faktura-vydana', 'faktura-prijata'])
        
        Note: This is a placeholder for webhook implementation.
        FlexiBee webhook support depends on server configuration.
        """
        if events is None:
            events = ['faktura-vydana', 'faktura-prijata']
        
        # TODO: Implement webhook registration via FlexiBee API
        # This would typically involve:
        # 1. POST to /webhook endpoint with callback URL
        # 2. Store webhook ID in config
        # 3. Handle webhook verification
        
        print(f"Webhook registration requested for {webhook_url}")
        print(f"Events: {events}")
        print("Note: Webhook implementation requires FlexiBee server support")
        
        return {
            "status": "pending",
            "message": "Webhook support is planned but not yet implemented",
            "webhook_url": webhook_url,
            "events": events
        }

