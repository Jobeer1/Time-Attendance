import requests
import json

# Test the pending applications endpoint
url = "https://localhost:5003/api/leave/applications/pending"
try:
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        data = response.json()
        print("✅ Pending Applications Response:")
        print(json.dumps(data, indent=2))
        print(f"\nNumber of pending applications: {len(data.get('applications', []))}")
    else:
        print(f"❌ Failed to fetch pending applications: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error fetching pending applications: {e}")

# Test the all applications endpoint
url_all = "https://localhost:5003/api/leave/applications/all"
try:
    response = requests.get(url_all, verify=False)
    if response.status_code == 200:
        data = response.json()
        print("\n✅ All Applications Response:")
        print(json.dumps(data, indent=2))
        print(f"\nTotal applications: {len(data.get('applications', []))}")
    else:
        print(f"❌ Failed to fetch all applications: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error fetching all applications: {e}")
