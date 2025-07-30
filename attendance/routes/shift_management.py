"""
Shift management: CRUD, assignment, shift-employee relations
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from datetime import datetime, time, timedelta
from ..services.database import db
from ..utils.auth import is_admin_authenticated

bp_shift = Blueprint('shift_management', __name__)

# Shift CRUD, assignment, and shift-employee relation routes go here

@bp_shift.route('/shifts')
def shifts():
    """List all shifts"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    
    try:
        # Get all shifts from database
        all_shifts = db.get_all('shifts')
        print(f"[DEBUG] Found {len(all_shifts)} shifts for template")
        shifts = []
        
        for shift in all_shifts:
            # Determine shift type based on start time if not explicitly set
            start_hour = 0
            if hasattr(shift, 'start_time'):
                try:
                    if ':' in str(shift.start_time):
                        start_hour = int(str(shift.start_time).split(':')[0])
                    else:
                        start_hour = int(str(shift.start_time))
                except:
                    start_hour = 9
            
            # Auto-detect shift type based on start time
            auto_shift_type = 'day'
            if start_hour >= 18 or start_hour < 6:  # 6 PM to 6 AM is night shift
                auto_shift_type = 'night'
            
            shift_data = {
                'id': shift.id,
                'name': shift.name if hasattr(shift, 'name') else 'Unnamed Shift',
                'shift_type': shift.shift_type if hasattr(shift, 'shift_type') and shift.shift_type else auto_shift_type,
                'start_time': shift.start_time if hasattr(shift, 'start_time') else '09:00',
                'end_time': shift.end_time if hasattr(shift, 'end_time') else '17:00',
                'duration_hours': shift.duration_hours if hasattr(shift, 'duration_hours') else 8,
                'is_active': shift.is_active if hasattr(shift, 'is_active') else True,
                'description': shift.description if hasattr(shift, 'description') else '',
                'assigned_employees': []  # Will be calculated separately
            }
            shifts.append(shift_data)
            print(f"[DEBUG] Template shift: {shift_data['name']} ({shift_data['start_time']} - {shift_data['end_time']}) Type: {shift_data['shift_type']}")
        
        print(f"[DEBUG] Rendering template with {len(shifts)} shifts")
        return render_template('attendance/shifts.html', shifts=shifts)
        
    except Exception as e:
        print(f"[ERROR] Failed to load shifts: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('attendance/shifts.html', shifts=[])

@bp_shift.route('/api/shifts')
def api_shifts():
    """API endpoint to get all shifts"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        all_shifts = db.get_all('shifts')
        print(f"[DEBUG] Found {len(all_shifts)} shifts in database")
        
        shifts = []
        
        for shift in all_shifts:
            # Determine shift type based on start time if not explicitly set
            start_hour = 0
            if hasattr(shift, 'start_time'):
                try:
                    if ':' in str(shift.start_time):
                        start_hour = int(str(shift.start_time).split(':')[0])
                    else:
                        start_hour = int(str(shift.start_time))
                except:
                    start_hour = 9
            
            # Auto-detect shift type based on start time
            auto_shift_type = 'day'
            if start_hour >= 18 or start_hour < 6:  # 6 PM to 6 AM is night shift
                auto_shift_type = 'night'
            
            shift_data = {
                'id': shift.id,
                'name': shift.name if hasattr(shift, 'name') else 'Unnamed Shift',
                'shift_type': shift.shift_type if hasattr(shift, 'shift_type') and shift.shift_type else auto_shift_type,
                'start_time': shift.start_time if hasattr(shift, 'start_time') else '09:00',
                'end_time': shift.end_time if hasattr(shift, 'end_time') else '17:00',
                'duration_hours': shift.duration_hours if hasattr(shift, 'duration_hours') else 8,
                'is_active': shift.is_active if hasattr(shift, 'is_active') else True,
                'description': shift.description if hasattr(shift, 'description') else '',
                'assigned_employees': 0  # Will be calculated separately
            }
            shifts.append(shift_data)
            print(f"[DEBUG] API Shift: {shift_data['name']} ({shift_data['start_time']} - {shift_data['end_time']}) Type: {shift_data['shift_type']}")
        
        print(f"[DEBUG] Returning {len(shifts)} shifts to frontend")
        return jsonify({'success': True, 'shifts': shifts})
        
    except Exception as e:
        print(f"[ERROR] Failed to load shifts API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to load shifts'}), 500

@bp_shift.route('/api/shifts', methods=['POST'])
def api_create_shift():
    """Create a new shift"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        print(f"[DEBUG] Creating shift with data: {data}")
        
        # Validate required fields
        required_fields = ['name', 'shift_type', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Calculate duration
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # Handle overnight shifts
        if end_time < start_time:
            duration = (datetime.combine(datetime.today(), end_time) + timedelta(days=1) - 
                       datetime.combine(datetime.today(), start_time)).total_seconds() / 3600
        else:
            duration = (datetime.combine(datetime.today(), end_time) - 
                       datetime.combine(datetime.today(), start_time)).total_seconds() / 3600
        
        # Create shift object (using a simple class for now)
        class SimpleShift:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        shift = SimpleShift(
            name=data['name'],
            shift_type=data['shift_type'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration_hours=round(duration, 2),
            break_duration=data.get('break_duration', 30),
            max_overtime_hours=data.get('max_overtime_hours', 2),
            working_days=data.get('working_days', ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']),
            description=data.get('description', ''),
            is_active=data.get('is_active', True),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Save to database
        created_shift = db.create('shifts', shift)
        
        if created_shift:
            return jsonify({'success': True, 'message': 'Shift created successfully', 'shift_id': created_shift.id})
        else:
            return jsonify({'error': 'Failed to create shift'}), 500
        
    except Exception as e:
        print(f"[ERROR] Failed to create shift: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to create shift'}), 500

@bp_shift.route('/api/shifts/<shift_id>')
def api_get_shift(shift_id):
    """Get a specific shift"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        shift = db.get_by_id('shifts', shift_id)
        
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        shift_data = {
            'id': shift.id,
            'name': shift.name if hasattr(shift, 'name') else 'Unnamed Shift',
            'shift_type': shift.shift_type if hasattr(shift, 'shift_type') else 'day',
            'start_time': shift.start_time if hasattr(shift, 'start_time') else '09:00',
            'end_time': shift.end_time if hasattr(shift, 'end_time') else '17:00',
            'duration_hours': shift.duration_hours if hasattr(shift, 'duration_hours') else 8,
            'is_active': shift.is_active if hasattr(shift, 'is_active') else True,
            'description': shift.description if hasattr(shift, 'description') else '',
            'break_duration': shift.break_duration if hasattr(shift, 'break_duration') else 30,
            'max_overtime_hours': shift.max_overtime_hours if hasattr(shift, 'max_overtime_hours') else 2,
            'working_days': shift.working_days if hasattr(shift, 'working_days') else ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        }
        
        return jsonify({'success': True, 'shift': shift_data})
        
    except Exception as e:
        print(f"[ERROR] Failed to get shift: {str(e)}")
        return jsonify({'error': 'Failed to load shift'}), 500

@bp_shift.route('/api/shifts/<shift_id>', methods=['PUT'])
def api_update_shift(shift_id):
    """Update a shift"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        print(f"[DEBUG] Updating shift {shift_id} with data: {data}")
        
        # Check if shift exists
        shift = db.get_by_id('shifts', shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        # Calculate duration if times are provided
        updates = {}
        for key, value in data.items():
            if key not in ['shift_id']:  # Exclude internal fields
                updates[key] = value
        
        if 'start_time' in updates and 'end_time' in updates:
            start_time = datetime.strptime(updates['start_time'], '%H:%M').time()
            end_time = datetime.strptime(updates['end_time'], '%H:%M').time()
            
            if end_time < start_time:
                duration = (datetime.combine(datetime.today(), end_time) + timedelta(days=1) - 
                           datetime.combine(datetime.today(), start_time)).total_seconds() / 3600
            else:
                duration = (datetime.combine(datetime.today(), end_time) - 
                           datetime.combine(datetime.today(), start_time)).total_seconds() / 3600
            
            updates['duration_hours'] = round(duration, 2)
        
        updates['updated_at'] = datetime.now().isoformat()
        
        # Update the shift
        updated_shift = db.update('shifts', shift_id, updates)
        
        if updated_shift:
            return jsonify({'success': True, 'message': 'Shift updated successfully'})
        else:
            return jsonify({'error': 'Failed to update shift'}), 500
        
    except Exception as e:
        print(f"[ERROR] Failed to update shift: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to update shift'}), 500

@bp_shift.route('/api/shifts/<shift_id>', methods=['DELETE'])
def api_delete_shift(shift_id):
    """Delete a shift"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Check if shift exists
        shift = db.get_by_id('shifts', shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        # TODO: Check if shift is assigned to any employees
        # For now, just delete it
        
        success = db.delete('shifts', shift_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Shift deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete shift'}), 500
        
    except Exception as e:
        print(f"[ERROR] Failed to delete shift: {str(e)}")
        return jsonify({'error': 'Failed to delete shift'}), 500

@bp_shift.route('/shifts/<shift_id>')
def shift_detail(shift_id):
    """View shift details"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    
    try:
        shift = db.get_by_id('shifts', shift_id)
        
        if not shift:
            return redirect(url_for('shift_management.shifts'))
        
        # Convert to dict for template
        shift_data = {
            'id': shift.id,
            'name': shift.name if hasattr(shift, 'name') else 'Unnamed Shift',
            'shift_type': shift.shift_type if hasattr(shift, 'shift_type') else 'day',
            'start_time': shift.start_time if hasattr(shift, 'start_time') else '09:00',
            'end_time': shift.end_time if hasattr(shift, 'end_time') else '17:00',
            'duration_hours': shift.duration_hours if hasattr(shift, 'duration_hours') else 8,
            'is_active': shift.is_active if hasattr(shift, 'is_active') else True,
            'description': shift.description if hasattr(shift, 'description') else '',
            'break_duration': shift.break_duration if hasattr(shift, 'break_duration') else 30,
            'max_overtime_hours': shift.max_overtime_hours if hasattr(shift, 'max_overtime_hours') else 2,
            'working_days': shift.working_days if hasattr(shift, 'working_days') else ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        }
        
        return render_template('attendance/shift_detail.html', shift=shift_data)
        
    except Exception as e:
        print(f"[ERROR] Failed to load shift detail: {str(e)}")
        return redirect(url_for('shift_management.shifts'))
