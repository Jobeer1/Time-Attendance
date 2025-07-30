#!/usr/bin/env python3
"""
Test script to debug DHCP discovery API endpoints
"""

import requests
import json
import time
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = "https://localhost:5003"

def test_discovery_api():
    """Test the DHCP discovery API endpoints"""
    
    print("🧪 Testing DHCP Discovery API")
    print("=" * 50)
    
    try:
        # 1. Start discovery
        print("1. Starting DHCP discovery...")
        response = requests.post(
            f"{base_url}/admin/terminal-management/api/discover-dhcp-devices",
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                session_id = result.get('session_id')
                print(f"   ✅ Discovery started with session: {session_id}")
            else:
                print(f"   ❌ Discovery failed: {result.get('error')}")
                return
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
        # 2. Poll for progress
        print("2. Polling for progress...")
        max_polls = 20
        poll_count = 0
        
        while poll_count < max_polls:
            time.sleep(2)
            poll_count += 1
            
            response = requests.get(
                f"{base_url}/admin/terminal-management/api/discovery-progress/{session_id}",
                verify=False
            )
            
            if response.status_code == 200:
                progress_data = response.json()
                print(f"   Poll {poll_count}: Status={progress_data.get('discovery', {}).get('status', 'unknown')}, "
                      f"Device Count={progress_data.get('device_count', 0)}, "
                      f"Progress={progress_data.get('discovery', {}).get('progress', 0)}%")
                
                if progress_data.get('discovery', {}).get('status') == 'completed':
                    print("   🎉 Discovery completed!")
                    print(f"   📊 Final device count: {progress_data.get('device_count', 0)}")
                    
                    # Show found devices
                    found_devices = progress_data.get('discovery', {}).get('found_devices', [])
                    print(f"   📱 Found devices details:")
                    for i, device in enumerate(found_devices[:5]):  # Show first 5
                        print(f"      {i+1}. {device.get('ip_address')} - {device.get('hostname')} - {'🟢' if device.get('online') else '🔴'}")
                    if len(found_devices) > 5:
                        print(f"      ... and {len(found_devices) - 5} more devices")
                    
                    break
                elif progress_data.get('discovery', {}).get('status') == 'error':
                    print(f"   ❌ Discovery error: {progress_data.get('discovery', {}).get('error', 'Unknown error')}")
                    break
            else:
                print(f"   ❌ Progress request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                break
                
        if poll_count >= max_polls:
            print("   ⏰ Timeout: Discovery took too long")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed")

if __name__ == "__main__":
    test_discovery_api()
