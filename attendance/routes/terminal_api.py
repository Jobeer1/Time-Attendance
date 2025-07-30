"""
Terminal Management API Endpoints
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from datetime import datetime
import ipaddress
import uuid
from .helpers import *
from ..services.database import db
from ..models.terminal import Terminal
from ..utils.auth import is_admin_authenticated

bp_terminal = Blueprint('terminal_api', __name__, url_prefix='/admin/terminal-management')

# Terminal HTML Routes

@bp_terminal.route('/terminals')
def terminals():
    """List all terminals"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    
    try:
        # Get all terminals from DB (for core info)
        terminals = db.get_all_terminals()
        # For each terminal, enrich with device info from cache
        for term in terminals:
            ip = getattr(term, 'ip_address', None)
            if ip:
                cache_info = get_cached_device_info(ip)
                if cache_info:
                    term.custom_name = cache_info.get('custom_name', cache_info.get('hostname'))
                    term.device_type = cache_info.get('device_type')
                    term.manufacturer = cache_info.get('manufacturer')
                    term.is_cached = True
                else:
                    term.is_cached = False
        return render_template('attendance/terminals.html', terminals=terminals)
    except Exception as e:
        flash(f'Error loading terminals: {str(e)}', 'error')
        return render_template('attendance/terminals.html', terminals=[])

@bp_terminal.route('/assignments')
def terminal_assignments():
    """Terminal assignment management page"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    
    try:
        assignments = db.get_all_employee_terminal_assignments()
        terminals = db.get_all_terminals()
        employees = db.get_all_employees()
        
        return render_template('attendance/terminal_assignments.html', 
                             assignments=assignments, 
                             terminals=terminals, 
                             employees=employees)
    except Exception as e:
        flash(f'Error loading assignments: {str(e)}', 'error')
        return render_template('attendance/terminal_assignments.html', 
                             assignments=[], 
                             terminals=[], 
                             employees=[])

# Terminal CRUD API Endpoints

@bp_terminal.route('/api/terminals', methods=['GET'])
def api_get_terminals():
    """API endpoint to get all terminals with status"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        terminals = db.get_all_terminals()
        terminal_list = []
        for terminal in terminals:
            status = check_terminal_status(terminal.ip_address)
            cache_info = get_cached_device_info(terminal.ip_address)
            terminal_data = {
                'id': terminal.id,
                'name': terminal.name,
                'location': terminal.location,
                'ip_address': terminal.ip_address,
                'mac_address': terminal.mac_address,
                'status': status,
                'last_activity': terminal.last_activity,
                'face_recognition_enabled': terminal.supports_face_recognition,
                'pin_enabled': terminal.supports_pin,
                'card_enabled': terminal.supports_password,
                'description': terminal.description,
                'custom_name': cache_info.get('custom_name', cache_info.get('hostname')) if cache_info else None,
                'device_type': cache_info.get('device_type') if cache_info else None,
                'manufacturer': cache_info.get('manufacturer') if cache_info else None,
                'is_cached': bool(cache_info)
            }
            terminal_list.append(terminal_data)
        return jsonify({'success': True, 'terminals': terminal_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_terminal.route('/api/terminals', methods=['POST'])
def api_add_terminal():
    """Add a new terminal"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('location'):
            return jsonify({'error': 'Name and location are required'}), 400
        
        # Validate IP address if provided
        ip_address = data.get('ip_address', '')
        if ip_address:
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                return jsonify({'error': 'Invalid IP address format'}), 400
        
        # Create terminal object
        terminal = Terminal(
            id=str(uuid.uuid4()),
            terminal_id=f"TERM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=data['name'],
            location=data['location'],
            description=data.get('description', ''),
            ip_address=ip_address,
            mac_address=data.get('mac_address', ''),
            supports_face_recognition=data.get('face_recognition_enabled', True),
            supports_pin=data.get('pin_enabled', False),
            supports_password=data.get('card_enabled', False),
            is_active=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Save to database
        if db.save_terminal(terminal):
            return jsonify({'success': True, 'terminal_id': terminal.id, 'message': 'Terminal added successfully'})
        else:
            return jsonify({'error': 'Failed to save terminal'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_terminal.route('/api/terminals/<terminal_id>', methods=['GET'])
def api_get_terminal(terminal_id):
    """Get terminal details"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        terminal = db.get_terminal(terminal_id)
        if not terminal:
            return jsonify({'error': 'Terminal not found'}), 404
        
        status = check_terminal_status(terminal.ip_address)
        cache_info = get_cached_device_info(terminal.ip_address)
        terminal_data = {
            'id': terminal.id,
            'name': terminal.name,
            'location': terminal.location,
            'description': terminal.description,
            'ip_address': terminal.ip_address,
            'mac_address': terminal.mac_address,
            'status': status,
            'last_activity': terminal.last_activity,
            'face_recognition_enabled': terminal.supports_face_recognition,
            'pin_enabled': terminal.supports_pin,
            'card_enabled': terminal.supports_password,
            'is_active': terminal.is_active,
            'custom_name': cache_info.get('custom_name', cache_info.get('hostname')) if cache_info else None,
            'device_type': cache_info.get('device_type') if cache_info else None,
            'manufacturer': cache_info.get('manufacturer') if cache_info else None,
            'is_cached': bool(cache_info)
        }
        return jsonify({'success': True, 'terminal': terminal_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_terminal.route('/api/terminals/<terminal_id>', methods=['PUT'])
def api_update_terminal(terminal_id):
    """Update terminal"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        terminal = db.get_terminal(terminal_id)
        if not terminal:
            return jsonify({'error': 'Terminal not found'}), 404
        
        data = request.get_json()
        
        # Validate IP address if provided
        ip_address = data.get('ip_address', terminal.ip_address)
        if ip_address:
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                return jsonify({'error': 'Invalid IP address format'}), 400
        
        # Update terminal properties
        terminal.name = data.get('name', terminal.name)
        terminal.location = data.get('location', terminal.location)
        terminal.description = data.get('description', terminal.description)
        terminal.ip_address = ip_address
        terminal.mac_address = data.get('mac_address', terminal.mac_address)
        terminal.supports_face_recognition = data.get('face_recognition_enabled', terminal.supports_face_recognition)
        terminal.supports_pin = data.get('pin_enabled', terminal.supports_pin)
        terminal.supports_password = data.get('card_enabled', terminal.supports_password)
        terminal.is_active = data.get('is_active', terminal.is_active)
        terminal.updated_at = datetime.now().isoformat()
        
        if db.save_terminal(terminal):
            return jsonify({'success': True, 'message': 'Terminal updated successfully'})
        else:
            return jsonify({'error': 'Failed to update terminal'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_terminal.route('/api/terminals/<terminal_id>', methods=['DELETE'])
def api_delete_terminal(terminal_id):
    """Delete terminal"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if db.delete_terminal(terminal_id):
            return jsonify({'success': True, 'message': 'Terminal deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete terminal'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Terminal Management API Endpoints

@bp_terminal.route('/api/terminals/<terminal_id>/ping', methods=['POST'])
def api_ping_terminal(terminal_id):
    """Ping terminal to check connectivity"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        terminal = db.get_terminal(terminal_id)
        if not terminal:
            return jsonify({'error': 'Terminal not found'}), 404
        
        if not terminal.ip_address:
            return jsonify({'error': 'No IP address configured'}), 400
        
        # Ping the terminal
        result = ping_host_enhanced(terminal.ip_address)
        
        # Update terminal status
        terminal.is_online = result['online']
        terminal.last_heartbeat = datetime.now().isoformat()
        db.save_terminal(terminal)
        
        return jsonify({
            'success': True,
            'online': result['online'],
            'response_time': result.get('response_time'),
            'min_response_time': result.get('min_response_time'),
            'max_response_time': result.get('max_response_time'),
            'packet_loss': result.get('packet_loss'),
            'message': result.get('message')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_terminal.route('/api/get-mac-address', methods=['POST'])
def api_get_mac_address():
    """Get MAC address from IP address"""
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
        
        # Get MAC address using different methods
        mac_address = get_mac_from_ip(ip_address)
        
        if mac_address:
            return jsonify({
                'success': True,
                'ip_address': ip_address,
                'mac_address': mac_address,
                'message': 'MAC address found successfully'
            })
        else:
            return jsonify({
                'success': False,
                'ip_address': ip_address,
                'mac_address': None,
                'message': 'Could not retrieve MAC address. Device may be offline or not in ARP table.'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_terminal.route('/api/terminals/<terminal_id>/restart', methods=['POST'])
def api_restart_terminal(terminal_id):
    """Restart terminal (if supported)"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        terminal = db.get_terminal(terminal_id)
        if not terminal:
            return jsonify({'error': 'Terminal not found'}), 404
        
        # Log restart action
        log_terminal_action(terminal_id, 'restart', {'initiated_by': 'admin'})
        
        # In a real implementation, you would send a restart command to the terminal
        # For now, we'll just simulate it
        return jsonify({
            'success': True,
            'message': 'Restart command sent to terminal'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_terminal.route('/api/terminals/<terminal_id>/logs', methods=['GET'])
def api_get_terminal_logs(terminal_id):
    """Get terminal logs"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        terminal = db.get_terminal(terminal_id)
        if not terminal:
            return jsonify({'error': 'Terminal not found'}), 404
        
        # Get query parameters for filtering
        level = request.args.get('level', '')
        date_filter = request.args.get('date', '')
        limit = int(request.args.get('limit', 100))
        
        # Get logs from database (implement this in your database service)
        logs = db.get_terminal_logs(terminal_id, level=level, date_filter=date_filter, limit=limit)
        
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_terminal.route('/api/terminals/<terminal_id>/sync', methods=['POST'])
def api_sync_terminal(terminal_id):
    """Force data synchronization with terminal"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        terminal = db.get_terminal(terminal_id)
        if not terminal:
            return jsonify({'error': 'Terminal not found'}), 404
        
        # Log sync action
        log_terminal_action(terminal_id, 'sync', {'initiated_by': 'admin'})
        
        # In a real implementation, you would trigger data sync
        return jsonify({
            'success': True,
            'message': 'Data synchronization initiated'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Employee-Terminal Assignment API Endpoints

@bp_terminal.route('/api/assignments', methods=['GET'])
def api_get_assignments():
    """API endpoint to get all employee-terminal assignments"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        assignments = db.get_all_employee_terminal_assignments()
        assignment_list = []
        
        for assignment in assignments:
            # Get employee and terminal info
            employee = db.get_employee(assignment.employee_id)
            terminal = db.get_terminal(assignment.terminal_id)
            
            assignment_data = assignment.to_dict()
            assignment_data['employee_name'] = employee.full_name if employee else 'Unknown'
            assignment_data['employee_id_display'] = employee.employee_id if employee else 'Unknown'
            assignment_data['terminal_name'] = terminal.name if terminal else 'Unknown'
            assignment_data['terminal_location'] = terminal.location if terminal else 'Unknown'
            assignment_list.append(assignment_data)
        
        return jsonify({'success': True, 'assignments': assignment_list})
    
    except Exception as e:
        return jsonify({'error': f'Failed to get assignments: {str(e)}'}), 500

@bp_terminal.route('/api/assignments/<assignment_id>', methods=['GET'])
def api_get_assignment(assignment_id):
    """API endpoint to get a specific assignment"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        assignment = db.get_employee_terminal_assignment(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        return jsonify({'success': True, 'assignment': assignment.to_dict()})
    
    except Exception as e:
        return jsonify({'error': f'Failed to get assignment: {str(e)}'}), 500

@bp_terminal.route('/api/assignments', methods=['POST'])
def api_create_assignment():
    """API endpoint to create a new employee-terminal assignment"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['employee_id', 'terminal_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if employee and terminal exist
        employee = db.get_employee(data['employee_id'])
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        terminal = db.get_terminal(data['terminal_id'])
        if not terminal:
            return jsonify({'error': 'Terminal not found'}), 404
        
        # Create assignment
        from flask import session
        assignment = db.assign_employee_to_terminal(
            employee_id=data['employee_id'],
            terminal_id=data['terminal_id'],
            assigned_by=session.get('admin_id', 'system'),
            reason=data.get('reason', ''),
            assignment_type=data.get('assignment_type', 'exclusive'),
            allowed_time_start=data.get('allowed_time_start', ''),
            allowed_time_end=data.get('allowed_time_end', ''),
            allowed_days=data.get('allowed_days', []),
            expiry_date=data.get('expiry_date', ''),
            notes=data.get('notes', '')
        )
        
        if assignment:
            return jsonify({
                'success': True,
                'message': 'Assignment created successfully',
                'assignment': assignment.to_dict()
            }), 201
        else:
            return jsonify({'error': 'Failed to create assignment'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Failed to create assignment: {str(e)}'}), 500

@bp_terminal.route('/api/assignments/<assignment_id>', methods=['PUT'])
def api_update_assignment(assignment_id):
    """API endpoint to update an assignment"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        assignment = db.get_employee_terminal_assignment(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update assignment fields
        updatable_fields = [
            'is_active', 'reason', 'notes', 'assignment_type',
            'allowed_time_start', 'allowed_time_end', 'allowed_days',
            'expiry_date', 'priority'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(assignment, field, data[field])
        
        if db.save_employee_terminal_assignment(assignment):
            return jsonify({
                'success': True,
                'message': 'Assignment updated successfully',
                'assignment': assignment.to_dict()
            })
        else:
            return jsonify({'error': 'Failed to update assignment'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Failed to update assignment: {str(e)}'}), 500

@bp_terminal.route('/api/assignments/<assignment_id>', methods=['DELETE'])
def api_delete_assignment(assignment_id):
    """API endpoint to delete an assignment"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        assignment = db.get_employee_terminal_assignment(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        if db.delete_employee_terminal_assignment(assignment_id):
            return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete assignment'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Failed to delete assignment: {str(e)}'}), 500

@bp_terminal.route('/api/employees/<employee_id>/assignments', methods=['GET'])
def api_get_employee_assignments(employee_id):
    """API endpoint to get all assignments for a specific employee"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        assignments = db.get_assignments_for_employee(employee_id)
        
        assignment_list = []
        for assignment in assignments:
            terminal = db.get_terminal(assignment.terminal_id)
            assignment_data = assignment.to_dict()
            assignment_data['terminal_name'] = terminal.name if terminal else 'Unknown'
            assignment_data['terminal_location'] = terminal.location if terminal else 'Unknown'
            assignment_list.append(assignment_data)
        
        return jsonify({'success': True, 'assignments': assignment_list})
    
    except Exception as e:
        return jsonify({'error': f'Failed to get employee assignments: {str(e)}'}), 500

@bp_terminal.route('/api/terminals/<terminal_id>/assignments', methods=['GET'])
def api_get_terminal_assignments(terminal_id):
    """API endpoint to get all assignments for a specific terminal"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        assignments = db.get_assignments_for_terminal(terminal_id)
        
        assignment_list = []
        for assignment in assignments:
            employee = db.get_employee(assignment.employee_id)
            assignment_data = assignment.to_dict()
            assignment_data['employee_name'] = employee.full_name if employee else 'Unknown'
            assignment_data['employee_id_display'] = employee.employee_id if employee else 'Unknown'
            assignment_list.append(assignment_data)
        
        return jsonify({'success': True, 'assignments': assignment_list})
    
    except Exception as e:
        return jsonify({'error': f'Failed to get terminal assignments: {str(e)}'}), 500

@bp_terminal.route('/api/employees/<employee_id>/allowed-terminals', methods=['GET'])
def api_get_allowed_terminals(employee_id):
    """API endpoint to get terminals that an employee is allowed to use"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        allowed_terminal_ids = db.get_allowed_terminals_for_employee(employee_id)
        terminals = []
        
        for terminal_id in allowed_terminal_ids:
            terminal = db.get_terminal(terminal_id)
            if terminal:
                terminals.append({
                    'id': terminal.id,
                    'name': terminal.name,
                    'location': terminal.location,
                    'ip_address': terminal.ip_address
                })
        
        return jsonify({'success': True, 'allowed_terminals': terminals})
    
    except Exception as e:
        return jsonify({'error': f'Failed to get allowed terminals: {str(e)}'}), 500

@bp_terminal.route('/api/check-access', methods=['POST'])
def api_check_terminal_access():
    """API endpoint to check if an employee can access a terminal"""
    try:
        data = request.get_json()
        if not data or 'employee_id' not in data or 'terminal_id' not in data:
            return jsonify({'error': 'Employee ID and Terminal ID required'}), 400
        
        employee_id = data['employee_id']
        terminal_id = data['terminal_id']
        
        # Check access
        has_access = db.is_employee_allowed_terminal(employee_id, terminal_id)
        
        response = {
            'success': True,
            'has_access': has_access,
            'employee_id': employee_id,
            'terminal_id': terminal_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add additional info if access is denied
        if not has_access:
            allowed_terminals = db.get_allowed_terminals_for_employee(employee_id)
            response['allowed_terminals'] = allowed_terminals
            response['message'] = 'Employee is not authorized to use this terminal'
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'Failed to check access: {str(e)}'}), 500

@bp_terminal.route('/api/system-config', methods=['GET'])
def api_get_system_config():
    """API endpoint to get system configuration"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        config = db.get_system_config()
        if config:
            return jsonify({'success': True, 'config': config.to_dict()})
        else:
            # Return default config if none exists
            return jsonify({'success': True, 'config': {'terminals_open_by_default': True}})
    except Exception as e:
        return jsonify({'error': f'Failed to get system config: {str(e)}'}), 500

@bp_terminal.route('/api/system-config', methods=['PUT'])
def api_update_system_config():
    """API endpoint to update system configuration"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update system configuration
        if db.update_system_config(**data):
            return jsonify({'success': True, 'message': 'System configuration updated successfully'})
        else:
            return jsonify({'error': 'Failed to update system configuration'}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to update system config: {str(e)}'}), 500
