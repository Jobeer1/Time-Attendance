# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\models\__init__.py
"""
Database Models for Time Attendance System
JSON-based storage with backup support
"""

from .employee import Employee
from .attendance import AttendanceRecord
from .shift import Shift, ShiftAssignment
from .terminal import Terminal
from .admin import Admin, SystemConfig, AuditLog
from .camera import Camera
from .leave_request import LeaveRequest

__all__ = ['Employee', 'AttendanceRecord', 'Shift', 'ShiftAssignment', 'Terminal', 'Admin', 'SystemConfig', 'AuditLog', 'Camera', 'LeaveRequest']
