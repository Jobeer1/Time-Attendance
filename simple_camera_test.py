#!/usr/bin/env python3
"""
Simple Camera Test - Direct API calls with shorter timeouts
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

def quick_status_check():
    """Quick status check with short timeout"""
    logger.info("🔍 Quick status check...")
    try:
        response = requests.get(
            f"{API_BASE}/status",
            verify=False,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            total_cameras = result.get('status', {}).get('total_cameras', 0)
            active_cameras = result.get('status', {}).get('active_cameras', 0)
            cameras = result.get('cameras', {})
            
            logger.info(f"✅ Status OK - Total: {total_cameras}, Active: {active_cameras}")
            
            if cameras:
                logger.info("📹 Cameras in system:")
                for camera_id, info in cameras.items():
                    status = "Running" if info.get('running') else "Stopped"
                    logger.info(f"   - {camera_id}: {status}")
            
            return cameras
        else:
            logger.error(f"❌ Status check failed: {response.status_code}")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return {}

def add_simple_webcam():
    """Add a simple webcam with minimal settings"""
    logger.info("📹 Adding simple webcam...")
    
    camera_data = {
        "camera_id": "simple_webcam",
        "name": "Simple Webcam",
        "stream_url": "0",
        "zone_id": "entrance_main",
        "enabled": True
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/cameras",
            json=camera_data,
            verify=False,
            timeout=8
        )
        
        logger.info(f"Add response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info("✅ Simple webcam added!")
                return True
            else:
                logger.error(f"❌ Add failed: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Add error: {e}")
        return False

def start_camera_simple(camera_id):
    """Start camera with short timeout"""
    logger.info(f"🎯 Starting {camera_id}...")
    
    try:
        response = requests.post(
            f"{API_BASE}/cameras/{camera_id}/start",
            verify=False,
            timeout=8
        )
        
        logger.info(f"Start response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ {camera_id} started!")
                return True
            else:
                logger.error(f"❌ Start failed: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Start error: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Simple Camera Test")
    logger.info("=" * 30)
    
    # Step 1: Check current status
    cameras = quick_status_check()
    
    # Step 2: Add webcam if none exist
    if not cameras:
        logger.info("📹 No cameras found, adding simple webcam...")
        if add_simple_webcam():
            time.sleep(2)
            cameras = quick_status_check()
    
    # Step 3: Start cameras
    if cameras:
        logger.info("🎯 Starting cameras...")
        for camera_id, info in cameras.items():
            if not info.get('running'):
                start_camera_simple(camera_id)
                time.sleep(1)
    
    # Step 4: Final check
    logger.info("📊 Final status...")
    final_cameras = quick_status_check()
    
    running_count = sum(1 for info in final_cameras.values() if info.get('running'))
    
    if running_count > 0:
        logger.info(f"✅ SUCCESS! {running_count} cameras running")
        logger.info("🎯 Open https://localhost:5003/admin/cameras to see them")
        logger.info("🎯 Face recognition should now work!")
    else:
        logger.error("❌ No cameras are running")
        logger.info("💡 Try manually starting cameras via the web interface")

if __name__ == "__main__":
    main()
