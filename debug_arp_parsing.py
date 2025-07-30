#!/usr/bin/env python3
"""
Debug script for ARP parsing
"""

import subprocess
import re
import ipaddress

def test_arp_parsing():
    """Test ARP table parsing"""
    try:
        print("=== Testing ARP Parsing ===")
        output = subprocess.check_output('arp -a', shell=True, text=True, timeout=30)
        print(f"ARP Output:\n{output}")
        print("\n=== Parsing Results ===")
        
        valid_entries = []
        for line_num, line in enumerate(output.splitlines()):
            print(f"Line {line_num}: '{line.strip()}'")
            line = line.strip()
            
            if not line or line.startswith('Interface:') or 'Internet Address' in line or '---' in line:
                print(f"  -> Skipped (header/empty)")
                continue

            parts = line.split()
            print(f"  -> Parts: {parts}")
            
            if len(parts) >= 2:
                ip_address = parts[0]
                mac_address = parts[1]
                
                print(f"  -> IP: {ip_address}, MAC: {mac_address}")

                # Validate IP address
                try:
                    ipaddress.ip_address(ip_address)
                    print(f"  -> IP valid")
                except ValueError as e:
                    print(f"  -> IP invalid: {e}")
                    continue

                # Validate MAC address format
                mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
                if re.match(mac_pattern, mac_address):
                    print(f"  -> MAC valid")
                    valid_entries.append({'ip': ip_address, 'mac': mac_address})
                else:
                    print(f"  -> MAC invalid (pattern doesn't match)")
            else:
                print(f"  -> Not enough parts")
        
        print(f"\n=== Summary ===")
        print(f"Found {len(valid_entries)} valid ARP entries:")
        for entry in valid_entries:
            print(f"  {entry['ip']} -> {entry['mac']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_arp_parsing()
