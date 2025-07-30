#!/usr/bin/env python3
"""
Test Terminal Ping Function
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

def test_terminal_ping():
    """Test the terminal ping functionality"""
    
    logger.info("🔍 Testing Terminal Ping Function")
    logger.info("=" * 40)
    
    # First, get the list of terminals
    try:
        response = requests.get(
            f"{BASE_URL}/admin/terminal-management/api/terminals",
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            terminals = result.get('terminals', [])
            
            logger.info(f"✅ Found {len(terminals)} terminals")
            
            if terminals:
                for terminal in terminals:
                    logger.info(f"📱 Terminal: {terminal['name']} ({terminal['id']})")
                    logger.info(f"   IP: {terminal['ip_address']}")
                    logger.info(f"   Status: {terminal['status']}")
                    
                    # Test ping for this terminal
                    if terminal['ip_address']:
                        test_ping_terminal(terminal['id'], terminal['name'])
                    else:
                        logger.warning(f"   ⚠️ No IP address configured for {terminal['name']}")
                    
                    logger.info("")
            else:
                logger.warning("❌ No terminals found")
        else:
            logger.error(f"❌ Failed to get terminals: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error getting terminals: {e}")

def test_ping_terminal(terminal_id, terminal_name):
    """Test ping for a specific terminal"""
    logger.info(f"🔄 Pinging terminal: {terminal_name}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/admin/terminal-management/api/terminals/{terminal_id}/ping",
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"   Response: {json.dumps(result, indent=4)}")
            
            if result.get('online'):
                response_time = result.get('response_time', 'N/A')
                logger.info(f"   ✅ Terminal is ONLINE (Response time: {response_time}ms)")
                logger.info(f"   📝 Message: {result.get('message', 'No message')}")
            else:
                logger.info(f"   ❌ Terminal is OFFLINE")
                logger.info(f"   📝 Message: {result.get('message', 'No message')}")
        else:
            logger.error(f"   ❌ Ping failed: {response.status_code}")
            logger.error(f"   📝 Response: {response.text}")
            
    except Exception as e:
        logger.error(f"   ❌ Error pinging terminal: {e}")

def main():
    """Main function"""
    logger.info("🚀 Terminal Ping Test")
    
    test_terminal_ping()
    
    logger.info("")
    logger.info("✅ Test completed!")
    logger.info("💡 Check the terminal management page to see if ping results show up")

if __name__ == "__main__":
    main()
