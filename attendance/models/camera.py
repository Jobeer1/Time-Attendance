"""
Camera model for Time Attendance System
"""

from typing import Dict, Any
from datetime import datetime
from .base import BaseModel

class Camera(BaseModel):
    """Camera model for managing configured cameras"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Basic information
        self.name = kwargs.get('name', '')
        self.location = kwargs.get('location', '')
        self.description = kwargs.get('description', '')
        
        # Technical details
        self.url = kwargs.get('url', '')
        self.camera_type = kwargs.get('camera_type', 'ip_camera')  # ip_camera, rtsp, http, webrtc
        self.resolution = kwargs.get('resolution', '640x480')
        self.fps = kwargs.get('fps', 30)
        
        # Network settings
        self.ip_address = kwargs.get('ip_address', '')
        self.port = kwargs.get('port', 80)
        self.username = kwargs.get('username', '')
        self.password = kwargs.get('password', '')
        
        # Status and configuration
        self.is_active = kwargs.get('is_active', True)
        self.enabled = kwargs.get('enabled', True)  # Add enabled attribute
        self.is_online = kwargs.get('is_online', False)
        self.last_tested = kwargs.get('last_tested', '')
        self.test_status = kwargs.get('test_status', 'untested')  # untested, success, failed
        
        # Access control
        self.allowed_terminals = kwargs.get('allowed_terminals', [])  # List of terminal IDs that can use this camera
        self.requires_authentication = kwargs.get('requires_authentication', False)
        
        # Stream settings
        self.stream_quality = kwargs.get('stream_quality', 'medium')  # low, medium, high
        self.enable_recording = kwargs.get('enable_recording', False)
        self.recording_path = kwargs.get('recording_path', '')
        
        # Maintenance
        self.maintenance_schedule = kwargs.get('maintenance_schedule', [])
        self.notes = kwargs.get('notes', '')
    
    def validate(self) -> bool:
        """Validate camera data"""
        if not self.name or not self.url or not self.location:
            return False
        
        # Basic URL validation
        if not (self.url.startswith('http://') or 
                self.url.startswith('https://') or 
                self.url.startswith('rtsp://') or
                self.url.startswith('webrtc://')):
            return False
        
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """Test camera connection (placeholder for actual implementation)"""
        # This would be implemented with actual camera testing logic
        import time
        
        try:
            # Simulate testing delay
            time.sleep(0.5)
            
            # Update status
            self.last_tested = datetime.now().isoformat()
            self.test_status = 'success'
            self.is_online = True
            
            return {
                'success': True,
                'message': 'Camera connection successful',
                'response_time': 0.5,
                'resolution_detected': self.resolution
            }
        except Exception as e:
            self.test_status = 'failed'
            self.is_online = False
            return {
                'success': False,
                'message': f'Camera connection failed: {str(e)}',
                'error': str(e)
            }
    
    def get_stream_url(self) -> str:
        """Get the stream URL for this camera"""
        return self.url
    
    def is_accessible_by_terminal(self, terminal_id: str) -> bool:
        """Check if this camera can be accessed by a specific terminal"""
        if not self.allowed_terminals:
            return True  # If no restrictions, allow all terminals
        return terminal_id in self.allowed_terminals
