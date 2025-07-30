"""
Live Camera Face Recognition Service
Integrates IP cameras with real-time face recognition for attendance tracking
"""

import cv2
import numpy as np
import threading
import time
import requests
from urllib.parse import urlparse
from typing import Dict, List, Optional, Callable
import logging
from dataclasses import dataclass
from datetime import datetime

from .face_recognition import face_service
from .advanced_enrollment import AdvancedEnrollmentService
from .zone_attendance import ZoneAttendanceService
from .database import db_service

logger = logging.getLogger(__name__)

@dataclass
class LiveCameraConfig:
    camera_id: str
    name: str
    stream_url: str
    zone_id: str
    enabled: bool = True
    recognition_interval: float = 2.0  # seconds between face recognition attempts
    confidence_threshold: float = 0.7
    frame_skip: int = 5  # process every 5th frame for performance

@dataclass
class RecognitionEvent:
    camera_id: str
    employee_id: str
    employee_name: str
    confidence: float
    timestamp: datetime
    zone_id: str
    face_location: tuple

class LiveCameraRecognitionService:
    """Service for real-time face recognition from IP camera streams"""
    
    def __init__(self, face_recognition_service=None, enrollment_service=None, zone_service=None):
        self.face_service = face_recognition_service or face_service
        self.enrollment_service = enrollment_service
        self.zone_service = zone_service
        self.db_service = db_service
        
        # Active camera streams
        self.active_cameras: Dict[str, LiveCameraConfig] = {}
        self.camera_threads: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, threading.Event] = {}
        
        # Recognition state
        self.last_recognitions: Dict[str, Dict] = {}  # Prevent duplicate recognitions
        self.recognition_cooldown = 10.0  # seconds before recognizing same person again
        
        # Event callbacks
        self.recognition_callbacks: List[Callable] = []
        
        # Load cameras from database
        self._load_cameras_from_db()
        
        logger.info("Live Camera Recognition Service initialized")
    
    def _load_cameras_from_db(self):
        """Load cameras from database on service initialization"""
        try:
            cameras = self.db_service.get_live_cameras()
            loaded_count = 0
            
            for camera_data in cameras:
                try:
                    camera_config = LiveCameraConfig(
                        camera_id=camera_data.get('camera_id'),
                        name=camera_data.get('name'),
                        stream_url=camera_data.get('stream_url'),
                        zone_id=camera_data.get('zone_id'),
                        enabled=camera_data.get('enabled', True),
                        recognition_interval=camera_data.get('recognition_interval', 2.0),
                        confidence_threshold=camera_data.get('confidence_threshold', 0.7),
                        frame_skip=camera_data.get('frame_skip', 5)
                    )
                    
                    # Add to active cameras (without saving to DB again)
                    self.active_cameras[camera_config.camera_id] = camera_config
                    loaded_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to load camera {camera_data.get('camera_id', 'unknown')}: {e}")
                    continue
                    
            logger.info(f"Loaded {loaded_count} cameras from database")
            
        except Exception as e:
            logger.warning(f"Failed to load cameras from database: {e}")
            # Continue without loaded cameras
    
    def add_camera(self, camera_config: LiveCameraConfig) -> bool:
        """Add a camera for live recognition"""
        try:
            logger.info(f"Attempting to add camera: {camera_config.camera_id}")
            logger.info(f"Camera config: name='{camera_config.name}', stream_url='{camera_config.stream_url}', zone_id='{camera_config.zone_id}'")
            logger.info(f"Stream URL type: {type(camera_config.stream_url)}, value: '{camera_config.stream_url}'")
            
            # Validate stream URL
            logger.info(f"Validating stream URL: {camera_config.stream_url}")
            validation_result = self._validate_stream_url(camera_config.stream_url)
            logger.info(f"Validation result: {validation_result}")
            
            if not validation_result:
                logger.error(f"Stream URL validation failed for camera {camera_config.camera_id}")
                return False
            
            logger.info(f"Stream URL validation passed for camera {camera_config.camera_id}")
            
            # Check if camera already exists
            if camera_config.camera_id in self.active_cameras:
                logger.error(f"Camera {camera_config.camera_id} already exists")
                return False
            
            # Add to active cameras in memory
            self.active_cameras[camera_config.camera_id] = camera_config
            logger.info(f"Added camera {camera_config.camera_id} to active cameras")
            
            # Save to database for persistence
            try:
                camera_data = {
                    'camera_id': camera_config.camera_id,
                    'name': camera_config.name,
                    'stream_url': camera_config.stream_url,
                    'zone_id': camera_config.zone_id,
                    'enabled': camera_config.enabled,
                    'recognition_interval': camera_config.recognition_interval,
                    'confidence_threshold': camera_config.confidence_threshold,
                    'frame_skip': camera_config.frame_skip,
                    'created_at': datetime.now().isoformat()
                }
                logger.info(f"Attempting to save camera data: {camera_data}")
                save_result = self.db_service.save_live_camera(camera_data)
                logger.info(f"Database save result: {save_result}")
                
                if save_result:
                    logger.info(f"Camera {camera_config.camera_id} saved to database successfully")
                else:
                    logger.warning(f"Failed to save camera to database, but continuing with in-memory storage")
                    
            except Exception as db_error:
                logger.warning(f"Failed to save camera to database: {db_error}")
                logger.warning(f"Database error details: {type(db_error).__name__}: {str(db_error)}")
                # Continue anyway, camera is still in memory
            
            logger.info(f"Successfully added camera {camera_config.name} ({camera_config.camera_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding camera {camera_config.camera_id}: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def start_camera_recognition(self, camera_id: str) -> bool:
        """Start live recognition for a specific camera"""
        if camera_id not in self.active_cameras:
            logger.error(f"Camera {camera_id} not found")
            return False
        
        if camera_id in self.camera_threads and self.camera_threads[camera_id].is_alive():
            logger.warning(f"Camera {camera_id} already running")
            return True
        
        try:
            # Create stop flag
            self.stop_flags[camera_id] = threading.Event()
            
            # Start camera thread
            thread = threading.Thread(
                target=self._camera_recognition_worker,
                args=(camera_id,),
                daemon=True,
                name=f"Camera-{camera_id}"
            )
            thread.start()
            self.camera_threads[camera_id] = thread
            
            logger.info(f"Started live recognition for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera {camera_id}: {e}")
            return False
    
    def stop_camera_recognition(self, camera_id: str) -> bool:
        """Stop live recognition for a specific camera"""
        try:
            if camera_id in self.stop_flags:
                self.stop_flags[camera_id].set()
            
            if camera_id in self.camera_threads:
                thread = self.camera_threads[camera_id]
                thread.join(timeout=5.0)  # Wait up to 5 seconds
                del self.camera_threads[camera_id]
            
            if camera_id in self.stop_flags:
                del self.stop_flags[camera_id]
            
            logger.info(f"Stopped live recognition for camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping camera {camera_id}: {e}")
            return False
    
    def start_all_cameras(self) -> Dict[str, bool]:
        """Start live recognition for all configured cameras"""
        results = {}
        for camera_id in self.active_cameras:
            if self.active_cameras[camera_id].enabled:
                results[camera_id] = self.start_camera_recognition(camera_id)
            else:
                results[camera_id] = False
                logger.info(f"Camera {camera_id} is disabled, skipping")
        return results
    
    def stop_all_cameras(self) -> Dict[str, bool]:
        """Stop live recognition for all cameras"""
        results = {}
        for camera_id in list(self.camera_threads.keys()):
            results[camera_id] = self.stop_camera_recognition(camera_id)
        return results
    
    def _validate_stream_url(self, stream_url: str) -> bool:
        """Validate that the stream URL is accessible"""
        try:
            logger.info(f"Validating stream URL: '{stream_url}' (type: {type(stream_url)})")
            
            # Check if stream_url is None or empty
            if not stream_url or stream_url.strip() == "":
                logger.error(f"Empty or None stream URL provided")
                return False
            
            # Handle numeric webcam indices (0, 1, 2, etc.)
            if stream_url.isdigit():
                logger.info(f"Detected numeric webcam index: {stream_url}")
                # For webcam indices, always return True to allow configuration
                # The actual webcam test will happen when the camera is started
                logger.info(f"Allowing webcam index {stream_url} (will test when starting)")
                return True
            
            # Basic URL validation
            parsed = urlparse(stream_url)
            logger.info(f"Parsed URL - scheme: '{parsed.scheme}', netloc: '{parsed.netloc}'")
            
            if not all([parsed.scheme, parsed.netloc]):
                logger.warning(f"Invalid URL format: {stream_url} - missing scheme or netloc")
                return False
            
            # If this is a web page URL, try to convert it to a stream URL
            if stream_url.endswith('.html') or '/webcamera.html' in stream_url:
                logger.info(f"Detected web page URL, allowing configuration: {stream_url}")
                
                # For web page URLs, don't test connectivity during validation
                # The actual stream URL will be determined when the camera is started
                logger.info(f"Skipping connectivity test for web page URL: {stream_url}")
                return True
            
            # For direct stream URLs, test connectivity with timeout
            logger.info(f"Testing connectivity for direct stream URL: {stream_url}")
            
            # Use threading with timeout to prevent hanging
            import threading
            result = [False]
            
            def test_connectivity():
                try:
                    result[0] = self._test_stream_connectivity(stream_url)
                except Exception as e:
                    logger.warning(f"Connectivity test exception: {e}")
                    result[0] = False
            
            thread = threading.Thread(target=test_connectivity)
            thread.daemon = True
            thread.start()
            thread.join(timeout=8)  # 8 second timeout for entire validation
            
            if thread.is_alive():
                logger.warning(f"Stream validation timed out for: {stream_url}")
                logger.info(f"Allowing configuration anyway: {stream_url}")
                return True  # Allow configuration even if test times out
            
            if result[0]:
                logger.info(f"Stream URL validation passed for: {stream_url}")
                return True
            else:
                logger.warning(f"Stream URL not accessible but allowing configuration: {stream_url}")
                # Return True to allow cameras to be added even if temporarily unreachable
                return True
            
        except Exception as e:
            logger.error(f"Stream validation error: {e}")
            # Return True to allow configuration in case of validation errors
            return True
    
    def _generate_stream_urls(self, base_url: str) -> list:
        """Generate possible stream URLs from a base camera URL"""
        try:
            parsed = urlparse(base_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            
            # Common IP camera stream URL patterns
            patterns = [
                f"{base}/video.cgi",
                f"{base}/video.mjpg",
                f"{base}/mjpeg.cgi",
                f"{base}/videostream.cgi",
                f"{base}/axis-cgi/mjpg/video.cgi",
                f"{base}/cgi-bin/video.cgi",
                f"{base}/cgi-bin/mjpg/video.cgi",
                f"{base}/webcam.mjpg",
                f"{base}/mjpg/video.mjpg",
                f"{base}/video1.mjpg",
                f"rtsp://{parsed.netloc}/stream",
                f"rtsp://{parsed.netloc}/live",
                f"rtsp://{parsed.netloc}/cam/realmonitor?channel=1&subtype=0",
                f"rtsp://{parsed.netloc}:554/stream",
                f"rtsp://{parsed.netloc}:554/live.sdp"
            ]
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error generating stream URLs: {e}")
            return []
    
    def _test_stream_connectivity(self, stream_url: str) -> bool:
        """Test if a stream URL is accessible with short timeout"""
        try:
            logger.info(f"Testing stream connectivity: {stream_url}")
            
            # For IP camera URLs, try HTTP request first (faster)
            if stream_url.startswith(('http://', 'https://')):
                try:
                    import requests
                    response = requests.get(
                        stream_url, 
                        timeout=3,  # Short timeout
                        stream=True,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"HTTP stream test successful: {stream_url}")
                        return True
                    else:
                        logger.warning(f"HTTP stream returned {response.status_code}: {stream_url}")
                        # Don't return False immediately, try OpenCV
                        
                except Exception as http_error:
                    logger.warning(f"HTTP test failed for {stream_url}: {http_error}")
                    # Continue to OpenCV test
            
            # Quick test with OpenCV (with timeout handling)
            import cv2
            import threading
            import time
            
            result = [False]  # Use list to allow modification in thread
            
            def test_opencv():
                try:
                    cap = cv2.VideoCapture(stream_url)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        cap.release()
                        if ret and frame is not None:
                            result[0] = True
                        else:
                            result[0] = False
                    else:
                        result[0] = False
                except Exception as e:
                    logger.warning(f"OpenCV test error: {e}")
                    result[0] = False
            
            # Run OpenCV test in thread with timeout
            thread = threading.Thread(target=test_opencv)
            thread.daemon = True
            thread.start()
            thread.join(timeout=5)  # 5 second timeout
            
            if thread.is_alive():
                logger.warning(f"OpenCV test timed out for: {stream_url}")
                return False
            
            if result[0]:
                logger.info(f"OpenCV stream test successful: {stream_url}")
                return True
            else:
                logger.warning(f"OpenCV stream test failed: {stream_url}")
                return False
                
        except Exception as e:
            logger.error(f"Stream connectivity test error: {e}")
            return False
    
    def _camera_recognition_worker(self, camera_id: str):
        """Worker thread for continuous camera recognition"""
        camera_config = self.active_cameras[camera_id]
        stop_flag = self.stop_flags[camera_id]
        
        logger.info(f"Starting recognition worker for camera {camera_config.name}")
        
        cap = None
        frame_count = 0
        last_recognition_time = 0
        
        try:
            # Try to initialize video capture with primary URL
            cap = cv2.VideoCapture(camera_config.stream_url)
            
            if not cap.isOpened():
                logger.warning(f"Primary stream URL failed: {camera_config.stream_url}")
                
                # If the primary URL looks like a web page, try alternative URLs
                if camera_config.stream_url.endswith('.html') or '/webcamera.html' in camera_config.stream_url:
                    logger.info(f"Trying alternative stream URLs for {camera_config.name}")
                    alternative_urls = self._generate_stream_urls(camera_config.stream_url)
                    
                    for alt_url in alternative_urls:
                        logger.info(f"Attempting stream URL: {alt_url}")
                        cap = cv2.VideoCapture(alt_url)
                        
                        if cap.isOpened():
                            ret, test_frame = cap.read()
                            if ret and test_frame is not None:
                                logger.info(f"Successfully connected using: {alt_url}")
                                camera_config.stream_url = alt_url  # Update the config
                                break
                            else:
                                cap.release()
                        else:
                            cap.release()
                    
                    if not cap.isOpened():
                        logger.error(f"All stream URLs failed for camera: {camera_config.name}")
                        return
                else:
                    logger.error(f"Failed to open camera stream: {camera_config.stream_url}")
                    return
            
            # Set capture properties for better performance
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for real-time
            cap.set(cv2.CAP_PROP_FPS, 15)       # Limit FPS for performance
            
            logger.info(f"Successfully connected to camera stream: {camera_config.name}")
            
            while not stop_flag.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from camera {camera_id}")
                    time.sleep(1)  # Wait before retrying
                    continue
                
                frame_count += 1
                current_time = time.time()
                
                # Skip frames for performance
                if frame_count % camera_config.frame_skip != 0:
                    continue
                
                # Check recognition interval
                if current_time - last_recognition_time < camera_config.recognition_interval:
                    continue
                
                # Process frame for face recognition
                try:
                    recognition_result = self._process_frame_for_recognition(
                        frame, camera_config, current_time
                    )
                    
                    if recognition_result:
                        self._handle_recognition_event(recognition_result)
                        last_recognition_time = current_time
                
                except Exception as e:
                    logger.error(f"Error processing frame for camera {camera_id}: {e}")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Camera worker error for {camera_id}: {e}")
        
        finally:
            if cap:
                cap.release()
            logger.info(f"Camera worker stopped for {camera_id}")
    
    def _process_frame_for_recognition(self, frame: np.ndarray, 
                                     camera_config: LiveCameraConfig, 
                                     timestamp: float) -> Optional[RecognitionEvent]:
        """Process a single frame for face recognition"""
        try:
            # Use enhanced face recognition if available
            if self.enrollment_service:
                recognition_result = self.enrollment_service.recognize_employee(
                    frame, camera_config.camera_id
                )
                
                if recognition_result and recognition_result['confidence'] >= camera_config.confidence_threshold:
                    # Check for duplicate recognition (cooldown)
                    employee_id = recognition_result['employee_id']
                    last_recognition = self.last_recognitions.get(
                        f"{camera_config.camera_id}_{employee_id}"
                    )
                    
                    if last_recognition and (timestamp - last_recognition['timestamp']) < self.recognition_cooldown:
                        return None  # Skip duplicate recognition
                    
                    # Create recognition event
                    event = RecognitionEvent(
                        camera_id=camera_config.camera_id,
                        employee_id=employee_id,
                        employee_name=recognition_result['employee_name'],
                        confidence=recognition_result['confidence'],
                        timestamp=datetime.fromtimestamp(timestamp),
                        zone_id=camera_config.zone_id,
                        face_location=recognition_result['face_location']
                    )
                    
                    # Update last recognition
                    self.last_recognitions[f"{camera_config.camera_id}_{employee_id}"] = {
                        'timestamp': timestamp,
                        'confidence': recognition_result['confidence']
                    }
                    
                    return event
            
            return None
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            return None
    
    def _handle_recognition_event(self, event: RecognitionEvent):
        """Handle a recognition event"""
        try:
            logger.info(f"Recognition: {event.employee_name} detected on camera {event.camera_id} "
                       f"with {event.confidence:.1%} confidence")
            
            # Record attendance if zone service is available
            if self.zone_service:
                self.zone_service.record_zone_event(
                    employee_id=event.employee_id,
                    zone_id=event.zone_id,
                    event_type='detection',
                    timestamp=event.timestamp,
                    metadata={
                        'camera_id': event.camera_id,
                        'confidence': event.confidence,
                        'face_location': event.face_location
                    }
                )
            
            # Call registered callbacks
            for callback in self.recognition_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        except Exception as e:
            logger.error(f"Error handling recognition event: {e}")
    
    def add_recognition_callback(self, callback: Callable[[RecognitionEvent], None]):
        """Add a callback function for recognition events"""
        self.recognition_callbacks.append(callback)
    
    def get_camera_status(self) -> Dict[str, Dict]:
        """Get status of all cameras"""
        status = {}
        for camera_id, config in self.active_cameras.items():
            is_running = (camera_id in self.camera_threads and 
                         self.camera_threads[camera_id].is_alive())
            
            status[camera_id] = {
                'name': config.name,
                'enabled': config.enabled,
                'running': is_running,
                'stream_url': config.stream_url,
                'zone_id': config.zone_id,
                'last_recognition': self.last_recognitions.get(camera_id, {})
            }
        
        return status
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from the system"""
        try:
            # Stop recognition if running
            self.stop_camera_recognition(camera_id)
            
            # Remove from active cameras
            if camera_id in self.active_cameras:
                del self.active_cameras[camera_id]
            
            logger.info(f"Removed camera {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing camera {camera_id}: {e}")
            return False

# Global instance
live_camera_service = LiveCameraRecognitionService()
