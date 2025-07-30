#!/usr/bin/env python3
"""
Start Existing IP Cameras for Face Recognition
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

def start_camera(camera_id):
    """Start a specific camera"""
    logger.info(f"🎯 Starting camera: {camera_id}")
    try:
        response = requests.post(
            f"{API_BASE}/cameras/{camera_id}/start",
            verify=False,
            timeout=10
        )
        
        logger.info(f"Response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Camera {camera_id} started successfully!")
                return True
            else:
                logger.error(f"❌ Failed to start {camera_id}: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error starting {camera_id}: {e}")
        return False

def main():
    """Start all IP cameras"""
    logger.info("🚀 Starting IP Cameras for Face Recognition")
    
    # List of cameras that were added from the direct test
    cameras_to_start = [
        "ip_camera_direct",
        "ip_camera_alt_1", 
        "ip_camera_alt_2",
        "ip_camera_alt_3",
        "ip_camera_alt_4",
        "ip_camera_alt_5"
    ]
    
    logger.info(f"📹 Found {len(cameras_to_start)} cameras to start")
    
    started_cameras = []
    
    for camera_id in cameras_to_start:
        if start_camera(camera_id):
            started_cameras.append(camera_id)
            time.sleep(2)  # Wait between starts
    
    logger.info(f"✅ Successfully started {len(started_cameras)} cameras!")
    
    if started_cameras:
        logger.info("🎯 Cameras now running:")
        for camera_id in started_cameras:
            logger.info(f"   - {camera_id}")
        
        logger.info("")
        logger.info("🔗 Open these links to test:")
        logger.info("   📹 Cameras: https://localhost:5003/admin/cameras")
        logger.info("   📊 Present Today: https://localhost:5003/admin/present-today")
        logger.info("   👥 Enrollment: https://localhost:5003/admin/enrollment")
        
        logger.info("")
        logger.info("🎯 Face recognition is now active!")
        logger.info("💡 Make sure you have enrolled faces before testing recognition")
    else:
        logger.error("❌ No cameras could be started")
        logger.info("💡 Try adding a local webcam with stream_url '0' as backup")

if __name__ == "__main__":
    main()
