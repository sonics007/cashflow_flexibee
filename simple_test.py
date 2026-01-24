import requests
import urllib3
urllib3.disable_warnings()

url = "https://81.201.61.106:5434/c/2prnet_s_r_o_/status.json"
auth = ("eshop", "50635063")

print(f"Testing: {url}")
print(f"Auth: {auth[0]} / {'*' * len(auth[1])}")
print()

try:
    response = requests.get(url, auth=auth, verify=False, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text:\n{response.text}")
    
    if response.status_code == 404:
        import json
        data = json.loads(response.text)
        if 'winstrom' in data:
            print(f"\nFlexiBee Message: {data['winstrom'].get('message', 'N/A')}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
