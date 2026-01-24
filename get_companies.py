import requests
import urllib3
import json
urllib3.disable_warnings()

base_url = "https://81.201.61.106:5434"
auth = ("eshop", "50635063")

print("="*70)
print("HĽADÁM DOSTUPNÉ SPOLOČNOSTI NA FLEXIBEE SERVERI")
print("="*70)

# Try different endpoints
endpoints = [
    "/status.json",
    "/c/winstrom/company.json",
    "/companies.json",
]

for endpoint in endpoints:
    url = base_url + endpoint
    print(f"\nSkúšam: {url}")
    
    try:
        response = requests.get(url, auth=auth, verify=False, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Úspech! Odpoveď:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check for companies
            if 'winstrom' in data and 'company' in data.get('winstrom', {}):
                companies = data['winstrom']['company']
                print("\n" + "="*70)
                print("NÁJDENÉ SPOLOČNOSTI:")
                print("="*70)
                for c in companies:
                    print(f"Kód: {c.get('kod', 'N/A'):30} | {c.get('nazev', 'N/A')}")
                print("="*70)
                break
        else:
            print(f"⚠️  Chyba: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Chyba: {e}")

print("\n" + "="*70)
print("TIP: Prihláste sa do web rozhrania a pozrite sa na URL:")
print("https://81.201.61.106:5434/c/SPRAVNY_KOD/...")
print("="*70)

