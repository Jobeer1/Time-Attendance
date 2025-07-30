#!/usr/bin/env python3
"""Test the updated static discovery logic"""

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

def refresh_arp_table():
    """Refresh the ARP table and return the parsed results."""
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            arp_entries = []
            for line in lines:
                # Match lines with IP and MAC addresses
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2})', line, re.IGNORECASE)
                if match:
                    arp_entries.append({
                        'ip_address': match.group(1),
                        'mac_address': match.group(2).upper()
                    })
            return arp_entries
        else:
            print("Failed to refresh ARP table: Non-zero return code")
            return []
    except Exception as e:
        print(f"Error refreshing ARP table: {e}")
        return []

def test_updated_logic():
    """Test the updated static discovery logic that includes devices without MAC"""
    
    # Test a smaller range with known responsive devices
    start_ip = ipaddress.ip_address('10.0.0.113')
    end_ip = ipaddress.ip_address('10.0.0.125')
    
    ip_list = []
    current_ip = start_ip
    while current_ip <= end_ip:
        ip_list.append(str(current_ip))
        current_ip += 1
    
    print(f"Testing UPDATED logic: {start_ip} to {end_ip}")
    print(f"Total IPs to scan: {len(ip_list)}")
    print("=" * 60)
    
    devices = []
    
    # Scan IPs in batches (mimic the app logic)
    batch_size = 20
    for i in range(0, len(ip_list), batch_size):
        batch = ip_list[i:i+batch_size]
        print(f"\nProcessing batch: {batch[0]} to {batch[-1]}")
        
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
                    
                    if result['online']:
                        print(f"  ✅ {ip} - ONLINE")
                        
                        # Get MAC address and hostname
                        mac_address = get_mac_from_ip(ip)
                        hostname = 'Unknown'  # Simplified for test
                        
                        # NEW LOGIC: Include devices even without MAC addresses
                        if not mac_address or mac_address in ['Unknown', 'N/A', '', None]:
                            print(f"      ℹ️  No MAC in ARP table, setting to 'Unknown'")
                            mac_address = 'Unknown'  # Set to 'Unknown' instead of skipping
                        else:
                            print(f"      ✅ MAC: {mac_address}")
                        
                        device = {
                            'ip_address': ip,
                            'mac_address': mac_address,  # May be 'Unknown' for static discovery
                            'hostname': hostname,
                            'online': True,
                        }
                        devices.append(device)
                        print(f"      ➕ ADDED to results")
                        
                except Exception as e:
                    print(f"    ❌ Error scanning IP {ip}: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"FINAL RESULTS WITH UPDATED LOGIC:")
    print(f"  Total devices found: {len(devices)}")
    print()
    
    if devices:
        print("Devices found:")
        devices_with_mac = 0
        devices_unknown_mac = 0
        
        for device in devices:
            mac_status = "Known MAC" if device['mac_address'] != 'Unknown' else "Unknown MAC"
            print(f"  - {device['ip_address']} ({device['mac_address']}) [{mac_status}]")
            
            if device['mac_address'] != 'Unknown':
                devices_with_mac += 1
            else:
                devices_unknown_mac += 1
        
        print(f"\nBreakdown:")
        print(f"  - Devices with known MAC: {devices_with_mac}")
        print(f"  - Devices with unknown MAC: {devices_unknown_mac}")
        print(f"  - Total: {len(devices)}")
        
        print(f"\n✅ SUCCESS! The updated logic should now find {len(devices)} devices instead of 0.")
    else:
        print("❌ STILL NO DEVICES FOUND!")
    
    return devices

if __name__ == "__main__":
    # Refresh ARP table before starting
    print("Refreshing ARP table...")
    arp_entries = refresh_arp_table()
    if not arp_entries:
        print("No ARP entries found. Retry or check network settings.")
    else:
        print(f"Found {len(arp_entries)} ARP entries.")

    test_updated_logic()
