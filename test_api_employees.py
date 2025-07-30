import requests
import json
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test the messaging API endpoint
try:
    response = requests.get('https://localhost:5003/api/employees/list', verify=False)
    if response.status_code == 200:
        data = response.json()
        print(f"API Response Status: {data.get('status', 'unknown')}")
        print(f"Total employees returned: {len(data.get('employees', []))}")
        
        print("\n=== Employees from API ===")
        for emp in data.get('employees', []):
            print(f"ID: {emp.get('employee_id')}, Name: {emp.get('full_name')}")
            
        print("\n=== Search Test for 'sara' ===")
        search_results = [emp for emp in data.get('employees', []) if 'sara' in emp.get('full_name', '').lower()]
        if search_results:
            for emp in search_results:
                print(f"Found: {emp.get('full_name')} ({emp.get('employee_id')})")
        else:
            print("No employees found matching 'sara' in API results")
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"Connection error: {e}")
    print("Make sure the Flask app is running on https://localhost:5003")
