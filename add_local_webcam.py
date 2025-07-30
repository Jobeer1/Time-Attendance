#!/usr/bin/env python3
"""
Add Local Webcam for Face Recognition
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

def add_local_webcam():
    """Add local webcam camera"""
    logger.info("📹 Adding local webcam...")
    
    camera_data = {
        "camera_id": "local_webcam_backup",
        "name": "Local Webcam Backup",
        "stream_url": "0",  # Default webcam
        "zone_id": "entrance_main",
        "enabled": True,
        "recognition_interval": 1.5,
        "confidence_threshold": 0.7,
        "frame_skip": 2
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/cameras",
            json=camera_data,
            verify=False,
            timeout=10
        )
        
        logger.info(f"Response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Local webcam added successfully!")
                return True
            else:
                logger.error(f"❌ Failed to add webcam: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding webcam: {e}")
        return False

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
    """Add and start local webcam"""
    logger.info("🚀 Setting up Local Webcam for Face Recognition")
    
    # Add local webcam
    if add_local_webcam():
        logger.info("⏳ Waiting 3 seconds for camera to initialize...")
        time.sleep(3)
        
        # Start the camera
        if start_camera("local_webcam_backup"):
            logger.info("✅ Local webcam is now running!")
            logger.info("")
            logger.info("🔗 Test the system:")
            logger.info("   📹 Cameras: https://localhost:5003/admin/cameras")
            logger.info("   📊 Present Today: https://localhost:5003/admin/present-today")
            logger.info("   👥 Enrollment: https://localhost:5003/admin/enrollment")
            logger.info("")
            logger.info("🎯 Face recognition should now work with your local webcam!")
            logger.info("💡 Make sure you have enrolled faces before testing recognition")
        else:
            logger.error("❌ Failed to start local webcam")
    else:
        logger.error("❌ Failed to add local webcam")

if __name__ == "__main__":
    main()
