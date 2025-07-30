#!/usr/bin/env python3
"""
Camera Stream Discovery Tool
Finds the direct video stream URL for web-based cameras
"""

import requests
import time
from urllib.parse import urljoin

def discover_camera_streams(base_url):
    """Discover video stream endpoints for a camera"""
    
    print(f"🔍 Discovering streams for: {base_url}")
    
    # Common video stream endpoints
    endpoints = [
        '/mjpeg',
        '/video.cgi',
        '/videostream.cgi',
        '/snapshot.cgi',
        '/image.jpg',
        '/webcam.jpg',
        '/cam.jpg',
        '/camera.jpg',
        '/live.jpg',
        '/capture.jpg',
        '/axis-cgi/mjpg/video.cgi',
        '/cgi-bin/video.cgi',
        '/cgi-bin/snapshot.cgi',
        '/streaming/channels/1/preview',
        '/ISAPI/Streaming/channels/1/preview',
        '/cam/realmonitor?channel=1&subtype=0',
        '/h264Preview_01_main',
        '/jpg/image.jpg',
        '/webcapture.jpg?command=snap&channel=1'
    ]
    
    working_streams = []
    
    for endpoint in endpoints:
        try:
            full_url = urljoin(base_url, endpoint)
            print(f"Testing: {full_url}")
            
            # Test with a quick HEAD request first
            response = requests.head(full_url, timeout=5, allow_redirects=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'image' in content_type or 'video' in content_type or 'mjpeg' in content_type:
                    working_streams.append({
                        'url': full_url,
                        'endpoint': endpoint,
                        'content_type': content_type,
                        'status': response.status_code
                    })
                    print(f"✅ Found stream: {full_url} ({content_type})")
                
        except Exception as e:
            print(f"❌ Failed {endpoint}: {e}")
            continue
    
    return working_streams

def test_camera_url(base_url):
    """Test your specific camera URL"""
    
    print("🎥 Testing Camera Stream Discovery")
    print("=" * 50)
    
    streams = discover_camera_streams(base_url)
    
    if streams:
        print(f"\n🎉 Found {len(streams)} working stream(s):")
        print("-" * 40)
        
        for i, stream in enumerate(streams, 1):
            print(f"{i}. {stream['url']}")
            print(f"   Content-Type: {stream['content_type']}")
            print(f"   Status: {stream['status']}")
            print()
            
        print("💡 Recommended URLs to use in the attendance system:")
        for stream in streams:
            if 'mjpeg' in stream['content_type'] or 'video' in stream['content_type']:
                print(f"🎯 {stream['url']} (Best for live streaming)")
            elif 'image' in stream['content_type']:
                print(f"📸 {stream['url']} (Good for snapshots)")
    else:
        print("❌ No video streams found")
        print("\n💡 Suggestions:")
        print("1. Check if camera requires authentication")
        print("2. Try accessing camera web interface first")
        print("3. Check camera documentation for stream URLs")
        print("4. Camera might use RTSP instead of HTTP")

if __name__ == "__main__":
    # Test your camera
    camera_ip = "155.235.81.65"
    base_url = f"http://{camera_ip}"
    
    test_camera_url(base_url)
    
    print("\n" + "=" * 50)
    print("🔧 Next Steps:")
    print("1. Use any working URL in the camera management UI")
    print("2. Go to /admin/cameras in your attendance app") 
    print("3. Add new camera with the discovered stream URL")
    print("4. Test the connection using the UI's test feature")
