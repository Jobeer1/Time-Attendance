#!/usr/bin/env python3
"""
Simple test to add IP camera bypassing validation
"""

import requests
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_add_camera_direct():
    """Test adding camera directly via web interface"""
    print("🚀 Testing direct camera addition...")
    
    # Use the web interface to add the camera
    url = "https://localhost:5003/admin/cameras"
    print(f"📱 Open this URL in your browser: {url}")
    print(f"📹 Camera URL: http://155.235.81.65/webcamera.html")
    print(f"🔐 Credentials: admin/123456")
    
    # Try to add via API with minimal validation
    try:
        response = requests.post(
            'https://localhost:5003/api/live-camera/cameras',
            json={
                'camera_id': 'ip_camera_direct',
                'name': 'IP Camera Direct',
                'stream_url': 'http://admin:123456@155.235.81.65/video.cgi',  # Direct stream URL
                'zone_id': 'entrance_main',
                'enabled': True
            },
            verify=False,
            timeout=10
        )
        
        print(f"✅ Direct stream URL test: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Try alternative stream URLs
    alternative_urls = [
        f"http://admin:123456@155.235.81.65/mjpeg.cgi",
        f"http://admin:123456@155.235.81.65/videostream.cgi",
        f"http://admin:123456@155.235.81.65/axis-cgi/mjpg/video.cgi",
        f"rtsp://admin:123456@155.235.81.65/stream1",
        f"rtsp://admin:123456@155.235.81.65/live.sdp"
    ]
    
    for i, stream_url in enumerate(alternative_urls):
        try:
            camera_id = f"ip_camera_alt_{i+1}"
            print(f"🔄 Testing alternative URL {i+1}: {stream_url}")
            
            response = requests.post(
                'https://localhost:5003/api/live-camera/cameras',
                json={
                    'camera_id': camera_id,
                    'name': f'IP Camera Alt {i+1}',
                    'stream_url': stream_url,
                    'zone_id': 'entrance_main',
                    'enabled': True
                },
                verify=False,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: {result.get('message')}")
                break  # Stop at first success
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n🎯 Manual Steps:")
    print("1. Open https://localhost:5003/admin/cameras")
    print("2. Click 'Add Live Camera'")
    print("3. Enter Camera ID: ip_camera_manual")
    print("4. Enter Name: IP Camera Manual")
    print("5. Enter Stream URL: http://155.235.81.65/webcamera.html")
    print("6. Select Zone: Main Entrance")
    print("7. Click 'Add Camera'")
    print("8. Start the camera")

if __name__ == "__main__":
    test_add_camera_direct()
