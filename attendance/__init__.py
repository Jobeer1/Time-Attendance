# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\__init__.py
"""
Time Attendance System - Main Module
"""

from flask import Blueprint
from .routes import terminal, api
from .routes import register_blueprints
from .services import database, shift_manager
from .services.face_recognition import face_service

def create_attendance_app(app):
    """Initialize attendance module with Flask app"""
    
    # Initialize services
    database.init_app(app)
    face_service.init_app(app)
    shift_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(terminal.bp, url_prefix='/terminal')
    app.register_blueprint(api.bp, url_prefix='/api')
    
    # Register all modular admin blueprints
    register_blueprints(app)
    
    return app
