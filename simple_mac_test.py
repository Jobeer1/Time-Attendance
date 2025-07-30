#!/usr/bin/env python3
"""
Simple MAC lookup test
"""

import subprocess
import platform
import re

def test_mac_lookup_direct():
    """Test MAC address lookup directly"""
    ip = "155.235.81.127"  # Local server IP
    
    print(f"Testing MAC lookup for {ip}")
    
    # Test ping first
    try:
        if platform.system().lower() == 'windows':
            result = subprocess.run(['ping', '-n', '1', ip], capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(['ping', '-c', '1', ip], capture_output=True, text=True, timeout=5)
        
        print(f"Ping result: {result.returncode}")
        if result.returncode == 0:
            print("✅ Ping successful")
        else:
            print("❌ Ping failed")
            
    except Exception as e:
        print(f"❌ Ping error: {e}")
    
    # Test ARP lookup
    try:
        if platform.system().lower() == 'windows':
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
            print(f"ARP result: {result.returncode}")
            
            if result.returncode == 0:
                print("ARP table output:")
                for line in result.stdout.splitlines():
                    if ip in line:
                        print(f"  Found: {line}")
                        # Extract MAC address
                        parts = line.split()
                        if len(parts) >= 2:
                            mac = parts[1]
                            print(f"  MAC: {mac}")
        else:
            result = subprocess.run(['arp', ip], capture_output=True, text=True, timeout=10)
            print(f"ARP result: {result.returncode}")
            if result.returncode == 0:
                print(f"ARP output: {result.stdout}")
                
    except Exception as e:
        print(f"❌ ARP error: {e}")

if __name__ == "__main__":
    test_mac_lookup_direct()
