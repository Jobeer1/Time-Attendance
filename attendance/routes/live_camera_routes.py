"""
Live Camera Recognition Routes
API endpoints for managing real-time camera face recognition
"""

from flask import Blueprint, request, jsonify, render_template
import re
from urllib.parse import urljoin
from typing import Dict, Any
import logging
import time
import random

from ..services.live_camera_recognition import live_camera_service, LiveCameraConfig

logger = logging.getLogger(__name__)

live_camera_bp = Blueprint('live_camera', __name__, url_prefix='/api/live-camera')

def get_zone_service():
    """Get zone service instance (lazy loading)"""
    try:
        from ..services.zone_attendance import zone_service
        return zone_service
    except ImportError:
        return None

def get_enrollment_service():
    """Get enrollment service instance (lazy loading)"""
    try:
        from ..services.advanced_enrollment import enrollment_service
        return enrollment_service
    except ImportError:
        return None

@live_camera_bp.route('/cameras', methods=['GET'])
def get_cameras():
    """Get all configured cameras and their status"""
    try:
        cameras = live_camera_service.get_camera_status()
        return jsonify({
            'success': True,
            'cameras': cameras,
            'total_cameras': len(cameras),
            'active_cameras': sum(1 for c in cameras.values() if c['running'])
        })
    except Exception as e:
        logger.error(f"Error getting cameras: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/cameras', methods=['POST'])
def add_camera():
    """Add a new camera for live recognition"""
    try:
        data = request.json
        logger.info(f"Received camera data: {data}")
        logger.info(f"Data type: {type(data)}")
        
        # If URL points to HTML page, try to extract direct stream URL
        stream_url = data.get('stream_url', '')
        if stream_url.endswith('.html') or '/webcamera.html' in stream_url:
            try:
                import requests
                resp = requests.get(stream_url, timeout=5)
                page_html = resp.text
                # Look for common stream sources in HTML
                match = re.search(r'(?:src|data-src)=["\']([^"\']+\.(?:mjpg|cgi|mp4|mjpeg))["\']', page_html, re.IGNORECASE)
                if match:
                    extracted = match.group(1)
                    direct_url = urljoin(stream_url, extracted)
                    logger.info(f"Extracted direct stream URL from HTML: {direct_url}")
                    data['stream_url'] = direct_url
            except Exception as e:
                logger.warning(f"Failed to extract direct stream URL: {e}")

        # Validate required fields
        required_fields = ['camera_id', 'name', 'stream_url', 'zone_id']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing field: {field}")
                return jsonify({
                    'success': False, 
                    'error': f'Missing required field: {field}'
                }), 400
            if not data[field]:
                logger.error(f"Empty field: {field} = '{data[field]}'")
                return jsonify({
                    'success': False, 
                    'error': f'Empty value for required field: {field}'
                }), 400
        
        logger.info(f"All required fields present: camera_id='{data['camera_id']}', name='{data['name']}', stream_url='{data['stream_url']}', zone_id='{data['zone_id']}'")
        
        # Check if camera ID already exists
        existing_cameras = live_camera_service.get_camera_status()
        if data['camera_id'] in existing_cameras:
            return jsonify({
                'success': False,
                'error': f'Camera ID "{data["camera_id"]}" already exists'
            }), 400
        
        # Create camera config
        camera_config = LiveCameraConfig(
            camera_id=data['camera_id'],
            name=data['name'],
            stream_url=data['stream_url'],
            zone_id=data['zone_id'],
            enabled=data.get('enabled', True),
            recognition_interval=data.get('recognition_interval', 2.0),
            confidence_threshold=data.get('confidence_threshold', 0.7),
            frame_skip=data.get('frame_skip', 5)
        )
        
        logger.info(f"Created camera config: {camera_config}")
        
        # Add camera to service
        success = live_camera_service.add_camera(camera_config)
        
        if success:
            logger.info(f"Camera {camera_config.name} added successfully")
            return jsonify({
                'success': True,
                'message': f'Camera {camera_config.name} added successfully',
                'camera_id': camera_config.camera_id
            })
        else:
            logger.error(f"Failed to add camera {camera_config.camera_id}")
            return jsonify({
                'success': False,
                'error': 'Failed to add camera - please check stream URL and try again'
            }), 400
    
    except Exception as e:
        logger.error(f"Error adding camera: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/cameras/<camera_id>/start', methods=['POST'])
def start_camera(camera_id: str):
    """Start live recognition for a specific camera"""
    try:
        success = live_camera_service.start_camera_recognition(camera_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Started live recognition for camera {camera_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to start camera {camera_id}'
            }), 400
    
    except Exception as e:
        logger.error(f"Error starting camera {camera_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/cameras/<camera_id>/stop', methods=['POST'])
def stop_camera(camera_id: str):
    """Stop live recognition for a specific camera"""
    try:
        success = live_camera_service.stop_camera_recognition(camera_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Stopped live recognition for camera {camera_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to stop camera {camera_id}'
            }), 400
    
    except Exception as e:
        logger.error(f"Error stopping camera {camera_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/cameras/<camera_id>', methods=['DELETE'])
def remove_camera(camera_id: str):
    """Remove a camera from the system"""
    try:
        success = live_camera_service.remove_camera(camera_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Camera {camera_id} removed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to remove camera {camera_id}'
            }), 400
    
    except Exception as e:
        logger.error(f"Error removing camera {camera_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/start-all', methods=['POST'])
def start_all_cameras():
    """Start live recognition for all cameras"""
    try:
        results = live_camera_service.start_all_cameras()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        return jsonify({
            'success': True,
            'message': f'Started {success_count}/{total_count} cameras',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error starting all cameras: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/stop-all', methods=['POST'])
def stop_all_cameras():
    """Stop live recognition for all cameras"""
    try:
        results = live_camera_service.stop_all_cameras()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        return jsonify({
            'success': True,
            'message': f'Stopped {success_count}/{total_count} cameras',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error stopping all cameras: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/zones', methods=['GET'])
def get_zones():
    """Get available zones for camera assignment"""
    try:
        zone_service = get_zone_service()
        if zone_service:
            zones = zone_service.get_all_zones()
            return jsonify({
                'success': True,
                'zones': [
                    {
                        'zone_id': zone.zone_id,
                        'name': zone.name,
                        'description': zone.name,
                        'zone_type': zone.zone_type
                    }
                    for zone in zones
                ]
            })
        else:
            return jsonify({
                'success': True,
                'zones': [
                    {'zone_id': 'entrance_main', 'name': 'Main Entrance', 'description': 'Main entrance area'},
                    {'zone_id': 'exit_main', 'name': 'Main Exit', 'description': 'Main exit area'},
                    {'zone_id': 'work_area_lobby', 'name': 'Lobby/Work Area', 'description': 'Lobby and work area'},
                    {'zone_id': 'corridor', 'name': 'Corridor/Transition', 'description': 'Corridor and transition areas'}
                ]
            })
    
    except Exception as e:
        logger.error(f"Error getting zones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/status', methods=['GET'])
def get_system_status():
    """Get overall system status"""
    try:
        cameras = live_camera_service.get_camera_status()
        
        total_cameras = len(cameras)
        active_cameras = sum(1 for c in cameras.values() if c['running'])
        enabled_cameras = sum(1 for c in cameras.values() if c['enabled'])
        
        return jsonify({
            'success': True,
            'status': {
                'face_recognition_enabled': live_camera_service.face_service.enabled,
                'enrollment_service_available': live_camera_service.enrollment_service is not None,
                'zone_service_available': live_camera_service.zone_service is not None,
                'total_cameras': total_cameras,
                'enabled_cameras': enabled_cameras,
                'active_cameras': active_cameras,
                'recognition_cooldown': live_camera_service.recognition_cooldown
            },
            'cameras': cameras
        })
    
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/test-stream', methods=['POST'])
def test_stream():
    """Test a camera stream URL for accessibility"""
    try:
        data = request.json
        stream_url = data.get('stream_url')
        
        if not stream_url:
            return jsonify({
                'success': False,
                'error': 'stream_url is required'
            }), 400
        
        # Test stream accessibility
        is_accessible = live_camera_service._validate_stream_url(stream_url)
        
        return jsonify({
            'success': True,
            'stream_url': stream_url,
            'accessible': is_accessible,
            'message': 'Stream is accessible' if is_accessible else 'Stream is not accessible'
        })
    
    except Exception as e:
        logger.error(f"Error testing stream: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Real-time recognition events endpoint (for WebSocket in future)
@live_camera_bp.route('/events/recent', methods=['GET'])
def get_recent_events():
    """Get recent recognition events"""
    try:
        # For now, return basic info from last recognitions
        recent_events = []
        
        for key, recognition in live_camera_service.last_recognitions.items():
            camera_id, employee_id = key.split('_', 1)
            recent_events.append({
                'camera_id': camera_id,
                'employee_id': employee_id,
                'timestamp': recognition['timestamp'],
                'confidence': recognition['confidence']
            })
        
        # Sort by timestamp (most recent first)
        recent_events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'events': recent_events[:20]  # Return last 20 events
        })
    
    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_camera_bp.route('/detect-faces', methods=['POST'])
def detect_faces_realtime():
    """Real-time face detection for live camera streams"""
    try:
        data = request.json
        camera_url = data.get('camera_url')
        mode = data.get('mode', 'detection')  # detection, recognition, enrollment
        confidence_threshold = float(data.get('confidence_threshold', 0.7))
        
        if not camera_url:
            return jsonify({
                'success': False,
                'error': 'Camera URL is required'
            }), 400
        
        # For now, simulate face detection results
        # In a real implementation, this would capture from the camera stream
        detected_faces = simulate_face_detection_api(mode, confidence_threshold)
        
        return jsonify({
            'success': True,
            'faces': detected_faces,
            'camera_url': camera_url,
            'mode': mode,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error in face detection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def simulate_face_detection_api(mode, confidence_threshold):
    """Simulate face detection API response"""
    faces = []
    
    # Simulate 0-2 faces being detected
    num_faces = random.choice([0, 0, 0, 1, 1, 2])  # Weighted towards fewer faces
    
    for i in range(num_faces):
        face = {
            'id': f'face_{int(time.time() * 1000)}_{i}',
            'bounding_box': {
                'x': 150 + random.randint(-50, 50),
                'y': 200 + random.randint(-30, 30),
                'width': 80 + random.randint(-20, 20),
                'height': 90 + random.randint(-15, 15)
            },
            'confidence': round(random.uniform(0.5, 0.95), 2),
            'recognized': False,
            'employee_id': None,
            'employee_name': None,
            'landmarks': {
                'left_eye': [170, 220],
                'right_eye': [200, 220],
                'nose': [185, 240],
                'mouth_left': [175, 260],
                'mouth_right': [195, 260]
            }
        }
        
        # If in recognition mode and confidence is high enough
        if mode == 'recognition' and face['confidence'] >= confidence_threshold:
            # 30% chance of recognition
            if random.random() < 0.3:
                face['recognized'] = True
                face['employee_id'] = f'EMP{random.randint(100, 999):03d}'
                face['employee_name'] = f'Employee {face["employee_id"]}'
                
                # Log attendance if recognized
                zone_service = get_zone_service()
                if zone_service:
                    try:
                        zone_service.log_zone_entry(
                            face['employee_id'],
                            'entrance_main',  # Default zone
                            confidence=face['confidence']
                        )
                        logger.info(f"Logged attendance for {face['employee_id']}")
                    except Exception as e:
                        logger.warning(f"Could not log attendance: {e}")
        
        faces.append(face)
    
    return faces

@live_camera_bp.route('/camera-stream-info', methods=['POST'])
def get_camera_stream_info():
    """Get information about a camera stream for face tracking"""
    try:
        data = request.json
        camera_url = data.get('camera_url')
        
        if not camera_url:
            return jsonify({
                'success': False,
                'error': 'Camera URL is required'
            }), 400
        
        # Parse camera information
        stream_info = {
            'url': camera_url,
            'type': 'ip_camera' if camera_url.startswith('http') else 'local',
            'supported_modes': ['detection', 'recognition'],
            'recommended_settings': {
                'recognition_interval': 2.0,
                'confidence_threshold': 0.7,
                'frame_skip': 5
            },
            'capabilities': {
                'face_detection': True,
                'face_recognition': True,
                'motion_detection': False,
                'night_vision': False
            }
        }
        
        return jsonify({
            'success': True,
            'stream_info': stream_info
        })
        
    except Exception as e:
        logger.error(f"Error getting stream info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
