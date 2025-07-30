# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\models\base.py
"""
Base model class with JSON serialization and validation
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class BaseModel:
    """Base model class for JSON storage"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now().isoformat())
        
        # Set attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary"""
        return cls(**data)
    
    def update(self, **kwargs):
        """Update model attributes"""
        self.updated_at = datetime.now().isoformat()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def validate(self) -> bool:
        """Validate model data - override in subclasses"""
        return True
    
    @classmethod
    def get_collection_name(cls) -> str:
        """Get collection name for this model"""
        return cls.__name__.lower() + 's'
