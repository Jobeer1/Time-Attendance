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
import logging

from ..models.base import BaseModel
from ..models import (
    Employee, AttendanceRecord, Shift, ShiftAssignment, 
    Terminal, Admin, SystemConfig, AuditLog, Camera, LeaveRequest
)
from ..models.employee_terminal_assignment import EmployeeTerminalAssignment

class DatabaseService:
    """JSON-based database service with backup support"""
    
    def __init__(self, data_dir: str = 'attendance_data'):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / 'backups'
        self.daily_backup_dir = self.backup_dir / 'daily'
        self.weekly_backup_dir = self.backup_dir / 'weekly'
        
        # Thread safety
        self._lock = Lock()
        
        # Logger setup
        self.logger = logging.getLogger(__name__)
        
        # Ensure directories exist with proper permissions
        self._ensure_directories()
        
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
            'cameras': Camera,
            'employee_terminal_assignments': EmployeeTerminalAssignment,
            'leave_requests': LeaveRequest  # Add leave requests model
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
                self._save_collection(collection, data)
                return model
        
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

    # Terminal management methods
    def get_all_terminals(self) -> List[Terminal]:
        """Get all terminals"""
        return self.get_all('terminals')
    
    def get_terminal(self, terminal_id: str) -> Optional[Terminal]:
        """Get terminal by ID"""
        return self.get_by_id('terminals', terminal_id)
    
    # Employee management methods
    def get_all_employees(self) -> List[Employee]:
        """Get all employees"""
        return self.get_all('employees')
    
    def get_employee(self, employee_id: str) -> Optional[Employee]:
        """Get employee by employee_id"""
        employees = self.find('employees', {'employee_id': employee_id})
        return employees[0] if employees else None
    
    def save_terminal(self, terminal: Terminal) -> bool:
        """Save terminal"""
        return self.save('terminals', terminal)
    
    def delete_terminal(self, terminal_id: str) -> bool:
        """Delete terminal"""
        return self.delete('terminals', terminal_id)
    
    def get_terminal_by_ip(self, ip_address: str) -> Optional[Terminal]:
        """Get terminal by IP address"""
        terminals = self.get_all_terminals()
        for terminal in terminals:
            if terminal.ip_address == ip_address:
                return terminal
        return None
    
    def get_terminal_logs(self, terminal_id: str, level: str = '', 
                         date_filter: str = '', limit: int = 100) -> List[Dict[str, Any]]:
        """Get terminal logs with filtering"""
        try:
            # For now, return mock logs. In a real implementation, 
            # you would have a separate logs collection
            mock_logs = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'event': 'Terminal started',
                    'details': 'System initialization completed'
                },
                {
                    'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                    'level': 'info',
                    'event': 'Face recognition activated',
                    'details': 'Camera connected successfully'
                },
                {
                    'timestamp': (datetime.now() - timedelta(minutes=10)).isoformat(),
                    'level': 'warning',
                    'event': 'Authentication attempt failed',
                    'details': 'Unknown face detected'
                }
            ]
            
            # Apply filters
            filtered_logs = mock_logs
            if level:
                filtered_logs = [log for log in filtered_logs if log['level'] == level]
            
            if date_filter:
                filter_date = datetime.fromisoformat(date_filter).date()
                filtered_logs = [
                    log for log in filtered_logs 
                    if datetime.fromisoformat(log['timestamp']).date() == filter_date
                ]
            
            return filtered_logs[:limit]
        except Exception as e:
            print(f"Error getting terminal logs: {e}")
            return []
    
    def save_terminal_log(self, log_entry: Dict[str, Any]) -> bool:
        """Save terminal log entry"""
        try:
            # In a real implementation, you would save to a logs collection
            # For now, just print the log
            print(f"Terminal Log: {log_entry}")
            return True
        except Exception as e:
            print(f"Error saving terminal log: {e}")
            return False

    # Employee Terminal Assignment Management
    def get_all_employee_terminal_assignments(self) -> List[EmployeeTerminalAssignment]:
        """Get all employee-terminal assignments"""
        return self.get_all('employee_terminal_assignments')
    
    def get_employee_terminal_assignment(self, assignment_id: str) -> Optional[EmployeeTerminalAssignment]:
        """Get specific assignment by ID"""
        return self.get_by_id('employee_terminal_assignments', assignment_id)
    
    def get_assignments_for_employee(self, employee_id: str) -> List[EmployeeTerminalAssignment]:
        """Get all terminal assignments for a specific employee"""
        assignments = self.get_all('employee_terminal_assignments')
        return [a for a in assignments if a.employee_id == employee_id and a.is_active]
    
    def get_assignments_for_terminal(self, terminal_id: str) -> List[EmployeeTerminalAssignment]:
        """Get all employee assignments for a specific terminal"""
        assignments = self.get_all('employee_terminal_assignments')
        return [a for a in assignments if a.terminal_id == terminal_id and a.is_active]
    
    def save_employee_terminal_assignment(self, assignment: EmployeeTerminalAssignment) -> bool:
        """Save an employee-terminal assignment"""
        try:
            if not assignment.assignment_id:
                assignment.assignment_id = str(uuid.uuid4())
            
            assignment.updated_at = datetime.now().isoformat()
            return self.save('employee_terminal_assignments', assignment)
        except Exception as e:
            print(f"Error saving assignment: {e}")
            return False
    
    def delete_employee_terminal_assignment(self, assignment_id: str) -> bool:
        """Delete an employee-terminal assignment"""
        return self.delete('employee_terminal_assignments', assignment_id)
    
    def is_employee_allowed_terminal(self, employee_id: str, terminal_id: str, 
                                   check_time: datetime = None) -> bool:
        """Check if an employee is allowed to use a specific terminal"""
        if check_time is None:
            check_time = datetime.now()
        
        # Get all assignments for this employee
        assignments = self.get_assignments_for_employee(employee_id)
        
        # If no assignments exist, follow system default policy
        if not assignments:
            # Check system config for default behavior
            config = self.get_system_config()
            if config and hasattr(config, 'terminals_open_by_default'):
                return config.terminals_open_by_default
            else:
                # Default: terminals are open (allow access)
                return True
        
        # Check if employee has assignment for this terminal
        for assignment in assignments:
            if assignment.terminal_id == terminal_id:
                return assignment.is_valid_for_time(check_time)
        
        # Employee has assignments but not for this terminal - deny access
        return False
    
    def get_allowed_terminals_for_employee(self, employee_id: str, 
                                         check_time: datetime = None) -> List[str]:
        """Get list of terminal IDs that an employee is allowed to use"""
        if check_time is None:
            check_time = datetime.now()
        
        assignments = self.get_assignments_for_employee(employee_id)
        
        # If no assignments, check system default policy
        if not assignments:
            config = self.get_system_config()
            if config and hasattr(config, 'terminals_open_by_default') and config.terminals_open_by_default:
                # Return all active terminals
                terminals = self.get_all_terminals()
                return [t.terminal_id for t in terminals if t.is_active]
            else:
                return []
        
        # Return terminals from valid assignments
        allowed_terminals = []
        for assignment in assignments:
            if assignment.is_valid_for_time(check_time):
                allowed_terminals.append(assignment.terminal_id)
        
        return allowed_terminals
    
    def assign_employee_to_terminal(self, employee_id: str, terminal_id: str, 
                                  assigned_by: str, reason: str = '', 
                                  assignment_type: str = 'exclusive',
                                  **kwargs) -> Optional[EmployeeTerminalAssignment]:
        """Create a new employee-terminal assignment"""
        try:
            # Check if assignment already exists
            existing_assignments = self.get_assignments_for_employee(employee_id)
            for assignment in existing_assignments:
                if assignment.terminal_id == terminal_id and assignment.is_active:
                    # Assignment already exists
                    return assignment
            
            # Create new assignment
            assignment = EmployeeTerminalAssignment(
                employee_id=employee_id,
                terminal_id=terminal_id,
                assigned_by=assigned_by,
                reason=reason,
                assignment_type=assignment_type,
                **kwargs
            )
            
            if assignment.validate() and self.save_employee_terminal_assignment(assignment):
                return assignment
            else:
                return None
        except Exception as e:
            print(f"Error creating assignment: {e}")
            return None
    
    def remove_employee_from_terminal(self, employee_id: str, terminal_id: str) -> bool:
        """Remove employee's assignment to a specific terminal"""
        try:
            assignments = self.get_assignments_for_employee(employee_id)
            for assignment in assignments:
                if assignment.terminal_id == terminal_id and assignment.is_active:
                    assignment.is_active = False
                    assignment.updated_at = datetime.now().isoformat()
                    return self.save_employee_terminal_assignment(assignment)
            return True  # No assignment found to remove
        except Exception as e:
            print(f"Error removing assignment: {e}")
            return False
    
    def remove_all_employee_assignments(self, employee_id: str) -> bool:
        """Remove all terminal assignments for an employee"""
        try:
            assignments = self.get_assignments_for_employee(employee_id)
            for assignment in assignments:
                assignment.is_active = False
                assignment.updated_at = datetime.now().isoformat()
                self.save_employee_terminal_assignment(assignment)
            return True
        except Exception as e:
            print(f"Error removing all assignments: {e}")
            return False

    # System Configuration Management
    def get_system_config(self) -> Optional[SystemConfig]:
        """Get system configuration"""
        configs = self.get_all('system_config')
        return configs[0] if configs else None
    
    def save_system_config(self, config: SystemConfig) -> bool:
        """Save system configuration"""
        try:
            if not config.id:
                config.id = 'system_config'
            config.updated_at = datetime.now().isoformat()
            return self.save('system_config', config)
        except Exception as e:
            print(f"Error saving system config: {e}")
            return False
    
    def update_system_config(self, **kwargs) -> bool:
        """Update system configuration with new values"""
        try:
            config = self.get_system_config()
            if not config:
                config = SystemConfig(**kwargs)
            else:
                for key, value in kwargs.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            
            return self.save_system_config(config)
        except Exception as e:
            print(f"Error updating system config: {e}")
            return False

    # Live Camera helper methods
    def _load_data(self, collection: str, default_value: Any = None) -> Any:
        """Load data from a collection file"""
        try:
            file_path = self._get_file_path(collection)
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default_value if default_value is not None else []
    
    def _save_data(self, collection: str, data: Any):
        """Save data to a collection file"""
        file_path = self._get_file_path(collection)
        try:
            with self._lock:
                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Create backup before saving
                if file_path.exists():
                    backup_path = file_path.with_suffix('.json.backup')
                    shutil.copy2(file_path, backup_path)
                    self.logger.info(f'Backup created at {backup_path}')

                # Save new data
                self.logger.debug(f'Attempting to save data to {file_path}: {data}')
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                    self.logger.info(f'Data successfully saved to {file_path}')

                # Verify the file content
                with open(file_path, 'r') as f:
                    saved_data = json.load(f)
                    self.logger.debug(f'Verified saved data: {saved_data}')

                return True
        except Exception as e:
            self.logger.error(f'Error in _save_data for collection {collection}: {e}', exc_info=True)
            self.logger.error(f'Attempted to save to path: {file_path}')
            return False
    
    def _load_live_cameras_data(self) -> Dict[str, Any]:
        """Load live cameras data from file"""
        return self._load_data('live_cameras', {})
    
    def _save_live_cameras_data(self, cameras: Dict[str, Any]):
        """Save live cameras data to file"""
        self._save_data('live_cameras', cameras)

    # Live Camera Management
    def save_live_camera(self, camera_data: dict) -> bool:
        """Save a live camera configuration"""
        try:
            camera_id = camera_data.get('camera_id')
            if not camera_id:
                self.logger.error("Camera ID is required")
                return False
            
            # Add debug logging to track calls
            import traceback
            self.logger.info(f"save_live_camera called for {camera_id}")
            self.logger.debug(f"Call stack: {traceback.format_stack()}")
            
            with self._lock:
                # Load existing cameras
                cameras = self._load_data('live_cameras', {})
                
                # Add/update camera
                cameras[camera_id] = camera_data
                
                # Save back to file
                self._save_data('live_cameras', cameras)
                
                self.logger.info(f"Saved live camera: {camera_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving live camera: {e}")
            return False
    
    def get_live_cameras(self) -> List[dict]:
        """Get all live camera configurations"""
        try:
            with self._lock:
                cameras = self._load_data('live_cameras', {})
                return list(cameras.values())
                
        except Exception as e:
            self.logger.error(f"Error loading live cameras: {e}")
            return []
    
    def get_live_camera(self, camera_id: str) -> Optional[dict]:
        """Get a specific live camera configuration"""
        try:
            with self._lock:
                cameras = self._load_data('live_cameras', {})
                return cameras.get(camera_id)
                
        except Exception as e:
            self.logger.error(f"Error loading live camera {camera_id}: {e}")
            return None
    
    def delete_live_camera(self, camera_id: str) -> bool:
        """Delete a live camera configuration"""
        try:
            with self._lock:
                cameras = self._load_data('live_cameras', {})
                
                if camera_id in cameras:
                    del cameras[camera_id]
                    self._save_data('live_cameras', cameras)
                    self.logger.info(f"Deleted live camera: {camera_id}")
                    return True
                else:
                    self.logger.warning(f"Live camera {camera_id} not found")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error deleting live camera {camera_id}: {e}")
            return False

    # Device name management methods
    def save_device_name(self, device_data: Dict[str, Any]) -> bool:
        """Save custom device name"""
        try:
            with self._lock:
                # Load existing device names
                device_names = self._load_data('device_names', {})
                
                # Use IP address as key
                ip_address = device_data['ip_address']
                device_names[ip_address] = device_data
                
                # Save back to file
                return self._save_data('device_names', device_names)
                
        except Exception as e:
            self.logger.error(f"Error saving device name: {e}")
            return False
    
    def get_device_custom_name(self, ip_address: str) -> Optional[str]:
        """Get custom name for a device by IP address"""
        try:
            device_names = self._load_data('device_names', {})
            device_data = device_names.get(ip_address)
            
            if device_data:
                return device_data.get('device_name')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting device custom name: {e}")
            return None
    
    def get_all_device_names(self) -> Dict[str, Any]:
        """Get all saved device names"""
        try:
            return self._load_data('device_names', {})
        except Exception as e:
            self.logger.error(f"Error loading device names: {e}")
            return {}
    
    def delete_device_name(self, ip_address: str) -> bool:
        """Delete custom device name"""
        try:
            with self._lock:
                device_names = self._load_data('device_names', {})
                
                if ip_address in device_names:
                    del device_names[ip_address]
                    return self._save_data('device_names', device_names)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting device name: {e}")
            return False
    
    def save_device_name_by_mac(self, device_data: Dict[str, Any]) -> bool:
        """Save custom device name using MAC address as primary key"""
        try:
            with self._lock:
                # Load existing device names
                device_names = self._load_data('device_names_by_mac', {})
                
                # Use MAC address as key (normalized to uppercase)
                mac_address = device_data['mac_address'].upper()
                device_names[mac_address] = device_data
                
                # Save back to file
                return self._save_data('device_names_by_mac', device_names)
                
        except Exception as e:
            self.logger.error(f"Error saving device name by MAC: {e}")
            return False
    
    def get_device_name_by_mac(self, mac_address: str) -> Optional[Dict[str, Any]]:
        """Get device data by MAC address"""
        try:
            device_names = self._load_data('device_names_by_mac', {})
            mac_address = mac_address.upper()  # Normalize to uppercase
            return device_names.get(mac_address)
            
        except Exception as e:
            self.logger.error(f"Error getting device name by MAC: {e}")
            return None
    
    def get_all_device_names_by_mac(self) -> Dict[str, Any]:
        """Get all saved device names indexed by MAC address"""
        try:
            return self._load_data('device_names_by_mac', {})
        except Exception as e:
            self.logger.error(f"Error getting all device names by MAC: {e}")
            return {}
    
    def update_device_ip_by_mac(self, mac_address: str, new_ip: str) -> bool:
        """Update IP address for a device identified by MAC address"""
        try:
            with self._lock:
                device_names = self._load_data('device_names_by_mac', {})
                mac_address = mac_address.upper()
                
                if mac_address in device_names:
                    device_names[mac_address]['ip_address'] = new_ip
                    device_names[mac_address]['updated_at'] = datetime.now().isoformat()
                    return self._save_data('device_names_by_mac', device_names)
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating device IP by MAC: {e}")
            return False

    # Network settings management
    def save_network_settings(self, settings_data: Dict[str, Any]) -> bool:
        """Save network discovery settings"""
        try:
            self.logger.info(f"Attempting to save network settings: {settings_data}")
            # Overwrite the file with the new settings exactly as provided
            file_path = self._get_file_path('network_settings')
            with self._lock:
                with open(file_path, 'w') as f:
                    json.dump(settings_data, f, indent=2)
                self.logger.info(f"Network settings saved to {file_path}: {settings_data}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving network settings: {e}", exc_info=True)
            return False
    
    def get_network_settings(self) -> Dict[str, Any]:
        """Get network discovery settings"""
        try:
            default_settings = {
                'ip_range_start': '',
                'ip_range_end': '',
                'scan_timeout': 5,
                'concurrent_scans': 10,
                'updated_at': datetime.now().isoformat(),
                'message': 'Please adjust network settings in the admin interface.'
            }
            
            # First check if file exists
            file_path = self._get_file_path('network_settings')
            self.logger.info(f"Looking for network settings at: {file_path}")
            
            if file_path.exists():
                self.logger.info(f"Network settings file found, loading data")
                try:
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        if not content:
                            self.logger.warning("Network settings file is empty. Using defaults.")
                            self._save_data('network_settings', default_settings)
                            return default_settings
                        settings = json.loads(content)
                    self.logger.info(f"Loaded network settings: {settings}")
                    return settings
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.error(f"Error reading network settings file: {e}")
                    # Overwrite with defaults if corrupted
                    self._save_data('network_settings', default_settings)
                    return default_settings
            else:
                self.logger.info(f"Network settings file does not exist, using defaults")
                # Create the default file
                try:
                    with self._lock:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, 'w') as f:
                            json.dump(default_settings, f, indent=2)
                        self.logger.info(f"Created default network settings file")
                except Exception as e:
                    self.logger.error(f"Failed to create default network settings file: {e}")
                
                return default_settings
                
        except Exception as e:
            import traceback
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc(),
                'ip_range_start': '155.235.81.1',
                'ip_range_end': '155.235.81.254',
                'scan_timeout': 5,
                'concurrent_scans': 10,
                'updated_at': datetime.now().isoformat(),
                'message': 'Error loading network settings. See error details for debugging.'
            }
            self.logger.error(f"Error loading network settings: {error_details}")
            return error_details
    
    def _ensure_directories(self):
        """Ensure all required directories exist with proper permissions"""
        try:
            # Create main data directory
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Data directory exists at: {self.data_dir.absolute()}")
            
            # Create backup directories
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.daily_backup_dir.mkdir(parents=True, exist_ok=True)
            self.weekly_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = self.data_dir / 'permission_test.txt'
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                # Clean up test file
                test_file.unlink(missing_ok=True)
                self.logger.info("Data directory has write permissions")
            except (IOError, PermissionError) as e:
                self.logger.error(f"Data directory lacks write permissions: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to ensure directories: {e}", exc_info=True)

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

# Global database service instance - using the same instance as db
db_service = db

# Initialize Flask app with database
def init_db(app):
    """Initialize database with Flask app"""
    app.db = DatabaseService(app.config.get('DATA_DIR', 'attendance_data'))
    
    # Set default system configuration
    config = app.db.get_system_config()
    if not config:
        config = SystemConfig(
            timezone='UTC',
            work_hours_per_day=8,
            overtime_threshold=8,
            backup_enabled=True,
            terminals_open_by_default=True  # New setting for terminal access policy
        )
        app.db.save_system_config(config)
    
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
