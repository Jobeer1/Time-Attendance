#!/usr/bin/env python3
"""
Test MAC address API endpoint
"""

import requests
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_mac_api():
    """Test the MAC address API endpoint"""
    
    test_ip = "155.235.81.1"
    
    try:
        print(f"Testing MAC API for {test_ip}")
        
        response = requests.post(
            'https://localhost:5003/admin/terminal-management/api/get-mac-address',
            json={'ip_address': test_ip},
            verify=False,
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"MAC: {result.get('mac_address')}")
            print(f"Message: {result.get('message')}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mac_api()
