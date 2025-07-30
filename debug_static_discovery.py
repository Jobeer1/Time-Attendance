#!/usr/bin/env python3
"""Debug script to test static device discovery"""

import subprocess
import platform
import re
import ipaddress

def ping_host(host):
    """Ping a host to check connectivity"""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', host]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return {
                'online': True,
                'message': 'Host is reachable',
                'response_time': 'unknown'
            }
        else:
            return {
                'online': False,
                'message': 'Host is unreachable'
            }
    except Exception as e:
        return {
            'online': False,
            'message': f'Ping failed: {str(e)}'
        }

def get_mac_from_ip(ip_address):
    """Get MAC address from IP address using ARP table"""
    try:
        if platform.system().lower() == 'windows':
            # Windows ARP command
            result = subprocess.run(['arp', '-a', ip_address], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                for line in lines:
                    if ip_address in line:
                        # Extract MAC address (format: xx-xx-xx-xx-xx-xx)
                        mac_match = re.search(r'([0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2})', line, re.IGNORECASE)
                        if mac_match:
                            return mac_match.group(1).upper()
        else:
            # Linux/macOS ARP command
            result = subprocess.run(['arp', ip_address], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract MAC address (format: xx:xx:xx:xx:xx:xx)
                mac_match = re.search(r'([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', result.stdout, re.IGNORECASE)
                if mac_match:
                    return mac_match.group(1).upper()
        
        return None
    except Exception as e:
        print(f"Error getting MAC for {ip_address}: {e}")
        return None

def test_static_discovery():
    """Test static discovery logic"""
    
    # Test some known IPs from ARP table
    test_ips = ['10.0.0.113', '10.0.0.134', '10.0.0.140', '10.0.0.141', '10.0.0.115']
    
    print("Testing static discovery logic...")
    print("=" * 50)
    
    devices_found = []
    
    for ip in test_ips:
        print(f"\nTesting IP: {ip}")
        
        # Test ping
        ping_result = ping_host(ip)
        print(f"  Ping result: {ping_result}")
        
        if ping_result['online']:
            # Test MAC lookup
            mac_address = get_mac_from_ip(ip)
            print(f"  MAC address: {mac_address}")
            
            # Check if MAC is valid (this is the filter that might be causing issues)
            if not mac_address or mac_address in ['Unknown', 'N/A', '', None]:
                print(f"  ❌ FILTERED OUT: No valid MAC address found")
                continue
            else:
                print(f"  ✅ WOULD BE INCLUDED: Valid MAC address found")
                devices_found.append({
                    'ip': ip,
                    'mac': mac_address,
                    'online': True
                })
        else:
            print(f"  ❌ OFFLINE: Not responding to ping")
    
    print(f"\n" + "=" * 50)
    print(f"Summary: {len(devices_found)} devices would be included in results")
    for device in devices_found:
        print(f"  - {device['ip']} ({device['mac']})")
    
    if len(devices_found) == 0:
        print("\n🚨 NO DEVICES FOUND! This explains why discovery returns 0 devices.")
        print("Possible issues:")
        print("1. MAC address lookup is failing")
        print("2. Devices are being filtered out due to invalid MAC addresses")
        print("3. Ping is failing for some reason")

if __name__ == "__main__":
    test_static_discovery()
