#!/usr/bin/env python3
"""
Quick test script to check messaging API endpoints
"""

import requests
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = "https://localhost:5003"

def test_messaging_endpoints():
    print("🔍 Testing messaging API endpoints...")
    
    # Test inbox endpoint
    try:
        response = requests.get(f"{base_url}/api/messaging/inbox/EMP01", verify=False)
        print(f"📥 Inbox endpoint status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Messages count: {len(data.get('messages', []))}")
            print(f"   Success: {data.get('success', False)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test employees endpoint
    try:
        response = requests.get(f"{base_url}/api/messaging/employees", verify=False)
        print(f"👥 Employees endpoint status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Employees count: {len(data.get('employees', []))}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test unread count endpoint
    try:
        response = requests.get(f"{base_url}/api/messaging/unread-count/EMP01", verify=False)
        print(f"📊 Unread count endpoint status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Unread count: {data.get('unread_count', 0)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test messaging interface
    try:
        response = requests.get(f"{base_url}/api/messaging/interface?employee_id=EMP01", verify=False)
        print(f"🖥️ Interface endpoint status: {response.status_code}")
        print(f"   Content length: {len(response.content)} bytes")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")

if __name__ == "__main__":
    test_messaging_endpoints()
