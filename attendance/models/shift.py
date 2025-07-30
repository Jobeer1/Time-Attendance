# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\models\shift.py
"""
Shift and shift assignment models for Time Attendance System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, time
from .base import BaseModel

class Shift(BaseModel):
    """Shift model for defining work schedules"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Basic shift information
        self.name = kwargs.get('name', '')
        self.description = kwargs.get('description', '')
        self.start_time = kwargs.get('start_time', '09:00:00')  # HH:MM:SS format
        self.end_time = kwargs.get('end_time', '17:00:00')
        
        # Days of week (0=Monday, 6=Sunday)
        self.days_of_week = kwargs.get('days_of_week', [0, 1, 2, 3, 4])  # Monday to Friday
        
        # Overtime settings
        self.overtime_threshold = kwargs.get('overtime_threshold', 8.0)  # hours
        self.overtime_rate = kwargs.get('overtime_rate', 1.5)  # multiplier
        
        # Break settings
        self.break_duration = kwargs.get('break_duration', 60)  # minutes
        self.break_paid = kwargs.get('break_paid', True)
        
        # Grace periods
        self.late_grace_period = kwargs.get('late_grace_period', 15)  # minutes
        self.early_departure_grace_period = kwargs.get('early_departure_grace_period', 15)
        
        # Shift settings
        self.is_active = kwargs.get('is_active', True)
        self.requires_approval = kwargs.get('requires_approval', False)
        self.color = kwargs.get('color', '#3498db')  # For calendar display
        
        # Holiday and weekend settings
        self.weekend_rate = kwargs.get('weekend_rate', 1.5)
        self.holiday_rate = kwargs.get('holiday_rate', 2.0)
    
    @property
    def duration_hours(self) -> float:
        """Calculate shift duration in hours"""
        try:
            start = datetime.strptime(self.start_time, '%H:%M:%S').time()
            end = datetime.strptime(self.end_time, '%H:%M:%S').time()
            
            start_minutes = start.hour * 60 + start.minute
            end_minutes = end.hour * 60 + end.minute
            
            # Handle overnight shifts
            if end_minutes <= start_minutes:
                end_minutes += 24 * 60
            
            duration_minutes = end_minutes - start_minutes
            return round(duration_minutes / 60, 2)
        except ValueError:
            return 8.0  # Default
    
    def validate(self) -> bool:
        """Validate shift data"""
        if not self.name or not self.start_time or not self.end_time:
            return False
        
        try:
            datetime.strptime(self.start_time, '%H:%M:%S')
            datetime.strptime(self.end_time, '%H:%M:%S')
        except ValueError:
            return False
        
        if not self.days_of_week or not all(0 <= day <= 6 for day in self.days_of_week):
            return False
        
        return True

class ShiftAssignment(BaseModel):
    """Shift assignment model for employee scheduling"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Assignment information
        self.employee_id = kwargs.get('employee_id', '')
        self.shift_id = kwargs.get('shift_id', '')
        self.start_date = kwargs.get('start_date', datetime.now().date().isoformat())
        self.end_date = kwargs.get('end_date', '')  # Empty for ongoing assignments
        
        # Override settings for specific assignment
        self.custom_start_time = kwargs.get('custom_start_time', '')
        self.custom_end_time = kwargs.get('custom_end_time', '')
        self.custom_days = kwargs.get('custom_days', [])  # Override shift days
        
        # Assignment status
        self.is_active = kwargs.get('is_active', True)
        self.is_temporary = kwargs.get('is_temporary', False)
        self.priority = kwargs.get('priority', 1)  # For multiple assignments
        
        # Approval and notes
        self.assigned_by = kwargs.get('assigned_by', '')
        self.assignment_reason = kwargs.get('assignment_reason', '')
        self.notes = kwargs.get('notes', '')
        
        # Notification settings
        self.notify_employee = kwargs.get('notify_employee', True)
        self.notification_sent = kwargs.get('notification_sent', False)
    
    @property
    def is_current(self) -> bool:
        """Check if assignment is currently active"""
        if not self.is_active:
            return False
        
        today = datetime.now().date().isoformat()
        
        if today < self.start_date:
            return False
        
        if self.end_date and today > self.end_date:
            return False
        
        return True
    
    def validate(self) -> bool:
        """Validate shift assignment"""
        if not self.employee_id or not self.shift_id or not self.start_date:
            return False
        
        if self.end_date and self.end_date < self.start_date:
            return False
        
        return True
