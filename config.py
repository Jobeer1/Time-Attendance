"""
Configuration management for Time Attendance System
"""

import os
from pathlib import Path

class Config:
    """Base configuration class"""
    
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'attendance-secret-key-2024'
    DEBUG = False  # Add explicit DEBUG setting
    
    # Attendance system settings
    ATTENDANCE_MODE = os.environ.get('ATTENDANCE_MODE', 'standalone')  # standalone, integrated, hybrid
    ATTENDANCE_PORT = int(os.environ.get('ATTENDANCE_PORT', 5002))
    
    # RIS integration settings
    RIS_INTEGRATION_ENABLED = os.environ.get('RIS_INTEGRATION', 'false').lower() == 'true'
    RIS_URL = os.environ.get('RIS_URL', 'http://localhost:5000')
    RIS_API_KEY = os.environ.get('RIS_API_KEY', 'attendance_integration_2024')
    
    # Face recognition settings
    FACE_RECOGNITION_ENABLED = True
    FACE_CONFIDENCE_THRESHOLD = float(os.environ.get('FACE_THRESHOLD', 0.6))
    CAMERA_TIMEOUT = int(os.environ.get('CAMERA_TIMEOUT', 30))    # Data storage
    DATA_DIR = Path(os.environ.get('ATTENDANCE_DATA_DIR', 'data'))
    DATABASE_URI = str(DATA_DIR)  # For compatibility with tests
    BACKUP_ENABLED = True
    BACKUP_INTERVAL = 24 * 3600  # 24 hours
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATA_DIR}/attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Network settings
    ALLOWED_TERMINALS = [ip.strip() for ip in os.environ.get('ALLOWED_TERMINALS', '').split(',') if ip.strip()]
    MAX_TERMINALS = int(os.environ.get('MAX_TERMINALS', 10))
    
    # Security settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    
    # Performance settings
    RECOGNITION_TIMEOUT = int(os.environ.get('RECOGNITION_TIMEOUT', 5))  # seconds
    CACHE_DURATION = int(os.environ.get('CACHE_DURATION', 300))  # 5 minutes

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FACE_RECOGNITION_ENABLED = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{Config.DATA_DIR}/attendance.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FACE_RECOGNITION_ENABLED = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{Config.DATA_DIR}/attendance.db'
    DEBUG = False
    FACE_RECOGNITION_ENABLED = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    FACE_RECOGNITION_ENABLED = False  # Disable face recognition for testing

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
