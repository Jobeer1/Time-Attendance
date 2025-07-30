#!/usr/bin/env python3
"""Test a larger range to see how many devices are actually found"""

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
        return None

def test_range_discovery():
    """Test discovery on a range similar to the app"""
    
    # Test the same range but with fewer IPs (to avoid overwhelming)
    # Focus on the known range where devices exist
    start_ip = ipaddress.ip_address('10.0.0.110')
    end_ip = ipaddress.ip_address('10.0.0.160')
    
    ip_list = []
    current_ip = start_ip
    while current_ip <= end_ip:
        ip_list.append(str(current_ip))
        current_ip += 1
    
    print(f"Testing range discovery: {start_ip} to {end_ip}")
    print(f"Total IPs to scan: {len(ip_list)}")
    print("=" * 60)
    
    devices = []
    responsive_ips = []
    
    # Scan IPs in batches
    batch_size = 20
    for i in range(0, len(ip_list), batch_size):
        batch = ip_list[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}: {batch[0]} to {batch[-1]}")
        
        # Scan batch concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_ip = {
                executor.submit(ping_host, ip): ip 
                for ip in batch
            }
            
            batch_responsive = 0
            batch_with_mac = 0
            
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    
                    if result['online']:
                        responsive_ips.append(ip)
                        batch_responsive += 1
                        print(f"  ✅ {ip} - ONLINE")
                        
                        # Get MAC address
                        mac_address = get_mac_from_ip(ip)
                        
                        # Only proceed if we have a valid MAC address
                        if not mac_address or mac_address in ['Unknown', 'N/A', '', None]:
                            print(f"      ❌ No MAC - filtered out")
                            continue
                        
                        print(f"      ✅ MAC: {mac_address} - ADDED")
                        batch_with_mac += 1
                        
                        device = {
                            'ip_address': ip,
                            'mac_address': mac_address,
                            'online': True,
                        }
                        devices.append(device)
                        
                except Exception as e:
                    print(f"    ❌ Error scanning IP {ip}: {e}")
            
            print(f"  Batch summary: {batch_responsive} responsive, {batch_with_mac} with MAC")
    
    print(f"\n" + "=" * 60)
    print(f"FINAL RESULTS:")
    print(f"  Total IPs scanned: {len(ip_list)}")
    print(f"  Responsive IPs: {len(responsive_ips)}")
    print(f"  Devices with MAC (final result): {len(devices)}")
    print()
    
    if responsive_ips:
        print("Responsive IPs:")
        for ip in responsive_ips:
            print(f"  - {ip}")
    
    print()
    if devices:
        print("Final devices (with MAC):")
        for device in devices:
            print(f"  - {device['ip_address']} ({device['mac_address']})")
    else:
        print("❌ NO DEVICES WITH MAC ADDRESSES FOUND!")
        print("This explains why the app shows 0 devices.")
    
    return devices

if __name__ == "__main__":
    test_range_discovery()
