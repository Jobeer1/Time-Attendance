"""
Advanced Enrollment and CCTV Management Routes
Handles API endpoints for multi-angle enrollment and zone-based attendance
"""

from flask import Blueprint, request, jsonify, render_template, session
from typing import Dict, Any, List
import logging
import time
from datetime import datetime

# Import services
from ..services.advanced_enrollment import AdvancedEnrollmentService
from ..services.zone_attendance import ZoneAttendanceService
from ..services.cctv_integration import CCTVIntegrationService
from ..services.database import DatabaseService
from ..models.employee import Employee
from ..models.attendance import AttendanceRecord

# Create blueprint
advanced_bp = Blueprint('advanced', __name__, url_prefix='/api/advanced')

# Initialize services (will be properly injected by the main app)
enrollment_service = None
zone_service = None
cctv_service = None
db_service = None

logger = logging.getLogger(__name__)

def init_advanced_services(database_service: DatabaseService):
    """Initialize advanced services with database"""
    global enrollment_service, zone_service, cctv_service, db_service
    
    db_service = database_service
    enrollment_service = AdvancedEnrollmentService()
    zone_service = ZoneAttendanceService(db_service, enrollment_service)
    cctv_service = CCTVIntegrationService(db_service, enrollment_service, zone_service)
    
    logger.info("Advanced services initialized")

@advanced_bp.route('/enrollment/start', methods=['POST'])
def start_enrollment():
    """Start advanced multi-angle enrollment session"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        
        if not employee_id or not employee_name:
            return jsonify({'error': 'Employee ID and name are required'}), 400
        
        # Check if employee exists
        employees = db_service.find_all(Employee)
        employee = next((e for e in employees if e.employee_id == employee_id), None)
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Start enrollment session
        session_id = cctv_service.start_enrollment_session(employee_id, employee_name)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'employee_id': employee_id,
            'employee_name': employee_name,
            'message': 'Enrollment session started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting enrollment: {e}")
        return jsonify({'error': 'Failed to start enrollment session'}), 500

@advanced_bp.route('/enrollment/process', methods=['POST'])
def process_enrollment():
    """Process enrollment frame from camera"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        camera_id = data.get('camera_id', 'camera_01')
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Process enrollment frame
        result = cctv_service.process_enrollment_frame(camera_id, session_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing enrollment: {e}")
        return jsonify({'error': 'Failed to process enrollment frame'}), 500

@advanced_bp.route('/enrollment/status/<session_id>')
def get_enrollment_status(session_id):
    """Get enrollment session status"""
    try:
        # Get session info from enrollment service
        if session_id not in enrollment_service.enrollment_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_info = enrollment_service.enrollment_sessions[session_id]
        employee_id = session_info['employee_id']
        
        # Get employee profile
        profile = enrollment_service.employee_profiles.get(employee_id)
        
        if not profile:
            return jsonify({'error': 'Employee profile not found'}), 404
        
        # Calculate detailed progress
        captures = profile.captures
        progress_details = {
            'total_captures': len(captures),
            'min_required': profile.min_captures_required,
            'enrollment_complete': profile.enrollment_complete,
            'angle_coverage': len(set(c.angle for c in captures)),
            'lighting_coverage': len(set(c.lighting for c in captures)),
            'distance_coverage': len(set(c.distance for c in captures)),
            'expression_coverage': len(set(c.expression for c in captures)),
            'quality_scores': [c.quality_score for c in captures[-5:]] if captures else []
        }
        
        return jsonify({
            'session_id': session_id,
            'employee_id': employee_id,
            'employee_name': profile.name,
            'progress': progress_details,
            'current_phase': session_info.get('current_phase', 'unknown'),
            'instructions': session_info.get('instructions', ''),
            'captures_completed': len(captures)
        })
        
    except Exception as e:
        logger.error(f"Error getting enrollment status: {e}")
        return jsonify({'error': 'Failed to get enrollment status'}), 500

@advanced_bp.route('/zones/status')
def get_zone_status():
    """Get current status of all zones"""
    try:
        zone_overview = cctv_service.get_zone_overview()
        return jsonify(zone_overview)
        
    except Exception as e:
        logger.error(f"Error getting zone status: {e}")
        return jsonify({'error': 'Failed to get zone status'}), 500

@advanced_bp.route('/zones/configure', methods=['POST'])
def configure_zones():
    """Configure zones for cameras"""
    try:
        data = request.get_json()
        camera_config = data.get('camera_config', {})
        
        if not camera_config:
            return jsonify({'error': 'Camera configuration is required'}), 400
        
        # Configure zones
        zone_service.configure_zones_for_cameras(camera_config)
        
        return jsonify({
            'success': True,
            'message': f'Configured zones for {len(camera_config)} cameras'
        })
        
    except Exception as e:
        logger.error(f"Error configuring zones: {e}")
        return jsonify({'error': 'Failed to configure zones'}), 500

@advanced_bp.route('/cameras/status')
def get_camera_status():
    """Get status of all cameras"""
    try:
        camera_stats = cctv_service.get_camera_stats()
        detection_stats = cctv_service.get_detection_stats()
        
        return jsonify({
            'cameras': camera_stats,
            'detection': detection_stats,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        return jsonify({'error': 'Failed to get camera status'}), 500

@advanced_bp.route('/cameras/start', methods=['POST'])
def start_camera_monitoring():
    """Start CCTV monitoring system"""
    try:
        cctv_service.start_camera_monitoring()
        return jsonify({
            'success': True,
            'message': 'CCTV monitoring started',
            'active_cameras': len([c for c in cctv_service.camera_stats.values() if c.get('connected', False)])
        })
    except Exception as e:
        logger.error(f"Error starting camera monitoring: {e}")
        return jsonify({'error': 'Failed to start camera monitoring'}), 500

@advanced_bp.route('/cameras/stop', methods=['POST'])
def stop_camera_monitoring():
    """Stop CCTV monitoring system"""
    try:
        cctv_service.stop_camera_monitoring()
        return jsonify({
            'success': True,
            'message': 'CCTV monitoring stopped'
        })
    except Exception as e:
        logger.error(f"Error stopping camera monitoring: {e}")
        return jsonify({'error': 'Failed to stop camera monitoring'}), 500

@advanced_bp.route('/cameras/stream/<camera_id>')
def camera_stream(camera_id):
    """Get live stream from specific camera"""
    try:
        # Get frame from camera
        frame = cctv_service.get_live_frame(camera_id)
        
        if frame is None:
            return jsonify({'error': 'Camera not available'}), 404
        
        # Convert frame to base64 for web display
        import cv2
        import base64
        
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'camera_id': camera_id,
            'frame': f"data:image/jpeg;base64,{frame_base64}",
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error getting camera stream: {e}")
        return jsonify({'error': 'Failed to get camera stream'}), 500

@advanced_bp.route('/settings/threshold', methods=['POST'])
def update_detection_threshold():
    """Update face detection threshold"""
    try:
        data = request.get_json()
        threshold = data.get('threshold', 0.6)
        
        # Update threshold in services
        cctv_service.min_confidence_threshold = threshold
        if face_service:
            face_service.confidence_threshold = threshold
        
        return jsonify({
            'success': True,
            'threshold': threshold,
            'message': f'Detection threshold updated to {threshold}'
        })
        
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        return jsonify({'error': 'Failed to update threshold'}), 500

@advanced_bp.route('/settings/interval', methods=['POST'])
def update_detection_interval():
    """Update detection processing interval"""
    try:
        data = request.get_json()
        interval = data.get('interval', 2)
        
        # Update interval in CCTV service
        cctv_service.detection_interval = interval
        
        return jsonify({
            'success': True,
            'interval': interval,
            'message': f'Detection interval updated to {interval} seconds'
        })
        
    except Exception as e:
        logger.error(f"Error updating interval: {e}")
        return jsonify({'error': 'Failed to update interval'}), 500

@advanced_bp.route('/export/detection_data')
def export_detection_data():
    """Export detection data for analysis"""
    try:
        hours = request.args.get('hours', 24, type=int)
        data = cctv_service.export_detection_data(hours)
        
        return jsonify({
            'success': True,
            'data': data,
            'export_timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error exporting detection data: {e}")
        return jsonify({'error': 'Failed to export data'}), 500

# Template routes for admin interface
@advanced_bp.route('/dashboard')
def advanced_dashboard():
    """Advanced system dashboard"""
    return render_template('advanced/dashboard.html')

@advanced_bp.route('/enrollment')
def enrollment_interface():
    """Employee enrollment interface"""
    return render_template('advanced/enrollment.html')

@advanced_bp.route('/zones')
def zone_management():
    """Zone management interface"""
    return render_template('advanced/zones.html')

@advanced_bp.route('/cameras')
def camera_management():
    """Camera management interface"""
    return render_template('advanced/cameras.html')

# Error handlers
@advanced_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@advanced_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
