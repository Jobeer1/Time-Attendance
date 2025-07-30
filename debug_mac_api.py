#!/usr/bin/env python3
"""
Debug MAC Address API - Test the endpoint directly
"""

import requests
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_mac_lookup():
    """Test the MAC address lookup API"""
    
    # Test IPs
    test_ips = [
        '192.168.1.1',      # Common router
        '155.235.81.127',   # Local network
    ]
    
    # Create a session to handle cookies
    session = requests.Session()
    
    # First, try to login or get session
    try:
        login_response = session.get('https://localhost:5003/admin/login', verify=False, timeout=5)
        print(f"Login page status: {login_response.status_code}")
    except Exception as e:
        print(f"Login page error: {e}")
    
    for ip in test_ips:
        print(f"\n🔍 Testing MAC lookup for {ip}...")
        
        try:
            response = session.post(
                'https://localhost:5003/admin/terminal-management/api/get-mac-address',
                json={'ip_address': ip},
                verify=False,
                timeout=15
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: {result.get('success')}")
                print(f"MAC: {result.get('mac_address')}")
                print(f"Message: {result.get('message')}")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            
        # Short break between tests
        import time
        time.sleep(1)

if __name__ == "__main__":
    test_mac_lookup()
