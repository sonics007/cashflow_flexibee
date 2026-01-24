import requests
import urllib3
urllib3.disable_warnings()

url = "https://81.201.61.106:5434/c/2prnet_s_r_o_/faktura-vydana.json?limit=1"
auth = ("eshop", "50635063")

print(f"Testing NEW endpoint: {url}")
print(f"Auth: {auth[0]} / {'*' * len(auth[1])}")
print()

try:
    response = requests.get(url, auth=auth, verify=False, timeout=10)
    print(f"✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.text)
        print(f"✅ SUCCESS! FlexiBee connection works!")
        print(f"\nResponse keys: {list(data.keys())}")
        if 'winstrom' in data:
            print(f"Winstrom keys: {list(data['winstrom'].keys())}")
    else:
        print(f"Response:\n{response.text}")
            
except Exception as e:
    print(f"❌ Error: {e}")
