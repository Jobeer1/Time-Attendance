"""
Debug script to test DHCP discovery directly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attendance.routes.helpers import discover_dhcp_devices_with_progress
import threading
import uuid
from flask import Flask

def test_dhcp_discovery():
    """Test DHCP discovery directly"""
    
    # Create a minimal Flask app
    app = Flask(__name__)
    
    # Create progress tracking variables
    discovery_progress = {}
    discovery_lock = threading.Lock()
    session_id = str(uuid.uuid4())
    
    print(f"Testing DHCP discovery with session ID: {session_id}")
    
    # Initialize progress
    with discovery_lock:
        discovery_progress[session_id] = {
            'status': 'initializing',
            'progress': 0,
            'total': 0,
            'current': 0,
            'found_devices': [],
            'cancelled': False,
            'message': 'Initializing discovery...'
        }
    
    # Run discovery
    with app.app_context():
        try:
            discover_dhcp_devices_with_progress(session_id, app, discovery_progress, discovery_lock)
            
            # Check results
            with discovery_lock:
                result = discovery_progress[session_id]
                print(f"\n=== Discovery Results ===")
                print(f"Status: {result['status']}")
                print(f"Progress: {result['progress']}%")
                print(f"Message: {result['message']}")
                print(f"Found devices: {len(result['found_devices'])}")
                
                if result['found_devices']:
                    print("\n=== Device List ===")
                    for i, device in enumerate(result['found_devices'][:5]):  # Show first 5
                        print(f"  Device {i+1}:")
                        print(f"    IP: {device['ip_address']}")
                        print(f"    MAC: {device['mac_address']}")
                        print(f"    Hostname: {device['hostname']}")
                        print(f"    Online: {device['online']}")
                        print(f"    Discovery Method: {device['discovery_method']}")
                    
                    if len(result['found_devices']) > 5:
                        print(f"    ... and {len(result['found_devices']) - 5} more devices")
                else:
                    print("  No devices found")
                    if 'error' in result:
                        print(f"  Error: {result['error']}")
                        
        except Exception as e:
            print(f"Error during discovery: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_dhcp_discovery()
