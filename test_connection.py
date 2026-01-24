#!/usr/bin/env python3
"""
Direct FlexiBee Connection Test
Tests connection directly without needing to restart the app
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the updated FlexiBeeConnector
from flexibee_sync import FlexiBeeConnector

print("="*70)
print("PRIAMY TEST FLEXIBEE PRIPOJENIA")
print("="*70)

# Test configuration
test_config = {
    "host": "https://81.201.61.106:5434",
    "company": "2prnet_s_r_o_",
    "user": "eshop",
    "password": "50635063"
}

print(f"\nKonfigurácia:")
print(f"  Host:     {test_config['host']}")
print(f"  Company:  {test_config['company']}")
print(f"  User:     {test_config['user']}")
print(f"  Password: {'*' * len(test_config['password'])}")
print()

# Create connector and test
connector = FlexiBeeConnector()

result = connector.test_connection(
    test_config['host'],
    test_config['company'],
    test_config['user'],
    test_config['password']
)

print("\n" + "="*70)
print("VÝSLEDOK:")
print("="*70)

if result['status'] == 'success':
    print("✅ PRIPOJENIE ÚSPEŠNÉ!")
    print(f"FlexiBee verzia: {result.get('version', 'Unknown')}")
    print(f"Server: {result.get('server', 'Unknown')}")
else:
    print("❌ PRIPOJENIE ZLYHALO!")
    print(f"Chyba: {result.get('message', 'Unknown')}")
    if 'details' in result:
        print(f"Detaily: {result['details']}")

print("="*70)
