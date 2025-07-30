# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\models\employee.py
"""
Employee model for Time Attendance System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from .base import BaseModel

class Employee(BaseModel):
    """Employee model with face recognition support"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Personal information
        self.employee_id = kwargs.get('employee_id', '')
        self.first_name = kwargs.get('first_name', '')
        self.last_name = kwargs.get('last_name', '')
        self.email = kwargs.get('email', '')
        self.phone = kwargs.get('phone', '')
        self.department = kwargs.get('department', '')
        self.position = kwargs.get('position', '')
          # Employment details
        self.hire_date = kwargs.get('hire_date', datetime.now().date().isoformat())
        self.employment_status = kwargs.get('employment_status', 'active')  # active, inactive, terminated
        self.employment_type = kwargs.get('employment_type', 'full_time')  # full_time, part_time, contract
        self.salary = kwargs.get('salary', 0.0)  # Employee salary
        
        # Authentication
        self.password_hash = kwargs.get('password_hash', '')
        self.pin = kwargs.get('pin', '')  # 4-digit PIN for quick access
        
        # Face recognition
        self.face_encodings = kwargs.get('face_encodings', [])  # Multiple face encodings
        self.face_recognition_enabled = kwargs.get('face_recognition_enabled', True)
        self.face_photos = kwargs.get('face_photos', [])  # Paths to face photos
        self.photo = kwargs.get('photo', '')  # Main employee photo
        
        # Authentication requirements
        self.require_face_recognition = kwargs.get('require_face_recognition', False)
        self.require_pin = kwargs.get('require_pin', True)
        
        # Work permissions
        self.can_work_overtime = kwargs.get('can_work_overtime', True)
        
        # Shift assignments
        self.default_shift_id = kwargs.get('default_shift_id', '')
        self.current_shift_assignments = kwargs.get('current_shift_assignments', [])
        
        # Permissions
        self.is_admin = kwargs.get('is_admin', False)
        self.can_manage_employees = kwargs.get('can_manage_employees', False)
        self.can_view_reports = kwargs.get('can_view_reports', False)
        
        # Settings
        self.notification_preferences = kwargs.get('notification_preferences', {
            'email_notifications': True,
            'overtime_alerts': True,
            'schedule_changes': True
        })
        
        # Statistics
        self.total_hours_worked = kwargs.get('total_hours_worked', 0.0)
        self.total_overtime_hours = kwargs.get('total_overtime_hours', 0.0)
        self.attendance_streak = kwargs.get('attendance_streak', 0)
        self.last_clock_in = kwargs.get('last_clock_in', '')
        self.last_clock_out = kwargs.get('last_clock_out', '')
        
        # Notes and additional information
        self.notes = kwargs.get('notes', '')
    
    @property
    def full_name(self) -> str:
        """Get employee's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_active(self) -> bool:
        """Check if employee is active"""
        return self.employment_status == 'active'
    
    def validate(self) -> bool:
        """Validate employee data"""
        if not self.employee_id or not self.first_name or not self.last_name:
            return False
        
        if self.email and not self._is_valid_email(self.email):
            return False
        
        if self.pin and (len(self.pin) != 4 or not self.pin.isdigit()):
            return False
        
        return True
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def add_face_encoding(self, encoding: List[float], photo_path: str = ''):
        """Add a new face encoding"""
        self.face_encodings.append(encoding)
        if photo_path:
            self.face_photos.append(photo_path)
        self.updated_at = datetime.now().isoformat()
    
    def remove_face_encoding(self, index: int):
        """Remove a face encoding by index"""
        if 0 <= index < len(self.face_encodings):
            self.face_encodings.pop(index)
            if index < len(self.face_photos):
                self.face_photos.pop(index)
            self.updated_at = datetime.now().isoformat()
    
    def update_statistics(self, hours_worked: float, overtime_hours: float = 0.0):
        """Update employee statistics"""
        self.total_hours_worked += hours_worked
        self.total_overtime_hours += overtime_hours
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding sensitive data for API responses"""
        data = super().to_dict()
        return data
    
    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to dictionary excluding sensitive information"""
        data = self.to_dict()
        # Remove sensitive fields
        sensitive_fields = ['password_hash', 'face_encodings', 'pin']
        for field in sensitive_fields:
            data.pop(field, None)
        return data
    
    @staticmethod
    def get_all_employees():
        """Get all employees from database - compatibility method for messaging"""
        from ..services.database import db
        return db.get_all('employees')
