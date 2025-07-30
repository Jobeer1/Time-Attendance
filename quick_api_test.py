#!/usr/bin/env python3
"""
Quick test to check if the present employees API is working
"""
import requests
import json

try:
    # Test the API endpoint
    response = requests.get('http://localhost:5001/admin/api/present-employees')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response received successfully!")
        print(f"Success: {data.get('success')}")
        print(f"Total present: {data.get('total_present')}")
        print(f"Message: {data.get('message')}")
        
        if data.get('present_employees'):
            print("\nPresent employees:")
            for emp in data['present_employees']:
                print(f"- {emp['employee']['name']} ({emp['employee']['employee_id']})")
        else:
            print("No present employees found")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
