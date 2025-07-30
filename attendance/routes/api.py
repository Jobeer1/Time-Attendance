# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\routes\api.py
"""
API routes for Time Attendance System
Handles REST API endpoints for RIS integration and external systems
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
import hmac
import hashlib
import time

from ..services.database import db
from ..services.face_recognition import face_service
from ..services.shift_manager import shift_manager
from ..models import Employee, AttendanceRecord

bp = Blueprint('api', __name__)

@bp.route('/system/stats')
def get_system_stats():
    """Get system statistics for landing page"""
    try:
        # Get basic system stats
        total_employees = db.count('employees', {'employment_status': 'active'})
        
        # Today's attendance
        today = date.today().isoformat()
        present_today = db.count('attendance_records', {
            'date': today,
            'status': 'active'
        })
        
        # Active terminals
        active_terminals = db.count('terminals', {'is_active': True})
        
        return jsonify({
            'success': True,
            'stats': {
                'total_employees': total_employees,
                'present_today': present_today,
                'active_terminals': active_terminals
            }
        })
        
    except Exception as e:
        print(f"System stats error: {e}")
        return jsonify({
            'success': False,
            'stats': {
                'total_employees': 0,
                'present_today': 0,
                'active_terminals': 0
            }
        }), 500

@bp.route('/health')
def health():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'services': {
            'database': True,
            'face_recognition': face_service.enabled,
            'shift_manager': True
        }
    })

@bp.route('/face_recognition/status')
def face_recognition_status():
    """Face recognition service status"""
    return jsonify({
        'status': 'healthy' if face_service.enabled else 'disabled',
        'enabled': face_service.enabled,
        'confidence_threshold': face_service.confidence_threshold,
        'version': '1.0.0',
        'features': {
            'quality_validation': True,
            'face_encoding': True,
            'face_recognition': True
        }
    })

@bp.route('/employees')
def get_employees():
    """Get all active employees"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        employees = db.find('employees', {'employment_status': 'active'})
        
        return jsonify({
            'success': True,
            'count': len(employees),
            'employees': [emp.to_public_dict() for emp in employees]
        })
        
    except Exception as e:
        print(f"API employees error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/employees/<employee_id>')
def get_employee(employee_id):
    """Get specific employee"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        employee = db.get_employee_by_employee_id(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        return jsonify({
            'success': True,
            'employee': employee.to_public_dict()
        })
        
    except Exception as e:
        print(f"API get employee error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/employees/<employee_id>/status')
def get_employee_status(employee_id):
    """Get employee current status"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get current attendance record
        attendance = db.get_active_attendance_record(employee_id)
        
        if attendance:
            # Calculate current work duration
            work_duration = 0
            if attendance.clock_in_time:
                clock_in = datetime.fromisoformat(attendance.clock_in_time)
                work_duration = (datetime.now() - clock_in).total_seconds() / 3600  # hours
            
            return jsonify({
                'success': True,
                'employee_id': employee_id,
                'status': 'clocked_in',
                'clock_in_time': attendance.clock_in_time,
                'work_duration_hours': round(work_duration, 2),
                'on_break': attendance.is_on_break,
                'break_start_time': attendance.break_start_time,
                'date': attendance.date
            })
        else:
            return jsonify({
                'success': True,
                'employee_id': employee_id,
                'status': 'clocked_out',
                'clock_in_time': None,
                'work_duration_hours': 0,
                'on_break': False
            })
            
    except Exception as e:
        print(f"API employee status error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/attendance/today')
def get_todays_attendance():
    """Get today's attendance records"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        today = date.today().isoformat()
        records = db.find('attendance_records', {'date': today})
        
        # Group by status
        clocked_in = [r for r in records if r.status == 'active']
        completed = [r for r in records if r.status == 'completed']
        
        return jsonify({
            'success': True,
            'date': today,
            'summary': {
                'total_records': len(records),
                'clocked_in': len(clocked_in),
                'completed': len(completed)
            },
            'records': [r.to_dict() for r in records]
        })
        
    except Exception as e:
        print(f"API today's attendance error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/attendance/range')
def get_attendance_range():
    """Get attendance records for date range"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        employee_id = request.args.get('employee_id')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date required'}), 400
        
        records = db.get_attendance_records_by_date_range(start_date, end_date)
        
        if employee_id:
            records = [r for r in records if r.employee_id == employee_id]
        
        # Calculate summary
        total_hours = sum(r.total_hours or 0 for r in records)
        overtime_hours = sum(r.overtime_hours or 0 for r in records)
        
        return jsonify({
            'success': True,
            'start_date': start_date,
            'end_date': end_date,
            'employee_id': employee_id,
            'summary': {
                'total_records': len(records),
                'total_hours': round(total_hours, 2),
                'overtime_hours': round(overtime_hours, 2),
                'average_daily_hours': round(total_hours / max(len(set(r.date for r in records)), 1), 2)
            },
            'records': [r.to_dict() for r in records]
        })
        
    except Exception as e:
        print(f"API attendance range error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/clock_in', methods=['POST'])
def api_clock_in():
    """API endpoint for clocking in"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        employee_id = data.get('employee_id')
        terminal_id = data.get('terminal_id', 'api')
        
        if not employee_id:
            return jsonify({'error': 'employee_id required'}), 400
        
        # Get employee
        employee = db.get_employee_by_employee_id(employee_id)
        if not employee or not employee.is_active:
            return jsonify({'error': 'Employee not found or inactive'}), 404
        
        # Check if already clocked in
        existing_record = db.get_active_attendance_record(employee_id)
        if existing_record:
            return jsonify({
                'error': 'Employee already clocked in',
                'existing_record': existing_record.to_dict()
            }), 400
        
        # Create attendance record
        today = date.today()
        shift = shift_manager.get_employee_shift_for_date(employee_id, today)
        
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
        attendance.clock_in(terminal_id, 'api', request.remote_addr)
        
        # Calculate late status
        if shift:
            late_status = shift_manager.calculate_late_early_status(attendance, shift)
            attendance.is_late = late_status['is_late']
        
        attendance = db.create('attendance_records', attendance)
        
        return jsonify({
            'success': True,
            'message': 'Successfully clocked in',
            'attendance': attendance.to_dict()
        })
        
    except Exception as e:
        print(f"API clock in error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/clock_out', methods=['POST'])
def api_clock_out():
    """API endpoint for clocking out"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        employee_id = data.get('employee_id')
        terminal_id = data.get('terminal_id', 'api')
        
        if not employee_id:
            return jsonify({'error': 'employee_id required'}), 400
        
        # Get active attendance record
        attendance = db.get_active_attendance_record(employee_id)
        if not attendance:
            return jsonify({'error': 'No active attendance record found'}), 400
        
        # Clock out
        attendance.clock_out(terminal_id, 'api', request.remote_addr)
        
        # Calculate hours
        shift = None
        if attendance.shift_id:
            shift = db.get_by_id('shifts', attendance.shift_id)
        
        hours_data = shift_manager.calculate_work_hours(attendance, shift)
        attendance.regular_hours = hours_data['regular_hours']
        attendance.overtime_hours = hours_data['overtime_hours']
        attendance.total_hours = hours_data['total_hours']
        
        # Update record
        db.update('attendance_records', attendance.id, attendance.to_dict())
        
        return jsonify({
            'success': True,
            'message': 'Successfully clocked out',
            'attendance': attendance.to_dict(),
            'work_summary': {
                'total_hours': attendance.total_hours,
                'regular_hours': attendance.regular_hours,
                'overtime_hours': attendance.overtime_hours
            }
        })
        
    except Exception as e:
        print(f"API clock out error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/face_recognition/validate', methods=['POST'])
def validate_face():
    """Validate face image quality"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        image_data = data.get('image_data', '')
        
        if not image_data:
            return jsonify({'error': 'image_data required'}), 400
        
        quality = face_service.validate_face_quality(image_data)
        
        return jsonify({
            'success': True,
            'quality': quality
        })
        
    except Exception as e:
        print(f"API face validation error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/face_recognition/recognize', methods=['POST'])
def recognize_face():
    """Recognize face from image"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        image_data = data.get('image_data', '')
        
        if not image_data:
            return jsonify({'error': 'image_data required'}), 400
        
        # Get all employee encodings
        employees = db.find('employees', {
            'employment_status': 'active',
            'face_recognition_enabled': True
        })
        
        known_encodings = {}
        for employee in employees:
            if employee.face_encodings:
                known_encodings[employee.employee_id] = employee.face_encodings
        
        # Recognize face
        employee_id, confidence = face_service.recognize_face(image_data, known_encodings)
        
        if employee_id:
            employee = db.get_employee_by_employee_id(employee_id)
            return jsonify({
                'success': True,
                'recognized': True,
                'employee': employee.to_public_dict(),
                'confidence': confidence
            })
        else:
            return jsonify({
                'success': True,
                'recognized': False,
                'confidence': confidence
            })
        
    except Exception as e:
        print(f"API face recognition error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/reports/summary')
def get_reports_summary():
    """Get summary reports"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get parameters
        period = request.args.get('period', 'week')  # day, week, month
        employee_id = request.args.get('employee_id')
        
        # Calculate date range
        today = date.today()
        if period == 'day':
            start_date = today
            end_date = today
        elif period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'month':
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        else:
            return jsonify({'error': 'Invalid period'}), 400
        
        # Get records
        records = db.get_attendance_records_by_date_range(
            start_date.isoformat(), 
            end_date.isoformat()
        )
        
        if employee_id:
            records = [r for r in records if r.employee_id == employee_id]
        
        # Calculate summary
        total_records = len(records)
        total_hours = sum(r.total_hours or 0 for r in records)
        total_overtime = sum(r.overtime_hours or 0 for r in records)
        late_count = len([r for r in records if r.is_late])
        early_departure_count = len([r for r in records if r.is_early_departure])
        
        unique_employees = len(set(r.employee_id for r in records))
        unique_days = len(set(r.date for r in records))
        
        return jsonify({
            'success': True,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'summary': {
                'total_records': total_records,
                'total_hours': round(total_hours, 2),
                'total_overtime': round(total_overtime, 2),
                'average_hours_per_day': round(total_hours / max(unique_days, 1), 2),
                'late_count': late_count,
                'early_departure_count': early_departure_count,
                'unique_employees': unique_employees,
                'unique_days': unique_days
            }
        })
        
    except Exception as e:
        print(f"API reports summary error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/terminals')
def get_terminals():
    """Get all active terminals"""
    try:
        if not verify_api_key():
            return jsonify({'error': 'Unauthorized'}), 401
        
        terminals = db.get_all('terminals')
        
        return jsonify({
            'success': True,
            'count': len(terminals),
            'terminals': [terminal.to_dict() for terminal in terminals]
        })
        
    except Exception as e:
        print(f"API terminals error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Helper functions
def verify_api_key():
    """Verify API key from request"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return False
        
        # In production, this should verify against a secure API key
        # For now, accept any non-empty key
        return len(api_key) > 0
        
    except Exception as e:
        print(f"API key verification error: {e}")
        return False

def verify_hmac_signature():
    """Verify HMAC signature for enhanced security"""
    try:
        signature = request.headers.get('X-Signature')
        if not signature:
            return False
        
        # Get secret key (should be in config)
        secret = 'attendance_api_secret_2024'  # Move to config
        
        # Calculate expected signature
        body = request.get_data()
        expected = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
        
    except Exception as e:
        print(f"HMAC verification error: {e}")
        return False
