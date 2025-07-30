# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\routes\__init__.py
"""
Route blueprints for Time Attendance System
"""

from . import terminal
from . import admin
from . import api
from .api_init import register_blueprints

__all__ = ['terminal', 'admin', 'api', 'register_blueprints']
