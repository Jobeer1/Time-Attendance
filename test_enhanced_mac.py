#!/usr/bin/env python3
"""Test the enhanced MAC lookup functionality"""

import subprocess
import platform
import re
import time

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

def get_mac_from_ip_with_ping(ip_address):
    """Get MAC address from IP address, pinging first to populate ARP table if needed"""
    try:
        # First, try to get MAC from ARP table without ping
        mac = get_mac_from_ip(ip_address)
        if mac:
            print(f"  📍 MAC found in ARP table immediately: {mac}")
            return mac
        
        print(f"  🔍 No MAC in ARP table, pinging to populate...")
        
        # If no MAC found, ping first to populate ARP table, then retry
        if platform.system().lower() == 'windows':
            # Quick ping to populate ARP table
            ping_result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip_address], 
                                       capture_output=True, text=True, timeout=3)
            
            print(f"  📡 Ping result: {'SUCCESS' if ping_result.returncode == 0 else 'FAILED'}")
            
            # Wait a brief moment for ARP table to update
            time.sleep(0.2)
            
            # Now try to get MAC again
            if ping_result.returncode == 0:
                mac = get_mac_from_ip(ip_address)
                if mac:
                    print(f"  ✅ MAC found after ping: {mac}")
                    return mac
                else:
                    print(f"  ❌ No MAC found even after successful ping")
        
        return None
    except Exception as e:
        print(f"  ❌ Error getting MAC with ping for {ip_address}: {e}")
        return None

def test_enhanced_mac_lookup():
    """Test the enhanced MAC lookup on known devices"""
    print("=== Testing Enhanced MAC Lookup ===")
    
    # Test devices that we know are online
    test_ips = ['10.0.0.2', '10.0.0.6', '10.0.0.7', '10.0.0.8', '10.0.0.109']
    
    for ip in test_ips:
        print(f"\nTesting {ip}...")
        
        # Test basic lookup first
        print("  1. Basic ARP lookup:")
        basic_mac = get_mac_from_ip(ip)
        if basic_mac:
            print(f"     ✅ Found: {basic_mac}")
        else:
            print(f"     ❌ Not found in ARP table")
        
        # Test enhanced lookup
        print("  2. Enhanced lookup with ping:")
        enhanced_mac = get_mac_from_ip_with_ping(ip)
        if enhanced_mac:
            print(f"     ✅ Final result: {enhanced_mac}")
        else:
            print(f"     ❌ Still no MAC found")
    
    print("\n=== Current ARP Table (10.0.0.x devices) ===")
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            for line in lines:
                if '10.0.0.' in line and 'dynamic' in line:
                    print(f"  {line.strip()}")
    except Exception as e:
        print(f"Error reading ARP table: {e}")

if __name__ == "__main__":
    test_enhanced_mac_lookup()
