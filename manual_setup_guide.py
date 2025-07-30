#!/usr/bin/env python3
"""
Manual Face Recognition Setup Guide
"""

import webbrowser
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Manual setup guide"""
    
    logger.info("🎯 MANUAL FACE RECOGNITION SETUP")
    logger.info("=" * 40)
    
    logger.info("❗ Since API calls are timing out, let's set up manually:")
    logger.info("")
    
    # Step 1: Open cameras page
    logger.info("📱 STEP 1: Opening cameras page...")
    try:
        webbrowser.open("https://localhost:5003/admin/cameras")
        logger.info("✅ Cameras page opened")
    except:
        logger.info("🔗 Please open: https://localhost:5003/admin/cameras")
    
    logger.info("")
    logger.info("📋 STEP 2: ADD A CAMERA MANUALLY")
    logger.info("   1. Click the 'Add Live Camera' button")
    logger.info("   2. Fill in the form:")
    logger.info("      📝 Camera ID: webcam_main")
    logger.info("      📝 Name: Main Webcam")
    logger.info("      📝 Stream URL: 0")
    logger.info("      📝 Zone: Main Entrance")
    logger.info("      ☑️ Enable: Checked")
    logger.info("   3. Click 'Add Camera'")
    logger.info("   4. Wait for success message")
    
    logger.info("")
    logger.info("📋 STEP 3: START THE CAMERA")
    logger.info("   1. Look for your camera in the list")
    logger.info("   2. Click the 'Start' button next to it")
    logger.info("   3. Status should change to 'Running'")
    
    logger.info("")
    logger.info("📋 STEP 4: ENROLL FACES")
    logger.info("   1. Open: https://localhost:5003/admin/enrollment")
    logger.info("   2. Click 'Enroll New Face'")
    logger.info("   3. Enter employee ID (e.g., EMP001)")
    logger.info("   4. Take photos from different angles")
    logger.info("   5. Save enrollment")
    
    logger.info("")
    logger.info("📋 STEP 5: TEST RECOGNITION")
    logger.info("   1. Open: https://localhost:5003/admin/present-today")
    logger.info("   2. Stand in front of camera")
    logger.info("   3. Check for recognition results")
    
    logger.info("")
    logger.info("🔗 IMPORTANT LINKS:")
    logger.info("   📹 Cameras: https://localhost:5003/admin/cameras")
    logger.info("   👥 Enrollment: https://localhost:5003/admin/enrollment")
    logger.info("   📊 Present Today: https://localhost:5003/admin/present-today")
    
    logger.info("")
    logger.info("⚡ TROUBLESHOOTING:")
    logger.info("   • If camera doesn't start:")
    logger.info("     - Check if webcam is used by other apps")
    logger.info("     - Try different stream URLs: 0, 1, 2")
    logger.info("     - Refresh the page and try again")
    logger.info("")
    logger.info("   • If face recognition doesn't work:")
    logger.info("     - Make sure camera is 'Running'")
    logger.info("     - Ensure faces are enrolled")
    logger.info("     - Good lighting is important")
    logger.info("     - Stand 2-3 feet from camera")
    
    logger.info("")
    logger.info("✅ Follow these steps manually to get face recognition working!")
    
    # Open additional pages
    time.sleep(3)
    logger.info("📱 Opening additional pages...")
    
    try:
        webbrowser.open("https://localhost:5003/admin/enrollment")
        logger.info("✅ Enrollment page opened")
    except:
        logger.info("🔗 Please open: https://localhost:5003/admin/enrollment")
    
    time.sleep(2)
    
    try:
        webbrowser.open("https://localhost:5003/admin/present-today")
        logger.info("✅ Present Today page opened")
    except:
        logger.info("🔗 Please open: https://localhost:5003/admin/present-today")

if __name__ == "__main__":
    main()
