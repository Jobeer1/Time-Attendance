#!/usr/bin/env python3
"""
Test MAC Address Lookup Function
"""

import requests
import json
import logging
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://localhost:5003"

def test_mac_lookup():
    """Test MAC address lookup functionality"""
    
    logger.info("🔍 Testing MAC Address Lookup Function")
    logger.info("=" * 50)
    
    # Test with some common IP addresses
    test_ips = [
        "192.168.1.1",      # Common router IP
        "155.235.81.127",   # Your server IP
        "127.0.0.1",        # Localhost
        "8.8.8.8"           # Google DNS (likely no MAC)
    ]
    
    for ip in test_ips:
        logger.info(f"🔍 Testing IP: {ip}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/admin/terminal-management/api/get-mac-address",
                json={"ip_address": ip},
                verify=False,
                timeout=15
            )
            
            logger.info(f"   Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"   Result: {json.dumps(result, indent=6)}")
                
                if result.get('success') and result.get('mac_address'):
                    logger.info(f"   ✅ MAC found: {result['mac_address']}")
                else:
                    logger.info(f"   ⚠️ No MAC: {result.get('message')}")
            else:
                logger.error(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            logger.error(f"   ❌ Exception: {e}")
        
        logger.info("")
    
    logger.info("🎯 INSTRUCTIONS FOR MANUAL TESTING:")
    logger.info("=" * 40)
    logger.info("1. Open: https://localhost:5003/admin/terminal-management/terminals")
    logger.info("2. Click 'Add Terminal' button")
    logger.info("3. Enter an IP address in the IP field")
    logger.info("4. Click the 'Get MAC' button")
    logger.info("5. MAC address should be auto-filled")
    logger.info("")
    logger.info("💡 For best results:")
    logger.info("   • Use IP addresses on your local network")
    logger.info("   • Ping the IP first to populate ARP table")
    logger.info("   • Try your router IP (usually 192.168.1.1)")

def main():
    """Main function"""
    logger.info("🚀 MAC Address Lookup Test")
    
    test_mac_lookup()
    
    logger.info("✅ Test completed!")

if __name__ == "__main__":
    main()
