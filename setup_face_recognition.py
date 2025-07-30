#!/usr/bin/env python3
"""
Quick Camera Test with Web Interface
"""

import webbrowser
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to guide user through manual camera setup"""
    
    logger.info("🚀 Face Recognition Setup Guide")
    logger.info("=" * 50)
    
    # Step 1: Open the cameras page
    logger.info("📱 Step 1: Opening cameras management page...")
    camera_url = "https://localhost:5003/admin/cameras"
    
    try:
        webbrowser.open(camera_url)
        logger.info(f"✅ Opened: {camera_url}")
    except Exception as e:
        logger.error(f"❌ Could not open browser: {e}")
        logger.info(f"🔗 Please manually open: {camera_url}")
    
    logger.info("")
    logger.info("📋 Manual Setup Steps:")
    logger.info("=" * 30)
    
    # Step 2: Add IP Camera
    logger.info("🎯 Step 2: Add IP Camera")
    logger.info("   1. Click 'Add Live Camera' button")
    logger.info("   2. Fill in the form:")
    logger.info("      - Camera ID: ip_camera_main")
    logger.info("      - Name: Main IP Camera")
    logger.info("      - Stream URL: http://155.235.81.65/webcamera.html")
    logger.info("      - Zone: Main Entrance")
    logger.info("      - Enable: ✓ (checked)")
    logger.info("   3. Click 'Add Camera'")
    
    logger.info("")
    
    # Step 3: Add Local Webcam
    logger.info("🎯 Step 3: Add Local Webcam (backup)")
    logger.info("   1. Click 'Add Live Camera' button again")
    logger.info("   2. Fill in the form:")
    logger.info("      - Camera ID: local_webcam")
    logger.info("      - Name: Local Webcam")
    logger.info("      - Stream URL: 0")
    logger.info("      - Zone: Main Entrance")
    logger.info("      - Enable: ✓ (checked)")
    logger.info("   3. Click 'Add Camera'")
    
    logger.info("")
    
    # Step 4: Start cameras
    logger.info("🎯 Step 4: Start Cameras")
    logger.info("   1. Look for your cameras in the list")
    logger.info("   2. Click the 'Start' button for each camera")
    logger.info("   3. Watch for the status to change to 'Running'")
    
    logger.info("")
    
    # Step 5: Test recognition
    logger.info("🎯 Step 5: Test Face Recognition")
    logger.info("   1. Make sure you have enrolled faces in the system")
    logger.info("   2. Stand in front of the camera")
    logger.info("   3. Check the 'Present Today' page for recognition results")
    
    logger.info("")
    logger.info("🔗 Important Links:")
    logger.info(f"   📹 Cameras: https://localhost:5003/admin/cameras")
    logger.info(f"   👥 Enrollment: https://localhost:5003/admin/enrollment")
    logger.info(f"   📊 Present Today: https://localhost:5003/admin/present-today")
    logger.info(f"   🏠 Admin Dashboard: https://localhost:5003/admin")
    
    logger.info("")
    logger.info("⚡ Troubleshooting:")
    logger.info("   - If IP camera doesn't work, use local webcam (stream_url: 0)")
    logger.info("   - If validation fails, the camera might still work")
    logger.info("   - Check the browser console for any JavaScript errors")
    logger.info("   - Make sure your webcam is not being used by other applications")
    
    logger.info("")
    logger.info("✅ Setup guide complete!")
    logger.info("🎯 The system should now be ready for face recognition!")

if __name__ == "__main__":
    main()
