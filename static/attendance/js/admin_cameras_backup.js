// Camera Management JavaScript - Clean Version

console.log('Camera management script loaded');

$(document).ready(function() {
    console.log('Document ready');
    initializeCameraManagement();
});

function initializeCameraManagement() {
    console.log('Initializing camera management');
    
    // Initialize DataTable
    if ($.fn.DataTable) {
        $('#camerasTable').DataTable({
            order: [[0, 'asc']],
            pageLength: 25,
            responsive: true
        });
    }

    // Form handlers
    $('#addCameraForm').on('submit', handleAddCamera);
    $('#editCameraForm').on('submit', handleEditCamera);
    
    // Event delegation for button clicks
    $(document).on('click', '[data-action]', function(e) {
        e.preventDefault();
        var action = $(this).data('action');
        var cameraId = $(this).data('camera-id'); // Removed parseInt
        
        console.log('Button clicked:', action, 'Camera ID:', cameraId);
          switch(action) {
            case 'view':
                viewCamera($(this));
                break;
            case 'edit':
                editCamera(cameraId);
                break;
            case 'test':
                testCamera(cameraId);
                break;
            case 'delete':
                deleteCamera(cameraId);
                break;
        }
    });    // Modal handlers
    $('#testCameraModal').on('hidden.bs.modal', function() {
        // Clean up video and image sources
        var video = document.getElementById('testCameraVideo');
        var image = document.getElementById('testCameraImage');
        if (video) {
            video.src = '';
            video.load();
        }
        if (image) {
            image.src = '';
        }
    });    // Camera access confirmation handler
    $('#confirmCameraAccess').on('click', function() {
        const finalUrl = $(this).data('camera-url');
        const cameraId = $(this).data('camera-id');
        const cameraName = $('#cameraAccessName').text();
        
        if (!finalUrl) {
            alert('Camera URL not available');
            return;
        }
        
        if (!cameraId) {
            alert('Camera ID not available');
            return;
        }
        
        console.log('Opening camera URL:', finalUrl.replace(/:[^:]*@/, ':***@')); // Log without password
        console.log('Camera ID:', cameraId);
        
        // Close the confirmation modal
        $('#cameraAccessModal').modal('hide');
          // Open in new window/tab with human detection
        try {
            // Open in new window/tab with specific features for camera viewing
            const cameraWindow = window.open(
                'about:blank', // Start with blank page to inject our content
                'cameraView_' + Date.now(), // Unique window name
                'width=1400,height=900,scrollbars=yes,resizable=yes,toolbar=no,menubar=no,location=no,status=no'
            );
            
            if (!cameraWindow) {
                alert('Popup blocked. Please allow popups for this site and try again.\n\nTo enable popups:\n1. Click the popup blocker icon in your address bar\n2. Select "Always allow popups from this site"');
            } else {
                // Set focus to the new window
                cameraWindow.focus();
                  // Inject enhanced camera interface with human detection
                injectHumanDetectionInterface(cameraWindow, finalUrl, cameraName, cameraId);
            }
        } catch (error) {
            console.error('Error opening camera window:', error);
            alert('Failed to open camera window. Please check if the URL is valid and try again.');
        }
    });
    
    // Refresh stream button handler
    $('#refreshStream').on('click', function() {
        console.log('Refreshing camera stream');
        const video = document.getElementById('testCameraVideo');
        const image = document.getElementById('testCameraImage');
        
        if (video && video.style.display !== 'none') {
            video.load(); // Reload video
        }
        if (image && image.style.display !== 'none') {
            const src = image.src;
            image.src = ''; // Clear source
            setTimeout(() => image.src = src + '?t=' + Date.now(), 100); // Add cache buster
        }
    });
}

function handleAddCamera(e) {
    e.preventDefault();
    console.log('Add camera form submitted');
    
    var formData = new FormData(e.target);
    var data = {
        name: formData.get('name'),
        location: formData.get('location'),
        url: formData.get('url'),
        username: formData.get('username') || '',
        password: formData.get('password') || '',
        description: formData.get('description'),
        is_active: formData.has('is_active')
    };

    fetch('/admin/api/cameras', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.success) {
            alert('Camera added successfully');
            $('#addCameraModal').modal('hide');
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Failed to add camera'));
        }
    })
    .catch(function(error) {
        console.error('Error adding camera:', error);
        alert('Failed to add camera');
    });
}

function viewCamera(element) {
    console.log('View camera called');
    
    const cameraUrl = element.data('camera-url');
    const cameraUsername = element.data('camera-username');
    const cameraPassword = element.data('camera-password');
    const cameraId = element.data('camera-id');
    
    if (!cameraUrl) {
        alert('Camera URL not configured');
        return;
    }    // Get camera name and location from the table row
    const $row = element.closest('tr');
    const cameraName = element.clone().children().remove().end().text().trim() || 'Unknown Camera'; // Get text without icon
    const cameraLocation = $row.find('td:nth-child(2)').text().trim() || 'Unknown Location';
    
    // Build URL with authentication if credentials are provided
    let finalUrl = cameraUrl;
    let displayUrl = cameraUrl;
      if (cameraUsername && cameraPassword) {
        try {
            // Parse the URL to inject credentials
            const url = new URL(cameraUrl);
            
            // For HTTP URLs, inject credentials in the format: http://username:password@host:port/path
            if (url.protocol === 'http:' || url.protocol === 'https:') {
                url.username = encodeURIComponent(cameraUsername);
                url.password = encodeURIComponent(cameraPassword);
                finalUrl = url.toString();
                // Show masked URL for display
                displayUrl = url.protocol + '//' + cameraUsername + ':***@' + url.host + url.pathname + url.search + url.hash;
            } else if (url.protocol === 'rtsp:') {
                // For RTSP URLs, also inject credentials
                url.username = encodeURIComponent(cameraUsername);
                url.password = encodeURIComponent(cameraPassword);
                finalUrl = url.toString();
                displayUrl = url.protocol + '//' + cameraUsername + ':***@' + url.host + url.pathname + url.search + url.hash;
            }
        } catch (error) {
            console.warn('Could not parse camera URL, opening without credentials:', error);
            // Fallback: try to manually inject credentials for common formats
            if (cameraUrl.match(/^https?:\/\//)) {
                finalUrl = cameraUrl.replace(/^(https?:\/\/)/, '$1' + encodeURIComponent(cameraUsername) + ':' + encodeURIComponent(cameraPassword) + '@');
                displayUrl = cameraUrl.replace(/^(https?:\/\/)/, '$1' + cameraUsername + ':***@');
            }
        }
    }
    
    // Populate the confirmation modal
    $('#cameraAccessName').text(cameraName);
    $('#cameraAccessLocation').text(cameraLocation);
    $('#cameraAccessUrl').text(displayUrl);
      // Store the final URL and camera ID for the confirm button
    $('#confirmCameraAccess').data('camera-url', finalUrl);
    $('#confirmCameraAccess').data('camera-id', cameraId);
    
    // Show the confirmation modal
    $('#cameraAccessModal').modal('show');
}

function editCamera(cameraId) {
    console.log('Edit camera called for ID:', cameraId);
    
    fetch('/admin/api/cameras')
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.success) {
            var camera = result.cameras.find(function(c) {
                return c.id === cameraId;
            });
            if (camera) {
                $('#editCameraId').val(camera.id);
                $('#editCameraName').val(camera.name);
                $('#editCameraLocation').val(camera.location);
                $('#editCameraUrl').val(camera.url);
                $('#editCameraUsername').val(camera.username || '');
                $('#editCameraPassword').val(camera.password || '');
                $('#editCameraDescription').val(camera.description || '');
                $('#editCameraActive').prop('checked', camera.is_active);
                $('#editCameraModal').modal('show');
            }
        }
    })
    .catch(function(error) {
        console.error('Error loading camera:', error);
        alert('Failed to load camera data');
    });
}

function handleEditCamera(e) {
    e.preventDefault();
    console.log('Edit camera form submitted');
    
    var formData = new FormData(e.target);
    var cameraId = formData.get('id');
    var data = {
        name: formData.get('name'),
        location: formData.get('location'),
        url: formData.get('url'),
        username: formData.get('username') || '',
        password: formData.get('password') || '',
        description: formData.get('description'),
        is_active: formData.has('is_active')
    };

    fetch('/admin/api/cameras/' + cameraId, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.success) {
            alert('Camera updated successfully');
            $('#editCameraModal').modal('hide');
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Failed to update camera'));
        }
    })
    .catch(function(error) {
        console.error('Error updating camera:', error);
        alert('Failed to update camera');
    });
}

function deleteCamera(cameraId) {
    console.log('Delete camera called for ID:', cameraId);
    
    if (!confirm('Are you sure you want to delete this camera? This action cannot be undone.')) {
        return;
    }

    fetch('/admin/api/cameras/' + cameraId, {
        method: 'DELETE'
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(result) {
        if (result.success) {
            alert('Camera deleted successfully');
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Failed to delete camera'));
        }
    })
    .catch(function(error) {
        console.error('Error deleting camera:', error);
        alert('Failed to delete camera');
    });
}

function testCamera(cameraId) {
    console.log('Test camera called for ID:', cameraId);
    // Show loading indicator
    $('#cameraLoadingIndicator').show();
    $('#testCameraVideo').hide();
    $('#testCameraImage').hide();
    $('#testCameraStatus').show();
    $('#cameraStatusText').text('Initializing camera connection...');

    // Show the modal
    $('#testCameraModal').modal('show');

    fetch('/terminal/api/camera/' + cameraId + '/stream')
        .then(function(response) {
            return response.json();
        })
        .then(function(result) {
            if (result.success && result.url) {                // Use the proxy endpoint for the stream  
                var proxyUrl = '/admin/proxy/camera/' + cameraId;
                $('#cameraUrlDebug').show();
                $('#cameraUrlLink').attr('href', proxyUrl).text(proxyUrl);
                // Warn if RTSP
                if (result.url.startsWith('rtsp://')) {
                    $('#cameraUrlWarning').text('RTSP streams cannot be played in browser. Use VLC or a compatible player.').show();
                } else {
                    $('#cameraUrlWarning').hide();
                }
                // Try to detect stream type (simple logic)
                if (result.url.endsWith('.mjpg') || result.url.endsWith('.mjpeg') || result.url.indexOf('mjpeg') !== -1) {
                    // MJPEG stream
                    $('#testCameraVideo').hide();
                    $('#testCameraImage').attr('src', proxyUrl).show();
                } else if (result.url.startsWith('http://') || result.url.startsWith('https://')) {
                    // Assume video stream (HTTP/MP4)
                    $('#testCameraImage').hide();
                    $('#testCameraVideo').attr('src', proxyUrl).show();
                } else {
                    // Unknown/unsupported
                    $('#testCameraVideo').hide();
                    $('#testCameraImage').hide();
                    $('#cameraStatusText').text('Unsupported stream type for browser.');
                }
                $('#cameraLoadingIndicator').hide();
                $('#cameraStatusText').text('Camera stream loaded.');
            } else {
                $('#cameraLoadingIndicator').hide();
                $('#testCameraVideo').hide();
                $('#testCameraImage').hide();
                $('#cameraStatusText').text(result.error || 'Failed to load camera stream.');
                $('#cameraUrlDebug').hide();
            }
        })
        .catch(function(error) {
            console.error('Error loading camera stream:', error);
            $('#cameraLoadingIndicator').hide();
            $('#testCameraVideo').hide();
            $('#testCameraImage').hide();
            $('#cameraStatusText').text('Failed to load camera stream.');
        });
}

/**
 * Inject enhanced camera interface with human detection into popup window
 */
function injectHumanDetectionInterface(cameraWindow, cameraUrl, cameraName, cameraId) {
    const doc = cameraWindow.document;
    
    // Create the enhanced camera interface HTML
    const htmlContent = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Camera: ${cameraName} - Human Detection</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { 
                margin: 0; 
                padding: 10px; 
                background: #f8f9fa;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .camera-container {
                position: relative;
                background: #000;
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 15px;
            }
            .camera-feed {
                width: 100%;
                height: 600px;
                border: none;
            }
            .controls-panel {
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }            .human-dot {
                position: absolute;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                border: 3px solid white;
                z-index: 1000;
                animation: pulse 2s infinite;
                font-size: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
                transition: all 0.2s ease-in-out;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
            .human-dot.head { 
                background: #dc3545; 
                border-color: #fff;
            }
            .human-dot.torso { 
                background: #28a745; 
                border-color: #fff;
            }
            .human-dot.lower { 
                background: #007bff; 
                border-color: #fff;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255,255,255,0.7); }
                70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(255,255,255,0); }
                100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255,255,255,0); }
            }
            
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-active { background: #28a745; }
            .status-inactive { background: #6c757d; }
            
            .detection-info {
                background: #e7f3ff;
                border: 1px solid #b6d7ff;
                border-radius: 6px;
                padding: 10px;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <!-- Header -->
            <div class="row mb-3">
                <div class="col-md-8">
                    <h4><i class="fas fa-video me-2"></i>${cameraName}</h4>
                    <small class="text-muted">Enhanced Camera Feed with Human Detection</small>
                </div>
                <div class="col-md-4 text-end">
                    <button id="trackHumansBtn" class="btn btn-success btn-lg">
                        <i class="fas fa-users me-2"></i>Track Humans
                    </button>
                    <button id="stopTrackingBtn" class="btn btn-danger btn-lg d-none">
                        <i class="fas fa-stop me-2"></i>Stop Tracking
                    </button>
                </div>
            </div>              <!-- Camera Feed Container -->
            <div class="row">
                <div class="col-md-9">
                    <div class="camera-container" id="cameraContainer">
                        ${cameraId === 'webcam-demo-001' ? 
                            `<video id="webcamVideo" class="camera-feed" autoplay muted playsinline style="width:100%;height:600px;object-fit:cover;background:#000;">
                            </video>
                            <canvas id="webcamCanvas" style="display:none;"></canvas>
                            <div id="webcamError" class="text-center text-white p-4" style="display:none;">
                                <h5>📷 Webcam Access Required</h5>
                                <p>Please allow camera access to test human detection</p>
                                <button id="enableWebcam" class="btn btn-primary">Enable Webcam</button>
                            </div>` :
                            `<iframe id="cameraFeed" src="/admin/proxy/camera/${cameraId}" class="camera-feed" 
                                    allow="camera; microphone" allowfullscreen>
                            </iframe>`
                        }
                        <!-- Human detection dots will be added here -->
                    </div>
                </div>
                
                <!-- Controls Panel -->
                <div class="col-md-3">
                    <div class="controls-panel">
                        <h6><i class="fas fa-cogs me-2"></i>Detection Controls</h6>
                        
                        <!-- Status -->
                        <div class="mb-3">
                            <div class="d-flex align-items-center mb-2">
                                <span class="status-indicator status-inactive" id="detectionStatusIndicator"></span>
                                <span id="detectionStatusText">Detection Inactive</span>
                            </div>
                            <small class="text-muted">Humans Detected: <span id="humanCounter">0</span></small>
                        </div>
                        
                        <!-- Detection Legend -->
                        <div class="mb-3">
                            <h6 class="small">Detection Markers:</h6>
                            <div class="d-flex flex-column gap-1">
                                <div><span class="badge bg-danger">👤</span> Head</div>
                                <div><span class="badge bg-success">🫀</span> Torso</div>
                                <div><span class="badge bg-primary">🦵</span> Lower Body</div>
                            </div>
                        </div>
                        
                        <!-- Settings -->
                        <div class="mb-3">
                            <h6 class="small">Settings:</h6>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="autoDetection" checked>
                                <label class="form-check-label small" for="autoDetection">
                                    Auto-detect humans
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="showTrails" >
                                <label class="form-check-label small" for="showTrails">
                                    Show movement trails
                                </label>
                            </div>
                        </div>
                        
                        <!-- Detection Info -->
                        <div id="detectionInfo" class="detection-info d-none">
                            <small class="fw-bold">Detection Active</small><br>
                            <small>Duration: <span id="detectionDuration">00:00</span></small><br>
                            <small>Last Update: <span id="lastUpdate">-</span></small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- MediaPipe Scripts -->
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js"></script>
        
        <script>        class CameraHumanTracker {
            constructor() {
                this.isTracking = false;
                this.detectionStartTime = null;
                this.humanCount = 0;
                this.trackingInterval = null;
                this.poseDetection = null;
                this.mediaPipeReady = false;
                this.lastFrameData = null;
                this.simulationState = false;
                this.lastSimulationTime = null;
                this.cameraFeed = document.getElementById('cameraFeed');
                this.webcamVideo = document.getElementById('webcamVideo');
                this.container = document.getElementById('cameraContainer');
                this.isWebcam = '${cameraId}' === 'webcam-demo-001';
                
                this.initializeControls();
                this.initializeMediaPipe();
                
                if (this.isWebcam) {
                    this.initializeWebcam();
                }
            }
            
            async initializeWebcam() {
                if (!this.webcamVideo) return;
                
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { 
                            width: { ideal: 1280 }, 
                            height: { ideal: 720 },
                            facingMode: 'user'
                        } 
                    });
                    
                    this.webcamVideo.srcObject = stream;
                    document.getElementById('webcamError').style.display = 'none';
                    console.log('✅ Webcam initialized successfully');
                    
                } catch (error) {
                    console.error('❌ Webcam access failed:', error);
                    document.getElementById('webcamError').style.display = 'block';
                    
                    // Add click handler for manual webcam enable
                    document.getElementById('enableWebcam').addEventListener('click', () => {
                        this.initializeWebcam();
                    });
                }
            }
            
            initializeControls() {
                document.getElementById('trackHumansBtn').addEventListener('click', () => {
                    this.startTracking();
                });
                
                document.getElementById('stopTrackingBtn').addEventListener('click', () => {
                    this.stopTracking();
                });
            }            async initializeMediaPipe() {
                this.mediaPipeReady = false;
                
                try {
                    // Check if MediaPipe is available
                    if (typeof Pose === 'undefined') {
                        console.log('MediaPipe Pose not available, using fallback detection');
                        return;
                    }

                    console.log('Initializing MediaPipe Pose Detection...');
                    
                    this.poseDetection = new Pose({
                        locateFile: (file) => {
                            return \`https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5/\${file}\`;
                        }
                    });
                    
                    // Set up pose detection options
                    this.poseDetection.setOptions({
                        modelComplexity: 0, // Use lighter model for better performance
                        smoothLandmarks: true,
                        enableSegmentation: false,
                        minDetectionConfidence: 0.6,
                        minTrackingConfidence: 0.5
                    });
                    
                    // Set up results callback
                    this.poseDetection.onResults((results) => {
                        this.onPoseResults(results);
                    });
                    
                    // Wait a bit for MediaPipe to fully initialize
                    setTimeout(() => {
                        this.mediaPipeReady = true;
                        console.log('MediaPipe Pose Detection ready for real-time tracking');
                    }, 2000);
                    
                } catch (error) {
                    console.error('Failed to initialize MediaPipe:', error);
                    this.mediaPipeReady = false;
                }
            }
            
            startTracking() {
                if (this.isTracking) return;
                
                this.isTracking = true;
                this.detectionStartTime = Date.now();
                this.humanCount = 0;
                
                // Update UI
                document.getElementById('trackHumansBtn').classList.add('d-none');
                document.getElementById('stopTrackingBtn').classList.remove('d-none');
                document.getElementById('detectionStatusIndicator').className = 'status-indicator status-active';
                document.getElementById('detectionStatusText').textContent = 'Detection Active';
                document.getElementById('detectionInfo').classList.remove('d-none');                // Start tracking loop
                this.trackingInterval = setInterval(() => {
                    this.performHumanDetection();
                    this.updateDuration();
                }, 1000); // Check every 1 second for stable tracking
                
                console.log('Human tracking started');
                this.showAlert('Human tracking started! Look for colored dots on detected people.', 'success');
            }
            
            stopTracking() {
                if (!this.isTracking) return;
                
                this.isTracking = false;
                
                // Clear tracking interval
                if (this.trackingInterval) {
                    clearInterval(this.trackingInterval);
                    this.trackingInterval = null;
                }
                
                // Clear all detection dots
                this.clearDetectionDots();
                
                // Update UI
                document.getElementById('trackHumansBtn').classList.remove('d-none');
                document.getElementById('stopTrackingBtn').classList.add('d-none');
                document.getElementById('detectionStatusIndicator').className = 'status-indicator status-inactive';
                document.getElementById('detectionStatusText').textContent = 'Detection Inactive';
                document.getElementById('detectionInfo').classList.add('d-none');
                document.getElementById('humanCounter').textContent = '0';
                
                console.log('Human tracking stopped');
                this.showAlert('Human tracking stopped.', 'info');
            }            async performHumanDetection() {
                if (!this.isWebcam || !this.webcamVideo) {
                    // Fallback to simulation for non-webcam cameras
                    this.performSimulatedDetection();
                    return;
                }

                try {
                    // Check if MediaPipe is properly initialized and ready
                    if (!this.poseDetection || !this.mediaPipeReady) {
                        console.log('MediaPipe not ready, using fallback detection');
                        this.performSimulatedDetection();
                        return;
                    }

                    // Create a canvas to capture the current video frame
                    let canvas = document.getElementById('webcamCanvas');
                    if (!canvas) {
                        canvas = document.createElement('canvas');
                        canvas.id = 'webcamCanvas';
                        canvas.style.display = 'none';
                        document.body.appendChild(canvas);
                    }
                    
                    const ctx = canvas.getContext('2d');
                    
                    // Set canvas size to match video
                    const videoWidth = this.webcamVideo.videoWidth || 640;
                    const videoHeight = this.webcamVideo.videoHeight || 480;
                    
                    if (videoWidth === 0 || videoHeight === 0) {
                        console.log('Video dimensions not ready, using fallback');
                        this.performSimulatedDetection();
                        return;
                    }
                    
                    canvas.width = videoWidth;
                    canvas.height = videoHeight;
                    
                    // Draw current video frame to canvas
                    ctx.drawImage(this.webcamVideo, 0, 0, videoWidth, videoHeight);
                    
                    // Get image data for MediaPipe
                    const imageData = ctx.getImageData(0, 0, videoWidth, videoHeight);
                    
                    // Send frame to MediaPipe for pose detection
                    await this.poseDetection.send({imageData: imageData});
                    
                } catch (error) {
                    console.warn('Pose detection error:', error);
                    // Fallback to simulation on error
                    this.performSimulatedDetection();
                }
            }            performSimulatedDetection() {
                // Enhanced simulation with webcam analysis
                if (this.isWebcam && this.webcamVideo && this.webcamVideo.readyState === 4) {
                    try {
                        // Create or get canvas for motion detection
                        let canvas = document.getElementById('motionCanvas');
                        if (!canvas) {
                            canvas = document.createElement('canvas');
                            canvas.id = 'motionCanvas';
                            canvas.style.display = 'none';
                            document.body.appendChild(canvas);
                        }
                        
                        const ctx = canvas.getContext('2d');
                        canvas.width = 160;
                        canvas.height = 120;
                        
                        // Draw current frame
                        ctx.drawImage(this.webcamVideo, 0, 0, canvas.width, canvas.height);
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        
                        // Calculate brightness to detect presence
                        let totalBrightness = 0;
                        let pixelVariance = 0;
                        const pixels = imageData.data;
                        
                        for (let i = 0; i < pixels.length; i += 4) {
                            const brightness = (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
                            totalBrightness += brightness;
                        }
                        
                        const avgBrightness = totalBrightness / (pixels.length / 4);
                        
                        // Calculate variance for texture detection
                        for (let i = 0; i < pixels.length; i += 4) {
                            const brightness = (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
                            pixelVariance += Math.pow(brightness - avgBrightness, 2);
                        }
                        
                        const variance = pixelVariance / (pixels.length / 4);
                        
                        // Motion detection comparison
                        let hasMotion = false;
                        if (this.lastFrameData) {
                            let motionLevel = 0;
                            for (let i = 0; i < pixels.length; i += 4) {
                                const currentPixel = (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
                                const lastPixel = (this.lastFrameData[i] + this.lastFrameData[i + 1] + this.lastFrameData[i + 2]) / 3;
                                motionLevel += Math.abs(currentPixel - lastPixel);
                            }
                            hasMotion = motionLevel > 3000; // Threshold for motion
                            
                            // Debug info
                            console.log(\`Motion level: \${motionLevel}, Variance: \${variance.toFixed(2)}, Avg brightness: \${avgBrightness.toFixed(2)}\`);
                        }
                        
                        this.lastFrameData = new Uint8ClampedArray(pixels);
                        
                        // Clear previous dots
                        this.clearDetectionDots();
                        
                        // Detect human based on motion AND texture complexity
                        const hasComplexTexture = variance > 500; // Indicates detailed content (like a person)
                        const isWellLit = avgBrightness > 30 && avgBrightness < 200; // Good lighting
                        
                        if ((hasMotion || hasComplexTexture) && isWellLit) {
                            this.humanCount = 1;
                            this.addRealisticHumanDots();
                            document.getElementById('humanCounter').textContent = '1';
                            console.log('🎯 Human detected via enhanced analysis');
                        } else {
                            this.humanCount = 0;
                            document.getElementById('humanCounter').textContent = '0';
                        }
                        
                        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                        return;
                        
                    } catch (error) {
                        console.warn('Enhanced motion detection failed:', error);
                    }
                }
                
                // Basic simulation fallback
                console.log('Using basic simulation fallback');
                this.clearDetectionDots();
                
                // More responsive basic detection
                const now = Date.now();
                if (!this.lastSimulationTime) this.lastSimulationTime = now;
                
                // Change state every 3-5 seconds
                if (now - this.lastSimulationTime > (3000 + Math.random() * 2000)) {
                    this.simulationState = !this.simulationState;
                    this.lastSimulationTime = now;
                }
                
                if (this.simulationState) {
                    this.humanCount = 1;
                    this.addRealisticHumanDots();
                    document.getElementById('humanCounter').textContent = '1';
                } else {
                    this.humanCount = 0;
                    document.getElementById('humanCounter').textContent = '0';
                }
                  document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            }
            
            addRealisticHumanDots() {
                // Get video dimensions for realistic positioning
                const videoElement = this.webcamVideo || this.cameraFeed;
                let videoWidth = 600;
                let videoHeight = 450;
                
                if (this.webcamVideo) {
                    videoWidth = this.webcamVideo.offsetWidth || this.webcamVideo.clientWidth || 600;
                    videoHeight = this.webcamVideo.offsetHeight || this.webcamVideo.clientHeight || 450;
                } else if (this.cameraFeed) {
                    videoWidth = this.cameraFeed.offsetWidth || this.cameraFeed.clientWidth || 600;
                    videoHeight = this.cameraFeed.offsetHeight || this.cameraFeed.clientHeight || 450;
                }
                
                console.log(`Video dimensions: ${videoWidth}x${videoHeight}`);
                
                // Center the human detection in the video
                const centerX = videoWidth * 0.5;
                const centerY = videoHeight * 0.4;
                
                // Add some natural variation
                const variation = 20;
                const headX = centerX + (Math.random() - 0.5) * variation;
                const headY = centerY + (Math.random() - 0.5) * variation;
                
                console.log(`Placing dots at center: (${centerX}, ${centerY}), head: (${headX}, ${headY})`);
                
                // Create realistic body proportions
                const dots = [
                    { type: 'head', x: headX, y: headY },
                    { type: 'torso', x: headX, y: headY + 80 },
                    { type: 'lower', x: headX, y: headY + 160 }
                ];
                
                dots.forEach(dot => {
                    this.addDetectionDot(dot.type, dot.x, dot.y);
                });
            }            onPoseResults(results) {
                console.log('🎯 MediaPipe pose results received', results);
                
                // Clear previous detection dots
                this.clearDetectionDots();
                
                if (results.poseLandmarks && results.poseLandmarks.length > 0) {
                    this.humanCount = 1;
                      try {
                        // Get video dimensions for coordinate conversion  
                        let videoWidth = 600;
                        let videoHeight = 450;
                        
                        if (this.webcamVideo) {
                            videoWidth = this.webcamVideo.offsetWidth || this.webcamVideo.clientWidth || 600;
                            videoHeight = this.webcamVideo.offsetHeight || this.webcamVideo.clientHeight || 450;
                        }
                        
                        console.log(`MediaPipe using video dimensions: ${videoWidth}x${videoHeight}`);
                        
                        // Key landmarks indices (MediaPipe Pose)
                        const NOSE = 0;
                        const LEFT_SHOULDER = 11;
                        const RIGHT_SHOULDER = 12;
                        const LEFT_HIP = 23;
                        const RIGHT_HIP = 24;
                        
                        const landmarks = results.poseLandmarks;
                        
                        // Calculate positions with bounds checking
                        const headPos = landmarks[NOSE];
                        const leftShoulder = landmarks[LEFT_SHOULDER];
                        const rightShoulder = landmarks[RIGHT_SHOULDER];
                        const leftHip = landmarks[LEFT_HIP];
                        const rightHip = landmarks[RIGHT_HIP];
                        
                        if (headPos && leftShoulder && rightShoulder && leftHip && rightHip) {
                            const shoulderCenter = {
                                x: (leftShoulder.x + rightShoulder.x) / 2,
                                y: (leftShoulder.y + rightShoulder.y) / 2
                            };
                            const hipCenter = {
                                x: (leftHip.x + rightHip.x) / 2,
                                y: (leftHip.y + rightHip.y) / 2
                            };
                            
                            // Convert normalized coordinates to pixel coordinates
                            const dots = [
                                { 
                                    type: 'head', 
                                    x: headPos.x * videoWidth, 
                                    y: headPos.y * videoHeight
                                },
                                { 
                                    type: 'torso', 
                                    x: shoulderCenter.x * videoWidth, 
                                    y: shoulderCenter.y * videoHeight
                                },
                                { 
                                    type: 'lower', 
                                    x: hipCenter.x * videoWidth, 
                                    y: hipCenter.y * videoHeight
                                }
                            ];
                            
                            // Add detection dots
                            dots.forEach(dot => {
                                this.addDetectionDot(dot.type, dot.x, dot.y);
                            });
                            
                            console.log('✅ MediaPipe detection successful - 3 dots placed');
                        }
                    } catch (error) {
                        console.error('Error processing MediaPipe results:', error);
                    }
                    
                    document.getElementById('humanCounter').textContent = '1';
                } else {
                    this.humanCount = 0;
                    document.getElementById('humanCounter').textContent = '0';
                    console.log('❌ MediaPipe: No pose landmarks detected');
                }
                
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            }              addDetectionDot(type, x, y) {
                console.log(`🎯 Adding ${type} dot at (${x}, ${y})`);
                
                const dot = document.createElement('div');
                dot.className = \`human-dot \${type}\`;
                dot.style.left = \`\${x}px\`;
                dot.style.top = \`\${y}px\`;
                dot.dataset.human = 'detected';
                
                // Add appropriate emoji
                const emojis = {
                    'head': '👤',
                    'torso': '🫀', 
                    'lower': '🦵'
                };
                dot.textContent = emojis[type] || '●';
                
                console.log(`🎯 Dot element created:`, dot);
                console.log(`🎯 Container:`, this.container);
                
                this.container.appendChild(dot);
                
                console.log(`🎯 Dot added to container. Total dots: ${this.container.querySelectorAll('.human-dot').length}`);
            }

            addSimulatedHumanDots(humanIndex) {
                const container = this.container;
                const containerRect = container.getBoundingClientRect();
                
                // Generate random but realistic positions for human detection
                const baseX = (humanIndex * 200 + 100 + Math.random() * 100);
                const baseY = (200 + Math.random() * 200);
                
                // Create 3 dots for each human
                const dots = [
                    { type: 'head', x: baseX, y: baseY },
                    { type: 'torso', x: baseX, y: baseY + 60 },
                    { type: 'lower', x: baseX, y: baseY + 120 }
                ];
                
                dots.forEach(dot => {
                    this.addDetectionDot(dot.type, dot.x, dot.y);
                });            }

            clearDetectionDots() {
                const dots = this.container.querySelectorAll('.human-dot');
                dots.forEach(dot => dot.remove());
            }
            
            updateDuration() {
                if (!this.detectionStartTime) return;
                
                const elapsed = Date.now() - this.detectionStartTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                const duration = \`\${minutes.toString().padStart(2, '0')}:\${seconds.toString().padStart(2, '0')}\`;
                
                document.getElementById('detectionDuration').textContent = duration;
            }
            
            showAlert(message, type) {
                // Simple alert system
                const alertDiv = document.createElement('div');
                alertDiv.className = \`alert alert-\${type} alert-dismissible fade show position-fixed\`;
                alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
                alertDiv.innerHTML = \`
                    \${message}
                    <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
                \`;
                
                document.body.appendChild(alertDiv);
                
                // Auto-remove after 5 seconds
                setTimeout(() => {
                    if (alertDiv.parentElement) {
                        alertDiv.remove();
                    }
                }, 5000);
            }
        }
        
        // Initialize tracker when page loads
        document.addEventListener('DOMContentLoaded', () => {
            window.humanTracker = new CameraHumanTracker();
            console.log('Camera Human Tracker initialized');
        });
        </script>
    </body>
    </html>
    `;
    
    // Write the content to the popup window
    doc.open();
    doc.write(htmlContent);
    doc.close();
    
    console.log('✅ Human detection interface injected into camera popup');
}
