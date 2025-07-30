# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\models\terminal.py
"""
Terminal model for Time Attendance System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import BaseModel

class Terminal(BaseModel):
    """Terminal model for attendance devices"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Terminal identification
        self.terminal_id = kwargs.get('terminal_id', '')
        self.name = kwargs.get('name', '')
        self.description = kwargs.get('description', '')
        self.location = kwargs.get('location', '')
        
        # Network settings
        self.ip_address = kwargs.get('ip_address', '')
        self.mac_address = kwargs.get('mac_address', '')
        self.port = kwargs.get('port', 5001)
        
        # Capabilities
        self.supports_face_recognition = kwargs.get('supports_face_recognition', True)
        self.supports_pin = kwargs.get('supports_pin', True)
        self.supports_password = kwargs.get('supports_password', False)
        self.has_camera = kwargs.get('has_camera', True)
        self.camera_type = kwargs.get('camera_type', 'webcam')  # webcam, smartphone, ip_camera
        
        # Status
        self.is_active = kwargs.get('is_active', True)
        self.is_online = kwargs.get('is_online', False)
        self.last_heartbeat = kwargs.get('last_heartbeat', '')
        self.last_activity = kwargs.get('last_activity', '')
        
        # Configuration
        self.max_concurrent_users = kwargs.get('max_concurrent_users', 1)
        self.session_timeout = kwargs.get('session_timeout', 300)  # seconds
        self.recognition_timeout = kwargs.get('recognition_timeout', 30)
        
        # Security
        self.allowed_methods = kwargs.get('allowed_methods', ['face_recognition', 'pin'])
        self.require_dual_auth = kwargs.get('require_dual_auth', False)
        self.lockout_threshold = kwargs.get('lockout_threshold', 5)
        self.lockout_duration = kwargs.get('lockout_duration', 300)  # seconds
        
        # Statistics
        self.total_logins = kwargs.get('total_logins', 0)
        self.successful_logins = kwargs.get('successful_logins', 0)
        self.failed_attempts = kwargs.get('failed_attempts', 0)
        self.uptime_minutes = kwargs.get('uptime_minutes', 0)
        
        # Current state
        self.current_users = kwargs.get('current_users', [])
        self.is_locked = kwargs.get('is_locked', False)
        self.lock_reason = kwargs.get('lock_reason', '')
        self.locked_until = kwargs.get('locked_until', '')
    
    @property
    def success_rate(self) -> float:
        """Calculate login success rate"""
        if self.total_logins == 0:
            return 0.0
        return round((self.successful_logins / self.total_logins) * 100, 2)
    
    @property
    def is_available(self) -> bool:
        """Check if terminal is available for use"""
        return (self.is_active and 
                self.is_online and 
                not self.is_locked and 
                len(self.current_users) < self.max_concurrent_users)
    
    def heartbeat(self):
        """Update terminal heartbeat"""
        self.last_heartbeat = datetime.now().isoformat()
        self.is_online = True
        self.updated_at = datetime.now().isoformat()
    
    def record_activity(self, activity_type: str = 'login'):
        """Record terminal activity"""
        self.last_activity = datetime.now().isoformat()
        if activity_type == 'login':
            self.total_logins += 1
        self.updated_at = datetime.now().isoformat()
    
    def record_successful_login(self, employee_id: str):
        """Record successful login"""
        self.successful_logins += 1
        self.record_activity('login')
        if employee_id not in self.current_users:
            self.current_users.append(employee_id)
    
    def record_failed_attempt(self):
        """Record failed login attempt"""
        self.failed_attempts += 1
        self.record_activity('failed_login')
        
        # Check if should be locked
        if self.failed_attempts >= self.lockout_threshold:
            self.lock_terminal('Too many failed attempts')
    
    def lock_terminal(self, reason: str = '', duration_seconds: int = None):
        """Lock terminal for security"""
        self.is_locked = True
        self.lock_reason = reason
        duration = duration_seconds or self.lockout_duration
        lock_until = datetime.now().timestamp() + duration
        self.locked_until = datetime.fromtimestamp(lock_until).isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def unlock_terminal(self):
        """Unlock terminal"""
        self.is_locked = False
        self.lock_reason = ''
        self.locked_until = ''
        self.failed_attempts = 0
        self.updated_at = datetime.now().isoformat()
    
    def check_lock_expiry(self):
        """Check if lock has expired"""
        if self.is_locked and self.locked_until:
            try:
                lock_time = datetime.fromisoformat(self.locked_until)
                if datetime.now() >= lock_time:
                    self.unlock_terminal()
            except ValueError:
                pass
    
    def remove_user(self, employee_id: str):
        """Remove user from current users list"""
        if employee_id in self.current_users:
            self.current_users.remove(employee_id)
            self.updated_at = datetime.now().isoformat()
    
    def validate(self) -> bool:
        """Validate terminal data"""
        if not self.terminal_id or not self.name:
            return False
        
        if self.ip_address and not self._is_valid_ip(self.ip_address):
            return False
        
        return True
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False
