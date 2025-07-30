# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\services\shift_manager.py
"""
Shift Management Service for Time Attendance System
Handles shift scheduling, overtime calculation, and time tracking
"""

from datetime import datetime, time, timedelta, date
from typing import List, Optional, Dict, Any, Tuple
import calendar

from .database import db
from ..models import Shift, ShiftAssignment, Employee, AttendanceRecord

class ShiftManagerService:
    """Service for managing shifts and calculating work hours"""
    
    def __init__(self):
        self.default_overtime_threshold = 8.0
        self.default_overtime_rate = 1.5
        self.default_break_duration = 60  # minutes
        
    def init_app(self, app):
        """Initialize with Flask app configuration"""
        self.default_overtime_threshold = app.config.get('OVERTIME_THRESHOLD', 8.0)
        self.default_overtime_rate = app.config.get('OVERTIME_RATE', 1.5)
        self.default_break_duration = app.config.get('BREAK_DURATION', 60)
        
        print("Shift Manager Service initialized")
    
    def get_employee_shift_for_date(self, employee_id: str, target_date: date) -> Optional[Shift]:
        """Get the shift assigned to an employee for a specific date"""
        try:
            # Get current shift assignments for employee
            assignments = db.find('shift_assignments', {
                'employee_id': employee_id,
                'is_active': True
            })
            
            if not assignments:
                return None
            
            # Find the most appropriate assignment for the date
            target_date_str = target_date.isoformat()
            target_weekday = target_date.weekday()  # 0=Monday, 6=Sunday
            
            best_assignment = None
            for assignment in assignments:
                # Check date range
                if assignment.start_date <= target_date_str:
                    if not assignment.end_date or assignment.end_date >= target_date_str:
                        if not best_assignment or assignment.priority > best_assignment.priority:
                            best_assignment = assignment
            
            if not best_assignment:
                return None
            
            # Get the shift details
            shift = db.get_by_id('shifts', best_assignment.shift_id)
            if not shift or not shift.is_active:
                return None
            
            # Check if shift applies to this day of week
            shift_days = best_assignment.custom_days or shift.days_of_week
            if target_weekday not in shift_days:
                return None
            
            # Apply custom times if specified
            if best_assignment.custom_start_time or best_assignment.custom_end_time:
                custom_shift = Shift(**shift.to_dict())
                if best_assignment.custom_start_time:
                    custom_shift.start_time = best_assignment.custom_start_time
                if best_assignment.custom_end_time:
                    custom_shift.end_time = best_assignment.custom_end_time
                return custom_shift
            
            return shift
            
        except Exception as e:
            print(f"Error getting employee shift: {e}")
            return None
    
    def calculate_late_early_status(self, attendance: AttendanceRecord, shift: Shift) -> Dict[str, Any]:
        """Calculate if employee is late or left early"""
        try:
            result = {
                'is_late': False,
                'late_minutes': 0,
                'is_early_departure': False,
                'early_departure_minutes': 0
            }
            
            if not attendance.clock_in_time or not shift:
                return result
            
            # Parse times
            clock_in = datetime.fromisoformat(attendance.clock_in_time).time()
            scheduled_start = datetime.strptime(shift.start_time, '%H:%M:%S').time()
            
            # Calculate late arrival
            clock_in_minutes = clock_in.hour * 60 + clock_in.minute
            scheduled_start_minutes = scheduled_start.hour * 60 + scheduled_start.minute
            
            if clock_in_minutes > scheduled_start_minutes + shift.late_grace_period:
                result['is_late'] = True
                result['late_minutes'] = clock_in_minutes - scheduled_start_minutes
                attendance.is_late = True
            
            # Calculate early departure if clocked out
            if attendance.clock_out_time:
                clock_out = datetime.fromisoformat(attendance.clock_out_time).time()
                scheduled_end = datetime.strptime(shift.end_time, '%H:%M:%S').time()
                
                clock_out_minutes = clock_out.hour * 60 + clock_out.minute
                scheduled_end_minutes = scheduled_end.hour * 60 + scheduled_end.minute
                
                if clock_out_minutes < scheduled_end_minutes - shift.early_departure_grace_period:
                    result['is_early_departure'] = True
                    result['early_departure_minutes'] = scheduled_end_minutes - clock_out_minutes
                    attendance.is_early_departure = True
            
            return result
            
        except Exception as e:
            print(f"Error calculating late/early status: {e}")
            return result
    
    def calculate_work_hours(self, attendance: AttendanceRecord, shift: Optional[Shift] = None) -> Dict[str, float]:
        """Calculate regular and overtime hours for attendance record"""
        try:
            if not attendance.clock_in_time or not attendance.clock_out_time:
                return {'regular_hours': 0.0, 'overtime_hours': 0.0, 'total_hours': 0.0}
            
            # Parse times
            clock_in = datetime.fromisoformat(attendance.clock_in_time)
            clock_out = datetime.fromisoformat(attendance.clock_out_time)
            
            # Calculate total duration
            total_duration = clock_out - clock_in
            total_minutes = total_duration.total_seconds() / 60
            
            # Subtract break time
            break_minutes = attendance.break_duration or (shift.break_duration if shift else self.default_break_duration)
            if not shift or shift.break_paid:
                # Don't subtract break time if breaks are paid
                break_minutes = 0
            
            total_minutes -= break_minutes
            total_hours = max(0, total_minutes / 60)
            
            # Determine overtime threshold
            if shift:
                overtime_threshold = shift.overtime_threshold
                overtime_rate = shift.overtime_rate
            else:
                overtime_threshold = self.default_overtime_threshold
                overtime_rate = self.default_overtime_rate
            
            # Calculate regular vs overtime
            if total_hours <= overtime_threshold:
                regular_hours = total_hours
                overtime_hours = 0.0
            else:
                regular_hours = overtime_threshold
                overtime_hours = total_hours - overtime_threshold
            
            # Apply weekend/holiday rates if applicable
            work_date = datetime.fromisoformat(attendance.date).date()
            if attendance.is_weekend and shift:
                overtime_hours = total_hours  # All hours are overtime on weekends
                regular_hours = 0.0
            elif attendance.is_holiday and shift:
                overtime_hours = total_hours  # All hours are overtime on holidays
                regular_hours = 0.0
            
            return {
                'regular_hours': round(regular_hours, 2),
                'overtime_hours': round(overtime_hours, 2),
                'total_hours': round(total_hours, 2)
            }
            
        except Exception as e:
            print(f"Error calculating work hours: {e}")
            return {'regular_hours': 0.0, 'overtime_hours': 0.0, 'total_hours': 0.0}
    
    def get_employee_schedule(self, employee_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get employee schedule for date range"""
        schedule = []
        current_date = start_date
        
        while current_date <= end_date:
            shift = self.get_employee_shift_for_date(employee_id, current_date)
            
            schedule_entry = {
                'date': current_date.isoformat(),
                'weekday': current_date.strftime('%A'),
                'has_shift': shift is not None,
                'shift': shift.to_dict() if shift else None,
                'is_weekend': current_date.weekday() >= 5,
                'is_holiday': self.is_holiday(current_date)
            }
            
            schedule.append(schedule_entry)
            current_date += timedelta(days=1)
        
        return schedule
    
    def get_team_schedule(self, employee_ids: List[str], target_date: date) -> Dict[str, Any]:
        """Get schedule for multiple employees on a specific date"""
        team_schedule = {
            'date': target_date.isoformat(),
            'weekday': target_date.strftime('%A'),
            'is_weekend': target_date.weekday() >= 5,
            'is_holiday': self.is_holiday(target_date),
            'employees': []
        }
        
        for employee_id in employee_ids:
            employee = db.get_by_id('employees', employee_id)
            if not employee:
                continue
            
            shift = self.get_employee_shift_for_date(employee_id, target_date)
            
            employee_schedule = {
                'employee_id': employee_id,
                'employee_name': employee.full_name,
                'has_shift': shift is not None,
                'shift': shift.to_dict() if shift else None,
                'status': 'scheduled' if shift else 'off'
            }
            
            team_schedule['employees'].append(employee_schedule)
        
        return team_schedule
    
    def assign_shift_to_employee(self, employee_id: str, shift_id: str, start_date: date, 
                               end_date: Optional[date] = None, assigned_by: str = '',
                               custom_times: Dict[str, str] = None) -> ShiftAssignment:
        """Assign a shift to an employee"""
        try:
            # Validate employee exists
            employee = db.get_by_id('employees', employee_id)
            if not employee:
                raise ValueError("Employee not found")
            
            # Validate shift exists
            shift = db.get_by_id('shifts', shift_id)
            if not shift:
                raise ValueError("Shift not found")
            
            # Create assignment
            assignment_data = {
                'employee_id': employee_id,
                'shift_id': shift_id,
                'start_date': start_date.isoformat(),
                'assigned_by': assigned_by,
                'is_active': True
            }
            
            if end_date:
                assignment_data['end_date'] = end_date.isoformat()
            
            if custom_times:
                assignment_data.update(custom_times)
            
            assignment = ShiftAssignment(**assignment_data)
            return db.create('shift_assignments', assignment)
            
        except Exception as e:
            print(f"Error assigning shift: {e}")
            raise
    
    def remove_shift_assignment(self, assignment_id: str) -> bool:
        """Remove or deactivate a shift assignment"""
        try:
            return db.update('shift_assignments', assignment_id, {'is_active': False})
        except Exception as e:
            print(f"Error removing shift assignment: {e}")
            return False
    
    def is_holiday(self, check_date: date) -> bool:
        """Check if date is a holiday (basic implementation)"""
        # This is a basic implementation - you should integrate with a proper holiday calendar
        # For now, just check for major holidays
        holidays = [
            (1, 1),   # New Year's Day
            (12, 25), # Christmas Day
            (12, 26), # Boxing Day (if applicable)
        ]
        
        return (check_date.month, check_date.day) in holidays
    
    def get_overtime_summary(self, employee_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get overtime summary for employee in date range"""
        try:
            # Get attendance records
            records = db.find('attendance_records', {
                'employee_id': employee_id,
                'status': 'completed'
            })
            
            # Filter by date range
            filtered_records = [
                record for record in records
                if start_date.isoformat() <= record.date <= end_date.isoformat()
            ]
            
            total_regular_hours = 0.0
            total_overtime_hours = 0.0
            total_hours = 0.0
            overtime_days = 0
            
            for record in filtered_records:
                total_regular_hours += record.regular_hours or 0.0
                total_overtime_hours += record.overtime_hours or 0.0
                total_hours += record.total_hours or 0.0
                
                if (record.overtime_hours or 0.0) > 0:
                    overtime_days += 1
            
            return {
                'employee_id': employee_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_regular_hours': round(total_regular_hours, 2),
                'total_overtime_hours': round(total_overtime_hours, 2),
                'total_hours': round(total_hours, 2),
                'overtime_days': overtime_days,
                'average_daily_hours': round(total_hours / len(filtered_records), 2) if filtered_records else 0.0,
                'records_count': len(filtered_records)
            }
            
        except Exception as e:
            print(f"Error getting overtime summary: {e}")
            return {}

# Global shift manager service instance
shift_manager = ShiftManagerService()

def init_app(app):
    """Initialize shift manager service with Flask app"""
    global shift_manager
    shift_manager.init_app(app)
