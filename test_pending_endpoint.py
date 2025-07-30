import requests

url = "https://localhost:5003/api/leave/applications/pending"
response = requests.get(url, verify=False)

if response.status_code == 200:
    print("Pending Applications:", response.json())
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")
