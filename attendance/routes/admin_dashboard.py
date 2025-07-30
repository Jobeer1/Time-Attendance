"""
Admin dashboard, login/logout, settings, and main admin routes
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, date, timedelta
from ..services.database import db
from ..utils.auth import is_admin_authenticated
from ..utils.dashboard import get_dashboard_stats, get_today_activity
from models.leave_management import leave_manager  # Import the shared leave manager directly

bp_dashboard = Blueprint('admin_dashboard', __name__)

@bp_dashboard.route('/')
def dashboard():
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    stats = get_dashboard_stats()
    today_activity = get_today_activity()
    # Count pending leave applications via LeaveManager for consistency
    try:
        # Force reload of leave requests to get latest data
        leave_manager._load_leave_requests()
        
        pending_apps = []
        for app in leave_manager.leave_applications.values():
            status_value = app.status.value if hasattr(app.status, 'value') else str(app.status)
            if status_value.lower() == 'pending':
                pending_apps.append(app)
        pending_leaves = len(pending_apps)
    except Exception as e:
        print(f"[ERROR] Failed to count pending leaves: {e}")
        pending_leaves = 0
    return render_template('attendance/admin_dashboard.html', stats=stats, today_activity=today_activity, pending_leaves=pending_leaves)

@bp_dashboard.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('attendance/admin_login.html')
        
        # Get admin user from database
        try:
            admin_users = db.get_all('admins')
            admin_user = None
            
            for user in admin_users:
                if user.username == username:
                    admin_user = user
                    break
            
            if admin_user and admin_user.check_password(password):
                # Login successful
                session['admin_logged_in'] = True
                session['admin_id'] = admin_user.id
                session['admin_name'] = admin_user.full_name or admin_user.username
                session['admin_role'] = admin_user.role
                
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard.dashboard'))
            else:
                flash('Invalid username or password', 'error')
                
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
    
    return render_template('attendance/admin_login.html')

@bp_dashboard.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_dashboard.login'))

@bp_dashboard.route('/settings')
def settings():
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    stats = get_dashboard_stats()
    today_activity = get_today_activity()
    return render_template('attendance/admin_dashboard.html', stats=stats, today_activity=today_activity)

@bp_dashboard.route('/leave')
def leave_management():
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    return render_template('attendance/admin_leave.html')

@bp_dashboard.route('/api/today-activity')
def today_activity_api():
    """API endpoint for today's activity data"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    today_activity = get_today_activity()
    return jsonify(today_activity)

@bp_dashboard.route('/api/present-employees')
def present_employees_api():
    """API endpoint for present employees data"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get real present employees from database
        today = date.today().isoformat()
        all_attendance_records = db.get_all('attendance_records')
        
        # Filter for today's records where employees are clocked in but not out
        today_records = [r for r in all_attendance_records if r.date == today]
        present_records = [r for r in today_records if r.clock_in_time and not r.clock_out_time]
        
        present_employees = []
        for record in present_records:
            # Get employee details
            employee = db.get_employee_by_employee_id(record.employee_id)
            if not employee:
                continue
                
            # Parse clock in time for display
            try:
                clock_in_dt = datetime.fromisoformat(record.clock_in_time)
                timestamp = clock_in_dt.strftime('%H:%M')
            except:
                timestamp = record.clock_in_time
            
            # Generate initials for placeholder image
            name_parts = employee.full_name.split()
            initials = ''.join([part[0].upper() for part in name_parts[:2]])
            
            present_employee = {
                'employee': {
                    'employee_id': employee.employee_id,
                    'name': employee.full_name,
                    'department': employee.department,
                    'photo': f'https://via.placeholder.com/40x40/007bff/ffffff?text={initials}'
                },
                'action_type': 'Clock In' + (' (Late)' if record.is_late else ''),
                'action_color': 'warning' if record.is_late else 'success',
                'action_icon': 'clock',
                'timestamp': timestamp,
                'ip_address': record.clock_in_ip or 'Unknown',
                'terminal': record.clock_in_terminal or 'Unknown',
                'location': 'Office',  # Default location
                'is_late': record.is_late or False
            }
            present_employees.append(present_employee)
        
        return jsonify({
            'success': True,
            'present_employees': present_employees,
            'total': len(present_employees)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_dashboard.route('/api/system-status')
def system_status_api():
    """API endpoint for system status data"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Basic system status implementation
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'face_recognition': 'active',
            'cameras': 'operational',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_dashboard.route('/api/late-employees')
def late_employees_api():
    """API endpoint for late employees data"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get real late employees from database
        today = date.today().isoformat()
        all_attendance_records = db.get_all('attendance_records')
        
        # Filter for today's records where employees are late
        today_records = [r for r in all_attendance_records if r.date == today]
        late_records = [r for r in today_records if r.is_late]
        
        late_employees = []
        for record in late_records:
            # Get employee details
            employee = db.get_employee_by_employee_id(record.employee_id)
            if not employee:
                continue
                
            # Parse clock in time for display
            try:
                clock_in_dt = datetime.fromisoformat(record.clock_in_time)
                timestamp = clock_in_dt.strftime('%H:%M')
            except:
                timestamp = record.clock_in_time
            
            # Generate initials for placeholder image
            name_parts = employee.full_name.split()
            initials = ''.join([part[0].upper() for part in name_parts[:2]])
            
            late_employee = {
                'employee': {
                    'employee_id': employee.employee_id,
                    'name': employee.full_name,
                    'department': employee.department,
                    'photo': f'https://via.placeholder.com/40x40/dc3545/ffffff?text={initials}'
                },
                'action_type': 'Clock In (Late)',
                'action_color': 'warning',
                'action_icon': 'clock',
                'timestamp': timestamp,
                'expected_time': record.scheduled_start or '09:00',
                'actual_time': timestamp,
                'late_by': 'Late arrival',  # Could calculate exact minutes if needed
                'ip_address': record.clock_in_ip or 'Unknown',
                'terminal': record.clock_in_terminal or 'Unknown',
                'is_late': True
            }
            late_employees.append(late_employee)
        
        return jsonify({
            'success': True,
            'late_employees': late_employees,
            'total': len(late_employees)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_dashboard.route('/api/absent-employees')
def absent_employees_api():
    """API endpoint for absent employees data"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get all active employees
        all_employees = db.get_all('employees')
        active_employees = [e for e in all_employees if e.employment_status == 'active']
        
        # Get today's attendance records
        today = date.today().isoformat()
        all_attendance_records = db.get_all('attendance_records')
        today_records = [r for r in all_attendance_records if r.date == today]
        
        # Get employees who clocked in today
        present_employee_ids = [r.employee_id for r in today_records if r.clock_in_time]
        
        # Find absent employees (active employees who haven't clocked in today)
        absent_employees = []
        for employee in active_employees:
            if employee.employee_id not in present_employee_ids:
                # Get their last attendance record
                employee_records = [r for r in all_attendance_records if r.employee_id == employee.employee_id]
                employee_records.sort(key=lambda x: x.date, reverse=True)
                
                last_record = employee_records[0] if employee_records else None
                
                # Determine absence reason and status
                absence_reason = "Absent"
                action_color = "danger"
                action_icon = "user-times"
                
                # Check if employee is on break (clocked in yesterday but not out)
                if last_record and last_record.clock_in_time and not last_record.clock_out_time:
                    # Check if it's from yesterday or earlier
                    if last_record.date != today:
                        absence_reason = "On Extended Break"
                        action_color = "warning"
                        action_icon = "coffee"
                elif last_record:
                    # Determine professional absence reason based on patterns
                    days_since_last = (date.today() - date.fromisoformat(last_record.date)).days
                    
                    if days_since_last == 1:
                        absence_reason = "Personal Day"
                        action_color = "info"
                        action_icon = "user-clock"
                    elif days_since_last <= 3:
                        absence_reason = "On Leave"
                        action_color = "warning"
                        action_icon = "calendar-times"
                    elif days_since_last <= 7:
                        absence_reason = "Extended Leave"
                        action_color = "warning"
                        action_icon = "calendar-minus"
                    else:
                        absence_reason = "Long-term Absence"
                        action_color = "danger"
                        action_icon = "user-times"
                else:
                    absence_reason = "No Attendance History"
                    action_color = "secondary"
                    action_icon = "question-circle"
                
                # Format last known information
                last_seen = "Never"
                last_ip = "Unknown"
                if last_record:
                    try:
                        last_date = date.fromisoformat(last_record.date)
                        if last_date == date.today():
                            last_seen = "Today"
                        elif last_date == date.today() - timedelta(days=1):
                            last_seen = "Yesterday"
                        else:
                            last_seen = last_date.strftime('%Y-%m-%d')
                    except:
                        last_seen = last_record.date
                    
                    last_ip = last_record.clock_in_ip or last_record.clock_out_ip or "Unknown"
                
                # Generate initials for placeholder image
                name_parts = employee.full_name.split()
                initials = ''.join([part[0].upper() for part in name_parts[:2]])
                
                absent_employee = {
                    'employee': {
                        'employee_id': employee.employee_id,
                        'name': employee.full_name,
                        'department': employee.department,
                        'photo': f'https://via.placeholder.com/40x40/{action_color[0:6]}/ffffff?text={initials}'
                    },
                    'action_type': absence_reason,
                    'action_color': action_color,
                    'action_icon': action_icon,
                    'timestamp': last_seen,
                    'ip_address': last_ip,
                    'terminal': last_record.clock_in_terminal if last_record else 'Unknown',
                    'last_clock_in': last_record.clock_in_time if last_record else None,
                    'days_absent': (date.today() - date.fromisoformat(last_record.date)).days if last_record else 0,
                    'is_absent': True
                }
                absent_employees.append(absent_employee)
        
        return jsonify({
            'success': True,
            'absent_employees': absent_employees,
            'total': len(absent_employees)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
