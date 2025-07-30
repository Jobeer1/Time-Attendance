#!/usr/bin/env python3
"""
Test Face Recognition with Web Camera
"""

import requests
import json
import time
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://localhost:5003"
API_BASE = f"{BASE_URL}/api/live-camera"

def test_stream_url_validation():
    """Test stream URL validation endpoint"""
    test_urls = [
        "0",  # Webcam index
        "1",  # Another webcam index
        "http://192.168.1.100:8080/video",  # IP camera
        "rtsp://192.168.1.100:554/stream",  # RTSP stream
        "invalid_url"  # Invalid URL
    ]
    
    logger.info("🔍 Testing stream URL validation...")
    
    for url in test_urls:
        try:
            response = requests.post(
                f"{API_BASE}/test-stream",
                json={"stream_url": url},
                verify=False,
                timeout=10
            )
            
            logger.info(f"Stream URL '{url}': Status {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                logger.info(f"  ✅ Validation result: {result}")
            else:
                logger.error(f"  ❌ Validation failed: {response.text}")
                
        except Exception as e:
            logger.error(f"  ❌ Error testing '{url}': {e}")

def test_add_webcam():
    """Test adding a web camera for face recognition"""
    
    # Test camera configuration
    camera_data = {
        "camera_id": "webcam_test_01",
        "name": "Test Webcam",
        "stream_url": "0",  # Default webcam
        "zone_id": "entrance_main",
        "enabled": True,
        "recognition_interval": 2.0,
        "confidence_threshold": 0.6,
        "frame_skip": 3
    }
    
    logger.info("📹 Testing live camera save...")
    logger.info(f"Camera data to submit: {json.dumps(camera_data, indent=2)}")
    
    try:
        # Add camera with detailed logging
        logger.info(f"🔗 Making POST request to: {API_BASE}/cameras")
        response = requests.post(
            f"{API_BASE}/cameras",
            json=camera_data,
            verify=False,  # Skip SSL verification for localhost
            timeout=30
        )
        
        logger.info(f"📊 Response status: {response.status_code}")
        logger.info(f"📊 Response headers: {dict(response.headers)}")
        logger.info(f"📊 Response content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Camera added successfully!")
                logger.info(f"   Message: {result.get('message')}")
                logger.info(f"   Camera ID: {result.get('camera_id')}")
                return True
            else:
                logger.error(f"❌ API returned success=false")
                logger.error(f"   Error: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                logger.error(f"   Error details: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"   Raw error response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(f"   Exception type: {type(e)}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return False

def test_camera_status():
    """Test getting camera status"""
    logger.info("📊 Testing system status...")
    try:
        response = requests.get(
            f"{API_BASE}/status",
            verify=False,
            timeout=10
        )
        
        logger.info(f"Status response: {response.status_code}")
        logger.info(f"Status content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ System status received")
            logger.info(f"   Face Recognition: {result.get('status', {}).get('face_recognition_enabled')}")
            logger.info(f"   Total Cameras: {result.get('status', {}).get('total_cameras')}")
            logger.info(f"   Active Cameras: {result.get('status', {}).get('active_cameras')}")
            logger.info(f"   Zone Service: {result.get('status', {}).get('zone_service_available')}")
            logger.info(f"   Enrollment Service: {result.get('status', {}).get('enrollment_service_available')}")
            return True
        else:
            logger.error(f"❌ Status check failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking status: {e}")
        return False

def test_start_camera():
    """Test starting camera recognition"""
    logger.info("🎯 Testing camera start...")
    try:
        response = requests.post(
            f"{API_BASE}/cameras/webcam_test_01/start",
            verify=False,
            timeout=10
        )
        
        logger.info(f"Start response: {response.status_code}")
        logger.info(f"Start content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ Camera started: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Failed to start camera: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ Start failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error starting camera: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting Face Recognition Test")
    
    # Test 0: Stream URL validation
    logger.info("🔍 Testing stream URL validation...")
    test_stream_url_validation()
    
    # Test 1: Check system status
    logger.info("📊 Testing system status...")
    if not test_camera_status():
        logger.error("❌ System status check failed")
        return
    
    # Test 2: Add webcam
    logger.info("📹 Testing camera addition...")
    if not test_add_webcam():
        logger.error("❌ Camera addition failed")
        return
    
    # Test 3: Start camera recognition
    logger.info("🎯 Testing camera start...")
    if not test_start_camera():
        logger.error("❌ Camera start failed")
        return
    
    logger.info("✅ All tests passed! Face recognition should now be working.")
    logger.info("🎯 Open the cameras page to see live recognition results.")
    
    # Test 4: Monitor for a few seconds
    logger.info("👀 Monitoring system for 10 seconds...")
    for i in range(10):
        time.sleep(1)
        logger.info(f"   {i+1}/10 seconds...")
    
    # Test 5: Final status check
    logger.info("📊 Final status check...")
    test_camera_status()

if __name__ == "__main__":
    main()
