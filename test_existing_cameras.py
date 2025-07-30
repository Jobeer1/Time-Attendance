#!/usr/bin/env python3
"""
Test Face Recognition with Existing Cameras
"""

import requests
import json
import time
import logging
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://localhost:5003"
API_BASE = f"{BASE_URL}/api/live-camera"

def test_camera_status():
    """Test getting camera status"""
    logger.info("📊 Testing system status...")
    try:
        response = requests.get(
            f"{API_BASE}/status",
            verify=False,
            timeout=15
        )
        
        logger.info(f"Status response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ System status received")
            logger.info(f"   Face Recognition: {result.get('status', {}).get('face_recognition_enabled')}")
            logger.info(f"   Total Cameras: {result.get('status', {}).get('total_cameras')}")
            logger.info(f"   Active Cameras: {result.get('status', {}).get('active_cameras')}")
            logger.info(f"   Zone Service: {result.get('status', {}).get('zone_service_available')}")
            logger.info(f"   Enrollment Service: {result.get('status', {}).get('enrollment_service_available')}")
            
            # Show camera details
            cameras = result.get('cameras', {})
            if cameras:
                logger.info(f"📹 Found {len(cameras)} cameras:")
                for camera_id, camera_info in cameras.items():
                    logger.info(f"   - {camera_id}: {camera_info.get('name', 'Unknown')} ({camera_info.get('stream_url', 'No URL')})")
                    logger.info(f"     Status: {'Running' if camera_info.get('running') else 'Stopped'}")
                    logger.info(f"     Zone: {camera_info.get('zone_id', 'Unknown')}")
            else:
                logger.info("📹 No cameras found in system")
            
            return True, cameras
        else:
            logger.error(f"❌ Status check failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False, {}
            
    except Exception as e:
        logger.error(f"❌ Error checking status: {e}")
        return False, {}

def test_start_camera(camera_id):
    """Test starting a specific camera"""
    logger.info(f"🎯 Testing camera start for: {camera_id}")
    try:
        response = requests.post(
            f"{API_BASE}/cameras/{camera_id}/start",
            verify=False,
            timeout=15
        )
        
        logger.info(f"Start response: {response.status_code}")
        logger.info(f"Start content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Camera {camera_id} started: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Failed to start camera {camera_id}: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ Start failed for {camera_id}: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error starting camera {camera_id}: {e}")
        return False

def add_webcam_camera():
    """Add a local webcam camera"""
    logger.info("📹 Adding local webcam camera...")
    
    camera_data = {
        "camera_id": "local_webcam",
        "name": "Local Webcam",
        "stream_url": "0",  # Default webcam
        "zone_id": "entrance_main",
        "enabled": True,
        "recognition_interval": 2.0,
        "confidence_threshold": 0.7,
        "frame_skip": 3
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/cameras",
            json=camera_data,
            verify=False,
            timeout=15
        )
        
        logger.info(f"Add camera response: {response.status_code}")
        logger.info(f"Add camera content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Local webcam added successfully!")
                return True
            else:
                logger.error(f"❌ Failed to add local webcam: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ Add camera failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding local webcam: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting Face Recognition Test with Existing Cameras")
    
    # Test 1: Check system status and get existing cameras
    logger.info("📊 Checking system status...")
    status_ok, cameras = test_camera_status()
    
    if not status_ok:
        logger.error("❌ System status check failed")
        return
    
    # Test 2: Add local webcam if no cameras exist
    if not cameras:
        logger.info("📹 No cameras found, adding local webcam...")
        if add_webcam_camera():
            # Check status again to get the new camera
            status_ok, cameras = test_camera_status()
    
    # Test 3: Start all cameras
    if cameras:
        logger.info("🎯 Starting all cameras...")
        for camera_id, camera_info in cameras.items():
            if not camera_info.get('running'):
                logger.info(f"🔄 Starting camera: {camera_id}")
                test_start_camera(camera_id)
            else:
                logger.info(f"✅ Camera {camera_id} is already running")
    
    # Test 4: Final status check
    logger.info("📊 Final status check...")
    status_ok, cameras = test_camera_status()
    
    if cameras:
        running_cameras = [cid for cid, cinfo in cameras.items() if cinfo.get('running')]
        logger.info(f"✅ {len(running_cameras)} cameras are now running!")
        logger.info("🎯 Open https://localhost:5003/admin/cameras to see live recognition")
        logger.info("🎯 The system is ready for face recognition!")
    else:
        logger.error("❌ No cameras are running")

if __name__ == "__main__":
    main()
