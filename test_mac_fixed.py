#!/usr/bin/env python3
"""
Test MAC address lookup after fixes
"""

import subprocess
import platform
import re
import ipaddress

def test_mac_lookup_fixed():
    """Test the fixed MAC address lookup"""
    
    # Test with a known IP from the ARP table
    test_ip = "155.235.81.1"  # Gateway IP
    
    print(f"Testing MAC lookup for {test_ip}")
    
    try:
        # First ping to populate ARP table
        if platform.system().lower() == 'windows':
            result = subprocess.run(['ping', '-n', '1', test_ip], capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(['ping', '-c', '1', test_ip], capture_output=True, text=True, timeout=5)
        
        print(f"Ping result: {result.returncode}")
        
        # Now try ARP lookup
        if platform.system().lower() == 'windows':
            output = subprocess.check_output(f'arp -a {test_ip}', shell=True, text=True, timeout=10)
            
            print(f"ARP output:\n{output}")
            
            # Parse the output
            for line in output.splitlines():
                line = line.strip()
                if test_ip in line and not line.startswith('Interface:'):
                    print(f"Found line: {line}")
                    parts = line.split()
                    print(f"Parts: {parts}")
                    if len(parts) >= 2:
                        mac_candidate = parts[1]
                        print(f"MAC candidate: {mac_candidate}")
                        # Validate MAC address format
                        if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_candidate):
                            print(f"✅ Valid MAC found: {mac_candidate}")
                            return mac_candidate
                        else:
                            print(f"❌ Invalid MAC format: {mac_candidate}")
        
        print("❌ No MAC address found")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    test_mac_lookup_fixed()
