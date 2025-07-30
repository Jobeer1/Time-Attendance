"""
CCTV Integration Service for Multi-Camera Attendance System
Handles live camera feeds, face detection, and coordinates all camera-based services
"""

import cv2
import threading
import time
import queue
import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging
from pathlib import Path

@dataclass
class CameraConfig:
    camera_id: str
    name: str
    url: str
    location: str
    enabled: bool = True
    fps: int = 30
    resolution: Tuple[int, int] = (1280, 720)
    detection_enabled: bool = True
    recording_enabled: bool = False

@dataclass
class DetectionResult:
    camera_id: str
    timestamp: float
    employee_id: Optional[str]
    employee_name: Optional[str]
    confidence: float
    face_location: Tuple[int, int, int, int]
    frame_with_detection: np.ndarray

class CCTVIntegrationService:
    """Main CCTV integration service for attendance system"""
    
    def __init__(self, database_service, advanced_enrollment_service, zone_attendance_service):
        self.db_service = database_service
        self.enrollment_service = advanced_enrollment_service
        self.zone_service = zone_attendance_service
        
        # Camera management
        self.cameras = {}
        self.camera_threads = {}
        self.camera_queues = {}
        self.camera_stats = {}
        
        # Detection settings
        self.detection_interval = 2.0  # Process every 2 seconds
        self.max_detection_distance = 0.6  # Maximum face distance for recognition
        self.min_confidence_threshold = 0.6
        
        # Processing
        self.running = False
        self.detection_executor = ThreadPoolExecutor(max_workers=4)
        self.frame_queues = {}
        
        # Callbacks
        self.detection_callbacks = []
        self.enrollment_callbacks = []
        
        # Statistics
        self.total_detections = 0
        self.successful_recognitions = 0
        self.failed_recognitions = 0
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load camera configuration
        self._load_camera_config()
    
    def _load_camera_config(self):
        """Load camera configuration from database or config file"""
        try:
            # Try to load from database first
            from ..models.camera import Camera
            cameras = self.db_service.find_all(Camera)
            
            for camera in cameras:
                if camera.enabled:
                    config = CameraConfig(
                        camera_id=camera.camera_id,
                        name=camera.name,
                        url=camera.url,
                        location=camera.location,
                        enabled=camera.enabled,
                        detection_enabled=camera.detection_enabled
                    )
                    self.cameras[camera.camera_id] = config
                    
            self.logger.info(f"Loaded {len(self.cameras)} cameras from database")
            
        except Exception as e:
            self.logger.warning(f"Could not load cameras from database: {e}")
            # Fallback to default configuration
            self._setup_default_cameras()
    
    def _setup_default_cameras(self):
        """Setup default camera configuration for 4-camera system"""
        default_cameras = [
            CameraConfig(
                camera_id="camera_01",
                name="Main Entrance Camera",
                url="rtsp://192.168.1.100:554/stream1",  # Replace with actual RTSP URLs
                location="main_entrance",
                detection_enabled=True
            ),
            CameraConfig(
                camera_id="camera_02",
                name="Lobby Camera",
                url="rtsp://192.168.1.101:554/stream1",
                location="lobby",
                detection_enabled=True
            ),
            CameraConfig(
                camera_id="camera_03",
                name="Corridor Camera",
                url="rtsp://192.168.1.102:554/stream1",
                location="corridor",
                detection_enabled=True
            ),
            CameraConfig(
                camera_id="camera_04",
                name="Exit Camera",
                url="rtsp://192.168.1.103:554/stream1",
                location="exit",
                detection_enabled=True
            )
        ]
        
        for camera in default_cameras:
            self.cameras[camera.camera_id] = camera
        
        self.logger.info(f"Setup {len(default_cameras)} default cameras")
    
    def start_camera_monitoring(self):
        """Start monitoring all configured cameras"""
        if self.running:
            self.logger.warning("Camera monitoring already running")
            return
        
        self.running = True
        
        # Start zone tracking
        self.zone_service.start_zone_tracking()
        
        # Configure zones based on camera layout
        camera_info = {
            cam_id: {'name': cam.name, 'location': cam.location}
            for cam_id, cam in self.cameras.items()
        }
        self.zone_service.configure_zones_for_cameras(camera_info)
        
        # Start camera threads
        for camera_id, camera_config in self.cameras.items():
            if camera_config.enabled:
                self._start_camera_thread(camera_config)
        
        self.logger.info(f"Started monitoring {len(self.cameras)} cameras")
    
    def stop_camera_monitoring(self):
        """Stop monitoring all cameras"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop camera threads
        for camera_id in list(self.camera_threads.keys()):
            self._stop_camera_thread(camera_id)
        
        # Stop zone tracking
        self.zone_service.stop_zone_tracking()
        
        # Shutdown executor
        self.detection_executor.shutdown(wait=True)
        
        self.logger.info("Stopped camera monitoring")
    
    def _start_camera_thread(self, camera_config: CameraConfig):
        """Start monitoring thread for a specific camera"""
        if camera_config.camera_id in self.camera_threads:
            return
        
        # Create frame queue
        self.frame_queues[camera_config.camera_id] = queue.Queue(maxsize=10)
        
        # Initialize camera stats
        self.camera_stats[camera_config.camera_id] = {
            'connected': False,
            'fps': 0,
            'frame_count': 0,
            'detection_count': 0,
            'last_detection': None,
            'errors': 0
        }
        
        # Start camera thread
        thread = threading.Thread(
            target=self._camera_loop,
            args=(camera_config,),
            daemon=True
        )
        thread.start()
        self.camera_threads[camera_config.camera_id] = thread
        
        # Start detection thread for this camera
        detection_thread = threading.Thread(
            target=self._detection_loop,
            args=(camera_config.camera_id,),
            daemon=True
        )
        detection_thread.start()
        
        self.logger.info(f"Started camera thread for {camera_config.name}")
    
    def _stop_camera_thread(self, camera_id: str):
        """Stop monitoring thread for a specific camera"""
        if camera_id in self.camera_threads:
            # Thread will stop when self.running becomes False
            self.camera_threads[camera_id].join(timeout=5)
            del self.camera_threads[camera_id]
        
        if camera_id in self.frame_queues:
            del self.frame_queues[camera_id]
        
        self.logger.info(f"Stopped camera thread for {camera_id}")
    
    def _camera_loop(self, camera_config: CameraConfig):
        """Main loop for camera frame capture"""
        camera_id = camera_config.camera_id
        stats = self.camera_stats[camera_id]
        
        # Try to connect to camera
        cap = None
        retry_count = 0
        max_retries = 5
        
        while self.running and retry_count < max_retries:
            try:
                # For demo purposes, use webcam (0) instead of RTSP
                # In production, use: cap = cv2.VideoCapture(camera_config.url)
                if camera_config.url.startswith('rtsp://'):
                    cap = cv2.VideoCapture(camera_config.url)
                else:
                    # Use webcam for demo
                    cap = cv2.VideoCapture(0)
                
                if cap and cap.isOpened():
                    stats['connected'] = True
                    self.logger.info(f"Connected to camera {camera_config.name}")
                    break
                else:
                    raise Exception("Could not open camera")
                    
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Failed to connect to camera {camera_config.name}: {e}")
                time.sleep(5)  # Wait before retry
        
        if not cap or not cap.isOpened():
            self.logger.error(f"Could not connect to camera {camera_config.name} after {max_retries} attempts")
            stats['connected'] = False
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_config.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_config.resolution[1])
        cap.set(cv2.CAP_PROP_FPS, camera_config.fps)
        
        frame_count = 0
        last_fps_time = time.time()
        
        try:
            while self.running and cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    self.logger.warning(f"Failed to read frame from {camera_config.name}")
                    stats['errors'] += 1
                    continue
                
                frame_count += 1
                stats['frame_count'] = frame_count
                
                # Calculate FPS
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    stats['fps'] = frame_count - stats.get('last_frame_count', 0)
                    stats['last_frame_count'] = frame_count
                    last_fps_time = current_time
                
                # Add frame to queue for detection (non-blocking)
                if camera_config.detection_enabled:
                    try:
                        self.frame_queues[camera_id].put_nowait((current_time, frame.copy()))
                    except queue.Full:
                        # Queue is full, skip this frame
                        pass
                
                # Small delay to control frame rate
                time.sleep(1.0 / camera_config.fps)
                
        except Exception as e:
            self.logger.error(f"Error in camera loop for {camera_config.name}: {e}")
            stats['errors'] += 1
        
        finally:
            if cap:
                cap.release()
            stats['connected'] = False
            self.logger.info(f"Camera loop ended for {camera_config.name}")
    
    def _detection_loop(self, camera_id: str):
        """Detection loop for processing frames from a camera"""
        last_detection_time = 0
        frame_queue = self.frame_queues[camera_id]
        stats = self.camera_stats[camera_id]
        
        while self.running:
            try:
                # Get frame from queue (blocking with timeout)
                timestamp, frame = frame_queue.get(timeout=1.0)
                
                # Skip if too soon since last detection
                if timestamp - last_detection_time < self.detection_interval:
                    continue
                
                # Process frame for face detection and recognition
                detection_result = self._process_frame_for_detection(camera_id, frame, timestamp)
                
                if detection_result:
                    last_detection_time = timestamp
                    stats['detection_count'] += 1
                    stats['last_detection'] = timestamp
                    
                    # Process the detection
                    self._handle_detection_result(detection_result)
                
            except queue.Empty:
                # No frames in queue, continue
                continue
            except Exception as e:
                self.logger.error(f"Error in detection loop for {camera_id}: {e}")
                time.sleep(1)
    
    def _process_frame_for_detection(self, camera_id: str, frame: np.ndarray, timestamp: float) -> Optional[DetectionResult]:
        """Process frame for face detection and recognition"""
        try:
            # Use the advanced enrollment service for recognition
            recognition_result = self.enrollment_service.recognize_employee(frame, camera_id)
            
            if recognition_result:
                # Create detection result
                detection = DetectionResult(
                    camera_id=camera_id,
                    timestamp=timestamp,
                    employee_id=recognition_result['employee_id'],
                    employee_name=recognition_result['employee_name'],
                    confidence=recognition_result['confidence'],
                    face_location=recognition_result['face_location'],
                    frame_with_detection=self._draw_detection_box(frame, recognition_result)
                )
                
                self.total_detections += 1
                if recognition_result['confidence'] > self.min_confidence_threshold:
                    self.successful_recognitions += 1
                else:
                    self.failed_recognitions += 1
                
                return detection
            
        except Exception as e:
            self.logger.error(f"Error processing frame for detection: {e}")
        
        return None
    
    def _draw_detection_box(self, frame: np.ndarray, recognition_result: Dict) -> np.ndarray:
        """Draw detection box and employee info on frame"""
        frame_copy = frame.copy()
        
        # Get face location (top, right, bottom, left)
        top, right, bottom, left = recognition_result['face_location']
        
        # Draw rectangle around face
        color = (0, 255, 0) if recognition_result['confidence'] > self.min_confidence_threshold else (0, 255, 255)
        cv2.rectangle(frame_copy, (left, top), (right, bottom), color, 2)
        
        # Draw label with employee name and confidence
        label = f"{recognition_result['employee_name']} ({recognition_result['confidence']:.2f})"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        
        # Draw label background
        cv2.rectangle(frame_copy, (left, top - label_size[1] - 10), 
                     (left + label_size[0], top), color, -1)
        
        # Draw label text
        cv2.putText(frame_copy, label, (left, top - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame_copy
    
    def _handle_detection_result(self, detection: DetectionResult):
        """Handle a successful detection result"""
        # Send to zone attendance service
        if detection.employee_id and detection.confidence > self.min_confidence_threshold:
            self.zone_service.process_detection(
                camera_id=detection.camera_id,
                employee_id=detection.employee_id,
                employee_name=detection.employee_name,
                confidence=detection.confidence,
                detection_time=detection.timestamp
            )
        
        # Call registered callbacks
        for callback in self.detection_callbacks:
            try:
                callback(detection)
            except Exception as e:
                self.logger.error(f"Error in detection callback: {e}")
        
        self.logger.debug(f"Processed detection: {detection.employee_name} at {detection.camera_id}")
    
    def add_detection_callback(self, callback: Callable[[DetectionResult], None]):
        """Add callback function for detection events"""
        self.detection_callbacks.append(callback)
    
    def add_enrollment_callback(self, callback: Callable):
        """Add callback function for enrollment events"""
        self.enrollment_callbacks.append(callback)
    
    def get_camera_stats(self) -> Dict:
        """Get statistics for all cameras"""
        return self.camera_stats.copy()
    
    def get_detection_stats(self) -> Dict:
        """Get overall detection statistics"""
        return {
            'total_detections': self.total_detections,
            'successful_recognitions': self.successful_recognitions,
            'failed_recognitions': self.failed_recognitions,
            'success_rate': (self.successful_recognitions / max(self.total_detections, 1)) * 100,
            'cameras_active': len([c for c in self.camera_stats.values() if c['connected']]),
            'total_cameras': len(self.cameras)
        }
    
    def get_live_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get latest frame from a camera"""
        if camera_id not in self.frame_queues:
            return None
        
        try:
            # Get the most recent frame (non-blocking)
            while not self.frame_queues[camera_id].empty():
                timestamp, frame = self.frame_queues[camera_id].get_nowait()
            return frame
        except queue.Empty:
            return None
    
    def start_enrollment_session(self, employee_id: str, employee_name: str) -> str:
        """Start employee enrollment session across all cameras"""
        session_id = self.enrollment_service.start_employee_enrollment(employee_id, employee_name)
        
        # Notify callbacks
        for callback in self.enrollment_callbacks:
            try:
                callback('enrollment_started', {
                    'session_id': session_id,
                    'employee_id': employee_id,
                    'employee_name': employee_name
                })
            except Exception as e:
                self.logger.error(f"Error in enrollment callback: {e}")
        
        return session_id
    
    def process_enrollment_frame(self, camera_id: str, session_id: str) -> Dict:
        """Process current frame for enrollment"""
        frame = self.get_live_frame(camera_id)
        if frame is None:
            return {'error': 'No frame available'}
        
        return self.enrollment_service.process_enrollment_frame(camera_id, frame, session_id)
    
    def configure_camera(self, camera_config: CameraConfig):
        """Add or update camera configuration"""
        was_running = camera_config.camera_id in self.camera_threads
        
        if was_running:
            self._stop_camera_thread(camera_config.camera_id)
        
        self.cameras[camera_config.camera_id] = camera_config
        
        if was_running and self.running:
            self._start_camera_thread(camera_config)
        
        self.logger.info(f"Configured camera: {camera_config.name}")
    
    def remove_camera(self, camera_id: str):
        """Remove camera from monitoring"""
        if camera_id in self.camera_threads:
            self._stop_camera_thread(camera_id)
        
        if camera_id in self.cameras:
            del self.cameras[camera_id]
        
        self.logger.info(f"Removed camera: {camera_id}")
    
    def test_camera_connection(self, camera_url: str) -> Dict:
        """Test connection to a camera URL"""
        try:
            cap = cv2.VideoCapture(camera_url)
            
            if not cap.isOpened():
                return {'success': False, 'error': 'Could not open camera'}
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return {'success': False, 'error': 'Could not read frame'}
            
            return {
                'success': True,
                'resolution': (frame.shape[1], frame.shape[0]),
                'channels': frame.shape[2] if len(frame.shape) > 2 else 1
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_zone_overview(self) -> Dict:
        """Get overview of all zones and current employee locations"""
        zone_status = self.zone_service.get_zone_status()
        
        # Add camera information to zones
        for zone_id, zone_info in zone_status.items():
            zone = self.zone_service.zones.get(zone_id)
            if zone:
                zone_info['cameras'] = zone.camera_ids
                zone_info['dwell_time_required'] = zone.dwell_time_required
        
        return {
            'zones': zone_status,
            'total_employees_detected': sum(z['employees_present'] for z in zone_status.values()),
            'active_zones': len([z for z in zone_status.values() if z['employees_present'] > 0])
        }
    
    def export_detection_data(self, hours: int = 24) -> Dict:
        """Export detection data for analysis"""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        
        # Get movement history for all employees
        all_movements = {}
        for employee_id in self.zone_service.movement_history.keys():
            movements = self.zone_service.get_employee_movement_history(employee_id, hours)
            if movements:
                all_movements[employee_id] = movements
        
        return {
            'export_time': current_time,
            'hours_covered': hours,
            'camera_stats': self.get_camera_stats(),
            'detection_stats': self.get_detection_stats(),
            'zone_overview': self.get_zone_overview(),
            'employee_movements': all_movements
        }
