"""
Helper functions for terminal management, network discovery, and device cache
"""

import ipaddress, subprocess, socket, platform, re, time, concurrent.futures, threading
import os
from datetime import datetime
from flask import current_app
from ..services.database import db
from ..services.device_cache import DeviceCacheManager

# Initialize device cache manager
cache_file_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'device_cache.json')
device_cache_manager = DeviceCacheManager(cache_file_path)

def is_likely_dhcp_client(ip_address, mac_address):
    """Filter out non-DHCP client addresses from ARP table - less aggressive filtering"""
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        
        # Only exclude obvious non-device addresses
        
        # Exclude multicast addresses (224.0.0.0 - 239.255.255.255)
        if ip_obj.is_multicast:
            return False
            
        # Exclude broadcast addresses
        if ip_obj == ipaddress.ip_address('255.255.255.255'):
            return False
            
        # Exclude loopback addresses (127.x.x.x)
        if ip_obj.is_loopback:
            return False
            
        # Exclude link-local addresses (169.254.x.x)  
        if ip_obj.is_link_local:
            return False
        
        # Exclude broadcast MAC addresses
        mac_lower = mac_address.lower().replace(':', '-')
        if mac_lower == 'ff-ff-ff-ff-ff-ff':
            return False
            
        # Be more permissive - allow most other addresses
        # This includes private networks and some public ranges
        return True
        
    except Exception as e:
        # If there's any parsing error, include the entry (be permissive)
        return True

def discover_active_dhcp_clients(app, session_id, discovery_progress, discovery_lock):
    """Discover additional active DHCP clients by pinging common DHCP ranges"""
    try:
        # Update progress
        with discovery_lock:
            discovery_progress[session_id]['message'] = 'Scanning for additional DHCP clients...'
        
        additional_devices = []
        
        # Common DHCP ranges to scan
        dhcp_ranges = [
            ('10.0.0.1', '10.0.0.50'),    # Router to first 50 IPs
            ('192.168.1.1', '192.168.1.50'),
            ('192.168.0.1', '192.168.0.50'),
        ]
        
        for start_ip, end_ip in dhcp_ranges:
            try:
                start = ipaddress.ip_address(start_ip)
                end = ipaddress.ip_address(end_ip)
                
                # Only scan if we're in this network
                current_network = None
                try:
                    # Try to detect current network from existing ARP entries or system
                    import socket
                    hostname = socket.gethostname()
                    local_ip = socket.gethostbyname(hostname)
                    
                    if ipaddress.ip_address(local_ip).is_private:
                        # Determine if we should scan this range
                        local_network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
                        scan_network = ipaddress.ip_network(f"{start_ip}/24", strict=False)
                        
                        if local_network != scan_network:
                            continue  # Skip ranges not on our network
                        
                except Exception:
                    continue
                
                # Quick ping scan of the range
                current = start
                scan_count = 0
                max_scans = 20  # Limit to prevent long delays
                
                while current <= end and scan_count < max_scans:
                    try:
                        # Quick ping with very short timeout
                        ping_result = ping_host(str(current))
                        if ping_result['online']:
                            # Try to get MAC address for this IP
                            mac_address = get_mac_address_from_arp(str(current))
                            if mac_address and is_likely_dhcp_client(str(current), mac_address):
                                additional_devices.append({
                                    'ip': str(current),
                                    'mac': mac_address
                                })
                                app.logger.info(f"Found additional active device: {current}")
                    except Exception as e:
                        app.logger.debug(f"Error scanning {current}: {e}")
                    
                    current = ipaddress.ip_address(int(current) + 1)
                    scan_count += 1
                    
                    # Check if discovery was cancelled
                    with discovery_lock:
                        if discovery_progress[session_id]['cancelled']:
                            return additional_devices
                            
            except Exception as e:
                app.logger.debug(f"Error scanning range {start_ip}-{end_ip}: {e}")
                continue
        
        return additional_devices
        
    except Exception as e:
        app.logger.error(f"Error in discover_active_dhcp_clients: {e}")
        return []

def get_mac_address_from_arp(ip_address):
    """Get MAC address from ARP table for a specific IP"""
    try:
        if platform.system().lower() == 'windows':
            output = subprocess.check_output(f'arp -a {ip_address}', shell=True, text=True, timeout=5)
            for line in output.splitlines():
                if ip_address in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        mac = parts[1]
                        if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
                            return mac
        else:
            output = subprocess.check_output(['arp', '-n', ip_address], text=True, timeout=5)
            match = re.search(r'([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', output)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None

def check_terminal_status(ip_address):
    """Check if terminal is online"""
    if not ip_address:
        return 'offline'
    
    result = ping_host(ip_address)
    return 'online' if result['online'] else 'offline'

def ping_host(host):
    """Ping a host to check connectivity"""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', host]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return {
                'online': True,
                'message': 'Host is reachable'
            }
        else:
            return {
                'online': False,
                'message': 'Host is unreachable'
            }
    except Exception as e:
        return {
            'online': False,
            'message': f'Ping failed: {str(e)}'
        }

def ping_host_enhanced(host, timeout=5, count=3):
    """Enhanced ping function with multiple attempts and detailed results"""
    try:
        # Platform-specific ping command
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
        
        # Build ping command
        command = ['ping', param, str(count), timeout_param, str(timeout * 1000), host]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout * count + 5)
        
        response_times = []
        successful_pings = 0
        total_pings = count
        
        if result.returncode == 0:
            # Parse response times from output
            lines = result.stdout.splitlines()
            for line in lines:
                if 'time=' in line.lower() or 'time<' in line.lower():
                    # Extract time value
                    time_match = re.search(r'time[<=](\d+\.?\d*)ms', line.lower())
                    if time_match:
                        response_times.append(float(time_match.group(1)))
                        successful_pings += 1
        
        if response_times:
            return {
                'online': True,
                'response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'packet_loss': ((total_pings - successful_pings) / total_pings) * 100,
                'successful_pings': successful_pings,
                'total_pings': total_pings,
                'message': 'Host is reachable'
            }
        
        # If we get here, ping failed or no response times found
        return {
            'online': False,
            'response_time': None,
            'min_response_time': None,
            'max_response_time': None,
            'packet_loss': 100,
            'successful_pings': 0,
            'total_pings': total_pings,
            'message': 'Host is unreachable'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'online': False,
            'response_time': None,
            'min_response_time': None,
            'max_response_time': None,
            'packet_loss': 100,
            'successful_pings': 0,
            'total_pings': count,
            'message': f'Ping timed out after {timeout}s'
        }
    except Exception as e:
        return {
            'online': False,
            'response_time': None,
            'min_response_time': None,
            'max_response_time': None,
            'packet_loss': 100,
            'successful_pings': 0,
            'total_pings': count,
            'message': f'Ping failed: {str(e)}'
        }

def log_terminal_action(terminal_id, action, details=None):
    """Log terminal actions"""
    try:
        log_entry = {
            'terminal_id': terminal_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        # Save to database (implement this in your database service)
        db.save_terminal_log(log_entry)
    except Exception as e:
        print(f"Failed to log terminal action: {e}")

def get_hostname_from_ip(ip_address):
    """Get hostname from IP address using reverse DNS lookup"""
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
        return hostname
    except (socket.herror, socket.gaierror):
        # If reverse DNS fails, return the IP address
        return ip_address
    except Exception as e:
        print(f"Error getting hostname for {ip_address}: {e}")
        return ip_address

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
        try:
            # Try to get current app for logging if available
            from flask import current_app
            current_app.logger.debug(f"Error getting MAC for {ip_address}: {e}")
        except:
            # If no app context, just pass
            pass
        return None

def get_mac_from_ip_with_ping(ip_address):
    """Get MAC address from IP address, pinging first to populate ARP table if needed"""
    try:
        # First, try to get MAC from ARP table without ping
        mac = get_mac_from_ip(ip_address)
        if mac:
            return mac
        
        # If no MAC found, ping first to populate ARP table, then retry
        if platform.system().lower() == 'windows':
            # Quick ping to populate ARP table
            ping_result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip_address], 
                                       capture_output=True, text=True, timeout=3)
            
            # Wait a brief moment for ARP table to update
            import time
            time.sleep(0.1)
            
            # Now try to get MAC again
            if ping_result.returncode == 0:
                return get_mac_from_ip(ip_address)
        
        return None
    except Exception as e:
        try:
            # Try to get current app for logging if available
            from flask import current_app
            current_app.logger.debug(f"Error getting MAC with ping for {ip_address}: {e}")
        except:
            # If no app context, just pass
            pass
        return None

def get_cached_device_info(ip_address):
    """Get cached device information for known devices"""
    return device_cache_manager.get_device_info(ip_address)

def is_stoyanov_network(ip_range_start, ip_range_end):
    """Check if the discovery is for the Stoyanov network"""
    return (ip_range_start == "155.235.81.1" and ip_range_end == "155.235.81.254") or \
           (ip_range_start == "155.235.81.0" and ip_range_end == "155.235.81.255")

def discover_static_devices_with_progress(session_id, app, discovery_progress, discovery_lock, request_settings=None):
    """Discover static devices with progress tracking"""
    
    # Create application context for this thread
    with app.app_context():
        try:
            app.logger.info(f"Starting static device discovery for session {session_id}")
            
            # Use request settings if provided, otherwise fall back to database settings
            if request_settings:
                settings = request_settings
                app.logger.info(f"Using request settings: {settings}")
            else:
                # Get network settings from database as fallback
                settings = db.get_network_settings()
                if not settings:
                    settings = {
                        'ip_range_start': '192.168.1.1',
                        'ip_range_end': '192.168.1.254',
                        'scan_timeout': 5,
                        'concurrent_scans': 10
                    }
                app.logger.info(f"Using database/default settings: {settings}")
            
            # Parse IP range
            start_ip = ipaddress.ip_address(settings['ip_range_start'])
            end_ip = ipaddress.ip_address(settings['ip_range_end'])
            
            # Generate IP list
            ip_list = []
            current_ip = start_ip
            while current_ip <= end_ip:
                ip_list.append(str(current_ip))
                current_ip += 1
            
            total_ips = len(ip_list)
            app.logger.info(f"Scanning {total_ips} IP addresses...")
            
            # Update progress
            with discovery_lock:
                discovery_progress[session_id] = {
                    'status': 'scanning',
                    'progress': 0,
                    'total': total_ips,
                    'current': 0,
                    'found_devices': [],
                    'cancelled': False,
                    'message': f'Reading ARP table and scanning {total_ips} IP addresses...'
                }
            
            # Read ARP table first to get available MAC addresses - more efficient than individual lookups
            arp_lookup = {}
            mac_to_ip = {}
            if platform.system().lower() == 'windows':
                try:
                    app.logger.info("Reading ARP table for device identification...")
                    output = subprocess.check_output('arp -a', shell=True, text=True, timeout=10)
                    
                    app.logger.debug(f"Raw ARP output:\n{output[:500]}...")  # Log first 500 chars
                    
                    for line in output.split('\n'):
                        parts = line.strip().split()
                        if len(parts) >= 3 and '.' in parts[0] and '-' in parts[1]:
                            ip = parts[0].strip()
                            mac = parts[1].strip().upper().replace('-', ':')
                            
                            app.logger.debug(f"ARP line: {line.strip()} -> IP: {ip}, MAC: {mac}")
                            
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
                    
                    app.logger.info(f"ARP table loaded: {len(arp_lookup)} entries with {len(mac_to_ip)} unique MAC addresses")
                except Exception as e:
                    app.logger.warning(f"Could not read ARP table: {e}")
            
            devices = []
            
            # Scan IPs in batches
            batch_size = settings.get('concurrent_scans', 10)
            for i in range(0, total_ips, batch_size):
                # Check if cancelled
                with discovery_lock:
                    if discovery_progress[session_id]['cancelled']:
                        discovery_progress[session_id]['status'] = 'cancelled'
                        break

                batch = ip_list[i : i + batch_size]
                for ip in batch:
                    device = {
                        'ip_address': ip,
                        'mac_address': arp_lookup.get(ip, 'Unknown'),
                        'valid_mac': arp_lookup.get(ip) not in [None, 'Unknown', 'FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00']
                    }
                    devices.append(device)

            # Update progress with found devices
            with discovery_lock:
                discovery_progress[session_id]['found_devices'] = devices
                discovery_progress[session_id]['status'] = 'completed'
                discovery_progress[session_id]['message'] = f"Discovery completed. Found {len(devices)} devices."

            app.logger.info(f"Static scan completed: {len(devices)} devices found.")
            
            # Clean up progress after 5 minutes
            def cleanup_progress():
                time.sleep(300)  # 5 minutes
                with discovery_lock:
                    if session_id in discovery_progress:
                        del discovery_progress[session_id]
            
            cleanup_thread = threading.Thread(target=cleanup_progress)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
        except Exception as e:
            app.logger.error(f"Error discovering static devices: {e}")
            with discovery_lock:
                discovery_progress[session_id]['status'] = 'error'
                discovery_progress[session_id]['error'] = str(e)

def discover_dhcp_devices_with_progress(session_id, app, discovery_progress, discovery_lock):
    """Discover DHCP devices by scanning the configured network range"""
    
    # Create application context for this thread
    with app.app_context():
        try:
            # Get network settings for the range to scan
            settings = db.get_network_settings()
            if not settings:
                settings = {
                    'ip_range_start': '10.0.0.1',    # Default to current network range
                    'ip_range_end': '10.0.0.255',
                    'scan_timeout': 5,
                    'concurrent_scans': 20
                }
            
            # Parse IP range
            try:
                start_ip = ipaddress.ip_address(settings['ip_range_start'])
                end_ip = ipaddress.ip_address(settings['ip_range_end'])
            except ValueError:
                app.logger.error(f"Invalid IP range: {settings['ip_range_start']} - {settings['ip_range_end']}")
                with discovery_lock:
                    discovery_progress[session_id]['status'] = 'error'
                    discovery_progress[session_id]['error'] = 'Invalid IP range in network settings'
                return
            
            # Generate IP list to scan
            ip_list = []
            current_ip = start_ip
            while current_ip <= end_ip:
                ip_list.append(str(current_ip))
                current_ip += 1
            
            total_ips = len(ip_list)
            app.logger.info(f"DHCP Discovery: Scanning {total_ips} IP addresses from {start_ip} to {end_ip}")
            
            # Clean up cache first - remove any multicast/broadcast addresses that may have been cached
            try:
                removed_count = device_cache_manager.cleanup_invalid_devices()
                if removed_count > 0:
                    app.logger.info(f"Cleaned up {removed_count} invalid devices from cache before discovery")
            except Exception as e:
                app.logger.warning(f"Cache cleanup failed: {e}")
            
            # Update progress
            with discovery_lock:
                discovery_progress[session_id]['status'] = 'scanning'
                discovery_progress[session_id]['progress'] = 10
                discovery_progress[session_id]['total'] = total_ips
                discovery_progress[session_id]['current'] = 0
                discovery_progress[session_id]['found_devices'] = []
                discovery_progress[session_id]['cancelled'] = False
                discovery_progress[session_id]['message'] = f'Scanning {total_ips} IP addresses for DHCP devices...'
            
            # Get cached devices and filter to the requested IP range
            all_cached = device_cache_manager.get_all_devices()
            # Only include cached devices within the configured range
            def ip_in_range(ip_str):
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    return start_ip <= ip_obj <= end_ip
                except Exception:
                    return False
            cached_devices = {ip: info for ip, info in all_cached.items() if ip_in_range(ip)}
            cached_ips = set(cached_devices.keys())
            app.logger.info(f"Found {len(cached_ips)} cached devices to display immediately")
            
            # Quickly read ARP table to check for IP changes
            arp_lookup = {}
            mac_to_current_ip = {}  # Track current IP for each MAC address
            if platform.system().lower() == 'windows':
                try:
                    app.logger.info("Reading ARP table to check for device IP changes...")
                    output = subprocess.check_output('arp -a', shell=True, text=True, timeout=10)
                    
                    for line in output.split('\n'):
                        parts = line.strip().split()
                        if len(parts) >= 3 and '.' in parts[0] and '-' in parts[1]:
                            ip = parts[0].strip()
                            mac = parts[1].strip().upper().replace('-', ':')
                            # Only include ARP entries within the requested range
                            if not ip_in_range(ip):
                                continue
                            
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
                                mac_to_current_ip[mac] = ip
                    
                    app.logger.info(f"ARP table loaded: {len(arp_lookup)} entries with {len(mac_to_current_ip)} unique MAC addresses")
                except Exception as e:
                    app.logger.warning(f"Could not read ARP table: {e}")
            
            devices = []
            
            # Process cached devices, checking for IP changes first
            with discovery_lock:
                discovery_progress[session_id]['progress'] = 15
                discovery_progress[session_id]['message'] = 'Loading cached devices with MAC addresses...'
            
            for cached_ip, cached_info in cached_devices.items():
                # Only load cached devices that have valid MAC addresses
                cached_mac = cached_info.get('mac_address')
                if not cached_mac or cached_mac in ['Unknown', 'N/A', '', None]:
                    app.logger.debug(f"Skipping cached device {cached_ip} - no valid MAC address")
                    continue
                
                # Skip multicast/broadcast addresses that might be cached
                try:
                    ip_obj = ipaddress.ip_address(cached_ip)
                    if (ip_obj.is_multicast or 
                        cached_ip.endswith('.255') or 
                        cached_ip == '255.255.255.255' or
                        cached_mac.upper() in ['FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00'] or
                        cached_mac.upper().startswith('01:00:5E')):
                        app.logger.debug(f"Skipping cached multicast/broadcast device {cached_ip} - MAC: {cached_mac}")
                        continue
                except ValueError:
                    app.logger.debug(f"Skipping cached device {cached_ip} - invalid IP format")
                    continue
                
                # Check if this MAC address now has a different IP in ARP table
                normalized_mac = cached_mac.upper().replace('-', ':')
                current_ip_from_arp = mac_to_current_ip.get(normalized_mac)
                
                final_ip = cached_ip  # Default to cached IP
                ip_changed = False
                
                if current_ip_from_arp and current_ip_from_arp != cached_ip:
                    app.logger.info(f"MAC {normalized_mac} has changed IP: {cached_ip} → {current_ip_from_arp}")
                    final_ip = current_ip_from_arp
                    ip_changed = True
                    
                    # Update the cache with new IP
                    device_cache_manager.update_device_ip_by_mac(normalized_mac, current_ip_from_arp)
                else:
                    app.logger.debug(f"MAC {normalized_mac} IP unchanged: {cached_ip}")
                
                # Quick ping to check if device is online at final IP
                try:
                    ping_result = ping_host(final_ip)
                    is_online = ping_result['online']
                    response_time = ping_result.get('response_time')
                except Exception:
                    is_online = False
                    response_time = None
                
                # Determine display name prioritizing custom name bound to MAC address
                display_hostname = cached_info.get('hostname', f'Device-{final_ip.replace(".", "-")}')
                custom_name = cached_info.get('custom_name')
                
                cached_device = {
                    'ip_address': final_ip,  # Use the current IP (updated if changed)
                    'mac_address': cached_mac,
                    'hostname': display_hostname,
                    'custom_name': custom_name,  # This is bound to MAC address, not IP
                    'device_type': cached_info.get('device_type', 'unknown'),
                    'manufacturer': cached_info.get('manufacturer', 'unknown'),
                    'online': is_online,
                    'response_time': response_time,
                    'discovered_at': datetime.now().isoformat(),
                    'discovery_method': 'cache'
                }
                
                devices.append(cached_device)
                
                # Immediately update progress with each cached device for real-time display
                with discovery_lock:
                    discovery_progress[session_id]['found_devices'].append(cached_device)
                    if ip_changed:
                        app.logger.info(f"Added cached device with updated IP: {final_ip} ({cached_info.get('hostname', 'Unknown')}) - MAC: {cached_mac} (was {cached_ip})")
                    else:
                        app.logger.info(f"Added cached device to real-time display: {final_ip} ({cached_info.get('hostname', 'Unknown')}) - MAC: {cached_mac}")
            
            app.logger.info(f"Loaded {len(devices)} cached devices with valid MAC addresses for immediate display")
            
            # Continue with network scanning for any remaining devices
            # Filter out cached IPs from scanning (skip known devices unless IP changed)
            current_cached_ips = set(device['ip_address'] for device in devices)  # Use current IPs after updates
            ips_to_scan = [ip for ip in ip_list if ip not in current_cached_ips]
            app.logger.info(f"Scanning {len(ips_to_scan)} new IPs (skipping {len(current_cached_ips)} known devices)")
            
            # Scan IPs in batches
            batch_size = settings.get('concurrent_scans', 20)
            processed_count = 0
            
            with discovery_lock:
                discovery_progress[session_id]['progress'] = 25
                discovery_progress[session_id]['total'] = len(ips_to_scan)
                discovery_progress[session_id]['message'] = f'Scanning {len(ips_to_scan)} remaining IP addresses...'
            
            for i in range(0, len(ips_to_scan), batch_size):
                # Check if cancelled
                with discovery_lock:
                    if discovery_progress[session_id]['cancelled']:
                        return
                
                batch = ips_to_scan[i:i+batch_size]
                
                # Scan batch concurrently
                with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                    future_to_ip = {
                        executor.submit(ping_host, ip): ip 
                        for ip in batch
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_ip):
                        ip = future_to_ip[future]
                        processed_count += 1
                        
                        try:
                            # Update progress for each IP processed
                            progress_percent = 20 + int((processed_count / len(ips_to_scan)) * 70)  # 20% to 90%
                            with discovery_lock:
                                discovery_progress[session_id]['progress'] = progress_percent
                                discovery_progress[session_id]['current'] = processed_count
                                discovery_progress[session_id]['message'] = f'Checking {ip} ({processed_count}/{len(ips_to_scan)})...'
                            
                            ping_result = future.result()
                            if ping_result['online']:
                                # Get MAC address from cached ARP lookup or by querying
                                mac_address = arp_lookup.get(ip)
                                if not mac_address:
                                    mac_address = get_mac_from_ip(ip)
                                
                                # Only proceed if we have a valid MAC address and it's not multicast/broadcast
                                if not mac_address or mac_address in ['Unknown', 'N/A', '', None]:
                                    app.logger.debug(f"Skipping {ip} - no valid MAC address found")
                                    continue
                                
                                # Skip multicast/broadcast MAC addresses
                                if (mac_address.upper() in ['FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00'] or
                                    mac_address.upper().startswith('01:00:5E')):
                                    app.logger.debug(f"Skipping {ip} - multicast/broadcast MAC address: {mac_address}")
                                    continue
                                
                                # Check if this MAC address already exists in our current device list (avoid duplicates)
                                normalized_mac = mac_address.upper().replace('-', ':')
                                if any(device['mac_address'].upper().replace('-', ':') == normalized_mac for device in devices):
                                    app.logger.debug(f"Skipping {ip} - MAC {normalized_mac} already processed")
                                    continue
                                
                                # Check if this MAC address already exists in cache with different IP
                                cached_device_by_mac = device_cache_manager.get_device_by_mac(mac_address)
                                if cached_device_by_mac and cached_device_by_mac.get('ip_address') != ip:
                                    old_ip = cached_device_by_mac.get('ip_address')
                                    app.logger.info(f"MAC {mac_address} found at new IP {ip} (was cached as {old_ip})")
                                    # Update the IP address in cache for this MAC
                                    device_cache_manager.update_device_ip_by_mac(mac_address, ip)
                                    app.logger.info(f"Updated cache: MAC {mac_address} moved from {old_ip} to {ip}")
                                
                                # Get hostname with better fallback to MAC-based custom name
                                hostname = get_hostname_from_ip(ip)
                                if not hostname or hostname == ip:
                                    hostname = f'Device-{ip.replace(".", "-")}'
                                
                                # Check if we have any cached info for this device (by IP or by MAC)
                                cached_info = device_cache_manager.get_device_info(ip)
                                if not cached_info and cached_device_by_mac:
                                    # Use MAC-based cache info if no IP-based info exists
                                    cached_info = cached_device_by_mac
                                    app.logger.info(f"Using MAC-based info for {ip}: custom_name={cached_info.get('custom_name')}")
                                
                                # Priority for device name: custom_name from MAC > hostname > IP-based fallback
                                display_custom_name = cached_info.get('custom_name') if cached_info else None
                                
                                device_info = {
                                    'ip_address': ip,
                                    'mac_address': mac_address,
                                    'hostname': hostname,
                                    'custom_name': display_custom_name,  # Properly bound to MAC address
                                    'device_type': cached_info.get('device_type') if cached_info else 'unknown',
                                    'manufacturer': cached_info.get('manufacturer') if cached_info else 'unknown',
                                    'online': True,
                                    'response_time': ping_result.get('response_time'),
                                    'discovered_at': datetime.now().isoformat(),
                                    'discovery_method': 'network_scan'
                                }
                                
                                devices.append(device_info)
                                app.logger.info(f"Found new device with MAC: {ip} ({hostname}) - MAC: {mac_address}")
                                
                                # Immediately update progress with found device for real-time display
                                with discovery_lock:
                                    discovery_progress[session_id]['found_devices'].append(device_info)
                                    app.logger.info(f"Added new device to real-time display: {ip} ({hostname}) - Total devices: {len(discovery_progress[session_id]['found_devices'])}")
                                
                                # Update device cache ONLY if we have a valid MAC address
                                device_data = {
                                    'hostname': hostname,
                                    'mac_address': mac_address,  # This is guaranteed to be valid now
                                    'device_type': device_info['device_type'],
                                    'manufacturer': device_info['manufacturer'],
                                    'last_seen': datetime.now().isoformat()
                                }
                                device_cache_manager.update_device_info(ip, device_data)
                                app.logger.info(f"Saved device to cache: {ip} with MAC {mac_address}")
                                
                        except Exception as e:
                            app.logger.debug(f"Error scanning IP {ip}: {e}")
            
            # Scanning complete - just sort the devices by IP address
            with discovery_lock:
                discovery_progress[session_id]['progress'] = 95
                discovery_progress[session_id]['message'] = 'Finalizing device list...'
            
            # Sort devices by IP address
            devices.sort(key=lambda x: ipaddress.ip_address(x['ip_address']))
            
            # Update the sorted list in progress
            with discovery_lock:
                discovery_progress[session_id]['found_devices'] = devices
            
            total_devices = len(devices)
            new_devices = len([d for d in devices if d['discovery_method'] == 'network_scan'])
            cached_device_count = len([d for d in devices if d['discovery_method'] == 'cache'])
            
            app.logger.info(f"DHCP discovery completed: Found {total_devices} total devices ({new_devices} new from scan, {cached_device_count} from cache)")
            
            # Update final progress
            with discovery_lock:
                discovery_progress[session_id]['status'] = 'completed'
                discovery_progress[session_id]['progress'] = 100
                discovery_progress[session_id]['found_devices'] = devices
                discovery_progress[session_id]['message'] = f'Network scan completed: Found {new_devices} new devices, {cached_device_count} cached devices'
                
                app.logger.info(f"Final progress update for session {session_id}: {total_devices} devices total")

        except Exception as e:
            app.logger.error(f"Error discovering DHCP devices: {e}")
            with discovery_lock:
                discovery_progress[session_id]['status'] = 'error'
                discovery_progress[session_id]['error'] = str(e)
