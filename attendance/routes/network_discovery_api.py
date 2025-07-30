"""
Network Discovery API Endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import threading
import ipaddress
import subprocess
import platform
import concurrent.futures
import uuid
import time
from .helpers import *
from ..services.database import db
from ..utils.auth import is_admin_authenticated

# Global variables for progress tracking
discovery_progress = {}
discovery_lock = threading.Lock()

bp_network_discovery = Blueprint('network_discovery_api', __name__, url_prefix='/admin/terminal-management/api')

@bp_network_discovery.route('/discover-static-devices', methods=['POST'])
def api_discover_static_devices():
    """Discover devices on static IP range"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.get_json()
        current_app.logger.info(f"Received static discovery request: {data}")
        # Load saved network settings
        saved_settings = db.get_network_settings()
        ip_range_start = data.get('ip_range_start', saved_settings.get('ip_range_start', '192.168.1.1'))
        ip_range_end = data.get('ip_range_end', saved_settings.get('ip_range_end', '192.168.1.254'))
        scan_timeout = data.get('scan_timeout', saved_settings.get('scan_timeout', 5))
        concurrent_scans = data.get('concurrent_scans', saved_settings.get('concurrent_scans', 10))
        try:
            start_ip = ipaddress.ip_address(ip_range_start)
            end_ip = ipaddress.ip_address(ip_range_end)
            if start_ip > end_ip:
                return jsonify({'error': 'Invalid IP range'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid IP address format'}), 400
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        # Initialize progress tracking
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
        current_app.logger.info(f"Starting static device discovery: {ip_range_start} to {ip_range_end}")
        # Get current app for threading
        app = current_app._get_current_object()
        # Start discovery in background thread with request parameters
        def run_discovery(app_obj):
            try:
                # Pass request parameters to discovery function
                request_settings = {
                    'ip_range_start': ip_range_start,
                    'ip_range_end': ip_range_end,
                    'scan_timeout': scan_timeout,
                    'concurrent_scans': concurrent_scans
                }
                discover_static_devices_with_progress(session_id, app_obj, discovery_progress, discovery_lock, request_settings)
            except Exception as e:
                current_app.logger.error(f"Error in discovery thread: {e}")
        thread = threading.Thread(target=run_discovery, args=(app,))
        thread.daemon = True
        thread.start()
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Discovery started',
            'ip_range_start': ip_range_start,
            'ip_range_end': ip_range_end
        })
    except Exception as e:
        current_app.logger.error(f"Error in static device discovery: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/discover-dhcp-devices', methods=['POST'])
def api_discover_dhcp_devices():
    """Discover DHCP devices from ARP table"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        current_app.logger.info("Starting DHCP device discovery")
        # Load saved network settings
        saved_settings = db.get_network_settings()
        ip_range_start = saved_settings.get('ip_range_start', '192.168.1.1')
        ip_range_end = saved_settings.get('ip_range_end', '192.168.1.254')
        scan_timeout = saved_settings.get('scan_timeout', 5)
        concurrent_scans = saved_settings.get('concurrent_scans', 10)

        # Validate requested range against ARP table subnet
        import subprocess, re
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        output = result.stdout
        user_subnets = set()
        for line in output.splitlines():
            match = re.search(r'(\d+\.\d+\.\d+)\.\d+\s+([\w-]+)\s+[\w]+', line)
            if match:
                user_subnets.add(match.group(1))
        requested_subnet = '.'.join(ip_range_start.split('.')[:3])
        if requested_subnet not in user_subnets:
            return jsonify({
                'success': False,
                'error': f'Requested IP range ({ip_range_start} - {ip_range_end}) is outside your local subnet ({sorted(user_subnets)}). Please use a range within your subnet.'
            }), 400
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        # Initialize progress tracking
        with discovery_lock:
            discovery_progress[session_id] = {
                'status': 'initializing',
                'progress': 0,
                'total': 0,
                'current': 0,
                'found_devices': [],
                'cancelled': False,
                'message': 'Reading ARP table...',
                'ip_range_start': ip_range_start,
                'ip_range_end': ip_range_end,
                'scan_timeout': scan_timeout,
                'concurrent_scans': concurrent_scans
            }
        # Get current app for threading
        app = current_app._get_current_object()
        # Start DHCP discovery in background thread
        def run_dhcp_discovery(app_obj):
            try:
                discover_dhcp_devices_with_progress(session_id, app_obj, discovery_progress, discovery_lock)
            except Exception as e:
                current_app.logger.error(f"Error in DHCP discovery thread: {e}")
        thread = threading.Thread(target=run_dhcp_discovery, args=(app,))
        thread.daemon = True
        thread.start()
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'DHCP discovery started',
            'ip_range_start': ip_range_start,
            'ip_range_end': ip_range_end
        })
    except Exception as e:
        current_app.logger.error(f"Error in DHCP device discovery: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/discovery-progress/<session_id>', methods=['GET'])
def api_get_discovery_progress(session_id):
    """Get discovery progress for a session"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with discovery_lock:
            if session_id in discovery_progress:
                progress_data = discovery_progress[session_id].copy()
                
                # Enhanced response format for better frontend communication
                response = {
                    'success': True,
                    'session_id': session_id,
                    'discovery': {
                        'status': progress_data['status'],
                        'progress': progress_data['progress'],
                        'total': progress_data['total'],
                        'current': progress_data['current'],
                        'found_devices': progress_data['found_devices'],
                        'cancelled': progress_data['cancelled'],
                        'message': progress_data['message']
                    },
                    'device_count': len(progress_data['found_devices']),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Debug logging
                current_app.logger.info(f"Discovery progress response for {session_id}: status={progress_data['status']}, device_count={len(progress_data['found_devices'])}")
                
                # Add error information if available
                if 'error' in progress_data:
                    response['discovery']['error'] = progress_data['error']
                
                return jsonify(response)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Session not found or expired',
                    'session_id': session_id
                }), 404
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/discovery-cancel/<session_id>', methods=['POST'])
def api_cancel_discovery(session_id):
    """Cancel a running discovery session"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with discovery_lock:
            if session_id in discovery_progress:
                discovery_progress[session_id]['cancelled'] = True
                discovery_progress[session_id]['status'] = 'cancelled'
                discovery_progress[session_id]['message'] = 'Discovery cancelled by user'
                
                return jsonify({
                    'success': True,
                    'message': 'Discovery cancelled successfully',
                    'session_id': session_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Session not found',
                    'session_id': session_id
                }), 404
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/ping-device', methods=['POST'])
def api_ping_device():
    """Ping a single device"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return jsonify({'error': 'IP address is required'}), 400
        
        # Validate IP address format
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return jsonify({'error': 'Invalid IP address format'}), 400
        
        # Ping the device
        result = ping_host_enhanced(ip_address)
        
        # Get additional device information
        hostname = get_hostname_from_ip(ip_address)
        mac_address = get_mac_from_ip(ip_address)
        cache_info = get_cached_device_info(ip_address)
        
        response = {
            'success': True,
            'ip_address': ip_address,
            'online': result['online'],
            'hostname': hostname,
            'mac_address': mac_address,
            'response_time': result.get('response_time'),
            'min_response_time': result.get('min_response_time'),
            'max_response_time': result.get('max_response_time'),
            'packet_loss': result.get('packet_loss'),
            'message': result.get('message'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add cache information if available
        if cache_info:
            response['device_info'] = {
                'custom_name': cache_info.get('custom_name'),
                'device_type': cache_info.get('device_type'),
                'manufacturer': cache_info.get('manufacturer'),
                'is_cached': True
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/save-device-name', methods=['POST'])
def api_save_device_name():
    """Save custom name for a discovered device"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ip_address = data.get('ip_address')
        custom_name = data.get('custom_name')
        device_type = data.get('device_type', 'unknown')
        
        if not ip_address or not custom_name:
            return jsonify({'error': 'IP address and custom name are required'}), 400
        
        # Validate IP address
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return jsonify({'error': 'Invalid IP address format'}), 400
        
        # Get additional device info
        hostname = get_hostname_from_ip(ip_address)
        mac_address = get_mac_from_ip(ip_address)
        
        # Update device cache
        device_data = {
            'hostname': hostname,
            'mac_address': mac_address,
            'custom_name': custom_name,
            'device_type': device_type,
            'manufacturer': 'Unknown',
            'last_seen': datetime.now().isoformat(),
            'updated_by': 'admin'
        }
        
        success = device_cache_manager.update_device_info(ip_address, device_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Device name saved successfully',
                'device_info': device_data
            })
        else:
            return jsonify({'error': 'Failed to save device name'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error saving device name: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/network-settings', methods=['GET'])
def api_get_network_settings():
    """Get network discovery settings"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        settings = db.get_network_settings()
        if not settings:
            # Return default settings
            settings = {
                'ip_range_start': '192.168.1.1',
                'ip_range_end': '192.168.1.254',
                'scan_timeout': 5,
                'concurrent_scans': 10,
                'enable_mac_lookup': True,
                'enable_hostname_lookup': True
            }
        
        return jsonify({
            'success': True,
            'settings': settings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/network-settings', methods=['POST'])
def api_save_network_settings():
    """Save network discovery settings"""
    if not is_admin_authenticated():
        current_app.logger.warning('Unauthorized access attempt to save network settings.')
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        current_app.logger.debug(f'Received data for saving network settings: {data}')

        if not data:
            current_app.logger.error('No data provided in the request.')
            return jsonify({'error': 'No data provided'}), 400

        # Validate IP range if provided
        ip_range_start = data.get('ip_range_start')
        ip_range_end = data.get('ip_range_end')

        if ip_range_start and ip_range_end:
            try:
                start_ip = ipaddress.ip_address(ip_range_start)
                end_ip = ipaddress.ip_address(ip_range_end)
                if start_ip > end_ip:
                    current_app.logger.error(f'Invalid IP range: {ip_range_start} - {ip_range_end}')
                    return jsonify({'error': 'Invalid IP range: start IP must be less than or equal to end IP'}), 400
            except ValueError as e:
                current_app.logger.error(f'Invalid IP address format: {e}')
                return jsonify({'error': 'Invalid IP address format'}), 400

        # Save settings
        current_app.logger.info(f'Attempting to save network settings: {data}')
        success = db.save_network_settings(data)

        if success:
            current_app.logger.info('Network settings saved successfully.')
            updated_settings = db.get_network_settings()
            return jsonify({
                'success': True,
                'message': 'Network settings saved successfully',
                'settings': updated_settings
            })
        else:
            current_app.logger.error('Failed to save network settings.')
            return jsonify({'error': 'Failed to save network settings'}), 500

    except Exception as e:
        current_app.logger.error(f'Error in api_save_network_settings: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/update-device', methods=['POST'])
def api_update_device():
    """Update device information (custom name, type, etc.)"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ip_address = data.get('ip_address')
        mac_address = data.get('mac_address')
        custom_name = data.get('custom_name')
        device_type = data.get('device_type')
        manufacturer = data.get('manufacturer')
        
        if not ip_address:
            return jsonify({'error': 'IP address is required'}), 400
            
        if not mac_address:
            return jsonify({'error': 'MAC address is required for device updates'}), 400
        
        # Validate IP address
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return jsonify({'error': 'Invalid IP address format'}), 400
        
        # Get existing device info or create new
        existing_info = device_cache_manager.get_device_info(ip_address) or {}
        
        # Get additional device info if not cached
        hostname = existing_info.get('hostname') or get_hostname_from_ip(ip_address)
        
        # Update device data with provided values
        device_data = {
            'ip_address': ip_address,  # Store current IP (can change with DHCP)
            'hostname': hostname,
            'mac_address': mac_address,  # MAC address is the stable identifier
            'custom_name': custom_name or existing_info.get('custom_name'),
            'device_type': device_type or existing_info.get('device_type', 'unknown'),
            'manufacturer': manufacturer or existing_info.get('manufacturer', 'Unknown'),
            'last_seen': datetime.now().isoformat(),
            'updated_by': 'admin'
        }
        
        # Update device cache - we'll use MAC as key but also keep IP mapping
        success = device_cache_manager.update_device_info(ip_address, device_data)
        
        if success:
            current_app.logger.info(f"Updated device {ip_address} (MAC: {mac_address}): custom_name='{custom_name}', type='{device_type}'")
            return jsonify({
                'success': True,
                'message': 'Device updated successfully',
                'device_info': device_data
            })
        else:
            return jsonify({'error': 'Failed to update device information'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error updating device: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/cached-devices', methods=['GET'])
def api_get_cached_devices():
    """Get cached devices and ARP table findings"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Fetch cached devices from persistent storage and ARP table findings
        # Load all devices from cache file, including custom names
        all_devices_map = device_cache_manager.get_all_devices()
        cached_devices = []
        for ip_addr, info in all_devices_map.items():
            cached_devices.append({
                'ip_address': ip_addr,
                'mac_address': info.get('mac_address', ''),
                'status': info.get('status', 'unknown'),
                'device_type': info.get('device_type', info.get('manufacturer', 'unknown')),
                'custom_name': info.get('custom_name', ''),
                'discovery_method': info.get('discovery_method', 'cache')
            })

        # Simulate ARP table findings (replace with actual ARP table logic if available)
        arp_table = [
            {'ip': '192.168.1.1', 'mac': '00:11:22:33:44:55', 'status': 'online'},
            {'ip': '192.168.1.2', 'mac': '00:11:22:33:44:56', 'status': 'offline'}
        ]

        return jsonify({
            'success': True,
            'cached_devices': cached_devices,
            'arp_table': arp_table
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching cached devices: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_network_discovery.route('/refresh-arp-table', methods=['GET'])
def api_refresh_arp_table():
    """Refresh and return the current ARP table (Windows: arp -a)"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        import subprocess
        import re
        arp_table = []
        # Run arp -a and parse output
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        output = result.stdout
        # Parse lines for IP and MAC
        for line in output.splitlines():
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([\w-]+)\s+([\w]+)', line)
            if match:
                ip = match.group(1)
                mac = match.group(2).replace('-', ':')
                # Add all required fields for frontend actions
                arp_table.append({
                    'ip_address': ip,
                    'mac_address': mac,
                    'status': 'unknown',
                    'device_type': 'Network Device',
                    'custom_name': '',
                    'discovery_method': 'arp'
                })
        return jsonify({'success': True, 'arp_table': arp_table}), 200
    except Exception as e:
        current_app.logger.error(f"Error refreshing ARP table: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
