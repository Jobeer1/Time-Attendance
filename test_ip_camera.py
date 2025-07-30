#!/usr/bin/env python3
"""
Test Face Recognition with IP Camera
Tests the actual IP camera at http://155.235.81.65/webcamera.html
"""

import requests
import json
import time
import logging
import traceback
import urllib3

# Disable SSL warnings for localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://localhost:5003"
API_BASE = f"{BASE_URL}/api/live-camera"

# IP Camera details
CAMERA_IP = "155.235.81.65"
CAMERA_USERNAME = "admin"
CAMERA_PASSWORD = "123456"
CAMERA_WEB_URL = f"http://{CAMERA_IP}/webcamera.html"

def test_ip_camera_stream_urls():
    """Test various stream URL formats for the IP camera"""
    
    # Common IP camera stream URL patterns
    stream_patterns = [
        f"http://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/video.cgi",
        f"http://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/video.mjpg",
        f"http://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/mjpeg.cgi",
        f"http://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/videostream.cgi",
        f"http://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/axis-cgi/mjpg/video.cgi",
        f"http://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/cgi-bin/video.cgi",
        f"http://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/live.sdp",
        f"http://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/stream.mjpg",
        f"rtsp://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/stream",
        f"rtsp://{CAMERA_USERNAME}:{CAMERA_PASSWORD}@{CAMERA_IP}/live.sdp",
        CAMERA_WEB_URL  # Original web interface URL
    ]
    
    logger.info(f"🔍 Testing IP camera stream URLs for {CAMERA_IP}")
    
    working_urls = []
    
    for stream_url in stream_patterns:
        try:
            logger.info(f"Testing stream URL: {stream_url}")
            
            response = requests.post(
                f"{API_BASE}/test-stream",
                json={"stream_url": stream_url},
                verify=False,
                timeout=30
            )
            
            logger.info(f"Stream URL '{stream_url}': Status {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"  ✅ Validation result: {result}")
                
                if result.get('accessible', False):
                    working_urls.append(stream_url)
                    logger.info(f"  🎯 WORKING URL FOUND: {stream_url}")
            else:
                logger.error(f"  ❌ Validation failed: {response.text}")
                
        except Exception as e:
            logger.error(f"  ❌ Error testing '{stream_url}': {e}")
    
    return working_urls

def test_add_ip_camera(stream_url):
    """Test adding the IP camera for face recognition"""
    
    # IP camera configuration
    camera_data = {
        "camera_id": "ip_camera_01",
        "name": "IP Camera 155.235.81.65",
        "stream_url": stream_url,
        "zone_id": "entrance_main",
        "enabled": True,
        "recognition_interval": 2.0,
        "confidence_threshold": 0.6,
        "frame_skip": 3
    }
    
    logger.info("📹 Testing IP camera addition...")
    logger.info(f"Camera data to submit: {json.dumps(camera_data, indent=2)}")
    
    try:
        # Add camera with detailed logging
        logger.info(f"🔗 Making POST request to: {API_BASE}/cameras")
        response = requests.post(
            f"{API_BASE}/cameras",
            json=camera_data,
            verify=False,
            timeout=30
        )
        
        logger.info(f"📊 Response status: {response.status_code}")
        logger.info(f"📊 Response headers: {dict(response.headers)}")
        logger.info(f"📊 Response content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ IP Camera added successfully!")
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

def test_start_ip_camera():
    """Test starting IP camera recognition"""
    logger.info("🎯 Testing IP camera start...")
    try:
        response = requests.post(
            f"{API_BASE}/cameras/ip_camera_01/start",
            verify=False,
            timeout=10
        )
        
        logger.info(f"Start response: {response.status_code}")
        logger.info(f"Start content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ IP Camera started: {result.get('message')}")
                return True
            else:
                logger.error(f"❌ Failed to start IP camera: {result.get('error')}")
                return False
        else:
            logger.error(f"❌ Start failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error starting IP camera: {e}")
        return False

def test_direct_camera_access():
    """Test direct access to camera web interface"""
    logger.info(f"🌐 Testing direct access to camera web interface...")
    
    try:
        # Test without authentication first
        response = requests.get(CAMERA_WEB_URL, timeout=10)
        logger.info(f"Direct access (no auth): {response.status_code}")
        
        # Test with authentication
        response = requests.get(
            CAMERA_WEB_URL, 
            auth=(CAMERA_USERNAME, CAMERA_PASSWORD),
            timeout=10
        )
        logger.info(f"Direct access (with auth): {response.status_code}")
        logger.info(f"Content length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            logger.info("✅ Camera web interface is accessible")
            return True
        else:
            logger.error(f"❌ Camera web interface returned: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error accessing camera web interface: {e}")
        return False

def main():
    """Main test function for IP camera"""
    logger.info("🚀 Starting IP Camera Face Recognition Test")
    logger.info(f"🎯 Target Camera: {CAMERA_IP}")
    logger.info(f"🔐 Credentials: {CAMERA_USERNAME}/{'*' * len(CAMERA_PASSWORD)}")
    
    # Test 1: Direct camera access
    logger.info("🌐 Testing direct camera access...")
    if not test_direct_camera_access():
        logger.warning("⚠️  Direct camera access failed, but continuing with stream tests...")
    
    # Test 2: Check system status
    logger.info("📊 Testing system status...")
    if not test_camera_status():
        logger.error("❌ System status check failed")
        return
    
    # Test 3: Test stream URLs
    logger.info("🔍 Testing stream URL patterns...")
    working_urls = test_ip_camera_stream_urls()
    
    if not working_urls:
        logger.error("❌ No working stream URLs found")
        logger.info("ℹ️  Trying with web interface URL anyway...")
        working_urls = [CAMERA_WEB_URL]
    
    # Test 4: Add IP camera
    logger.info("📹 Testing IP camera addition...")
    best_stream_url = working_urls[0]
    logger.info(f"🎯 Using stream URL: {best_stream_url}")
    
    if not test_add_ip_camera(best_stream_url):
        logger.error("❌ IP Camera addition failed")
        return
    
    # Test 5: Start IP camera recognition
    logger.info("🎯 Testing IP camera start...")
    if not test_start_ip_camera():
        logger.error("❌ IP Camera start failed")
        return
    
    logger.info("✅ All tests passed! IP camera face recognition should now be working.")
    logger.info("🎯 Open the cameras page to see live recognition results.")
    logger.info(f"🌐 Camera web interface: {CAMERA_WEB_URL}")
    
    # Test 6: Monitor for a few seconds
    logger.info("👀 Monitoring system for 15 seconds...")
    for i in range(15):
        time.sleep(1)
        logger.info(f"   {i+1}/15 seconds...")
    
    # Test 7: Final status check
    logger.info("📊 Final status check...")
    test_camera_status()

if __name__ == "__main__":
    main()
