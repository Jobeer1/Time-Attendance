"""
Reports: attendance, department, overtime, summary, CSV export
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from datetime import datetime, date, timedelta
from ..services.database import db
from ..utils.auth import is_admin_authenticated

bp_reports = Blueprint('reports', __name__)

# Attendance, department, overtime, summary, and CSV export routes go here

@bp_reports.route('/reports')
def reports():
    """Reports page"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    return render_template('attendance/reports.html')

@bp_reports.route('/attendance_records')
def attendance_records():
    """Attendance records page"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    
    # Get filter parameters from request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    employee_id = request.args.get('employee_id', '')
    
    # Create filters object for template
    filters = {
        'date_from': date_from,
        'date_to': date_to,
        'employee_id': employee_id
    }
    
    try:
        # Get all active employees for the filter dropdown
        all_employees = db.find('employees', {'employment_status': 'active'})
        employees = [{'employee_id': emp.employee_id, 'name': emp.full_name} for emp in all_employees]
        employees.sort(key=lambda x: x['name'])
        
        # Get all attendance records
        all_attendance_records = db.get_all('attendance_records')
        
        # Apply filters
        filtered_records = []
        for record in all_attendance_records:
            # Convert date fields for comparison
            record_date = record.date if hasattr(record, 'date') else ''
            
            # Date filter
            if date_from and record_date < date_from:
                continue
            if date_to and record_date > date_to:
                continue
            
            # Employee filter - handle both string employee_id and UUID
            if employee_id:
                # Check if record.employee_id matches the selected employee_id (string) or UUID
                target_employee = next((emp for emp in all_employees if emp.employee_id == employee_id), None)
                if not (record.employee_id == employee_id or (target_employee and record.employee_id == target_employee.id)):
                    continue
                
            filtered_records.append(record)
        
        # Sort by date descending (most recent first)
        filtered_records.sort(key=lambda x: x.date or '', reverse=True)
        
        # Calculate pagination
        total_records = len(filtered_records)
        total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_records = filtered_records[start_index:end_index]
        
        # Get employee details for each record (use both UUID and employee_id for mapping)
        employee_map_by_uuid = {emp.id: emp for emp in all_employees}
        employee_map_by_id = {emp.employee_id: emp for emp in all_employees}
        
        # Format records for template
        records = []
        for record in paginated_records:
            # Try to find employee by UUID first, then by employee_id string
            employee = employee_map_by_uuid.get(record.employee_id) or employee_map_by_id.get(record.employee_id)
            
            # Determine action type and timestamp based on clock times
            action_type = 'clock_in'
            timestamp_str = record.clock_in_time
            terminal_name = record.clock_in_terminal
            
            if record.clock_out_time:
                action_type = 'clock_out'
                timestamp_str = record.clock_out_time
                terminal_name = record.clock_out_terminal
            
            # Parse timestamp
            try:
                if timestamp_str:
                    if 'T' in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    else:
                        timestamp = datetime.strptime(f"{record.date}T{timestamp_str}", "%Y-%m-%dT%H:%M:%S")
                else:
                    timestamp = datetime.now()
            except:
                timestamp = datetime.now()
            
            formatted_record = {
                'record_id': record.id,
                'employee_id': record.employee_id,
                'timestamp': timestamp,
                'action_type': action_type,
                'terminal_name': terminal_name or 'Unknown Terminal',
                'employee': {
                    'name': employee.full_name if employee else 'Unknown Employee',
                    'photo': employee.photo if employee and employee.photo else '/static/attendance/images/default-avatar.png'
                },
                'hours_worked': record.total_hours if hasattr(record, 'total_hours') else None,
                'overtime_hours': record.overtime_hours if hasattr(record, 'overtime_hours') else 0,
                'status': record.status if hasattr(record, 'status') else 'Valid'
            }
            
            # Add action color and icon
            if action_type == 'clock_in':
                formatted_record['action_color'] = 'success'
                formatted_record['action_icon'] = 'sign-in-alt'
            elif action_type == 'clock_out':
                formatted_record['action_color'] = 'danger'
                formatted_record['action_icon'] = 'sign-out-alt'
            else:
                formatted_record['action_color'] = 'secondary'
                formatted_record['action_icon'] = 'question'
            
            records.append(formatted_record)
        
        # Create pagination object with iter_pages method
        class Pagination:
            def __init__(self, page, per_page, total, pages):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = pages
                self.has_prev = page > 1
                self.has_next = page < pages
                self.prev_num = page - 1 if page > 1 else None
                self.next_num = page + 1 if page < pages else None
            
            def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                last = self.pages
                for num in range(1, last + 1):
                    if num <= left_edge or \
                       (self.page - left_current - 1 < num < self.page + right_current) or \
                       num > last - right_edge:
                        yield num
        
        pagination = Pagination(page, per_page, total_records, total_pages)
        
        print(f"[DEBUG] Attendance records loaded: {len(records)} records, page {page}/{total_pages}")
        
    except Exception as e:
        print(f"[ERROR] Failed to load attendance records: {str(e)}")
        import traceback
        traceback.print_exc()
        employees = []
        records = []
        
        class EmptyPagination:
            def __init__(self):
                self.page = 1
                self.per_page = per_page
                self.total = 0
                self.pages = 0
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
            
            def iter_pages(self):
                return []
        
        pagination = EmptyPagination()
    
    return render_template('attendance/attendance_records.html', 
                         records=records, 
                         pagination=pagination, 
                         filters=filters,
                         employees=employees)

@bp_reports.route('/api/attendance_records')
def api_attendance_records():
    """API endpoint for attendance records with filtering"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    employee_id = request.args.get('employee_id', '')
    
    try:
        # Get all active employees for filtering
        all_employees = db.find('employees', {'employment_status': 'active'})
        
        # Get all attendance records
        all_attendance_records = db.get_all('attendance_records')
        
        # Apply filters
        filtered_records = []
        for record in all_attendance_records:
            # Convert date fields for comparison
            record_date = record.date if hasattr(record, 'date') else ''
            
            # Date filter
            if date_from and record_date < date_from:
                continue
            if date_to and record_date > date_to:
                continue
            
            # Employee filter
            if employee_id:
                # Check if record.employee_id matches the selected employee_id (string) or UUID
                target_employee = next((emp for emp in all_employees if emp.employee_id == employee_id), None)
                if not (record.employee_id == employee_id or (target_employee and record.employee_id == target_employee.id)):
                    continue
                
            filtered_records.append(record)
        
        # Sort by date descending (most recent first)
        filtered_records.sort(key=lambda x: x.date or '', reverse=True)
        
        # Calculate pagination
        total_records = len(filtered_records)
        total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_records = filtered_records[start_index:end_index]
        
        # Get employee details for each record (use both UUID and employee_id for mapping)
        employee_map_by_uuid = {emp.id: emp for emp in all_employees}
        employee_map_by_id = {emp.employee_id: emp for emp in all_employees}
        
        # Format records for JSON response
        records = []
        for record in paginated_records:
            # Try to find employee by UUID first, then by employee_id string
            employee = employee_map_by_uuid.get(record.employee_id) or employee_map_by_id.get(record.employee_id)
            
            # Determine action type and timestamp based on clock times
            action_type = 'clock_in'
            timestamp_str = record.clock_in_time
            terminal_name = record.clock_in_terminal
            
            if record.clock_out_time:
                action_type = 'clock_out'
                timestamp_str = record.clock_out_time
                terminal_name = record.clock_out_terminal
            
            records.append({
                'record_id': record.id,
                'employee_id': record.employee_id,
                'timestamp': timestamp_str,
                'action_type': action_type,
                'terminal_name': terminal_name or 'Unknown Terminal',
                'employee_name': employee.full_name if employee else 'Unknown Employee',
                'employee_photo': employee.photo if employee and employee.photo else '/static/attendance/images/default-avatar.png'
            })
        
        return jsonify({
            'success': True,
            'records': records,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_records,
                'pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        })
        
    except Exception as e:
        print(f"[ERROR] API attendance records failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to load attendance records'}), 500

@bp_reports.route('/api/attendance_record/<record_id>')
def api_attendance_record_details(record_id):
    """Get detailed information about a specific attendance record"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get the attendance record
        record = db.get_by_id('attendance_records', record_id)
        
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        # Get employee details - try multiple approaches
        employee = None
        
        # First try by UUID (if record.employee_id is a UUID)
        try:
            employee = db.get_by_id('employees', record.employee_id)
        except:
            pass
        
        # If not found, try by employee_id string
        if not employee:
            all_employees = db.get_all('employees')
            employee = next((emp for emp in all_employees if emp.employee_id == record.employee_id), None)
        
        # Determine action type and timestamp based on clock times
        action_type = 'clock_in'
        timestamp_str = record.clock_in_time
        terminal_name = record.clock_in_terminal
        
        if record.clock_out_time:
            action_type = 'clock_out'
            timestamp_str = record.clock_out_time
            terminal_name = record.clock_out_terminal
        
        response_record = {
            'record_id': record.id,
            'employee_id': record.employee_id,
            'timestamp': timestamp_str,
            'action_type': action_type,
            'terminal_name': terminal_name,
            'employee': {
                'name': employee.full_name if employee else 'Unknown Employee',
                'employee_id': employee.employee_id if employee else record.employee_id,
                'photo': employee.photo if employee and employee.photo else '/static/attendance/images/default-avatar.png',
                'department': employee.department if employee else 'Unknown'
            }
        }
        
        return jsonify({'success': True, 'record': response_record})
        
    except Exception as e:
        print(f"[ERROR] Failed to get record details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to load record details'}), 500

@bp_reports.route('/api/attendance_record/<record_id>', methods=['PUT'])
def api_update_attendance_record(record_id):
    """Update an attendance record"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        print(f"[DEBUG] Update request data: {data}")
        
        timestamp = data.get('timestamp')
        action_type = data.get('action_type')
        notes = data.get('notes', '')
        
        if not timestamp:
            print(f"[ERROR] Missing timestamp in request")
            return jsonify({'error': 'Timestamp is required'}), 400
        
        # Check if record exists
        record = db.get_by_id('attendance_records', record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        # Parse the timestamp and action type to update the appropriate fields
        try:
            # Convert timestamp to the correct format
            if 'T' in timestamp:
                datetime_obj = datetime.fromisoformat(timestamp.replace('Z', ''))
            else:
                datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M')
            
            time_str = datetime_obj.isoformat()
            
            # Update the record based on action type
            updates = {'notes': notes}
            
            if action_type == 'clock_in':
                updates['clock_in_time'] = time_str
                if not record.clock_in_terminal:
                    updates['clock_in_terminal'] = 'Admin Edit'
            elif action_type == 'clock_out':
                updates['clock_out_time'] = time_str
                if not record.clock_out_terminal:
                    updates['clock_out_terminal'] = 'Admin Edit'
            else:
                # Default to clock_in if action_type is unclear
                updates['clock_in_time'] = time_str
                if not record.clock_in_terminal:
                    updates['clock_in_terminal'] = 'Admin Edit'
            
        except ValueError as e:
            return jsonify({'error': f'Invalid timestamp format: {str(e)}'}), 400
        
        updated_record = db.update('attendance_records', record_id, updates)
        
        if updated_record:
            return jsonify({'success': True, 'message': 'Record updated successfully'})
        else:
            return jsonify({'error': 'Failed to update record'}), 500
        
    except Exception as e:
        print(f"[ERROR] Failed to update record: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to update record'}), 500

@bp_reports.route('/api/attendance_record/<record_id>', methods=['DELETE'])
def api_delete_attendance_record(record_id):
    """Delete an attendance record"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Check if record exists
        record = db.get_by_id('attendance_records', record_id)
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        # Delete the record
        success = db.delete('attendance_records', record_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Record deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete record'}), 500
        
    except Exception as e:
        print(f"[ERROR] Failed to delete record: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to delete record'}), 500

@bp_reports.route('/api/export_attendance')
def api_export_attendance():
    """Export attendance records to CSV"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get filter parameters
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        employee_id = request.args.get('employee_id', '')
        
        # Get all active employees for filtering
        all_employees = db.get_all('employees')
        
        # Get all attendance records
        all_attendance_records = db.get_all('attendance_records')
        
        # Apply filters
        filtered_records = []
        for record in all_attendance_records:
            # Convert date fields for comparison
            record_date = record.date if hasattr(record, 'date') else ''
            
            # Date filter
            if date_from and record_date < date_from:
                continue
            if date_to and record_date > date_to:
                continue
            
            # Employee filter
            if employee_id:
                # Check if record.employee_id matches the selected employee_id (string) or UUID
                target_employee = next((emp for emp in all_employees if emp.employee_id == employee_id), None)
                if not (record.employee_id == employee_id or (target_employee and record.employee_id == target_employee.id)):
                    continue
                
            filtered_records.append(record)
        
        # Sort by date descending (most recent first)
        filtered_records.sort(key=lambda x: x.date or '', reverse=True)
        
        # Get employee details for each record (use both UUID and employee_id for mapping)
        employee_map_by_uuid = {emp.id: emp for emp in all_employees}
        employee_map_by_id = {emp.employee_id: emp for emp in all_employees}
        
        # Generate CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Employee ID', 'Employee Name', 'Date', 'Clock In', 'Clock Out', 'Total Hours', 'Terminal'])
        
        # Write data
        for record in filtered_records:
            # Try to find employee by UUID first, then by employee_id string
            employee = employee_map_by_uuid.get(record.employee_id) or employee_map_by_id.get(record.employee_id)
            
            writer.writerow([
                employee.employee_id if employee else record.employee_id,
                employee.full_name if employee else 'Unknown Employee',
                record.date,
                record.clock_in_time or '',
                record.clock_out_time or '',
                record.total_hours if hasattr(record, 'total_hours') else 0,
                record.clock_in_terminal or record.clock_out_terminal or 'Unknown'
            ])
        
        # Return CSV content as JSON
        csv_data = output.getvalue()
        output.close()
        
        return jsonify({
            'success': True,
            'csv_data': csv_data,
            'filename': f'attendance_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to export attendance: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to export attendance records'}), 500
