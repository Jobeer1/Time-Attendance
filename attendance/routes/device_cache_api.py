"""
Device Cache Management API Endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import ipaddress
from .helpers import *
from ..utils.auth import is_admin_authenticated

bp_device_cache = Blueprint('device_cache_api', __name__, url_prefix='/admin/terminal-management/api')

@bp_device_cache.route('/device-cache/update-name', methods=['POST'])
def update_device_name():
    """Update custom name for a device in the cache"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ip_address = data.get('ip_address')
        mac_address = data.get('mac_address')
        custom_name = data.get('custom_name')
        device_type = data.get('device_type', 'unknown')
        
        if not custom_name:
            return jsonify({'error': 'Custom name is required'}), 400
        
        # Update by IP address if provided
        if ip_address:
            # Validate IP address
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                return jsonify({'error': 'Invalid IP address format'}), 400
            
            # Get existing device info or create new
            existing_info = device_cache_manager.get_device_info(ip_address)
            if existing_info:
                device_data = existing_info.copy()
                device_data.update({
                    'custom_name': custom_name,
                    'device_type': device_type,
                    'updated_at': datetime.now().isoformat(),
                    'updated_by': 'admin'
                })
            else:
                # Create new device entry
                hostname = get_hostname_from_ip(ip_address)
                mac_addr = get_mac_from_ip(ip_address) if not mac_address else mac_address
                
                device_data = {
                    'hostname': hostname,
                    'mac_address': mac_addr,
                    'custom_name': custom_name,
                    'device_type': device_type,
                    'manufacturer': 'Unknown',
                    'last_seen': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'updated_by': 'admin'
                }
            
            success = device_cache_manager.update_device_info(ip_address, device_data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Device name updated successfully',
                    'device_info': device_data
                })
            else:
                return jsonify({'error': 'Failed to update device cache'}), 500
                
        elif mac_address:
            # Update by MAC address using custom name binding
            success = device_cache_manager.update_custom_name_by_mac(mac_address, custom_name)
            if success:
                # Fetch updated device info by MAC
                device_info = device_cache_manager.get_device_by_mac(mac_address)
                return jsonify({
                    'success': True,
                    'message': 'Device name updated successfully',
                    'device_info': device_info
                })
            else:
                return jsonify({'error': 'Device not found or failed to update'}), 404
        
        else:
            return jsonify({'error': 'Either IP address or MAC address is required'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating device name: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_device_cache.route('/device-cache/get-device', methods=['POST'])
def get_device_info():
    """Get device information from cache"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ip_address = data.get('ip_address')
        mac_address = data.get('mac_address')
        
        if ip_address:
            # Validate IP address
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                return jsonify({'error': 'Invalid IP address format'}), 400
            
            device_info = device_cache_manager.get_device_info(ip_address)
            
            if device_info:
                return jsonify({
                    'success': True,
                    'device_info': device_info,
                    'ip_address': ip_address
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Device not found in cache',
                    'ip_address': ip_address
                }), 404
        
        elif mac_address:
            device_info = device_cache_manager.get_device_by_mac(mac_address)
            
            if device_info:
                return jsonify({
                    'success': True,
                    'device_info': device_info,
                    'mac_address': mac_address
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Device not found in cache',
                    'mac_address': mac_address
                }), 404
        
        else:
            return jsonify({'error': 'Either IP address or MAC address is required'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error getting device info: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_device_cache.route('/device-cache/stats', methods=['GET'])
def get_cache_stats():
    """Get device cache statistics"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        stats = device_cache_manager.get_cache_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting cache stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_device_cache.route('/device-cache/reload', methods=['POST'])
def reload_cache():
    """Reload device cache from file"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        success = device_cache_manager.reload_cache()
        
        if success:
            stats = device_cache_manager.get_cache_stats()
            return jsonify({
                'success': True,
                'message': 'Device cache reloaded successfully',
                'stats': stats
            })
        else:
            return jsonify({'error': 'Failed to reload device cache'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error reloading cache: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_device_cache.route('/device-cache/clear', methods=['POST'])
def clear_cache():
    """Clear device cache"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        success = device_cache_manager.clear_cache()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Device cache cleared successfully'
            })
        else:
            return jsonify({'error': 'Failed to clear device cache'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_device_cache.route('/device-cache/export', methods=['GET'])
def export_cache():
    """Export device cache data"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        cache_data = device_cache_manager.get_all_devices()
        
        return jsonify({
            'success': True,
            'cache_data': cache_data,
            'export_timestamp': datetime.now().isoformat(),
            'device_count': len(cache_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error exporting cache: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_device_cache.route('/device-cache/import', methods=['POST'])
def import_cache():
    """Import device cache data"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        cache_data = data.get('cache_data')
        merge_mode = data.get('merge_mode', True)  # True to merge, False to replace
        
        if not cache_data:
            return jsonify({'error': 'No cache data provided'}), 400
        
        success = device_cache_manager.import_cache_data(cache_data, merge_mode)
        
        if success:
            stats = device_cache_manager.get_cache_stats()
            return jsonify({
                'success': True,
                'message': f'Device cache imported successfully ({"merged" if merge_mode else "replaced"})',
                'stats': stats
            })
        else:
            return jsonify({'error': 'Failed to import device cache'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error importing cache: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@bp_device_cache.route('/get-device-name/<mac_address>', methods=['GET'])
def api_get_device_name(mac_address):
    """Get device name by MAC address"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if not mac_address:
            return jsonify({'error': 'MAC address is required'}), 400
        
        # Normalize MAC address
        mac_address = mac_address.upper()
        
        # Get device info from cache
        device_info = device_cache_manager.get_device_by_mac(mac_address)
        
        if device_info:
            return jsonify({
                'success': True,
                'device_name': device_info.get('custom_name') or device_info.get('hostname'),
                'device_type': device_info.get('device_type'),
                'device_description': device_info.get('description'),
                'mac_address': mac_address,
                'hostname': device_info.get('hostname'),
                'manufacturer': device_info.get('manufacturer')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Device not found in cache',
                'mac_address': mac_address
            }), 404
        
    except Exception as e:
        current_app.logger.error(f"Error getting device name: {e}")
        return jsonify({'error': str(e)}), 500
