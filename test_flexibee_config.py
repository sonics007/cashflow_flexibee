"""
Diagnostic script for FlexiBee configuration issues
Run this to check if everything is working correctly
"""

import sys
import os

print("="*60)
print("FLEXIBEE DIAGNOSTICS")
print("="*60)

# 1. Check Python version
print(f"\n1. Python version: {sys.version}")

# 2. Check if cryptography is installed
print("\n2. Checking cryptography module...")
try:
    from cryptography.fernet import Fernet
    print("   ✅ cryptography module is installed")
except ImportError as e:
    print(f"   ❌ cryptography module NOT installed: {e}")
    print("   Run: pip install cryptography")
    sys.exit(1)

# 3. Check if data directory exists
print("\n3. Checking data directory...")
data_dir = os.path.join(os.path.dirname(__file__), 'data')
if os.path.exists(data_dir):
    print(f"   ✅ Data directory exists: {data_dir}")
else:
    print(f"   ❌ Data directory NOT found: {data_dir}")
    print("   Creating data directory...")
    os.makedirs(data_dir)
    print("   ✅ Data directory created")

# 4. Check if flexibee_config.json exists
print("\n4. Checking flexibee_config.json...")
config_file = os.path.join(data_dir, 'flexibee_config.json')
if os.path.exists(config_file):
    print(f"   ✅ Config file exists: {config_file}")
    
    # Try to load it
    import json
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"   ✅ Config file is valid JSON")
        print(f"   Keys: {list(config.keys())}")
    except Exception as e:
        print(f"   ❌ Config file is INVALID: {e}")
else:
    print(f"   ⚠️  Config file NOT found: {config_file}")
    print("   This is OK - it will be created on first save")

# 5. Test FlexiBeeConnector
print("\n5. Testing FlexiBeeConnector...")
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from flexibee_sync import FlexiBeeConnector
    
    connector = FlexiBeeConnector()
    print("   ✅ FlexiBeeConnector initialized successfully")
    
    # Try to load config
    config = connector.load_config()
    print(f"   ✅ Config loaded successfully")
    print(f"   Host: {config.get('host', 'Not set')}")
    print(f"   Company: {config.get('company', 'Not set')}")
    print(f"   User: {config.get('user', 'Not set')}")
    print(f"   Enabled: {config.get('enabled', False)}")
    print(f"   Password encrypted: {config.get('password_encrypted', False)}")
    
except Exception as e:
    print(f"   ❌ FlexiBeeConnector FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. Test password encryption/decryption
print("\n6. Testing password encryption...")
try:
    from flexibee_sync import PasswordEncryption
    
    test_password = "test123"
    encrypted = PasswordEncryption.encrypt(test_password)
    print(f"   ✅ Encryption successful: {encrypted[:50]}...")
    
    decrypted = PasswordEncryption.decrypt(encrypted)
    print(f"   ✅ Decryption successful: {decrypted}")
    
    if decrypted == test_password:
        print("   ✅ Encryption/Decryption working correctly!")
    else:
        print(f"   ❌ Decryption mismatch! Expected '{test_password}', got '{decrypted}'")
        
except Exception as e:
    print(f"   ❌ Password encryption FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("DIAGNOSTICS COMPLETE")
print("="*60)
print("\nIf all checks passed (✅), FlexiBee should work correctly.")
print("If any checks failed (❌), fix the issues above.\n")
