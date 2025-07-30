# filepath: c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\attendance\services\database.py
"""
JSON-based database service for Time Attendance System
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from threading import Lock
import uuid

from ..models.base import BaseModel
from ..models import (
    Employee, AttendanceRecord, Shift, ShiftAssignment, 
    Terminal, Admin, SystemConfig, AuditLog, Camera
)

class DatabaseService:
    """JSON-based database service with backup support"""
    
    def __init__(self, data_dir: str = 'attendance_data'):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / 'backups'
        self.daily_backup_dir = self.backup_dir / 'daily'
        self.weekly_backup_dir = self.backup_dir / 'weekly'
        
        # Thread safety
        self._lock = Lock()
          # Model mapping
        self.models = {
            'employees': Employee,
            'attendance_records': AttendanceRecord,
            'shifts': Shift,
            'shift_assignments': ShiftAssignment,
            'terminals': Terminal,
            'admins': Admin,
            'system_config': SystemConfig,
            'audit_logs': AuditLog,
            'cameras': Camera
        }
        
        self._init_directories()
        self._init_default_data()
    
    def _init_directories(self):
        """Initialize data directories"""
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.daily_backup_dir.mkdir(exist_ok=True)
        self.weekly_backup_dir.mkdir(exist_ok=True)
    
    def _init_default_data(self):
        """Initialize default data files"""
        for collection_name in self.models.keys():
            file_path = self.data_dir / f"{collection_name}.json"
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f, indent=2)
    
    def _get_file_path(self, collection: str) -> Path:
        """Get file path for collection"""
        return self.data_dir / f"{collection}.json"
    
    def _load_collection(self, collection: str) -> List[Dict]:
        """Load collection from JSON file"""
        file_path = self._get_file_path(collection)
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_collection(self, collection: str, data: List[Dict]):
        """Save collection to JSON file"""
        file_path = self._get_file_path(collection)
        with self._lock:
            # Create backup before saving
            if file_path.exists():
                backup_path = file_path.with_suffix('.json.backup')
                shutil.copy2(file_path, backup_path)
            
            # Save new data
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
    
    # CRUD Operations
    def create(self, collection: str, model: BaseModel) -> BaseModel:
        """Create a new record"""
        if not model.validate():
            raise ValueError("Model validation failed")
        
        data = self._load_collection(collection)
        
        # Ensure unique ID
        if not model.id:
            model.id = str(uuid.uuid4())
        
        # Check for duplicate ID
        if any(record.get('id') == model.id for record in data):
            model.id = str(uuid.uuid4())
        
        data.append(model.to_dict())
        self._save_collection(collection, data)
        
        return model
    
    def get_by_id(self, collection: str, record_id: str) -> Optional[BaseModel]:
        """Get record by ID"""
        data = self._load_collection(collection)
        model_class = self.models.get(collection)
        
        if not model_class:
            return None
        
        for record in data:
            if record.get('id') == record_id:
                return model_class.from_dict(record)
        
        return None
    
    def get_all(self, collection: str) -> List[BaseModel]:
        """Get all records from collection"""
        data = self._load_collection(collection)
        model_class = self.models.get(collection)
        
        if not model_class:
            return []
        
        return [model_class.from_dict(record) for record in data]
    
    def find(self, collection: str, filters: Dict[str, Any] = None, 
             limit: int = None, skip: int = 0) -> List[BaseModel]:
        """Find records with filters"""
        data = self._load_collection(collection)
        model_class = self.models.get(collection)
        
        if not model_class:
            return []
        
        # Apply filters
        if filters:
            filtered_data = []
            for record in data:
                match = True
                for key, value in filters.items():
                    if key not in record or record[key] != value:
                        match = False
                        break
                if match:
                    filtered_data.append(record)
            data = filtered_data
        
        # Apply skip and limit
        if skip > 0:
            data = data[skip:]
        if limit:
            data = data[:limit]
        
        return [model_class.from_dict(record) for record in data]
    
    def update(self, collection: str, record_id: str, updates: Dict[str, Any]) -> Optional[BaseModel]:
        """Update record by ID"""
        data = self._load_collection(collection)
        model_class = self.models.get(collection)
        
        if not model_class:
            return None
        for i, record in enumerate(data):
            if record.get('id') == record_id:
                # Update record
                record.update(updates)
                record['updated_at'] = datetime.now().isoformat()

                # Validate updated record
                model = model_class.from_dict(record)
                if not model.validate():
                    raise ValueError("Updated model validation failed")
                data[i] = model.to_dict()
                self._save_collection(collection, data)                return model
        
        return None

    def delete(self, collection: str, record_id: str) -> bool:
        """Delete record by ID"""
        data = self._load_collection(collection)
        
        for i, record in enumerate(data):
            if record.get('id') == record_id:
                del data[i]
                self._save_collection(collection, data)
                return True
        
        return False

    def count(self, collection: str, filters: Dict[str, Any] = None) -> int:
        """Count records in collection"""
        data = self._load_collection(collection)
        
        if not filters:
            return len(data)
        
        count = 0
        for record in data:
            match = True
            for key, value in filters.items():
                if key not in record or record[key] != value:
                    match = False
                    break
            if match:
                count += 1
        
        return count
    
    def save(self, model_or_collection, model=None) -> BaseModel:
        """Save a model (create or update based on ID existence)
        Can be called as:
        - save(model) - Auto-detects collection from model type
        - save(collection, model) - Explicit collection name
        """
        if model is None:
            # Called as save(model)
            model = model_or_collection
            collection = self._get_collection_name_from_model(model)
        else:
            # Called as save(collection, model)
            collection = model_or_collection
        
        if hasattr(model, 'id') and model.id:
            # Check if record exists
            existing = self.get_by_id(collection, model.id)
            if existing:
                # Update existing record
                updates = model.to_dict()
                return self.update(collection, model.id, updates)
        
        # Create new record
        return self.create(collection, model)
    
    def find_all(self, model_class_or_collection, filters: Dict[str, Any] = None) -> List[BaseModel]:
        """Find all records matching filters
        Can be called as:
        - find_all(ModelClass) - Auto-detects collection from model class
        - find_all(collection, filters) - Explicit collection name
        """
        if isinstance(model_class_or_collection, str):
            # Called as find_all(collection, filters)
            collection = model_class_or_collection
        else:
            # Called as find_all(ModelClass) - treat filters as first arg if passed
            model_class = model_class_or_collection
            collection = self._get_collection_name_from_model_class(model_class)
            # If filters was passed as second argument, use it
            if filters is None and hasattr(self, '_find_all_filters'):
                filters = self._find_all_filters
                delattr(self, '_find_all_filters')
        
        return self.find(collection, filters)
    
    def _get_collection_name_from_model(self, model) -> str:
        """Get collection name from model instance"""
        model_class = type(model)
        return self._get_collection_name_from_model_class(model_class)
    
    def _get_collection_name_from_model_class(self, model_class) -> str:
        """Get collection name from model class"""
        # Map model classes to collection names
        class_to_collection = {
            Employee: 'employees',
            AttendanceRecord: 'attendance_records',
            Shift: 'shifts',
            ShiftAssignment: 'shift_assignments',
            Terminal: 'terminals',
            Admin: 'admins',
            SystemConfig: 'system_config',
            AuditLog: 'audit_logs',
            Camera: 'cameras'
        }
        
        collection = class_to_collection.get(model_class)
        if not collection:
            # Fallback: use class name in lowercase with 's' suffix
            collection = model_class.__name__.lower() + 's'
        
        return collection

    # Specialized methods
    def get_employee_by_employee_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by employee ID"""
        employees = self.find('employees', {'employee_id': employee_id})
        return employees[0] if employees else None
    
    def get_active_attendance_record(self, employee_id: str) -> Optional[AttendanceRecord]:
        """Get active attendance record for employee"""
        # Look for any active attendance record for this employee, regardless of date
        # This handles cases where employees forgot to clock out on previous days
        records = self.find('attendance_records', {
            'employee_id': employee_id,
            'status': 'active'
        })
        
        if records:
            # Sort by date descending to get the most recent active record
            records.sort(key=lambda x: x.date, reverse=True)
            return records[0]
        
        return None
    
    def get_attendance_records_by_date_range(self, start_date: str, end_date: str) -> List[AttendanceRecord]:
        """Get attendance records within date range"""
        all_records = self.get_all('attendance_records')
        filtered_records = []
        
        for record in all_records:
            if start_date <= record.date <= end_date:
                filtered_records.append(record)
        
        return filtered_records
    
    def backup_database(self, backup_type: str = 'daily'):
        """Create database backup"""
        backup_dir = self.daily_backup_dir if backup_type == 'daily' else self.weekly_backup_dir
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_subdir = backup_dir / f"backup_{timestamp}"
        backup_subdir.mkdir(exist_ok=True)
        
        # Copy all data files
        for collection in self.models.keys():
            source_file = self._get_file_path(collection)
            if source_file.exists():
                target_file = backup_subdir / source_file.name
                shutil.copy2(source_file, target_file)
        
        print(f"Database backup created: {backup_subdir}")
        
        # Clean old backups
        self._clean_old_backups(backup_dir, max_backups=30 if backup_type == 'daily' else 12)
    
    def _clean_old_backups(self, backup_dir: Path, max_backups: int):
        """Clean old backup directories"""
        backup_dirs = [d for d in backup_dir.iterdir() if d.is_dir()]
        backup_dirs.sort(key=lambda x: x.name)
        
        while len(backup_dirs) > max_backups:
            oldest_backup = backup_dirs.pop(0)
            shutil.rmtree(oldest_backup)
            print(f"Removed old backup: {oldest_backup}")
    
    def restore_from_backup(self, backup_path: str):
        """Restore database from backup"""
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            raise FileNotFoundError(f"Backup directory not found: {backup_path}")
        
        with self._lock:
            # Create current backup before restore
            self.backup_database('restore_backup')
            
            # Restore files
            for backup_file in backup_dir.glob('*.json'):
                target_file = self.data_dir / backup_file.name
                shutil.copy2(backup_file, target_file)
            
            print(f"Database restored from backup: {backup_path}")

# Global database instance
db = DatabaseService()

def init_app(app):
    """Initialize database service with Flask app"""
    global db
    data_dir = app.config.get('DATA_DIR', 'attendance_data')
    db = DatabaseService(data_dir)
    
    # Schedule daily backups
    if app.config.get('BACKUP_ENABLED', True):
        import threading
        import time
        
        def backup_scheduler():
            while True:
                time.sleep(app.config.get('BACKUP_INTERVAL', 24 * 3600))  # 24 hours
                try:
                    db.backup_database('daily')
                except Exception as e:
                    print(f"Backup failed: {e}")
        
        backup_thread = threading.Thread(target=backup_scheduler, daemon=True)
        backup_thread.start()
