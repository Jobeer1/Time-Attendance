# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\models\admin.py
"""
Admin and system configuration models for Time Attendance System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import BaseModel

class Admin(BaseModel):
    """Admin user model"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
          # Basic information
        self.username = kwargs.get('username', '')
        self.password_hash = kwargs.get('password_hash', '')
        self.email = kwargs.get('email', '')
        self.full_name = kwargs.get('full_name', '')
          # Permissions and role
        self.is_super_admin = kwargs.get('is_super_admin', False)
        # Set role based on is_super_admin if role not explicitly provided
        if 'role' in kwargs:
            self.role = kwargs.get('role')
        else:
            self.role = 'super_admin' if self.is_super_admin else 'admin'
        
        # Update is_super_admin based on role if needed
        if self.role == 'super_admin' and not self.is_super_admin:
            self.is_super_admin = True
            
        self.permissions = kwargs.get('permissions', [])
        
        # Status
        self.is_active = kwargs.get('is_active', True)
        self.last_login = kwargs.get('last_login', '')
        self.login_attempts = kwargs.get('login_attempts', 0)
        self.locked_until = kwargs.get('locked_until', '')
        
        # Settings
        self.notification_preferences = kwargs.get('notification_preferences', {})
        self.dashboard_config = kwargs.get('dashboard_config', {})

        # Access restrictions: allowed terminals and IPs
        self.allowed_terminal_ids = kwargs.get('allowed_terminal_ids', [])
        self.allowed_ip_addresses = kwargs.get('allowed_ip_addresses', [])
    
    def validate(self) -> bool:
        """Validate admin data"""
        return bool(self.username and self.password_hash)
    
    def set_password(self, password: str) -> None:
        """Set password with hash"""
        import hashlib
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches stored hash"""
        import hashlib
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def is_locked(self) -> bool:
        """Check if admin account is locked"""
        if not self.locked_until:
            return False
        try:
            from datetime import datetime
            lock_time = datetime.fromisoformat(self.locked_until)
            return datetime.now() < lock_time
        except:
            return False


class SystemConfig(BaseModel):
    """System configuration model"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # General settings
        self.system_name = kwargs.get('system_name', 'Time Attendance System')
        self.company_name = kwargs.get('company_name', '')
        self.company_logo = kwargs.get('company_logo', '')
        self.timezone = kwargs.get('timezone', 'UTC')
        
        # Authentication settings
        self.require_face_recognition = kwargs.get('require_face_recognition', True)
        self.allow_pin_auth = kwargs.get('allow_pin_auth', True)
        self.allow_password_auth = kwargs.get('allow_password_auth', False)
        self.dual_auth_required = kwargs.get('dual_auth_required', False)
        
        # Face recognition settings
        self.face_confidence_threshold = kwargs.get('face_confidence_threshold', 0.6)
        self.max_face_encodings_per_user = kwargs.get('max_face_encodings_per_user', 5)
        self.face_recognition_timeout = kwargs.get('face_recognition_timeout', 30)
        
        # Time settings
        self.default_shift_hours = kwargs.get('default_shift_hours', 8.0)
        self.overtime_threshold = kwargs.get('overtime_threshold', 8.0)
        self.overtime_rate = kwargs.get('overtime_rate', 1.5)
        self.break_duration = kwargs.get('break_duration', 60)  # minutes
        
        # Grace periods
        self.late_grace_period = kwargs.get('late_grace_period', 15)  # minutes
        self.early_departure_grace = kwargs.get('early_departure_grace', 15)
        
        # Security settings
        self.max_login_attempts = kwargs.get('max_login_attempts', 5)
        self.lockout_duration = kwargs.get('lockout_duration', 300)  # seconds
        self.session_timeout = kwargs.get('session_timeout', 3600)
        
        # Data retention
        self.attendance_retention_days = kwargs.get('attendance_retention_days', 365)
        self.backup_frequency_hours = kwargs.get('backup_frequency_hours', 24)
        self.max_backups_to_keep = kwargs.get('max_backups_to_keep', 30)
        
        # Notifications
        self.email_notifications_enabled = kwargs.get('email_notifications_enabled', False)
        self.smtp_server = kwargs.get('smtp_server', '')
        self.smtp_port = kwargs.get('smtp_port', 587)
        self.smtp_username = kwargs.get('smtp_username', '')
        self.smtp_password = kwargs.get('smtp_password', '')
        
        # RIS Integration
        self.ris_integration_enabled = kwargs.get('ris_integration_enabled', False)
        self.ris_url = kwargs.get('ris_url', '')
        self.ris_api_key = kwargs.get('ris_api_key', '')
        
        # Terminal settings
        self.max_terminals = kwargs.get('max_terminals', 10)
        self.terminal_heartbeat_interval = kwargs.get('terminal_heartbeat_interval', 60)
        self.offline_terminal_timeout = kwargs.get('offline_terminal_timeout', 300)
    
    def validate(self) -> bool:
        """Validate system configuration"""
        return True  # Basic validation


class AuditLog(BaseModel):
    """Audit log model for tracking system activities"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Event information
        self.event_type = kwargs.get('event_type', '')  # login, logout, admin_action, etc.
        self.event_description = kwargs.get('event_description', '')
        self.event_category = kwargs.get('event_category', 'general')  # security, attendance, admin
        
        # User information
        self.user_id = kwargs.get('user_id', '')
        self.user_name = kwargs.get('user_name', '')
        self.user_type = kwargs.get('user_type', 'employee')  # employee, admin
        
        # Context information
        self.terminal_id = kwargs.get('terminal_id', '')
        self.ip_address = kwargs.get('ip_address', '')
        self.user_agent = kwargs.get('user_agent', '')
        
        # Event details
        self.event_data = kwargs.get('event_data', {})
        self.severity = kwargs.get('severity', 'info')  # info, warning, error, critical
        self.success = kwargs.get('success', True)
        
        # Timestamp
        self.timestamp = kwargs.get('timestamp', datetime.now().isoformat())
    
    def validate(self) -> bool:
        """Validate audit log entry"""
        return bool(self.event_type and self.timestamp)
