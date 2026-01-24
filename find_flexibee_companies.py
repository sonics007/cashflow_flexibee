#!/usr/bin/env python3
"""
FlexiBee Company Finder
Finds all available companies on FlexiBee server via API
"""

import requests
import urllib3
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# FlexiBee server settings
HOST = "https://81.201.61.106:5434"
USER = "admin"  # CHANGE THIS!
PASSWORD = "your_password"  # CHANGE THIS!

print("="*70)
print("FLEXIBEE COMPANY FINDER")
print("="*70)
print(f"Server: {HOST}")
print(f"User:   {USER}")
print("="*70)

# Try different endpoints to find companies
endpoints = [
    "/c/default/company.json",
    "/c/winstrom/company.json", 
    "/status.json"
]

for endpoint in endpoints:
    url = f"{HOST}{endpoint}"
    print(f"\nTrying: {url}")
    
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
            
            # Check if it's company list
            if 'winstrom' in data and 'company' in data['winstrom']:
                companies = data['winstrom']['company']
                
                print("\n" + "="*70)
                print("✅ FOUND COMPANIES:")
                print("="*70)
                print(f"{'CODE':<30} | {'NAME'}")
                print("-"*70)
                
                for company in companies:
                    code = company.get('kod', 'N/A')
                    name = company.get('nazev', 'N/A')
                    print(f"{code:<30} | {name}")
                
                print("="*70)
                print("\n✅ Use one of these CODES in Cashflow app!")
                break
            
            # Check if it's status endpoint
            elif 'winstrom' in data:
                print(f"✅ Server is responding!")
                print(f"Data: {json.dumps(data, indent=2)}")
                
        elif response.status_code == 401:
            print("❌ Authentication failed! Check username/password.")
            break
        elif response.status_code == 404:
            print("⚠️  Endpoint not found, trying next...")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        break
    except requests.exceptions.Timeout:
        print(f"❌ Timeout - server not responding")
        break
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*70)
print("SEARCH COMPLETE")
print("="*70)
print("\nIf you found companies above, use the CODE (not name) in Cashflow.")
print("If authentication failed, check your username/password.")
print("="*70)
