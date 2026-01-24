#!/usr/bin/env python3
"""
FlexiBee Login - Find Company Code via Login API
Uses the login endpoint to authenticate and get company information
"""

import requests
import urllib3
import json
urllib3.disable_warnings()

HOST = "https://81.201.61.106:5434"
USER = "eshop"
PASSWORD = "50635063"

print("="*70)
print("FLEXIBEE LOGIN - ZISŤUJEM KÓD SPOLOČNOSTI")
print("="*70)

# Method 1: Try login endpoint
print("\n1. Skúšam login endpoint...")
login_url = f"{HOST}/login-logout/login.json"
login_data = {
    "username": USER,
    "password": PASSWORD
}

try:
    response = requests.post(
        login_url,
        json=login_data,
        verify=False,
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data.get('success'):
        print("\n✅ Prihlásenie úspešné!")
        auth_token = data.get('authSessionId')
        print(f"Auth token: {auth_token}")
        
        # Now try to get user info or companies
        print("\n2. Získavam informácie o užívateľovi...")
        
        # Try to get current user info
        user_url = f"{HOST}/login-logout/current-user.json"
        headers = {
            "X-authSessionId": auth_token
        }
        
        user_response = requests.get(
            user_url,
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"User data: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
            
    else:
        print(f"\n❌ Prihlásenie zlyhalo: {data.get('errors', {}).get('reason', 'Unknown')}")
        
except Exception as e:
    print(f"❌ Chyba: {e}")
    import traceback
    traceback.print_exc()

# Method 2: Try to list available companies
print("\n" + "="*70)
print("3. Skúšam získať zoznam spoločností...")
print("="*70)

# Try different endpoints with basic auth
endpoints = [
    "/c.json",
    "/companies.json", 
    "/login-logout/companies.json",
]

for endpoint in endpoints:
    url = HOST + endpoint
    print(f"\nSkúšam: {url}")
    
    try:
        response = requests.get(
            url,
            auth=(USER, PASSWORD),
            verify=False,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Úspech!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            break
        else:
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"Chyba: {e}")

print("\n" + "="*70)
print("ZÁVER")
print("="*70)
print("\nAk ste nenašli kód spoločnosti, skúste:")
print("1. Spustiť: python find_company_code.py")
print("2. Kontaktovať FlexiBee administrátora")
print("3. Použiť iný účet (nie REST_API typ)")
print("="*70)
