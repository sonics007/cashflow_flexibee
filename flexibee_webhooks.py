"""
FlexiBee Webhook Handler
Handles real-time notifications from FlexiBee server

This module provides:
1. Webhook endpoint for receiving FlexiBee notifications
2. Signature verification for security
3. Event processing and database updates
"""

from flask import request, jsonify
import hmac
import hashlib
import json
from datetime import datetime
import uuid

class WebhookHandler:
    """Handle incoming webhooks from FlexiBee"""
    
    def __init__(self, app, secret_key=None):
        """
        Initialize webhook handler
        
        Args:
            app: Flask application instance
            secret_key: Secret key for webhook signature verification
        """
        self.app = app
        self.secret_key = secret_key or "default_webhook_secret"
        self._register_routes()
    
    def _register_routes(self):
        """Register webhook routes with Flask app"""
        
        @self.app.route('/api/flexibee/webhook', methods=['POST'])
        def flexibee_webhook():
            """
            Receive webhook notifications from FlexiBee
            
            Expected payload format:
            {
                "event": "faktura-vydana.create",
                "data": {
                    "id": "123",
                    "code": "FV2026001",
                    ...
                },
                "timestamp": "2026-01-21T10:00:00",
                "signature": "sha256_hash"
            }
            """
            try:
                # Verify signature
                if not self._verify_signature(request):
                    return jsonify({"status": "error", "message": "Invalid signature"}), 401
                
                payload = request.json
                event = payload.get('event')
                data = payload.get('data', {})
                
                # Process event
                result = self._process_event(event, data)
                
                return jsonify({"status": "success", "result": result}), 200
                
            except Exception as e:
                print(f"Webhook error: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
    
    def _verify_signature(self, request):
        """
        Verify webhook signature for security
        
        Args:
            request: Flask request object
        
        Returns:
            bool: True if signature is valid
        """
        signature = request.headers.get('X-FlexiBee-Signature')
        if not signature:
            print("Warning: No signature provided in webhook")
            return True  # Allow for testing, should be False in production
        
        # Calculate expected signature
        payload = request.get_data()
        expected_signature = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _process_event(self, event, data):
        """
        Process webhook event and update database
        
        Args:
            event: Event type (e.g., 'faktura-vydana.create')
            data: Event data
        
        Returns:
            dict: Processing result
        """
        from db_wrapper import save_transactions, load_transactions
        
        event_type, action = event.split('.') if '.' in event else (event, 'unknown')
        
        if event_type == 'faktura-vydana':
            return self._process_issued_invoice(data, action)
        elif event_type == 'faktura-prijata':
            return self._process_received_invoice(data, action)
        else:
            print(f"Unknown event type: {event_type}")
            return {"processed": False, "reason": "Unknown event type"}
    
    def _process_issued_invoice(self, invoice_data, action):
        """Process issued invoice webhook"""
        from db_wrapper import save_transactions, load_transactions
        
        code = invoice_data.get('code')
        remote_id = f"flexibee:{code}"
        
        transactions = load_transactions()
        existing = None
        
        # Find existing transaction
        for t in transactions:
            if t.get('source_file') == remote_id:
                existing = t
                break
        
        if action == 'delete':
            # Remove transaction
            if existing:
                transactions = [t for t in transactions if t['id'] != existing['id']]
                save_transactions(transactions)
                return {"processed": True, "action": "deleted", "id": existing['id']}
            return {"processed": False, "reason": "Transaction not found"}
        
        # Create or update
        now = datetime.now()
        
        if not existing:
            existing = {
                'id': str(uuid.uuid4()),
                'created_at': now.isoformat()
            }
            transactions.append(existing)
        
        # Map fields
        existing['date'] = invoice_data.get('datSplat', '').split('T')[0]
        existing['amount'] = float(invoice_data.get('sumCelkem', 0))
        existing['type'] = 'Příjem'
        existing['customer'] = invoice_data.get('firma', {}).get('showAs', '') if isinstance(invoice_data.get('firma'), dict) else str(invoice_data.get('firma', ''))
        existing['supplier'] = ''
        existing['var_symbol'] = invoice_data.get('varSym', '')
        existing['description'] = invoice_data.get('popis', f"Faktura {code}")
        existing['payment_status'] = 'zaplaceno' if invoice_data.get('uhrazeno', 0) else 'nezaplaceno'
        existing['source_file'] = remote_id
        existing['modified_at'] = now.isoformat()
        
        save_transactions(transactions)
        
        return {
            "processed": True,
            "action": action,
            "id": existing['id'],
            "code": code
        }
    
    def _process_received_invoice(self, invoice_data, action):
        """Process received invoice webhook"""
        from db_wrapper import save_transactions, load_transactions
        
        code = invoice_data.get('code')
        remote_id = f"flexibee:{code}"
        
        transactions = load_transactions()
        existing = None
        
        # Find existing transaction
        for t in transactions:
            if t.get('source_file') == remote_id:
                existing = t
                break
        
        if action == 'delete':
            # Remove transaction
            if existing:
                transactions = [t for t in transactions if t['id'] != existing['id']]
                save_transactions(transactions)
                return {"processed": True, "action": "deleted", "id": existing['id']}
            return {"processed": False, "reason": "Transaction not found"}
        
        # Create or update
        now = datetime.now()
        
        if not existing:
            existing = {
                'id': str(uuid.uuid4()),
                'created_at': now.isoformat()
            }
            transactions.append(existing)
        
        # Map fields
        existing['date'] = invoice_data.get('datSplat', '').split('T')[0]
        amount = float(invoice_data.get('sumCelkem', 0))
        existing['amount'] = -abs(amount)
        existing['type'] = 'Výdaj'
        existing['customer'] = ''
        existing['supplier'] = invoice_data.get('firma', {}).get('showAs', '') if isinstance(invoice_data.get('firma'), dict) else str(invoice_data.get('firma', ''))
        existing['var_symbol'] = invoice_data.get('varSym', '')
        existing['description'] = invoice_data.get('popis', f"Faktura {code}")
        existing['payment_status'] = 'zaplaceno' if invoice_data.get('uhrazeno', 0) else 'nezaplaceno'
        existing['source_file'] = remote_id
        existing['modified_at'] = now.isoformat()
        
        save_transactions(transactions)
        
        return {
            "processed": True,
            "action": action,
            "id": existing['id'],
            "code": code
        }


def init_webhooks(app, secret_key=None):
    """
    Initialize webhook handler
    
    Usage in app.py:
        from flexibee_webhooks import init_webhooks
        init_webhooks(app, secret_key="your_secret_key")
    
    Args:
        app: Flask application instance
        secret_key: Secret key for signature verification
    
    Returns:
        WebhookHandler instance
    """
    return WebhookHandler(app, secret_key)
