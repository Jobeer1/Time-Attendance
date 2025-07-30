#!/usr/bin/env python3
"""Test concurrent scanning to see if that's causing the issue"""

import subprocess
import platform
import re
import concurrent.futures
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
        
        return None
    except Exception as e:
        print(f"Error getting MAC for {ip_address}: {e}")
        return None

def test_concurrent_discovery():
    """Test the exact concurrent discovery logic from the app"""
    
    # Generate IP list (just a small range for testing)
    start_ip = ipaddress.ip_address('10.0.0.113')
    end_ip = ipaddress.ip_address('10.0.0.117')
    
    ip_list = []
    current_ip = start_ip
    while current_ip <= end_ip:
        ip_list.append(str(current_ip))
        current_ip += 1
    
    print(f"Testing concurrent discovery with IPs: {ip_list}")
    print("=" * 50)
    
    devices = []
    
    # Scan IPs in batches (same logic as the app)
    batch_size = 10
    for i in range(0, len(ip_list), batch_size):
        batch = ip_list[i:i+batch_size]
        print(f"\nProcessing batch: {batch}")
        
        # Scan batch concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_ip = {
                executor.submit(ping_host, ip): ip 
                for ip in batch
            }
            
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    print(f"  {ip}: {result}")
                    
                    if result['online']:
                        # Get MAC address
                        mac_address = get_mac_from_ip(ip)
                        print(f"    MAC: {mac_address}")
                        
                        # Only proceed if we have a valid MAC address
                        if not mac_address or mac_address in ['Unknown', 'N/A', '', None]:
                            print(f"    ❌ Skipped: No valid MAC address")
                            continue
                        
                        device = {
                            'ip_address': ip,
                            'mac_address': mac_address,
                            'online': True,
                            'response_time': result.get('response_time'),
                        }
                        devices.append(device)
                        print(f"    ✅ Added to results")
                    else:
                        print(f"    ❌ Offline")
                        
                except Exception as e:
                    print(f"    ❌ Error scanning IP {ip}: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"Final results: {len(devices)} devices found")
    for device in devices:
        print(f"  - {device['ip_address']} ({device['mac_address']})")
    
    return devices

if __name__ == "__main__":
    test_concurrent_discovery()
