"""
Employee Terminal Assignment model for Time Attendance System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import BaseModel

class EmployeeTerminalAssignment(BaseModel):
    """Model for assigning employees to specific terminals"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Assignment identification
        self.assignment_id = kwargs.get('assignment_id', '')
        self.employee_id = kwargs.get('employee_id', '')
        self.terminal_id = kwargs.get('terminal_id', '')
        
        # Assignment details
        self.is_active = kwargs.get('is_active', True)
        self.assigned_by = kwargs.get('assigned_by', '')  # Admin who made the assignment
        self.assigned_date = kwargs.get('assigned_date', datetime.now().isoformat())
        self.effective_date = kwargs.get('effective_date', datetime.now().isoformat())
        self.expiry_date = kwargs.get('expiry_date', '')  # Optional expiry date
        
        # Assignment type and restrictions
        self.assignment_type = kwargs.get('assignment_type', 'exclusive')  # exclusive, shared
        self.priority = kwargs.get('priority', 1)  # Priority for multiple assignments
        
        # Time-based restrictions (optional)
        self.allowed_time_start = kwargs.get('allowed_time_start', '')  # HH:MM format
        self.allowed_time_end = kwargs.get('allowed_time_end', '')  # HH:MM format
        self.allowed_days = kwargs.get('allowed_days', [])  # ['monday', 'tuesday', ...]
        
        # Notes and reason
        self.reason = kwargs.get('reason', '')
        self.notes = kwargs.get('notes', '')
    
    def validate(self) -> bool:
        """Validate assignment data"""
        if not self.employee_id or not self.terminal_id:
            return False
        
        if self.assignment_type not in ['exclusive', 'shared']:
            return False
        
        if self.allowed_time_start and not self._is_valid_time(self.allowed_time_start):
            return False
        
        if self.allowed_time_end and not self._is_valid_time(self.allowed_time_end):
            return False
        
        return True
    
    def _is_valid_time(self, time_str: str) -> bool:
        """Validate time format HH:MM"""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, AttributeError):
            return False
    
    def is_valid_for_time(self, check_time: datetime = None) -> bool:
        """Check if assignment is valid for the given time"""
        if not self.is_active:
            return False
        
        if check_time is None:
            check_time = datetime.now()
        
        # Check date validity
        if self.expiry_date:
            try:
                expiry = datetime.fromisoformat(self.expiry_date)
                if check_time > expiry:
                    return False
            except ValueError:
                pass
        
        # Check time restrictions
        if self.allowed_time_start and self.allowed_time_end:
            current_time = check_time.strftime('%H:%M')
            if not (self.allowed_time_start <= current_time <= self.allowed_time_end):
                return False
        
        # Check day restrictions
        if self.allowed_days:
            current_day = check_time.strftime('%A').lower()
            if current_day not in self.allowed_days:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return super().to_dict()
    
    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return self.to_dict()
