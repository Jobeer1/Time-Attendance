#!/usr/bin/env python3
"""
Test script to verify network settings JSON cache functionality
"""

import json
import os
import requests
import time

# Configuration
BASE_URL = "http://localhost:5002"  # Using HTTP instead of HTTPS for testing
JSON_FILE_PATH = "network_settings.json"

def test_json_file_creation():
    """Test that the JSON file is created on startup"""
    print("🧪 Testing JSON file creation...")
    if os.path.exists(JSON_FILE_PATH):
        print("✅ JSON file exists")
        return True
    else:
        print("❌ JSON file does not exist")
        return False

def test_get_network_settings():
    """Test GET /api/network-settings endpoint"""
    print("\n🧪 Testing GET /api/network-settings...")
    try:
        response = requests.get(f"{BASE_URL}/api/network-settings", verify=False)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ GET endpoint working")
            return True
        else:
            print(f"❌ GET endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ GET endpoint error: {e}")
        return False

def test_post_network_settings():
    """Test POST /api/network-settings endpoint"""
    print("\n🧪 Testing POST /api/network-settings...")
    test_data = {
        "ip_range_start": "192.168.1.1",
        "ip_range_end": "192.168.1.254",
        "scan_timeout": 10,
        "concurrent_scans": 20
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/network-settings",
            json=test_data,
            verify=False
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ POST endpoint working")
            return True
        else:
            print(f"❌ POST endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ POST endpoint error: {e}")
        return False

def test_json_file_content():
    """Test that the JSON file contains the expected data"""
    print("\n🧪 Testing JSON file content...")
    try:
        with open(JSON_FILE_PATH, 'r') as f:
            data = json.load(f)
        
        print(f"JSON Content: {json.dumps(data, indent=2)}")
        
        if "network_settings" in data:
            print("✅ network_settings key exists")
        else:
            print("❌ network_settings key missing")
            return False
            
        if "discovered_devices" in data:
            print("✅ discovered_devices key exists")
        else:
            print("❌ discovered_devices key missing")
            return False
            
        return True
    except Exception as e:
        print(f"❌ JSON file read error: {e}")
        return False

def test_network_discovery_cache():
    """Test POST /api/network-discovery endpoint"""
    print("\n🧪 Testing POST /api/network-discovery...")
    test_devices = [
        {"ip": "192.168.1.100", "mac": "00:11:22:33:44:55", "type": "terminal"},
        {"ip": "192.168.1.101", "mac": "00:11:22:33:44:56", "type": "computer"}
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/network-discovery",
            json={"devices": test_devices},
            verify=False
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ Network discovery cache working")
            return True
        else:
            print(f"❌ Network discovery cache failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Network discovery cache error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Network Settings JSON Cache Tests")
    print("=" * 60)
    
    tests = [
        test_json_file_creation,
        test_get_network_settings,
        test_post_network_settings,
        test_json_file_content,
        test_network_discovery_cache
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if all(results):
        print("🎉 All tests passed! Network cache is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
