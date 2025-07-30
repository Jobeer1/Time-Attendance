#!/usr/bin/env python3
"""Quick test of ARP table reading and static discovery"""

import sys
import os
import subprocess
import ipaddress
import platform

# Add current directory to path
sys.path.append('.')

def test_arp_reading():
    """Test reading ARP table"""
    print("=== Testing ARP Table Reading ===")
    
    arp_lookup = {}
    mac_to_ip = {}
    
    if platform.system().lower() == 'windows':
        try:
            print("Reading ARP table...")
            output = subprocess.check_output('arp -a', shell=True, text=True, timeout=10)
            
            for line in output.split('\n'):
                parts = line.strip().split()
                if len(parts) >= 3 and '.' in parts[0] and '-' in parts[1]:
                    ip = parts[0].strip()
                    mac = parts[1].strip().upper().replace('-', ':')
                    
                    # Enhanced filtering for IP addresses
                    try:
                        ip_obj = ipaddress.ip_address(ip)
                        
                        # Skip multicast addresses (224.0.0.0 to 239.255.255.255)
                        if ip_obj.is_multicast:
                            continue
                            
                        # Skip broadcast addresses and special addresses
                        if (ip.endswith('.255') or 
                            ip == '255.255.255.255' or 
                            ip.startswith('255.')):
                            continue
                            
                    except ValueError:
                        continue  # Invalid IP format
                    
                    # Enhanced filtering for MAC addresses
                    if (mac and 
                        mac not in ['FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00'] and
                        not mac.startswith('01:00:5E')):  # Skip multicast MAC addresses
                        arp_lookup[ip] = mac
                        mac_to_ip[mac] = ip
                        print(f"  {ip} -> {mac}")
            
            print(f"ARP table loaded: {len(arp_lookup)} entries with {len(mac_to_ip)} unique MAC addresses")
            
            # Check if our test IPs are in ARP
            test_ips = ['10.0.0.2', '10.0.0.6', '10.0.0.7', '10.0.0.8', '10.0.0.109', '10.0.0.134']
            print(f"\nChecking test IPs in ARP table:")
            for ip in test_ips:
                mac = arp_lookup.get(ip, 'NOT FOUND')
                print(f"  {ip}: {mac}")
                
            return arp_lookup
            
        except Exception as e:
            print(f"Could not read ARP table: {e}")
            return {}
    else:
        print("Not on Windows - ARP reading not implemented")
        return {}

def test_ping(ip):
    """Test ping to specific IP"""
    print(f"\n=== Testing Ping to {ip} ===")
    try:
        if platform.system().lower() == 'windows':
            result = subprocess.run(['ping', '-n', '1', '-w', '3000', ip], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  {ip} is ONLINE")
                return True
            else:
                print(f"  {ip} is OFFLINE")
                return False
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '3', ip], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  {ip} is ONLINE")
                return True
            else:
                print(f"  {ip} is OFFLINE")
                return False
    except Exception as e:
        print(f"  Error pinging {ip}: {e}")
        return False

if __name__ == "__main__":
    # Test ARP reading
    arp_lookup = test_arp_reading()
    
    # Test ping to some of the problematic IPs
    test_ips = ['10.0.0.2', '10.0.0.6', '10.0.0.7', '10.0.0.8']
    print(f"\n=== Testing Ping to Problematic IPs ===")
    for ip in test_ips:
        is_online = test_ping(ip)
        mac = arp_lookup.get(ip, 'NOT IN ARP')
        print(f"  {ip}: Online={is_online}, MAC={mac}")
