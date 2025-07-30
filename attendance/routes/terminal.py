"""
Terminal routes for Time Attendance System
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, date
from typing import Optional
import hashlib

from ..services.database import db
from ..services.face_recognition import face_service
from ..services.shift_manager import shift_manager
from ..models import Employee, AttendanceRecord, Terminal

bp = Blueprint('terminal', __name__)

@bp.route('/')
def index():
    """Terminal main page - Using simplified interface with face tracking"""
    terminal_id = request.args.get('terminal_id', 'default')
    # Get or create terminal
    terminal = get_or_create_terminal(terminal_id)
    
    # Use simple terminal template for better UX
    return render_template('attendance/terminal_simple.html', 
                         terminal=terminal.to_dict())

@bp.route('/clock_in')
def clock_in_page():
    """Clock in page"""
    terminal_id = request.args.get('terminal_id', 'default')
    terminal = get_or_create_terminal(terminal_id)
    
    return render_template('attendance/terminal/clock_in.html', 
                         terminal=terminal.to_dict())

@bp.route('/clock_out')
def clock_out_page():
    """Clock out page"""
    terminal_id = request.args.get('terminal_id', 'default')
    terminal = get_or_create_terminal(terminal_id)
    
    return render_template('attendance/terminal/clock_out.html', 
                         terminal=terminal.to_dict())

@bp.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate employee for clock in/out"""
    try:
        data = request.get_json()
        auth_method = data.get('method', 'face_recognition')
        terminal_id = data.get('terminal_id', 'default')
        
        terminal = get_or_create_terminal(terminal_id)
        terminal.record_activity('authentication_attempt')
        
        employee = None
        confidence = 0.0
        
        if auth_method == 'face_recognition':
            employee, confidence = authenticate_by_face(data.get('image_data', ''))
        elif auth_method == 'pin':
            employee = authenticate_by_pin(data.get('pin', ''))
            confidence = 1.0 if employee else 0.0
        elif auth_method == 'employee_id':
            employee = authenticate_by_employee_id(data.get('employee_id', ''))
            confidence = 1.0 if employee else 0.0
        
        if employee:
            # CHECK TERMINAL ACCESS BEFORE ALLOWING AUTHENTICATION
            has_access = db.is_employee_allowed_terminal(employee.employee_id, terminal_id)
            if not has_access:
                # Log unauthorized access attempt
                log_audit_event('terminal_authentication_denied', {
                    'employee_id': employee.employee_id,
                    'terminal_id': terminal_id,
                    'method': auth_method,
                    'ip_address': request.remote_addr
                }, employee.employee_id, terminal_id)
                
                return jsonify({
                    'success': False,
                    'message': 'You are not authorized to use this terminal. Please contact your administrator.',
                    'error_code': 'TERMINAL_ACCESS_DENIED'
                }), 403
            
            terminal.record_successful_login(employee.employee_id)
            db.update('terminals', terminal.id, terminal.to_dict())
            
            # Log audit event
            log_audit_event('employee_authentication', {
                'employee_id': employee.employee_id,
                'method': auth_method,
                'terminal_id': terminal_id,
                'confidence': confidence
            }, employee.employee_id, terminal_id)
            
            return jsonify({
                'success': True,
                'employee': employee.to_public_dict(),
                'confidence': confidence,
                'method': auth_method
            })
        else:
            terminal.record_failed_attempt()
            db.update('terminals', terminal.id, terminal.to_dict())
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed',
                'confidence': confidence
            }), 401
            
    except Exception as e:
        print(f"Authentication error: {e}")
        return jsonify({'success': False, 'message': 'Authentication error'}), 500

@bp.route('/api/clock_in', methods=['POST'])
def clock_in():
    """Clock in employee"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        terminal_id = data.get('terminal_id', 'default')
        auth_method = data.get('auth_method', 'face_recognition')
        
        if not employee_id:
            return jsonify({'success': False, 'message': 'Employee ID required'}), 400
        
        # Get employee
        employee = db.find('employees', {'employee_id': employee_id})
        if not employee or not employee[0].is_active:
            return jsonify({'success': False, 'message': 'Employee not found or inactive'}), 404
        
        employee = employee[0]
        
        # CHECK TERMINAL ACCESS - NEW VALIDATION
        has_access = db.is_employee_allowed_terminal(employee_id, terminal_id)
        if not has_access:
            # Get allowed terminals for better error message
            allowed_terminals = db.get_allowed_terminals_for_employee(employee_id)
            if allowed_terminals:
                terminal_names = []
                for tid in allowed_terminals:
                    terminal = db.get_terminal(tid)
                    if terminal:
                        terminal_names.append(terminal.name)
                message = f'Access denied. You are only authorized to use: {", ".join(terminal_names)}'
            else:
                message = 'Access denied. You are not authorized to use any terminals. Please contact your administrator.'
            
            # Log unauthorized access attempt
            log_audit_event('terminal_access_denied', {
                'employee_id': employee_id,
                'terminal_id': terminal_id,
                'ip_address': request.remote_addr,
                'allowed_terminals': allowed_terminals
            }, employee_id, terminal_id)
            
            return jsonify({
                'success': False, 
                'message': message,
                'error_code': 'TERMINAL_ACCESS_DENIED',
                'allowed_terminals': allowed_terminals
            }), 403
        
        today = date.today()
        
        # Check if already clocked in today
        existing_record = db.get_active_attendance_record(employee_id)
        if existing_record:
            return jsonify({
                'success': False, 
                'message': 'Already clocked in today',
                'existing_record': existing_record.to_dict()
            }, 400)
        
        # Get employee's shift for today
        shift = shift_manager.get_employee_shift_for_date(employee_id, today)
        
        # Create attendance record
        attendance_data = {
            'employee_id': employee_id,
            'employee_name': employee.full_name,
            'date': today.isoformat(),
            'shift_id': shift.id if shift else '',
            'scheduled_start': shift.start_time if shift else '',
            'scheduled_end': shift.end_time if shift else '',
            'is_weekend': today.weekday() >= 5,
            'is_holiday': shift_manager.is_holiday(today)
        }
        
        attendance = AttendanceRecord(**attendance_data)
        attendance.clock_in(terminal_id, auth_method, request.remote_addr)
        
        # Calculate late status if shift exists
        if shift:
            late_status = shift_manager.calculate_late_early_status(attendance, shift)
            attendance.is_late = late_status['is_late']
        
        # Save attendance record
        attendance = db.create('attendance_records', attendance)
        
        # Update employee statistics
        employee.last_clock_in = attendance.clock_in_time
        db.update('employees', employee.id, {'last_clock_in': employee.last_clock_in})
        
        # Log audit event
        log_audit_event('clock_in', {
            'attendance_id': attendance.id,
            'terminal_id': terminal_id,
            'method': auth_method,
            'is_late': attendance.is_late
        }, employee_id, terminal_id)
        
        return jsonify({
            'success': True,
            'message': f'Successfully clocked in at {datetime.now().strftime("%H:%M")}',
            'attendance': attendance.to_dict(),
            'shift': shift.to_dict() if shift else None,
            'is_late': attendance.is_late
        })
        
    except Exception as e:
        print(f"Clock in error: {e}")
        return jsonify({'success': False, 'message': 'Clock in failed'}), 500

@bp.route('/api/clock_out', methods=['POST'])
def clock_out():
    """Clock out employee"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        terminal_id = data.get('terminal_id', 'default')
        auth_method = data.get('auth_method', 'face_recognition')
        
        if not employee_id:
            return jsonify({'success': False, 'message': 'Employee ID required'}), 400
        
        # CHECK TERMINAL ACCESS - NEW VALIDATION
        has_access = db.is_employee_allowed_terminal(employee_id, terminal_id)
        if not has_access:
            # Get allowed terminals for better error message
            allowed_terminals = db.get_allowed_terminals_for_employee(employee_id)
            if allowed_terminals:
                terminal_names = []
                for tid in allowed_terminals:
                    terminal = db.get_terminal(tid)
                    if terminal:
                        terminal_names.append(terminal.name)
                message = f'Access denied. You are only authorized to use: {", ".join(terminal_names)}'
            else:
                message = 'Access denied. You are not authorized to use any terminals. Please contact your administrator.'
            
            # Log unauthorized access attempt
            log_audit_event('terminal_access_denied', {
                'employee_id': employee_id,
                'terminal_id': terminal_id,
                'ip_address': request.remote_addr,
                'allowed_terminals': allowed_terminals,
                'attempted_action': 'clock_out'
            }, employee_id, terminal_id)
            
            return jsonify({
                'success': False, 
                'message': message,
                'error_code': 'TERMINAL_ACCESS_DENIED',
                'allowed_terminals': allowed_terminals
            }), 403
        
        # Get active attendance record
        attendance = db.get_active_attendance_record(employee_id)
        if not attendance:
            return jsonify({
                'success': False, 
                'message': 'No active clock-in record found'
            }), 400
        
        # Get shift for calculations
        shift = None
        if attendance.shift_id:
            shift = db.get_by_id('shifts', attendance.shift_id)
        
        # Clock out
        attendance.clock_out(terminal_id, auth_method, request.remote_addr)
        
        # Calculate work hours
        hours_data = shift_manager.calculate_work_hours(attendance, shift)
        attendance.regular_hours = hours_data['regular_hours']
        attendance.overtime_hours = hours_data['overtime_hours']
        attendance.total_hours = hours_data['total_hours']
        
        # Calculate early departure status
        if shift:
            early_status = shift_manager.calculate_late_early_status(attendance, shift)
            attendance.is_early_departure = early_status['is_early_departure']
        
        # Update attendance record
        db.update('attendance_records', attendance.id, attendance.to_dict())
        
        # Update employee statistics
        employee = db.find('employees', {'employee_id': employee_id})[0]
        employee.last_clock_out = attendance.clock_out_time
        employee.update_statistics(attendance.total_hours, attendance.overtime_hours)
        db.update('employees', employee.id, {
            'last_clock_out': employee.last_clock_out,
            'total_hours_worked': employee.total_hours_worked,
            'total_overtime_hours': employee.total_overtime_hours
        })
        
        # Remove from terminal's current users
        terminal = get_or_create_terminal(terminal_id)
        terminal.remove_user(employee_id)
        db.update('terminals', terminal.id, terminal.to_dict())
        
        # Log audit event
        log_audit_event('clock_out', {
            'attendance_id': attendance.id,
            'terminal_id': terminal_id,
            'method': auth_method,
            'total_hours': attendance.total_hours,
            'overtime_hours': attendance.overtime_hours,
            'is_early_departure': attendance.is_early_departure
        }, employee_id, terminal_id)
        
        return jsonify({
            'success': True,
            'message': f'Successfully clocked out at {datetime.now().strftime("%H:%M")}',
            'attendance': attendance.to_dict(),
            'hours_worked': attendance.total_hours,
            'overtime_hours': attendance.overtime_hours,
            'is_early_departure': attendance.is_early_departure
        })
        
    except Exception as e:
        print(f"Clock out error: {e}")
        return jsonify({'success': False, 'message': 'Clock out failed'}), 500

@bp.route('/api/status/<employee_id>')
def get_employee_status(employee_id):
    """Get current status of employee"""
    try:
        # Get active attendance record (including old records from previous dates)
        attendance = db.get_active_attendance_record(employee_id)
        
        if attendance:
            return jsonify({
                'success': True,
                'has_active_record': True,
                'status': 'clocked_in',
                'clocked_in': True,
                'clock_in_time': attendance.clock_in_time,
                'on_break': attendance.is_on_break,
                'break_start_time': attendance.break_start_time,
                'attendance': attendance.to_dict(),
                'is_old_record': attendance.date != date.today().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'has_active_record': False,
                'status': 'clocked_out',
                'clocked_in': False,
                'clock_in_time': None,
                'on_break': False,
                'attendance': None,
                'is_old_record': False
            })
            
    except Exception as e:
        print(f"Status check error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Status check failed',
            'message': str(e)
        }), 500

@bp.route('/api/break/start', methods=['POST'])
def start_break():
    """Start break period"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        
        attendance = db.get_active_attendance_record(employee_id)
        if not attendance:
            return jsonify({'success': False, 'message': 'No active attendance record'}), 400
        
        if attendance.is_on_break:
            return jsonify({'success': False, 'message': 'Already on break'}), 400
        
        attendance.start_break()
        db.update('attendance_records', attendance.id, attendance.to_dict())
        
        return jsonify({
            'success': True,
            'message': 'Break started',
            'break_start_time': attendance.break_start_time
        })
        
    except Exception as e:
        print(f"Start break error: {e}")
        return jsonify({'success': False, 'message': 'Failed to start break'}), 500

@bp.route('/api/break/end', methods=['POST'])
def end_break():
    """End break period"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        
        attendance = db.get_active_attendance_record(employee_id)
        if not attendance:
            return jsonify({'success': False, 'message': 'No active attendance record'}), 400
        
        if not attendance.is_on_break:
            return jsonify({'success': False, 'message': 'Not currently on break'}), 400
        
        attendance.end_break()
        db.update('attendance_records', attendance.id, attendance.to_dict())
        return jsonify({
            'success': True,
            'message': 'Break ended',
            'break_duration': attendance.break_duration
        })
        
    except Exception as e:
        print(f"End break error: {e}")
        return jsonify({'success': False, 'message': 'Failed to end break'}), 500

@bp.route('/api/clock_action', methods=['POST'])
def clock_action():
    """Unified endpoint for all clock actions"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        action = data.get('action')  # clock_in, clock_out, break_start, break_end
        terminal_id = data.get('terminal_id', 'default')
        auth_method = data.get('method', 'employee_id')
        
        if not employee_id or not action:
            return jsonify({'success': False, 'message': 'Employee ID and action required'}), 400
        
        if action == 'clock_in':
            return handle_clock_in(employee_id, terminal_id, auth_method)
        elif action == 'clock_out':
            return handle_clock_out(employee_id, terminal_id, auth_method)
        elif action == 'break_start':
            return handle_break_start(employee_id)
        elif action == 'break_end':
            return handle_break_end(employee_id)
        else:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
            
    except Exception as e:
        print(f"Clock action error: {e}")
        return jsonify({'success': False, 'message': 'Action failed'}), 500

def handle_clock_in(employee_id, terminal_id, auth_method):
    """Handle clock in action"""
    # Get employee
    employee = db.find('employees', {'employee_id': employee_id})
    if not employee or not employee[0].is_active:
        return jsonify({'success': False, 'message': 'Employee not found or inactive'}), 404
    
    employee = employee[0]
    today = date.today()
    
    # Check if already clocked in today
    existing_record = db.get_active_attendance_record(employee_id)
    if existing_record:
        return jsonify({
            'success': False, 
            'message': 'Already clocked in today',
            'status': 'clocked_in'
        }, 400)
    
    # Get employee's shift for today
    shift = shift_manager.get_employee_shift_for_date(employee_id, today)
    
    # Create attendance record
    attendance_data = {
        'employee_id': employee_id,
        'employee_name': employee.full_name,
        'date': today.isoformat(),
        'shift_id': shift.id if shift else '',
        'scheduled_start': shift.start_time if shift else '',
        'scheduled_end': shift.end_time if shift else '',
        'is_weekend': today.weekday() >= 5,
        'is_holiday': shift_manager.is_holiday(today)
    }
    
    attendance = AttendanceRecord(**attendance_data)
    attendance.clock_in(terminal_id, auth_method, request.remote_addr)
    
    # Calculate late status if shift exists
    if shift:
        late_status = shift_manager.calculate_late_early_status(attendance, shift)
        attendance.is_late = late_status['is_late']
    
    # Save attendance record
    attendance = db.create('attendance_records', attendance)
    
    # Update employee statistics
    employee.last_clock_in = attendance.clock_in_time
    db.update('employees', employee.id, {'last_clock_in': employee.last_clock_in})
    
    return jsonify({
        'success': True,
        'message': f'Successfully clocked in at {datetime.now().strftime("%H:%M")}',
        'status': 'clocked_in',
        'attendance': attendance.to_dict(),
        'is_late': attendance.is_late
    })

def handle_clock_out(employee_id, terminal_id, auth_method):
    """Handle clock out action"""
    # Get active attendance record
    attendance = db.get_active_attendance_record(employee_id)
    if not attendance:
        return jsonify({
            'success': False, 
            'message': 'No active clock-in record found',
            'status': 'clocked_out'
        }, 400)
    
    # Get shift for calculations
    shift = None
    if attendance.shift_id:
        shift = db.get_by_id('shifts', attendance.shift_id)
    
    # Clock out
    attendance.clock_out(terminal_id, auth_method, request.remote_addr)
    
    # Calculate work hours
    hours_data = shift_manager.calculate_work_hours(attendance, shift)
    attendance.regular_hours = hours_data['regular_hours']
    attendance.overtime_hours = hours_data['overtime_hours']
    attendance.total_hours = hours_data['total_hours']
    
    # Update attendance record
    db.update('attendance_records', attendance.id, attendance.to_dict())
    
    # Update employee statistics
    employee = db.find('employees', {'employee_id': employee_id})[0]
    employee.last_clock_out = attendance.clock_out_time
    employee.update_statistics(attendance.total_hours, attendance.overtime_hours)
    db.update('employees', employee.id, {
        'last_clock_out': employee.last_clock_out,
        'total_hours_worked': employee.total_hours_worked,
        'total_overtime_hours': employee.total_overtime_hours
    })
    
    return jsonify({
        'success': True,
        'message': f'Successfully clocked out at {datetime.now().strftime("%H:%M")}',
        'status': 'clocked_out',
        'hours_worked': attendance.total_hours,
        'overtime_hours': attendance.overtime_hours
    })

def handle_break_start(employee_id):
    """Handle break start action"""
    attendance = db.get_active_attendance_record(employee_id)
    if not attendance:
        return jsonify({'success': False, 'message': 'No active attendance record'}), 400
    
    if attendance.is_on_break:
        return jsonify({'success': False, 'message': 'Already on break'}), 400
    
    attendance.start_break()
    db.update('attendance_records', attendance.id, attendance.to_dict())
    
    return jsonify({
        'success': True,
        'message': 'Break started',
        'status': 'on_break',
        'break_start_time': attendance.break_start_time
    })

def handle_break_end(employee_id):
    """Handle break end action"""
    attendance = db.get_active_attendance_record(employee_id)
    if not attendance:
        return jsonify({'success': False, 'message': 'No active attendance record'}), 400
    
    if not attendance.is_on_break:
        return jsonify({'success': False, 'message': 'Not currently on break'}), 400
    
    attendance.end_break()
    db.update('attendance_records', attendance.id, attendance.to_dict())
    
    return jsonify({
        'success': True,
        'message': 'Break ended',
        'status': 'clocked_in',
        'break_duration': attendance.break_duration
    })

@bp.route('/health')
def health_check():
    """Health check endpoint for terminal monitoring"""
    try:
        # Basic system health checks
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': check_database_health(),
                'face_recognition': check_face_service_health(),
                'shift_manager': check_shift_manager_health()
            }
        }
        
        # Determine overall health
        all_healthy = all(service['status'] == 'healthy' for service in health_status['services'].values())
        health_status['status'] = 'healthy' if all_healthy else 'degraded'
        
        return jsonify(health_status), 200 if all_healthy else 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

def check_database_health():
    """Check database connectivity"""
    try:
        # Try to query a simple table
        employees = db.get_all('employees')
        return {'status': 'healthy', 'employee_count': len(employees)}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

def check_face_service_health():
    """Check face recognition service"""
    try:
        # Check if face service is initialized
        if face_service:
            return {'status': 'healthy', 'service': 'available'}
        else:
            return {'status': 'degraded', 'service': 'not_initialized'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

def check_shift_manager_health():
    """Check shift manager service"""
    try:
        # Check if shift manager is working
        if shift_manager:
            return {'status': 'healthy', 'service': 'available'}
        else:
            return {'status': 'degraded', 'service': 'not_initialized'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

# Helper functions
def get_or_create_terminal(terminal_id: str) -> Terminal:
    """Get existing terminal or create new one"""
    try:
        # Try to find existing terminal
        terminals = db.find('terminals', {'terminal_id': terminal_id})
        if terminals:
            terminal = terminals[0]
            terminal.heartbeat()
            return terminal
        
        # Create new terminal
        terminal_data = {
            'terminal_id': terminal_id,
            'name': f'Terminal {terminal_id}',
            'ip_address': request.remote_addr,
            'is_active': True,
            'is_online': True
        }
        
        terminal = Terminal(**terminal_data)
        terminal.heartbeat()
        return db.create('terminals', terminal)
        
    except Exception as e:
        print(f"Error getting/creating terminal: {e}")
        # Return a default terminal object if database fails
        return Terminal(terminal_id=terminal_id, name=f'Terminal {terminal_id}')

def authenticate_by_face(image_data: str) -> tuple:
    """Authenticate employee by face recognition"""
    if not face_service.enabled or not image_data:
        return None, 0.0
    
    try:
        # Get all active employees with face encodings
        employees = db.find('employees', {
            'employment_status': 'active',
            'face_recognition_enabled': True
        })
        
        # Build known encodings dictionary
        known_encodings = {}
        for employee in employees:
            if employee.face_encodings:
                known_encodings[employee.employee_id] = employee.face_encodings
        
        if not known_encodings:
            return None, 0.0
        
        # Recognize face
        employee_id, confidence = face_service.recognize_face(image_data, known_encodings)
        
        if employee_id:
            employee = db.get_employee_by_employee_id(employee_id)
            return employee, confidence
        
        return None, confidence
        
    except Exception as e:
        print(f"Face authentication error: {e}")
        return None, 0.0

def authenticate_by_pin(pin: str) -> Optional[Employee]:
    """Authenticate employee by PIN"""
    if not pin or len(pin) != 4:
        return None
    
    try:
        employees = db.find('employees', {
            'pin': pin,
            'employment_status': 'active'
        })
        return employees[0] if employees else None
        
    except Exception as e:
        print(f"PIN authentication error: {e}")
        return None

def authenticate_by_employee_id(employee_id: str) -> Optional[Employee]:
    """Authenticate employee by employee ID (for testing)"""
    if not employee_id:
        return None
    
    try:
        employee = db.get_employee_by_employee_id(employee_id)
        return employee if employee and employee.is_active else None
        
    except Exception as e:
        print(f"Employee ID authentication error: {e}")
        return None

def log_audit_event(event_type: str, event_data: dict, user_id: str = '', terminal_id: str = ''):
    """Log audit event"""
    try:
        from ..models.admin import AuditLog
        
        audit_data = {
            'event_type': event_type,
            'event_description': f'{event_type} event',
            'event_category': 'attendance',
            'user_id': user_id,
            'terminal_id': terminal_id,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'event_data': event_data,
            'severity': 'info',
            'success': True
        }
        
        audit_log = AuditLog(**audit_data)
        db.create('audit_logs', audit_log)
        
    except Exception as e:
        print(f"Audit logging error: {e}")

@bp.route('/api/available_cameras')
def api_available_cameras():
    """Get available cameras for terminal use (public endpoint)"""
    try:
        cameras = db.get_all('cameras') or []
        # Filter only active cameras and return only safe data
        available_cameras = []
        for camera in cameras:
            if camera.is_active:
                available_cameras.append({
                    'id': camera.id,
                    'name': camera.name,
                    'location': camera.location,
                    'description': camera.description
                })
        
        return jsonify({
            'success': True,
            'cameras': available_cameras
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@bp.route('/api/camera/<camera_id>/stream')
def api_camera_stream(camera_id):
    try:
        camera = db.get_by_id('cameras', camera_id)
        if not camera or not getattr(camera, 'is_active', False):
            return jsonify({'success': False, 'error': 'Camera not found or inactive'}), 404
        return jsonify({
            'success': True,
            'url': camera.url,
            'name': camera.name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/force_clock_out', methods=['POST'])
def force_clock_out():
    """Force clock out employee (admin override for stuck records)"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        terminal_id = data.get('terminal_id', 'admin_override')
        auth_method = data.get('auth_method', 'admin_override')
        
        if not employee_id:
            return jsonify({'success': False, 'message': 'Employee ID required'}), 400
        
        # Get any active attendance record (regardless of date)
        attendance = db.get_active_attendance_record(employee_id)
        if not attendance:
            return jsonify({
                'success': False, 
                'message': 'No active attendance record found'
            }), 400
        
        # Check if this is an old record
        today = date.today().isoformat()
        is_old_record = attendance.date != today
        
        # Clock out with special handling for old records
        attendance.clock_out(terminal_id, auth_method, request.remote_addr)
        
        # For old records, set clock_out_time to end of that day (e.g., 17:00)
        if is_old_record:
            from datetime import datetime, time
            old_date = datetime.fromisoformat(attendance.date)
            end_of_day = datetime.combine(old_date.date(), time(17, 0))  # 5 PM default
            attendance.clock_out_time = end_of_day.isoformat()
            attendance.admin_notes = f"Force clock-out by admin on {today} - original date: {attendance.date}"
        
        # Calculate work hours
        hours_data = {'regular_hours': 8.0, 'overtime_hours': 0.0, 'total_hours': 8.0}
        if hasattr(shift_manager, 'calculate_work_hours'):
            shift = None
            if attendance.shift_id:
                shift = db.get_by_id('shifts', attendance.shift_id)
            hours_data = shift_manager.calculate_work_hours(attendance, shift)
        
        attendance.regular_hours = hours_data['regular_hours']
        attendance.overtime_hours = hours_data['overtime_hours']
        attendance.total_hours = hours_data['total_hours']
        
        # Update attendance record
        db.update('attendance_records', attendance.id, attendance.to_dict())
        
        # Update employee statistics
        employee = db.find('employees', {'employee_id': employee_id})[0]
        employee.last_clock_out = attendance.clock_out_time
        db.update('employees', employee.id, {
            'last_clock_out': employee.last_clock_out,
            'total_hours_worked': getattr(employee, 'total_hours_worked', 0) + attendance.total_hours,
            'total_overtime_hours': getattr(employee, 'total_overtime_hours', 0) + attendance.overtime_hours
        })
        
        # Log audit event
        log_audit_event('force_clock_out', {
            'attendance_id': attendance.id,
            'original_date': attendance.date,
            'force_clock_out_date': today,
            'terminal_id': terminal_id,
            'method': auth_method,
            'total_hours': attendance.total_hours,
            'is_old_record': is_old_record
        }, employee_id, terminal_id)
        
        message = f'Force clock-out successful'
        if is_old_record:
            message = f'Force clock-out successful (from {attendance.date})'
            
        return jsonify({
            'success': True,
            'message': message,
            'attendance': attendance.to_dict(),
            'hours_worked': attendance.total_hours,
            'overtime_hours': attendance.overtime_hours,
            'was_old_record': is_old_record,
            'original_date': attendance.date
        })
        
    except Exception as e:
        print(f"Force clock out error: {e}")
        return jsonify({'success': False, 'message': 'Force clock out failed'}), 500
