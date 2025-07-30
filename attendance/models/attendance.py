# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\models\attendance.py
"""
Attendance record model for Time Attendance System
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseModel

class AttendanceRecord(BaseModel):
    """Attendance record model"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Employee information
        self.employee_id = kwargs.get('employee_id', '')
        self.employee_name = kwargs.get('employee_name', '')
        
        # Time tracking
        self.clock_in_time = kwargs.get('clock_in_time', '')
        self.clock_out_time = kwargs.get('clock_out_time', '')
        self.date = kwargs.get('date', datetime.now().date().isoformat())
        
        # Location and method
        self.clock_in_terminal = kwargs.get('clock_in_terminal', '')
        self.clock_out_terminal = kwargs.get('clock_out_terminal', '')
        self.clock_in_method = kwargs.get('clock_in_method', 'face_recognition')  # face_recognition, pin, password
        self.clock_out_method = kwargs.get('clock_out_method', 'face_recognition')
        
        # IP addresses for security
        self.clock_in_ip = kwargs.get('clock_in_ip', '')
        self.clock_out_ip = kwargs.get('clock_out_ip', '')
        
        # Shift information
        self.shift_id = kwargs.get('shift_id', '')
        self.scheduled_start = kwargs.get('scheduled_start', '')
        self.scheduled_end = kwargs.get('scheduled_end', '')
        
        # Time calculations
        self.regular_hours = kwargs.get('regular_hours', 0.0)
        self.overtime_hours = kwargs.get('overtime_hours', 0.0)
        self.total_hours = kwargs.get('total_hours', 0.0)
        
        # Break time
        self.break_start_time = kwargs.get('break_start_time', '')
        self.break_end_time = kwargs.get('break_end_time', '')
        self.break_duration = kwargs.get('break_duration', 0.0)  # in minutes
        
        # Status and flags
        self.status = kwargs.get('status', 'active')  # active, completed, cancelled
        self.is_late = kwargs.get('is_late', False)
        self.is_early_departure = kwargs.get('is_early_departure', False)
        self.is_holiday = kwargs.get('is_holiday', False)
        self.is_weekend = kwargs.get('is_weekend', False)
        
        # Notes and approvals
        self.notes = kwargs.get('notes', '')
        self.admin_notes = kwargs.get('admin_notes', '')
        self.approved_by = kwargs.get('approved_by', '')
        self.approval_date = kwargs.get('approval_date', '')
        
        # Geolocation (optional)
        self.clock_in_location = kwargs.get('clock_in_location', {})
        self.clock_out_location = kwargs.get('clock_out_location', {})
    
    @property
    def is_clocked_in(self) -> bool:
        """Check if employee is currently clocked in"""
        return bool(self.clock_in_time and not self.clock_out_time)
    
    @property
    def is_on_break(self) -> bool:
        """Check if employee is currently on break"""
        return bool(self.break_start_time and not self.break_end_time)
    
    def calculate_hours(self):
        """Calculate work hours based on clock in/out times"""
        if not self.clock_in_time or not self.clock_out_time:
            return
        
        try:
            clock_in = datetime.fromisoformat(self.clock_in_time)
            clock_out = datetime.fromisoformat(self.clock_out_time)
            
            # Calculate total duration
            duration = clock_out - clock_in
            total_minutes = duration.total_seconds() / 60
            
            # Subtract break time
            total_minutes -= self.break_duration
            
            # Convert to hours
            self.total_hours = round(total_minutes / 60, 2)
            
            # Calculate regular vs overtime hours
            if self.scheduled_start and self.scheduled_end:
                scheduled_start = datetime.fromisoformat(f"{self.date}T{self.scheduled_start}")
                scheduled_end = datetime.fromisoformat(f"{self.date}T{self.scheduled_end}")
                scheduled_duration = (scheduled_end - scheduled_start).total_seconds() / 3600
                
                if self.total_hours <= scheduled_duration:
                    self.regular_hours = self.total_hours
                    self.overtime_hours = 0.0
                else:
                    self.regular_hours = scheduled_duration
                    self.overtime_hours = self.total_hours - scheduled_duration
            else:
                # Default: 8 hours regular, rest overtime
                if self.total_hours <= 8:
                    self.regular_hours = self.total_hours
                    self.overtime_hours = 0.0
                else:
                    self.regular_hours = 8.0
                    self.overtime_hours = self.total_hours - 8.0
            
            self.updated_at = datetime.now().isoformat()
            
        except (ValueError, TypeError) as e:
            print(f"Error calculating hours: {e}")
    
    def clock_in(self, terminal_id: str = '', method: str = 'face_recognition', ip_address: str = ''):
        """Clock in employee"""
        self.clock_in_time = datetime.now().isoformat()
        self.clock_in_terminal = terminal_id
        self.clock_in_method = method
        self.clock_in_ip = ip_address
        self.status = 'active'
        self.updated_at = datetime.now().isoformat()
    
    def clock_out(self, terminal_id: str = '', method: str = 'face_recognition', ip_address: str = ''):
        """Clock out employee"""
        self.clock_out_time = datetime.now().isoformat()
        self.clock_out_terminal = terminal_id
        self.clock_out_method = method
        self.clock_out_ip = ip_address
        self.status = 'completed'
        self.calculate_hours()
        self.updated_at = datetime.now().isoformat()
    
    def start_break(self):
        """Start break period"""
        self.break_start_time = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def end_break(self):
        """End break period"""
        if self.break_start_time:
            self.break_end_time = datetime.now().isoformat()
            try:
                start = datetime.fromisoformat(self.break_start_time)
                end = datetime.fromisoformat(self.break_end_time)
                self.break_duration += (end - start).total_seconds() / 60
            except (ValueError, TypeError):
                pass
        self.updated_at = datetime.now().isoformat()
    
    def validate(self) -> bool:
        """Validate attendance record"""
        if not self.employee_id or not self.date:
            return False
        
        if self.clock_in_time and self.clock_out_time:
            try:
                clock_in = datetime.fromisoformat(self.clock_in_time)
                clock_out = datetime.fromisoformat(self.clock_out_time)
                if clock_out <= clock_in:
                    return False
            except ValueError:
                return False
        
        return True
