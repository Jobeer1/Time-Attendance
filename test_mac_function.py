#!/usr/bin/env python3
"""
Test the MAC address function directly
"""

import subprocess
import platform
import re
import time

def get_mac_address_from_ip(ip_address):
    """Get MAC address from IP address using ARP with improved detection"""
    try:
        print(f"🔍 Looking up MAC for {ip_address}")
        
        # First, ping the IP to ensure it's in the ARP table
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(['ping', '-n', '1', ip_address], 
                                      capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['ping', '-c', '1', ip_address], 
                                      capture_output=True, text=True, timeout=5)
            
            print(f"📡 Ping result: {result.returncode}")
        except Exception as e:
            print(f"❌ Ping error: {e}")
        
        # Wait a moment for ARP entry to be populated
        time.sleep(1)
        
        if platform.system().lower() == 'windows':
            # Use arp -a command on Windows
            try:
                output = subprocess.check_output('arp -a', shell=True, text=True, timeout=10)
                
                print(f"📋 ARP table output length: {len(output)} chars")
                
                # Parse the output to find the MAC address
                for line in output.splitlines():
                    line = line.strip()
                    if ip_address in line and not line.startswith('Interface:'):
                        print(f"🎯 Found line: {line}")
                        # Split the line and extract MAC address
                        parts = line.split()
                        print(f"📝 Line parts: {parts}")
                        if len(parts) >= 2:
                            # MAC address is typically the second field
                            mac_candidate = parts[1]
                            print(f"🔍 MAC candidate: {mac_candidate}")
                            # Validate MAC address format (xx-xx-xx-xx-xx-xx)
                            if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_candidate):
                                print(f"✅ Valid MAC found: {mac_candidate}")
                                return mac_candidate
            except subprocess.TimeoutExpired:
                print("⏱️ ARP command timed out")
            except Exception as e:
                print(f"❌ ARP error: {e}")
                
            # Try alternative method: arp -a <ip>
            try:
                output = subprocess.check_output(f'arp -a {ip_address}', shell=True, text=True, timeout=10)
                
                print(f"📋 Specific ARP output:\n{output}")
                
                # Parse the specific IP output
                for line in output.splitlines():
                    line = line.strip()
                    if ip_address in line and not line.startswith('Interface:'):
                        print(f"🎯 Found specific line: {line}")
                        parts = line.split()
                        print(f"📝 Specific line parts: {parts}")
                        if len(parts) >= 2:
                            mac_candidate = parts[1]
                            print(f"🔍 Specific MAC candidate: {mac_candidate}")
                            if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_candidate):
                                print(f"✅ Valid specific MAC found: {mac_candidate}")
                                return mac_candidate
            except subprocess.TimeoutExpired:
                print("⏱️ Specific ARP command timed out")
            except Exception as e:
                print(f"❌ Specific ARP error: {e}")
                
    except Exception as e:
        print(f"❌ Error getting MAC address for {ip_address}: {e}")
    
    print(f"❌ No MAC address found for {ip_address}")
    return None

if __name__ == "__main__":
    test_ips = ['155.235.81.1', '155.235.81.65', '192.168.1.1']
    
    for ip in test_ips:
        print(f"\n{'='*50}")
        result = get_mac_address_from_ip(ip)
        print(f"Final result for {ip}: {result}")
