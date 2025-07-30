"""
Zone-Based Automatic Attendance System
Automatically tracks clock-in/out based on camera zones and employee movement
"""

import time
import threading
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, date
import logging

class AttendanceAction(Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"

@dataclass
class ZoneDefinition:
    zone_id: str
    name: str
    camera_ids: List[str]
    zone_type: str  # 'entry', 'exit', 'work_area', 'break_area'
    coordinates: Optional[Dict] = None  # For polygon-based zones
    triggers_action: Optional[AttendanceAction] = None
    dwell_time_required: float = 3.0  # Seconds to confirm presence
    
@dataclass
class EmployeeMovement:
    employee_id: str
    employee_name: str
    timestamp: float
    zone_id: str
    camera_id: str
    confidence: float
    action_triggered: Optional[AttendanceAction] = None

class ZoneAttendanceService:
    """Automatic attendance tracking based on zone detection"""
    
    def __init__(self, database_service, advanced_enrollment_service=None):
        self.db_service = database_service
        self.enrollment_service = advanced_enrollment_service
        
        # Zone configuration
        self.zones = {}
        self.camera_zone_mapping = defaultdict(list)
        
        # Employee tracking
        self.employee_locations = {}  # Current location of each employee
        self.movement_history = defaultdict(deque)  # Recent movements per employee
        self.zone_dwell_timers = defaultdict(dict)  # Track time in zones
        self.pending_actions = defaultdict(list)
        
        # Recognition settings
        self.recognition_confidence_threshold = 0.6
        self.movement_timeout = 30  # Seconds before considering employee "left"
        self.action_cooldown = 60  # Seconds between same actions
        
        # Threading
        self.running = False
        self.processing_thread = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Setup default zones for 4-camera system
        self._setup_default_zones()
    
    def _setup_default_zones(self):
        """Setup default zones based on typical 4-camera layout"""
        # Define zones based on your camera layout
        zones = [
            ZoneDefinition(
                zone_id="entrance_main",
                name="Main Entrance",
                camera_ids=["camera_01", "camera_04"],  # Cameras covering entrance
                zone_type="entry",
                triggers_action=AttendanceAction.CLOCK_IN,
                dwell_time_required=3.0
            ),
            ZoneDefinition(
                zone_id="exit_main", 
                name="Main Exit",
                camera_ids=["camera_01", "camera_04"],  # Same cameras, different zone
                zone_type="exit",
                triggers_action=AttendanceAction.CLOCK_OUT,
                dwell_time_required=2.0
            ),
            ZoneDefinition(
                zone_id="work_area_lobby",
                name="Lobby/Work Area",
                camera_ids=["camera_02", "camera_03"],  # Interior cameras
                zone_type="work_area",
                dwell_time_required=5.0
            ),
            ZoneDefinition(
                zone_id="corridor",
                name="Corridor/Transition",
                camera_ids=["camera_02"],  # Corridor camera
                zone_type="transit",
                dwell_time_required=1.0
            )
        ]
        
        for zone in zones:
            self.add_zone(zone)
    
    def add_zone(self, zone: ZoneDefinition):
        """Add a zone to the tracking system"""
        self.zones[zone.zone_id] = zone
        
        # Update camera-zone mapping
        for camera_id in zone.camera_ids:
            self.camera_zone_mapping[camera_id].append(zone.zone_id)
        
        self.logger.info(f"Added zone: {zone.name} ({zone.zone_id})")
    
    def get_all_zones(self):
        """Get all configured zones"""
        return list(self.zones.values())
    
    def get_zone_by_id(self, zone_id: str) -> Optional[ZoneDefinition]:
        """Get zone by ID"""
        return self.zones.get(zone_id)
    
    def get_zones_for_camera(self, camera_id: str) -> List[str]:
        """Get zones that include the specified camera"""
        return self.camera_zone_mapping.get(camera_id, [])
    
    def log_zone_entry(self, employee_id: str, zone_id: str, confidence: float = 1.0):
        """Log an employee's entry to a zone"""
        try:
            detection_time = time.time()
            
            # Process the detection
            self.process_detection(
                camera_id=f"camera_{zone_id}",  # Mock camera ID
                employee_id=employee_id,
                employee_name=f"Employee {employee_id}",  # Mock name
                confidence=confidence,
                detection_time=detection_time
            )
            
            self.logger.info(f"Logged zone entry for {employee_id} in {zone_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error logging zone entry: {e}")
            return False
    
    def process_detection(self, camera_id: str, employee_id: str, employee_name: str, 
                         confidence: float, detection_time: float = None):
        """Process employee detection from camera"""
        if detection_time is None:
            detection_time = time.time()
        
        # Find zones for this camera
        camera_zones = self.camera_zone_mapping.get(camera_id, [])
        
        if not camera_zones:
            self.logger.warning(f"No zones defined for camera {camera_id}")
            return
        
        # Process detection for each zone
        for zone_id in camera_zones:
            zone = self.zones[zone_id]
            
            # Create movement record
            movement = EmployeeMovement(
                employee_id=employee_id,
                employee_name=employee_name,
                timestamp=detection_time,
                zone_id=zone_id,
                camera_id=camera_id,
                confidence=confidence
            )
            
            # Update employee location
            self.employee_locations[employee_id] = {
                'zone_id': zone_id,
                'camera_id': camera_id,
                'timestamp': detection_time,
                'confidence': confidence
            }
            
            # Add to movement history
            self.movement_history[employee_id].append(movement)
            
            # Keep only recent movements
            if len(self.movement_history[employee_id]) > 50:
                self.movement_history[employee_id].popleft()
            
            # Process zone dwell time
            self._process_zone_dwell(employee_id, zone_id, detection_time)
            
            self.logger.debug(f"Processed detection: {employee_name} in {zone.name} via {camera_id}")
    
    def _process_zone_dwell(self, employee_id: str, zone_id: str, detection_time: float):
        """Process employee dwell time in zone"""
        zone = self.zones[zone_id]
        
        # Initialize dwell timer if not exists
        if employee_id not in self.zone_dwell_timers:
            self.zone_dwell_timers[employee_id] = {}
        
        if zone_id not in self.zone_dwell_timers[employee_id]:
            self.zone_dwell_timers[employee_id][zone_id] = {
                'start_time': detection_time,
                'last_seen': detection_time,
                'triggered': False
            }
        else:
            # Update last seen time
            self.zone_dwell_timers[employee_id][zone_id]['last_seen'] = detection_time
        
        timer_info = self.zone_dwell_timers[employee_id][zone_id]
        dwell_time = detection_time - timer_info['start_time']
        
        # Check if dwell time requirement is met and action should be triggered
        if (dwell_time >= zone.dwell_time_required and 
            not timer_info['triggered'] and 
            zone.triggers_action):
            
            # Check if this action is appropriate based on context
            if self._should_trigger_action(employee_id, zone.triggers_action, detection_time):
                self._trigger_attendance_action(employee_id, zone.triggers_action, zone_id, detection_time)
                timer_info['triggered'] = True
    
    def _should_trigger_action(self, employee_id: str, action: AttendanceAction, current_time: float) -> bool:
        """Determine if attendance action should be triggered"""
        # Get current attendance status
        try:
            current_status = self._get_employee_attendance_status(employee_id)
        except Exception as e:
            self.logger.error(f"Error getting attendance status for {employee_id}: {e}")
            return False
        
        # Action logic based on current status
        if action == AttendanceAction.CLOCK_IN:
            # Only clock in if not already clocked in
            if current_status.get('is_clocked_in', False):
                self.logger.info(f"Employee {employee_id} already clocked in, skipping")
                return False
            
            # Check cooldown
            last_action_time = current_status.get('last_clock_in_time', 0)
            if current_time - last_action_time < self.action_cooldown:
                self.logger.info(f"Clock-in cooldown active for {employee_id}")
                return False
            
            return True
            
        elif action == AttendanceAction.CLOCK_OUT:
            # Only clock out if currently clocked in
            if not current_status.get('is_clocked_in', False):
                self.logger.info(f"Employee {employee_id} not clocked in, skipping clock-out")
                return False
            
            # Check minimum work time (e.g., must work at least 10 minutes)
            clock_in_time = current_status.get('clock_in_time', 0)
            if current_time - clock_in_time < 600:  # 10 minutes
                self.logger.info(f"Minimum work time not met for {employee_id}")
                return False
            
            # Check cooldown
            last_action_time = current_status.get('last_clock_out_time', 0)
            if current_time - last_action_time < self.action_cooldown:
                self.logger.info(f"Clock-out cooldown active for {employee_id}")
                return False
            
            return True
        
        return False
    
    def _get_employee_attendance_status(self, employee_id: str) -> Dict:
        """Get current attendance status for employee"""
        # Get today's attendance records
        today = date.today().isoformat()
        
        # Import the model here to avoid circular imports
        from ..models.attendance import AttendanceRecord
        
        # Query database for today's attendance
        attendance_records = self.db_service.find_all(AttendanceRecord)
        today_records = [r for r in attendance_records 
                        if r.employee_id == employee_id and r.date == today]
        
        if not today_records:
            return {'is_clocked_in': False}
        
        # Get latest record
        latest_record = max(today_records, key=lambda x: x.created_at or '')
        
        is_clocked_in = latest_record.clock_in_time and not latest_record.clock_out_time
        
        # Parse times for calculations
        clock_in_timestamp = 0
        if latest_record.clock_in_time:
            try:
                clock_in_dt = datetime.strptime(f"{today} {latest_record.clock_in_time}", '%Y-%m-%d %H:%M:%S')
                clock_in_timestamp = clock_in_dt.timestamp()
            except:
                pass
        
        last_clock_in_time = clock_in_timestamp
        last_clock_out_time = 0
        if latest_record.clock_out_time:
            try:
                clock_out_dt = datetime.strptime(f"{today} {latest_record.clock_out_time}", '%Y-%m-%d %H:%M:%S')
                last_clock_out_time = clock_out_dt.timestamp()
            except:
                pass
        
        return {
            'is_clocked_in': is_clocked_in,
            'clock_in_time': clock_in_timestamp,
            'last_clock_in_time': clock_in_timestamp,
            'last_clock_out_time': last_clock_out_time,
            'latest_record': latest_record
        }
    
    def _trigger_attendance_action(self, employee_id: str, action: AttendanceAction, 
                                 zone_id: str, timestamp: float):
        """Trigger attendance action (clock-in/out)"""
        try:
            # Import models here to avoid circular imports
            from ..models.employee import Employee
            from ..models.attendance import AttendanceRecord
            
            # Get employee info
            employees = self.db_service.find_all(Employee)
            employee = next((e for e in employees if e.employee_id == employee_id), None)
            
            if not employee:
                self.logger.error(f"Employee not found: {employee_id}")
                return
            
            # Create or update attendance record
            if action == AttendanceAction.CLOCK_IN:
                self._process_clock_in(employee, zone_id, timestamp)
            elif action == AttendanceAction.CLOCK_OUT:
                self._process_clock_out(employee, zone_id, timestamp)
            
            self.logger.info(f"Triggered {action.value} for {employee.first_name} {employee.last_name} in zone {zone_id}")
            
        except Exception as e:
            self.logger.error(f"Error triggering attendance action: {e}")
    
    def _process_clock_in(self, employee, zone_id: str, timestamp: float):
        """Process automatic clock-in"""
        from ..models.attendance import AttendanceRecord
        
        current_time = datetime.fromtimestamp(timestamp)
        today = current_time.date().isoformat()
        time_str = current_time.strftime('%H:%M:%S')
        
        # Create new attendance record
        attendance_record = AttendanceRecord(
            employee_id=employee.employee_id,
            employee_name=f"{employee.first_name} {employee.last_name}",
            clock_in_time=time_str,
            date=today,
            clock_in_terminal=f"zone_{zone_id}",
            clock_in_method="zone_detection_automatic",
            clock_in_ip="camera_system"
        )
        
        # Save to database
        self.db_service.save(attendance_record)
        
        self.logger.info(f"Automatic clock-in recorded for {employee.first_name} {employee.last_name}")
    
    def _process_clock_out(self, employee, zone_id: str, timestamp: float):
        """Process automatic clock-out"""
        from ..models.attendance import AttendanceRecord
        
        current_time = datetime.fromtimestamp(timestamp)
        today = current_time.date().isoformat()
        time_str = current_time.strftime('%H:%M:%S')
        
        # Find today's attendance record without clock-out
        attendance_records = self.db_service.find_all(AttendanceRecord)
        today_record = None
        
        for record in attendance_records:
            if (record.employee_id == employee.employee_id and 
                record.date == today and 
                record.clock_in_time and 
                not record.clock_out_time):
                today_record = record
                break
        
        if today_record:
            # Update existing record with clock-out
            today_record.clock_out_time = time_str
            today_record.clock_out_terminal = f"zone_{zone_id}"
            today_record.clock_out_method = "zone_detection_automatic"
            today_record.clock_out_ip = "camera_system"
            
            # Calculate total hours
            try:
                clock_in_dt = datetime.strptime(f"{today} {today_record.clock_in_time}", '%Y-%m-%d %H:%M:%S')
                clock_out_dt = datetime.strptime(f"{today} {time_str}", '%Y-%m-%d %H:%M:%S')
                total_seconds = (clock_out_dt - clock_in_dt).total_seconds()
                today_record.total_hours = total_seconds / 3600
            except:
                today_record.total_hours = 0
            
            # Save updated record
            self.db_service.save(today_record)
            
            self.logger.info(f"Automatic clock-out recorded for {employee.first_name} {employee.last_name}")
        else:
            self.logger.warning(f"No clock-in record found for {employee.first_name} {employee.last_name} today")
    
    def start_zone_tracking(self):
        """Start zone-based attendance tracking"""
        if self.running:
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.processing_thread.start()
        
        self.logger.info("Zone-based attendance tracking started")
    
    def stop_zone_tracking(self):
        """Stop zone-based attendance tracking"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
        
        self.logger.info("Zone-based attendance tracking stopped")
    
    def _cleanup_loop(self):
        """Background cleanup of old tracking data"""
        while self.running:
            try:
                current_time = time.time()
                
                # Clean up old location data
                for employee_id in list(self.employee_locations.keys()):
                    last_seen = self.employee_locations[employee_id]['timestamp']
                    if current_time - last_seen > self.movement_timeout:
                        del self.employee_locations[employee_id]
                        self.logger.debug(f"Cleaned up location data for {employee_id}")
                
                # Clean up old dwell timers
                for employee_id in list(self.zone_dwell_timers.keys()):
                    for zone_id in list(self.zone_dwell_timers[employee_id].keys()):
                        last_seen = self.zone_dwell_timers[employee_id][zone_id]['last_seen']
                        if current_time - last_seen > self.movement_timeout:
                            del self.zone_dwell_timers[employee_id][zone_id]
                    
                    # Remove employee if no active zones
                    if not self.zone_dwell_timers[employee_id]:
                        del self.zone_dwell_timers[employee_id]
                
                time.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)
    
    def get_zone_status(self) -> Dict:
        """Get current status of all zones"""
        status = {}
        
        for zone_id, zone in self.zones.items():
            # Count employees currently in zone
            employees_in_zone = []
            for employee_id, location in self.employee_locations.items():
                if location['zone_id'] == zone_id:
                    employees_in_zone.append({
                        'employee_id': employee_id,
                        'timestamp': location['timestamp'],
                        'confidence': location['confidence']
                    })
            
            status[zone_id] = {
                'zone_name': zone.name,
                'zone_type': zone.zone_type,
                'employees_present': len(employees_in_zone),
                'employees': employees_in_zone,
                'triggers_action': zone.triggers_action.value if zone.triggers_action else None
            }
        
        return status
    
    def get_employee_movement_history(self, employee_id: str, hours: int = 24) -> List[Dict]:
        """Get movement history for an employee"""
        if employee_id not in self.movement_history:
            return []
        
        cutoff_time = time.time() - (hours * 3600)
        recent_movements = [
            {
                'timestamp': m.timestamp,
                'zone_id': m.zone_id,
                'camera_id': m.camera_id,
                'confidence': m.confidence,
                'action_triggered': m.action_triggered.value if m.action_triggered else None
            }
            for m in self.movement_history[employee_id]
            if m.timestamp > cutoff_time
        ]
        
        return sorted(recent_movements, key=lambda x: x['timestamp'], reverse=True)
    
    def configure_zones_for_cameras(self, camera_config: Dict):
        """Configure zones based on camera layout"""
        # Clear existing zones
        self.zones.clear()
        self.camera_zone_mapping.clear()
        
        # Create zones based on camera configuration
        for camera_id, camera_info in camera_config.items():
            camera_name = camera_info.get('name', camera_id)
            camera_location = camera_info.get('location', 'unknown')
            
            # Create zones based on camera location
            if 'entrance' in camera_location.lower() or 'entry' in camera_location.lower():
                zone = ZoneDefinition(
                    zone_id=f"entry_{camera_id}",
                    name=f"Entry Zone - {camera_name}",
                    camera_ids=[camera_id],
                    zone_type="entry",
                    triggers_action=AttendanceAction.CLOCK_IN,
                    dwell_time_required=3.0
                )
                self.add_zone(zone)
                
            elif 'exit' in camera_location.lower():
                zone = ZoneDefinition(
                    zone_id=f"exit_{camera_id}",
                    name=f"Exit Zone - {camera_name}",
                    camera_ids=[camera_id],
                    zone_type="exit",
                    triggers_action=AttendanceAction.CLOCK_OUT,
                    dwell_time_required=2.0
                )
                self.add_zone(zone)
                
            else:
                # General work area
                zone = ZoneDefinition(
                    zone_id=f"work_{camera_id}",
                    name=f"Work Area - {camera_name}",
                    camera_ids=[camera_id],
                    zone_type="work_area",
                    dwell_time_required=5.0
                )
                self.add_zone(zone)
        
        self.logger.info(f"Configured {len(self.zones)} zones for {len(camera_config)} cameras")
    
    def set_zone_coordinates(self, zone_id: str, coordinates: List[Tuple[int, int]]):
        """Set polygon coordinates for a zone (for specific area detection within camera view)"""
        if zone_id in self.zones:
            self.zones[zone_id].coordinates = {
                'polygon': coordinates,
                'type': 'polygon'
            }
            self.logger.info(f"Set coordinates for zone {zone_id}: {len(coordinates)} points")
    
    def is_point_in_zone(self, zone_id: str, x: int, y: int) -> bool:
        """Check if a point (face center) is within a zone's defined area"""
        if zone_id not in self.zones:
            return False
        
        zone = self.zones[zone_id]
        if not zone.coordinates or zone.coordinates.get('type') != 'polygon':
            return True  # If no coordinates defined, consider entire camera view as zone
        
        # Point-in-polygon test
        polygon = zone.coordinates['polygon']
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

# Global service instance
zone_service = None

def initialize_zone_service(database_service, enrollment_service=None):
    """Initialize the global zone service instance"""
    global zone_service
    zone_service = ZoneAttendanceService(database_service, enrollment_service)
    return zone_service
