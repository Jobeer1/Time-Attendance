/* 
 * Browser Console Script for Adding Cameras
 * Copy and paste this into the browser console on the cameras page
 */

// Function to add a camera via browser console
function addCameraViaConsole() {
    console.log("🚀 Adding camera via browser console...");
    
    // Camera data
    const cameraData = {
        camera_id: "browser_webcam",
        name: "Browser Webcam",
        stream_url: "0",
        zone_id: "entrance_main",
        enabled: true
    };
    
    // Make the request
    fetch("/api/live-camera/cameras", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(cameraData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("✅ Camera added successfully!");
            console.log("Camera ID:", data.camera_id);
            location.reload(); // Refresh the page
        } else {
            console.error("❌ Failed to add camera:", data.error);
        }
    })
    .catch(error => {
        console.error("❌ Error:", error);
    });
}

// Function to start a camera
function startCameraViaConsole(cameraId) {
    console.log(`🎯 Starting camera: ${cameraId}`);
    
    fetch(`/api/live-camera/cameras/${cameraId}/start`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`✅ Camera ${cameraId} started successfully!`);
            location.reload(); // Refresh the page
        } else {
            console.error(`❌ Failed to start camera ${cameraId}:`, data.error);
        }
    })
    .catch(error => {
        console.error("❌ Error:", error);
    });
}

// Instructions
console.log("🎯 FACE RECOGNITION SETUP VIA BROWSER CONSOLE");
console.log("=" * 50);
console.log("1. Run: addCameraViaConsole()");
console.log("2. Wait for page to refresh");
console.log("3. Run: startCameraViaConsole('browser_webcam')");
console.log("4. Check if camera status changes to 'Running'");
console.log("");
console.log("💡 If the camera doesn't work, try:");
console.log("   - Close other applications using the webcam");
console.log("   - Try different stream URLs (0, 1, 2)");
console.log("   - Check browser permissions for camera access");

// Auto-run the function (comment out if you want to run manually)
// addCameraViaConsole();
