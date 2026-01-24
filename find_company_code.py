#!/usr/bin/env python3
"""
FlexiBee Company Code Finder
Automatically tries different company code combinations to find the correct one
"""

import requests
import urllib3
urllib3.disable_warnings()

# Configuration
HOST = "https://81.201.61.106:5434"
USER = "eshop"
PASSWORD = "50635063"

# Possible company codes to try
POSSIBLE_CODES = [
    # Based on license "2Pnet s.r.o."
    "2pnet",
    "2prnet", 
    "pnet",
    "2pnet-sro",
    "2prnet-sro",
    "2pnet_sro",
    "2prnet_sro",
    
    # Common variations
    "demo",
    "winstrom",
    "firma",
    "company",
    
    # With underscores
    "2_pnet",
    "2_prnet",
    
    # Uppercase
    "2PNET",
    "2PRNET",
    "PNET",
]

print("="*70)
print("AUTOMATICKÉ HĽADANIE SPRÁVNEHO KÓDU SPOLOČNOSTI")
print("="*70)
print(f"Server: {HOST}")
print(f"User:   {USER}")
print("="*70)

found = False

for code in POSSIBLE_CODES:
    url = f"{HOST}/c/{code}/status.json"
    print(f"\n🔍 Skúšam: {code:20} ... ", end="", flush=True)
    
    try:
        response = requests.get(
            url,
            auth=(USER, PASSWORD),
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'winstrom' in data or 'status' in data:
                print("✅ FUNGUJE!")
                print("\n" + "="*70)
                print("🎉 NAŠIEL SOM SPRÁVNY KÓD!")
                print("="*70)
                print(f"Kód spoločnosti: {code}")
                print(f"URL: {url}")
                print("\nPoužite tieto nastavenia v Cashflow:")
                print("-"*70)
                print(f"Host:       {HOST}")
                print(f"Společnost: {code}")
                print(f"Uživatel:   {USER}")
                print(f"Heslo:      {PASSWORD}")
                print("="*70)
                found = True
                break
        elif response.status_code == 404:
            # Try to parse error message
            try:
                error_data = response.json()
                message = error_data.get('winstrom', {}).get('message', '')
                if 'neexistuje' in message.lower() or 'not exist' in message.lower():
                    print("❌ Neexistuje")
                else:
                    print(f"❌ {response.status_code}: {message[:50]}")
            except:
                print(f"❌ 404")
        elif response.status_code == 401:
            print("❌ Nesprávne heslo")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏱️  Timeout")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error")
    except Exception as e:
        print(f"❌ {type(e).__name__}")

if not found:
    print("\n" + "="*70)
    print("❌ NENAŠIEL SOM SPRÁVNY KÓD")
    print("="*70)
    print("\nMožné riešenia:")
    print("1. Kontaktujte FlexiBee administrátora")
    print("2. Prihláste sa iným účtom (nie REST_API) do web rozhrania")
    print("3. Pozrite sa do FlexiBee dokumentácie")
    print("="*70)
else:
    print("\n✅ Hotovo! Použite nájdený kód v Cashflow aplikácii.\n")
