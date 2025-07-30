#!/usr/bin/env python3
"""Debug static discovery to see what's really happening"""

import sys
import subprocess
import platform
import concurrent.futures
import ipaddress

# Add current directory to path
sys.path.append('.')

def ping_host(host):
    """Ping a single host and return result"""
    try:
        if platform.system().lower() == 'windows':
            # Use ping -n 1 -w 3000 for Windows (1 ping, 3 second timeout)
            result = subprocess.run(['ping', '-n', '1', '-w', '3000', host], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract response time from ping output
                lines = result.stdout.splitlines()
                for line in lines:
                    if 'time=' in line.lower() or 'time<' in line.lower():
                        import re
                        time_match = re.search(r'time[<=](\d+)ms', line.lower())
                        if time_match:
                            response_time = int(time_match.group(1))
                        else:
                            response_time = 1
                        return {'online': True, 'response_time': response_time}
                return {'online': True, 'response_time': 1}
            else:
                return {'online': False, 'response_time': None}
        else:
            # Use ping -c 1 -W 3 for Linux/macOS (1 ping, 3 second timeout)
            result = subprocess.run(['ping', '-c', '1', '-W', '3', host], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract response time
                import re
                time_match = re.search(r'time=(\d+(?:\.\d+)?) ms', result.stdout)
                if time_match:
                    response_time = int(float(time_match.group(1)))
                else:
                    response_time = 1
                return {'online': True, 'response_time': response_time}
            else:
                return {'online': False, 'response_time': None}
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT pinging {host}")
        return {'online': False, 'response_time': None}
    except Exception as e:
        print(f"  ERROR pinging {host}: {e}")
        return {'online': False, 'response_time': None}

def test_static_discovery_range():
    """Test static discovery on a small range"""
    print("=== Testing Static Discovery Range ===")
    
    # Test the problematic IPs
    test_ips = ['10.0.0.2', '10.0.0.6', '10.0.0.7', '10.0.0.8', '10.0.0.109', '10.0.0.134']
    
    print(f"Testing {len(test_ips)} specific IPs...")
    
    online_devices = []
    offline_devices = []
    
    # Test each IP individually first
    print("\n--- Individual Ping Tests ---")
    for ip in test_ips:
        print(f"Testing {ip}...")
        result = ping_host(ip)
        if result['online']:
            online_devices.append(ip)
            print(f"  ✅ {ip} is ONLINE (response time: {result['response_time']}ms)")
        else:
            offline_devices.append(ip)
            print(f"  ❌ {ip} is OFFLINE")
    
    print(f"\nResults:")
    print(f"  Online devices: {len(online_devices)}")
    print(f"  Offline devices: {len(offline_devices)}")
    
    if online_devices:
        print(f"  Online IPs: {', '.join(online_devices)}")
    
    # Now test with concurrent scanning like the real discovery does
    print(f"\n--- Concurrent Ping Tests (like real discovery) ---")
    concurrent_results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ip = {executor.submit(ping_host, ip): ip for ip in test_ips}
        
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                result = future.result()
                concurrent_results[ip] = result
                status = "ONLINE" if result['online'] else "OFFLINE"
                response_time = f" ({result['response_time']}ms)" if result['online'] else ""
                print(f"  {ip}: {status}{response_time}")
            except Exception as e:
                print(f"  {ip}: ERROR - {e}")
                concurrent_results[ip] = {'online': False, 'response_time': None}
    
    # Compare individual vs concurrent results
    print(f"\n--- Comparison ---")
    for ip in test_ips:
        individual = ip in online_devices
        concurrent = concurrent_results.get(ip, {}).get('online', False)
        if individual != concurrent:
            print(f"  ⚠️ {ip}: Individual={individual}, Concurrent={concurrent}")
        else:
            print(f"  ✅ {ip}: Both tests agree ({individual})")

if __name__ == "__main__":
    test_static_discovery_range()
