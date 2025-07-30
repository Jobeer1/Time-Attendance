// Terminal Interface JavaScript

// Global variables
let faceRecognitionActive = false;
let captureAttempts = 0;
const maxCaptureAttempts = 3;
let terminalId = 'default'; // Add terminal ID support

// Auto-reset countdown functionality
let autoResetTimer = null;
let autoResetCountdownInterval = null;
const AUTO_RESET_DELAY = 2000; // 2 seconds for faster experience

// Current employee and processing state
let currentEmployee = null;
let isProcessing = false;

$(document).ready(function() {
    // Get terminal ID from URL parameters or use default
    const urlParams = new URLSearchParams(window.location.search);
    terminalId = urlParams.get('terminal_id') || 'default';
    
    console.log('Terminal ID:', terminalId);
    
    initializeTerminal();
    setupTerminalEventListeners();
    
    // Force check camera availability after everything is loaded
    setTimeout(() => {
        console.log('🔄 Performing delayed camera availability check...');
        checkCameraAvailability();
    }, 2000);
});

function initializeTerminal() {
    console.log('🚀 Initializing terminal...');
    
    // Auto-focus on first input
    $('#pinInput').focus();
    
    // Reset authentication state
    resetAuthState();
    
    // Check for auto-logout after inactivity
    startInactivityTimer();
    
    // Load available cameras
    loadAvailableCameras();
    
    // Check camera availability and set up demo mode if needed (with delay to ensure DOM is ready)
    setTimeout(() => {
        checkCameraAvailability();
    }, 1000);
    
    // Debug: Check if face tracking buttons are visible
    setTimeout(() => {
        debugButtonVisibility();
    }, 2000);
}

function debugButtonVisibility() {
    console.log('🔍 Debugging button visibility...');
    
    const testBtn = $('#testFaceTrackingBtn');
    const stopBtn = $('#stopFaceTrackingBtn');
    
    console.log('Test Face Tracking Button:');
    console.log('- Exists:', testBtn.length > 0);
    console.log('- Visible:', testBtn.is(':visible'));
    console.log('- CSS Display:', testBtn.css('display'));
    console.log('- Has d-none class:', testBtn.hasClass('d-none'));
    console.log('- Offset dimensions:', testBtn.width(), 'x', testBtn.height());
    console.log('- HTML content:', testBtn.html());
    console.log('- Parent element:', testBtn.parent().get(0));
    
    console.log('Stop Face Tracking Button:');
    console.log('- Exists:', stopBtn.length > 0);
    console.log('- Visible:', stopBtn.is(':visible'));
    console.log('- CSS Display:', stopBtn.css('display'));
    console.log('- Has d-none class:', stopBtn.hasClass('d-none'));
    
    // Force show the test button if it's hidden
    if (testBtn.length > 0 && !testBtn.is(':visible')) {
        console.log('⚠️ Test button is hidden, forcing it to show...');
        testBtn.removeClass('d-none').show();
    }
    
    // Also check if the alert container exists
    const alertContainer = testBtn.closest('.alert');
    if (alertContainer.length > 0) {
        console.log('Alert container found:', alertContainer.hasClass('d-none') ? 'HIDDEN' : 'VISIBLE');
        if (alertContainer.hasClass('d-none')) {
            console.log('🔧 Making alert container visible...');
            alertContainer.removeClass('d-none');
        }
    }
}

function highlightFaceTrackingButton() {
    console.log('✨ Highlighting face tracking button...');
    
    const testBtn = $('#testFaceTrackingBtn');
    if (testBtn.length > 0) {
        // Make sure the button is visible
        testBtn.removeClass('d-none').show();
        
        // Make sure parent container is visible
        const alertContainer = testBtn.closest('.alert');
        if (alertContainer.length > 0) {
            alertContainer.removeClass('d-none').show();
        }
        
        // Add a pulsing animation to draw attention
        testBtn.addClass('shadow-lg');
        
        // Add a temporary pulse effect
        const originalClass = testBtn.attr('class');
        
        // Pulse animation
        let pulseCount = 0;
        const pulseInterval = setInterval(() => {
            testBtn.toggleClass('btn-warning btn-outline-warning');
            pulseCount++;
            
            if (pulseCount >= 6) { // Pulse 3 times
                clearInterval(pulseInterval);
                testBtn.attr('class', originalClass + ' shadow-lg');
            }
        }, 500);
        
        // Add a floating notification to make it even more obvious
        const notification = $(`
            <div id="faceTrackingNotification" class="alert alert-warning alert-dismissible fade show position-fixed" 
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                <h6 class="alert-heading mb-2">
                    <i class="fas fa-eye me-2"></i>Face Tracking Test Available!
                </h6>
                <p class="mb-2">Face tracking test buttons are now visible in the Face Recognition tab.</p>
                <p class="mb-0 small">Click "Test Face Tracking" to verify visual markers are working.</p>
            </div>
        `);
        
        $('body').append(notification);
        
        // Auto-remove notification after 10 seconds
        setTimeout(() => {
            notification.fadeOut(() => notification.remove());
        }, 10000);
        
        console.log('✅ Face tracking button highlighted with pulse animation and notification');
    } else {
        console.log('❌ Face tracking button not found for highlighting');
    }
}

async function loadAvailableCameras() {
    console.log('Loading available cameras...');
    try {
        const cameraSelect = $('#cameraSelect');
        cameraSelect.empty();
        
        // First, always add the local device camera option
        cameraSelect.append('<option value="local">Local Device Camera (Browser)</option>');
        
        // Try to detect actual browser cameras
        let browserCameras = [];
        try {
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                // First try without permission to see what's available
                let devices = await navigator.mediaDevices.enumerateDevices();
                let videoDevices = devices.filter(device => device.kind === 'videoinput');
                
                console.log('Found video devices before permission:', videoDevices.length);
                
                // If we found devices, add them to the list
                videoDevices.forEach((device, index) => {
                    const deviceName = device.label || `Camera ${index + 1}`;
                    cameraSelect.append(`<option value="browser-${device.deviceId}">${deviceName}</option>`);
                });
                
                browserCameras = videoDevices;
            }
        } catch (error) {
            console.log('Browser camera detection error:', error);
        }
        
        // Also try to load database cameras (network cameras, etc.)
        try {
            const response = await fetch('/terminal/api/available_cameras');
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.cameras && data.cameras.length > 0) {
                    console.log('Processing', data.cameras.length, 'database cameras');
                    data.cameras.forEach(camera => {
                        if (camera.is_active !== false) {
                            console.log('Adding database camera to dropdown:', camera.name);
                            cameraSelect.append(
                                `<option value="db-${camera.id}">${camera.name} - ${camera.location}</option>`
                            );
                        }
                    });
                }
            }
        } catch (error) {
            console.log('Database camera loading error:', error);
        }
        
        // Show info about available cameras
        const totalCameras = browserCameras.length + cameraSelect.find('option').length - 1; // -1 for local option
        console.log('Total cameras available:', totalCameras);
        
        if (typeof showAlert === 'function') {
            showAlert('info', `Camera system loaded. ${browserCameras.length} browser cameras detected.`, 3000);
        }
        
        // Set up camera selection change handler
        cameraSelect.off('change').on('change', function() {
            const selectedCameraId = $(this).val();
            if (selectedCameraId && faceRecognitionActive) {
                // Restart camera with new selection
                stopFaceRecognition();
                setTimeout(() => startFaceRecognition(), 500);
            }
        });
        
    } catch (error) {
        console.error('Failed to load cameras:', error);
        console.error('Error details:', error.message, error.stack);
        // Fallback to local device camera
        const cameraSelect = $('#cameraSelect');
        cameraSelect.empty().append('<option value="local">Local Device Camera</option>');
        if (typeof showAlert === 'function') {
            showAlert('warning', 'Unable to load camera configuration. Using local device camera.', 3000);
        } else {
            console.log('ALERT: Unable to load camera configuration. Using local device camera.');
        }
    }
}

async function checkCameraAvailability() {
    console.log('🔍 Checking camera availability...');
    try {
        const hasCamera = await checkCameraPermissions();
        const startCameraBtn = $('#startCamera');
        
        console.log('Camera detected:', hasCamera);
        console.log('Button element found:', startCameraBtn.length > 0);
        
        if (!hasCamera) {
            // No camera available - offer demo mode
            startCameraBtn.prop('disabled', false);
            startCameraBtn.html('<i class="fas fa-video me-2"></i>Start Demo');
            startCameraBtn.addClass('btn-info').removeClass('btn-primary');
            startCameraBtn.attr('title', 'No camera detected - Click to see face tracking demo');
            
            console.log('✅ Demo mode button configured');
            // Show info message
            showAlert('info', 'No camera detected. Face recognition will run in demo mode to show how visual markers work.', 8000);
        } else {
            // Camera available
            startCameraBtn.prop('disabled', false);
            startCameraBtn.html('<i class="fas fa-camera me-2"></i>Start Camera');
            startCameraBtn.addClass('btn-primary').removeClass('btn-info');
            startCameraBtn.attr('title', 'Click to start camera for face recognition');
            console.log('✅ Camera mode button configured');
        }
    } catch (error) {
        console.error('Camera availability check failed:', error);
        const startCameraBtn = $('#startCamera');
        startCameraBtn.prop('disabled', false);
        startCameraBtn.html('<i class="fas fa-video me-2"></i>Demo Mode');
        startCameraBtn.addClass('btn-warning').removeClass('btn-primary');
        startCameraBtn.attr('title', 'Camera check failed - Click for demo mode');
        console.log('⚠️ Error mode button configured');
    }
}

function setupTerminalEventListeners() {
    console.log('🔧 Setting up terminal event listeners...');
    
    // Face Recognition
    $('#startCamera').on('click', startFaceRecognition);
    $('#captureImage').on('click', captureFaceImage);
    $('#stopCamera').on('click', stopFaceRecognition);
      // Face Tracking Test Controls
    $('#testFaceTrackingBtn').on('click', function() {
        console.log('🧪 Test Face Tracking button clicked');
        window.testFaceTracking();
    });
    $('#stopFaceTrackingBtn').on('click', function() {
        console.log('⏹️ Stop Face Tracking button clicked');
        window.stopFaceTrackingTest();
    });
    
    console.log('✅ Face tracking test button listeners set up');
    
    // Add a pulse animation to make the test button more visible
    setTimeout(() => {
        highlightFaceTrackingButton();
    }, 3000);

    // PIN Authentication
    $('#pinForm').on('submit', handlePinAuth);
    $('.keypad-btn').on('click', handleKeypadInput);

    // Employee ID Authentication  
    $('#idForm').on('submit', handleIdAuth);

    // Clock Actions
    $('#clockInBtn').on('click', () => performClockAction('clock_in'));
    $('#clockOutBtn').on('click', () => performClockAction('clock_out'));
    $('#breakStartBtn').on('click', () => performClockAction('break_start'));
    $('#breakEndBtn').on('click', () => performClockAction('break_end'));

    // Reset/New Action
    $('#newActionBtn').on('click', resetToAuthMode);

    // Admin Access
    $('#adminAccessBtn').on('click', () => $('#adminLoginModal').modal('show'));
    $('#adminLoginForm').on('submit', handleAdminLogin);

    // Tab switching
    $('button[data-bs-toggle="tab"]').on('shown.bs.tab', function(e) {
        const target = $(e.target).attr('data-bs-target');
        handleTabSwitch(target);
    });

    // Auto-logout on tab switch
    $('button[data-bs-toggle="tab"]').on('click', function() {
        if (currentEmployee) {
            // Don't auto-logout if user is authenticated
            return;
        }
        resetAuthState();
    });
    
    // Shift Info Button handler
    $('#shiftInfoBtn').off('click').on('click', async function() {
        if (!currentEmployee || !currentEmployee.employee_id) {
            showAlert('warning', 'Authenticate first to view shift info.');
            return;
        }
        try {
            const response = await fetch(`/terminal/api/status/${currentEmployee.employee_id}`);
            const data = await response.json();
            if (response.ok && data.success && data.shift) {
                const shift = data.shift;
                let info = `<strong>Shift Info</strong><br>`;
                info += `Employee: ${currentEmployee.full_name || currentEmployee.name || 'Unknown'}<br>`;
                info += `Shift Name: ${shift.name || 'N/A'}<br>`;
                info += `Start: ${shift.start_time || 'N/A'}<br>`;
                info += `End: ${shift.end_time || 'N/A'}<br>`;
                info += `Terminal: ${currentEmployee.terminal_id || 'N/A'}<br>`;
                showAlert('info', info);
            } else {
                showAlert('warning', 'No shift info found for this employee.');
            }
        } catch (err) {
            showAlert('error', 'Error loading shift info.');
        }
    });
}

// Face Recognition Functions
async function startFaceRecognition() {
    try {
        // Check if camera is available first
        const hasCamera = await checkCameraPermissions();
        
        if (!hasCamera) {
            // Start demo mode instead
            await startDemoMode();
            return;
        }

        const selectedCameraId = $('#cameraSelect').val();
        
        // Check if using a specific browser camera (starts with 'browser-')
        if (selectedCameraId && selectedCameraId.startsWith('browser-')) {
            const deviceId = selectedCameraId.replace('browser-', '');
            const video = document.getElementById('cameraVideo');
            if (!video) {
                showAlert('error', 'Camera video element not found.');
                return;
            }

            showAlert('info', 'Starting selected camera...');            // Use specific camera device
            const success = await startCameraWithDevice(video, deviceId, () => {
                $('#startCamera').addClass('d-none');
                $('#captureImage, #stopCamera').removeClass('d-none');
                faceRecognitionActive = true;                // Start face tracking when camera is ready (with enhanced timing)
                setTimeout(async () => {
                    console.log('🔍 Debugging face tracking startup (browser camera)...');
                    console.log('window.faceTracker exists:', !!window.faceTracker);
                    console.log('video.videoWidth:', video.videoWidth);
                    console.log('MediaPipe FaceDetection available:', typeof FaceDetection !== 'undefined');
                    
                    if (window.faceTracker) {
                        try {
                            // Always re-initialize to ensure latest MediaPipe state
                            console.log('🔄 Re-initializing face tracker for browser camera...');
                            await window.faceTracker.initialize();
                            
                            if (video.videoWidth > 0) {
                                console.log('🎯 Starting face tracking for terminal camera');
                                const trackingResult = window.faceTracker.startTracking(video);
                                console.log('✅ Face tracking started for browser camera, result:', trackingResult);
                                
                                // Verify overlay canvas creation
                                setTimeout(() => {
                                    const overlay = document.getElementById('faceTrackingOverlay');
                                    if (overlay) {
                                        console.log('✅ Terminal face tracking overlay created successfully');
                                        console.log('Overlay dimensions:', overlay.width, 'x', overlay.height);
                                    } else {
                                        console.warn('⚠️ Terminal face tracking overlay not found');
                                    }
                                }, 500);
                                
                            } else {
                                console.warn('⚠️ Browser camera video not ready, will retry...');
                                video.addEventListener('loadedmetadata', async () => {
                                    console.log('✅ Browser camera metadata loaded, starting face tracking');
                                    await window.faceTracker.initialize();
                                    window.faceTracker.startTracking(video);
                                }, { once: true });
                            }
                            
                            // Show face tracking info
                            $('#faceTrackingInfo').slideDown();
                            
                        } catch (error) {
                            console.error('❌ Face tracking initialization error (browser camera):', error);
                            console.log('🔄 Falling back to basic tracking');
                            
                            // Try fallback mode
                            if (video.videoWidth > 0) {
                                try {
                                    window.faceTracker.mediaPipeEnabled = false;
                                    window.faceTracker.startTracking(video);
                                    console.log('✅ Fallback face tracking started');
                                } catch (fallbackError) {
                                    console.error('❌ Fallback face tracking failed:', fallbackError);
                                }
                            }
                        }
                    } else {
                        console.warn('⚠️ Face tracker not available (browser camera)');
                    }
                }, 1500); // Increased delay for better MediaPipe availability
                
                showAlert('success', 'Camera started successfully!');
            });

            if (!success) {
                showAlert('error', 'Failed to start selected camera. Falling back to default camera.');
                // Fall back to default camera
                await startDefaultCamera();
            }
            return;
        }
        
        // Check if using a database camera (starts with 'db-')
        if (selectedCameraId && selectedCameraId.startsWith('db-')) {
            const cameraId = selectedCameraId.replace('db-', '');
            // Use configured camera stream
            const response = await fetch(`/terminal/api/camera/${cameraId}/stream`);
            const data = await response.json();
            
            if (data.success && data.stream_url) {
                // Set up camera stream
                const video = document.getElementById('cameraVideo');
                if (video) {                    video.src = data.stream_url;
                    video.play();
                    
                    $('#startCamera').addClass('d-none');
                    $('#captureImage, #stopCamera').removeClass('d-none');
                    faceRecognitionActive = true;
                    
                    // Start face tracking for database camera streams (with delay)
                    setTimeout(() => {
                        if (window.faceTracker) {                            console.log('🎯 Starting face tracking for database camera');
                            window.faceTracker.startTracking(video);
                            // Show face tracking info
                            $('#faceTrackingInfo').slideDown();
                        } else {
                            console.warn('⚠️ Face tracker not available');
                        }
                    }, 500);
                    
                    showAlert('success', `Connected to ${data.camera_name || 'camera'}`);
                    return;
                }
            } else {
                showAlert('warning', 'Selected camera unavailable, falling back to local device');
            }
        }
        
        // Default to local device camera
        await startDefaultCamera();
        
    } catch (error) {
        console.error('Face recognition start error:', error);
        showAlert('error', 'Camera access failed: ' + (error.message || 'Unknown error'));
        // Reset button states
        $('#startCamera').removeClass('d-none');
        $('#captureImage, #stopCamera').addClass('d-none');
    }
}

async function startDefaultCamera() {
    const hasCamera = await checkCameraPermissions();
    
    if (!hasCamera) {
        // Demo mode - simulate camera functionality
        showAlert('info', 'Running in demo mode - No camera detected');
        $('#startCamera').addClass('d-none');
        $('#captureImage, #stopCamera').removeClass('d-none');
        faceRecognitionActive = true;
        
        // Show a placeholder in the video element
        const video = document.getElementById('cameraVideo');
        if (video) {
            video.style.background = 'linear-gradient(45deg, #f0f0f0 25%, #e0e0e0 25%, #e0e0e0 50%, #f0f0f0 50%, #f0f0f0 75%, #e0e0e0 75%)';
            video.style.backgroundSize = '20px 20px';
            
            // Add demo text overlay
            const overlay = document.createElement('div');
            overlay.style.position = 'absolute';
            overlay.style.top = '50%';
            overlay.style.left = '50%';
            overlay.style.transform = 'translate(-50%, -50%)';
            overlay.style.color = '#666';
            overlay.style.fontSize = '14px';
            overlay.style.textAlign = 'center';
            overlay.innerHTML = '<i class="fas fa-camera-slash fa-3x mb-2"></i><br>Demo Mode<br>No Camera Detected';
            
            const container = video.parentElement;
            if (container) {
                container.style.position = 'relative';
                container.appendChild(overlay);
            }
        }
        
        showAlert('success', 'Demo mode activated - Click capture to simulate authentication');
        return;
    }

    const video = document.getElementById('cameraVideo');
    if (!video) {
        showAlert('error', 'Camera video element not found.');
        return;
    }

    showAlert('info', 'Starting local device camera...');    const success = await startCamera(video, () => {
        $('#startCamera').addClass('d-none');
        $('#captureImage, #stopCamera').removeClass('d-none');
        faceRecognitionActive = true;        // Start face tracking when local camera is ready (with enhanced timing)
        setTimeout(async () => {
            console.log('🔍 Debugging face tracking startup...');
            console.log('window.faceTracker exists:', !!window.faceTracker);
            console.log('video.videoWidth:', video.videoWidth);
            console.log('video.videoHeight:', video.videoHeight);
            console.log('video element:', video);
            console.log('MediaPipe FaceDetection available:', typeof FaceDetection !== 'undefined');
            
            if (window.faceTracker) {
                try {
                    // Always re-initialize to ensure proper MediaPipe state
                    console.log('🔄 Force re-initializing face tracker...');
                    await window.faceTracker.initialize();
                    console.log('✅ Face tracker re-initialized successfully');
                    
                    if (video.videoWidth > 0) {
                        console.log('🎯 Starting face tracking for local camera');
                        const trackingResult = window.faceTracker.startTracking(video);
                        console.log('✅ Face tracking started, result:', trackingResult);
                        
                        // Enhanced overlay verification
                        setTimeout(() => {
                            const overlay = document.getElementById('faceTrackingOverlay');
                            console.log('Face tracking overlay:', overlay);
                            if (overlay) {
                                console.log('✅ Overlay canvas found!');
                                console.log('Overlay canvas size:', overlay.width, 'x', overlay.height);
                                console.log('Overlay canvas style:', overlay.style.cssText);
                                console.log('Overlay parent:', overlay.parentElement);
                                
                                // Verify tracking is actually working
                                const ctx = overlay.getContext('2d');
                                if (ctx) {
                                    console.log('✅ Overlay canvas context available');
                                    
                                    // Test draw to verify canvas is working
                                    ctx.fillStyle = 'rgba(0, 255, 0, 0.5)';
                                    ctx.fillRect(10, 10, 100, 50);
                                    ctx.fillStyle = 'white';
                                    ctx.font = '14px Arial';
                                    ctx.fillText('Terminal Test', 15, 30);
                                    console.log('✅ Test draw completed on overlay canvas');
                                    
                                    // Clear test draw after 3 seconds
                                    setTimeout(() => {
                                        ctx.clearRect(0, 0, overlay.width, overlay.height);
                                        console.log('✅ Test draw cleared');
                                    }, 3000);
                                } else {
                                    console.error('❌ Failed to get overlay canvas context');
                                }
                            } else {
                                console.log('❌ No face tracking overlay canvas found - this might be the issue');
                                console.log('Available canvases:', document.querySelectorAll('canvas'));
                                console.log('Video container:', video.parentElement);
                                
                                // Try to manually trigger overlay creation
                                console.log('🔄 Attempting manual overlay creation...');
                                if (window.faceTracker.isTracking) {
                                    window.faceTracker.createTrackingOverlay(video);
                                    console.log('🔄 Manual overlay creation attempted');
                                }
                            }
                        }, 1000);
                        
                    } else {
                        console.warn('⚠️ Video not ready, will retry...');
                        // Enhanced retry logic
                        const retryTracking = async () => {
                            console.log('✅ Video metadata loaded, starting face tracking');
                            await window.faceTracker.initialize();
                            window.faceTracker.startTracking(video);
                        };
                        
                        video.addEventListener('loadedmetadata', retryTracking, { once: true });
                        
                        // Also try after a delay in case loadedmetadata already fired
                        setTimeout(async () => {
                            if (video.videoWidth > 0 && !window.faceTracker.isTracking) {
                                console.log('🔄 Delayed retry for face tracking startup');
                                await retryTracking();
                            }
                        }, 2000);
                    }
                    
                    // Show face tracking info
                    $('#faceTrackingInfo').slideDown();
                    
                } catch (error) {
                    console.error('❌ Face tracking startup error:', error);
                    console.log('🔄 Attempting fallback face tracking...');
                    
                    // Enhanced fallback attempt
                    try {
                        if (video.videoWidth > 0) {
                            window.faceTracker.mediaPipeEnabled = false;
                            await window.faceTracker.initialize();
                            window.faceTracker.startTracking(video);
                            console.log('✅ Fallback face tracking started successfully');
                            $('#faceTrackingInfo').slideDown();
                        }
                    } catch (fallbackError) {
                        console.error('❌ Fallback face tracking also failed:', fallbackError);
                    }
                }
            } else {
                console.warn('⚠️ Face tracker not available or video not ready');
                console.warn('- window.faceTracker:', window.faceTracker);
                console.warn('- video.videoWidth:', video.videoWidth);
                console.warn('- video.videoHeight:', video.videoHeight);
                
                // Try to wait for face tracker to become available
                let retryCount = 0;
                const waitForTracker = setInterval(() => {
                    retryCount++;
                    if (window.faceTracker && video.videoWidth > 0) {
                        console.log('🔄 Face tracker became available, starting tracking...');
                        clearInterval(waitForTracker);
                        window.faceTracker.initialize().then(() => {
                            window.faceTracker.startTracking(video);
                            $('#faceTrackingInfo').slideDown();
                        });
                    } else if (retryCount > 10) {
                        console.warn('⚠️ Gave up waiting for face tracker');
                        clearInterval(waitForTracker);
                    }
                }, 500);
            }
        }, 1500); // Increased delay for better MediaPipe availability
        
        showAlert('success', 'Camera started successfully!');
    });if (!success) {
        showAlert('error', 'Failed to start camera. Please check camera permissions and try again.');
        // Reset button states
        $('#startCamera').removeClass('d-none');
        $('#captureImage, #stopCamera').addClass('d-none');
    }
}

async function captureFaceImage() {
    if (!faceRecognitionActive) return;

    try {
        // Check if we're in demo mode (no camera)
        const hasCamera = await checkCameraPermissions();
        
        if (!hasCamera) {
            // Demo mode - simulate face recognition
            showAlert('info', 'Demo mode: Simulating face recognition...');
            showRecognitionStatus();
            
            // Simulate processing delay
            setTimeout(async () => {
                // Simulate successful recognition with a demo employee
                const demoResult = {
                    success: true,
                    employee: {
                        employee_id: 'DEMO001',
                        name: 'Demo Employee',
                        department: 'IT Department',
                        photo: null
                    }
                };
                
                await authenticateEmployee('face', demoResult);
                stopFaceRecognition();
                hideRecognitionStatus();
                showAlert('success', 'Demo authentication successful!');
            }, 2000);
            return;
        }

        const video = document.getElementById('cameraVideo');
        const canvas = document.getElementById('captureCanvas');
        
        showRecognitionStatus();
        
        captureImage(video, canvas, async (blob) => {
            try {
                const result = await recognizeFace(blob);
                
                if (result.success && result.employee) {
                    await authenticateEmployee('face', result);
                    stopFaceRecognition();
                    hideRecognitionStatus();
                } else {
                    captureAttempts++;
                    
                    if (captureAttempts >= maxCaptureAttempts) {
                        showAlert('error', 'Face not recognized after multiple attempts. Please try PIN or Employee ID.');
                        stopFaceRecognition();
                        captureAttempts = 0;
                    } else {
                        showAlert('warning', `Face not recognized. Attempt ${captureAttempts}/${maxCaptureAttempts}`);
                    }
                    
                    hideRecognitionStatus();
                }
            } catch (error) {
                console.error('Face recognition error:', error);
                showAlert('error', 'Face recognition failed. Please try again.');
                hideRecognitionStatus();
            }
        });
    } catch (error) {
        console.error('Capture error:', error);
        showAlert('error', 'Failed to capture image. Please try again.');
        hideRecognitionStatus();
    }
}

function stopFaceRecognition() {
    stopCamera();
    
    // Stop face tracking
    if (window.faceTracker) {
        console.log('🛑 Stopping face tracking');
        window.faceTracker.stopTracking();
    }
    
    // Hide face tracking info
    $('#faceTrackingInfo').slideUp();
    
    // Clean up demo mode
    const demoCanvas = document.getElementById('demoCanvas');
    if (demoCanvas) {
        demoCanvas.remove();
        console.log('🎭 Demo mode cleaned up');
    }
    
    // Show video element again if it was hidden
    const video = document.getElementById('cameraVideo');
    if (video) {
        video.style.display = 'block';
    }
    
    $('#startCamera').removeClass('d-none');
    $('#captureImage, #stopCamera').addClass('d-none');
    faceRecognitionActive = false;
    captureAttempts = 0;
}

// Authentication handlers - MISSING FUNCTIONS ADDED

// Handle PIN authentication
function handlePinAuth(e) {
    e.preventDefault();
    
    const pin = $('#pinInput').val().trim();
    
    if (!pin) {
        showAlert('warning', 'Please enter your PIN');
        $('#pinInput').focus();
        return;
    }
    
    if (pin.length !== 4) {
        showAlert('warning', 'PIN must be 4 digits');
        $('#pinInput').focus();
        return;
    }
    
    authenticateEmployee('pin', { pin: pin });
}

// Handle employee ID authentication
function handleIdAuth(e) {
    e.preventDefault();
    
    const employeeId = $('#employeeIdInput').val().trim().toUpperCase();
    
    if (!employeeId) {
        showAlert('warning', 'Please enter your Employee ID');
        $('#employeeIdInput').focus();
        return;
    }
    
    authenticateEmployee('employee_id', { employee_id: employeeId });
}

// Handle keypad input for PIN
function handleKeypadInput() {
    const digit = $(this).data('key'); // Fixed: was data('digit')
    const pinInput = $('#pinInput');
    const currentPin = pinInput.val();
    
    if (digit === 'clear') {
        pinInput.val('');
    } else if (digit === 'backspace') {
        pinInput.val(currentPin.slice(0, -1));
    } else if (currentPin.length < 4) {
        pinInput.val(currentPin + digit);
        
        // Auto-submit when 4 digits entered
        if (pinInput.val().length === 4) {
            setTimeout(() => {
                $('#pinForm').submit();
            }, 500);
        }
    }
    
    pinInput.focus();
}

// Main authentication function
async function authenticateEmployee(method, data) {
    if (isProcessing) {
        showAlert('warning', 'Please wait, processing authentication...');
        return;
    }
    
    isProcessing = true;
    
    try {
        // Show authentication in progress
        $('.recognition-status').removeClass('d-none');
        $('.recognition-status .alert').removeClass('alert-success alert-danger alert-warning')
            .addClass('alert-info')
            .html('<i class="fas fa-spinner fa-spin me-2"></i>Authenticating...');
        
        const requestData = {
            method: method,
            terminal_id: terminalId || 'default',
            ...data
        };
        
        console.log('Authenticating with method:', method);
        
        const response = await fetch('/terminal/api/authenticate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success && result.employee) {
            // Authentication successful
            currentEmployee = result.employee;
            currentEmployee.auth_method = method;
            currentEmployee.confidence = result.confidence;
            
            showAuthenticationSuccess(result);
            playNotificationSound('success');
            
        } else {
            // Authentication failed
            showAuthenticationFailure(result.message || 'Authentication failed');
            playNotificationSound('error');
            
            // Clear inputs
            clearAuthInputs();
        }
        
    } catch (error) {
        console.error('Authentication error:', error);
        showAuthenticationFailure('Network error. Please try again.');
        clearAuthInputs();
    } finally {
        isProcessing = false;
    }
}

// Show authentication success
function showAuthenticationSuccess(result) {
    const employee = result.employee;
    
    // Hide recognition status
    $('.recognition-status').addClass('d-none');
    
    // Show employee information
    $('#employeeStatus').removeClass('d-none');
    $('#employeeName').text(employee.full_name || employee.name);
    $('#employeeId').text(`ID: ${employee.employee_id}`);
    $('#employeeDepartment').text(`Department: ${employee.department || 'N/A'}`);
    
    // Set employee photo
    if (employee.photo_url) {
        $('#employeePhoto').attr('src', employee.photo_url).show();
        $('#employeePhotoPlaceholder').hide();
    } else {
        $('#employeePhoto').hide();
        $('#employeePhotoPlaceholder').show();
    }
    
    // Show clock actions
    $('#clockActions').removeClass('d-none');
    
    // Update status based on current attendance
    updateClockButtonStates(employee);
    
    // Hide authentication section
    $('#authenticationSection').addClass('d-none');
    
    // Show success message
    const confidenceText = result.confidence ? ` (${Math.round(result.confidence * 100)}% confidence)` : '';
    showAlert('success', `Welcome ${employee.full_name}!${confidenceText}`);
    
    console.log('Employee authenticated:', employee);
}

// Show authentication failure
function showAuthenticationFailure(message) {
    $('.recognition-status').removeClass('d-none');
    $('.recognition-status .alert').removeClass('alert-success alert-info alert-warning')
        .addClass('alert-danger')
        .html(`<i class="fas fa-exclamation-triangle me-2"></i>${message}`);
    
    setTimeout(() => {
        $('.recognition-status').addClass('d-none');
    }, 3000);
}

// Update clock button states based on employee status
function updateClockButtonStates(employee) {
    // Default state - enable clock in, disable others
    $('#clockInBtn').prop('disabled', false);
    $('#clockOutBtn').prop('disabled', true);
    $('#breakStartBtn').prop('disabled', true);
    $('#breakEndBtn').prop('disabled', true);
    
    // Set default status
    const statusBadge = $('#statusBadge');
    const statusText = $('#statusText');
    statusBadge.removeClass('status-in status-out status-break').addClass('status-out');
    statusText.html('<i class="fas fa-clock me-1"></i>Not Clocked In');
    $('#lastAction').text('');
    
    // If employee has active attendance, update accordingly
    if (employee.attendance && employee.attendance.clock_in_time && !employee.attendance.clock_out_time) {
        // Employee is clocked in
        statusBadge.removeClass('status-out status-break').addClass('status-in');
        statusText.html('<i class="fas fa-clock me-1"></i>Clocked In');
        $('#lastAction').text(`Clocked in at ${new Date(employee.attendance.clock_in_time).toLocaleTimeString()}`);
        
        $('#clockInBtn').prop('disabled', true);
        $('#clockOutBtn').prop('disabled', false);
        $('#breakStartBtn').prop('disabled', false);
        
        // Check if on break
        if (employee.attendance.is_on_break) {
            statusBadge.removeClass('status-in status-out').addClass('status-break');
            statusText.html('<i class="fas fa-coffee me-1"></i>On Break');
            $('#breakStartBtn').prop('disabled', true);
            $('#breakEndBtn').prop('disabled', false);
        }
    }
}

// Clear authentication inputs
function clearAuthInputs() {
    $('#pinInput').val('');
    $('#employeeIdInput').val('');
}

// Reset to authentication mode
function resetToAuthMode() {
    currentEmployee = null;
    
    // Hide employee status and clock actions
    $('#employeeStatus').addClass('d-none');
    $('#clockActions').addClass('d-none');
    
    // Hide leave details section
    $('#leaveDetailsSection').hide();
    
    // Show authentication section
    $('#authenticationSection').removeClass('d-none');
    
    // Hide recognition status
    $('.recognition-status').addClass('d-none');
    
    // Clear inputs
    clearAuthInputs();
    
    // Stop camera if active
    if (faceRecognitionActive) {
        stopFaceRecognition();
    }
    
    // Focus on first tab
    $('#face-tab').tab('show');
    
    console.log('Reset to authentication mode');
}

// Reset authentication state
function resetAuthState() {
    resetToAuthMode();
}

// Clock Actions
async function performClockAction(action) {
    if (!currentEmployee || isProcessing) return;

    // Add confirmation for clock out
    if (action === 'clock_out') {
        if (!confirm('Are you sure you want to clock out?')) {
            return;
        }
    }

    await clockAction(action);
}

// Clock action implementation - MISSING FUNCTION ADDED
async function clockAction(action) {
    if (!currentEmployee) {
        showAlert('error', 'No employee authenticated');
        return;
    }

    if (isProcessing) {
        showAlert('warning', 'Please wait, processing previous request...');
        return;
    }

    isProcessing = true;
    
    try {
        // Show processing state
        const actionBtn = $(`#${action.replace('_', '')}Btn`);
        const originalText = actionBtn.html();
        actionBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Processing...');

        // Prepare request data
        const requestData = {
            employee_id: currentEmployee.employee_id,
            terminal_id: terminalId || 'default',
            auth_method: currentEmployee.auth_method || 'face_recognition'
        };

        // Determine API endpoint
        let endpoint;
        switch (action) {
            case 'clock_in':
                endpoint = '/terminal/api/clock_in';
                break;
            case 'clock_out':
                endpoint = '/terminal/api/clock_out';
                break;
            case 'break_start':
                endpoint = '/terminal/api/break_start';
                break;
            case 'break_end':
                endpoint = '/terminal/api/break_end';
                break;
            default:
                throw new Error('Invalid action');
        }

        console.log(`Performing ${action} for employee ${currentEmployee.employee_id}`);

        // Make API request
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (data.success) {
            // Success feedback
            showAlert('success', data.message || `${action.replace('_', ' ')} successful`);
            // Update UI based on action
            updateEmployeeStatus(action, data);
            // Play success sound if available
            playNotificationSound('success');            // Auto-logout after successful action (except for break actions)
            if (action === 'clock_in' || action === 'clock_out') {
                // Show brief success message then reset immediately for faster workflow
                setTimeout(() => {
                    resetToAuthMode();
                    showAlert('success', 'Ready for next employee!');
                }, 1500); // Reset after 1.5 seconds
            }
        } else {
            // Handle errors
            const errorMessage = data.message || `${action.replace('_', ' ')} failed`;
            showAlert('error', errorMessage);
            console.error(`${action} error:`, data);
        }

        // Restore button state
        actionBtn.prop('disabled', false).html(originalText);

    } catch (error) {
        console.error(`${action} error:`, error);
        showAlert('error', `Failed to ${action.replace('_', ' ')}. Please try again.`);
        
        // Restore button state
        const actionBtn = $(`#${action.replace('_', '')}Btn`);
        actionBtn.prop('disabled', false);
    } finally {
        isProcessing = false;
    }
}

// Update employee status after clock action
function updateEmployeeStatus(action, responseData) {
    if (!currentEmployee) return;

    const statusBadge = $('#statusBadge');
    const statusText = $('#statusText');
    const lastAction = $('#lastAction');
    const now = new Date().toLocaleTimeString();

    switch (action) {
        case 'clock_in':
            statusBadge.removeClass('status-out status-break').addClass('status-in');
            statusText.html('<i class="fas fa-clock me-1"></i>Clocked In');
            lastAction.text(`Clocked in at ${now}`);
            
            // Enable clock out, disable clock in
            $('#clockInBtn').prop('disabled', true);
            $('#clockOutBtn').prop('disabled', false);
            $('#breakStartBtn').prop('disabled', false);
            
            // Load leave details after successful clock in
            if (typeof showLeaveDetailsAfterClockIn === 'function') {
                showLeaveDetailsAfterClockIn(currentEmployee.employee_id);
            }
            
            break;
            
        case 'clock_out':
            statusBadge.removeClass('status-in status-break').addClass('status-out');
            statusText.html('<i class="fas fa-sign-out-alt me-1"></i>Clocked Out');
            lastAction.text(`Clocked out at ${now}`);
            
            // Reset all buttons for next employee
            $('#clockInBtn').prop('disabled', false);
            $('#clockOutBtn').prop('disabled', true);
            $('#breakStartBtn').prop('disabled', true);
            $('#breakEndBtn').prop('disabled', true);
            
            break;
            
        case 'break_start':
            statusBadge.removeClass('status-in status-out').addClass('status-break');
            statusText.html('<i class="fas fa-coffee me-1"></i>On Break');
            lastAction.text(`Break started at ${now}`);
            
            $('#breakStartBtn').prop('disabled', true);
            $('#breakEndBtn').prop('disabled', false);
            
            break;
            
        case 'break_end':
            statusBadge.removeClass('status-break status-out').addClass('status-in');
            statusText.html('<i class="fas fa-clock me-1"></i>Clocked In');
            lastAction.text(`Break ended at ${now}`);
            
            $('#breakStartBtn').prop('disabled', false);
            $('#breakEndBtn').prop('disabled', true);
            
            break;
    }

    // Store updated status
    if (responseData.attendance) {
        currentEmployee.attendance = responseData.attendance;
    }
}

// Play notification sound
function playNotificationSound(type) {
    try {
        // Create audio context for different notification sounds
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Different frequencies for different types
        switch (type) {
            case 'success':
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
                break;
            case 'error':
                oscillator.frequency.setValueAtTime(300, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(200, audioContext.currentTime + 0.1);
                break;
            default:
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime);
        }
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
        console.log('Audio notification not available:', error.message);
    }
}

// Utility functions for terminal operation

// Show recognition status
function showRecognitionStatus() {
    $('.recognition-status').removeClass('d-none');
    $('.recognition-status .alert').removeClass('alert-success alert-danger alert-warning')
        .addClass('alert-info')
        .html('<i class="fas fa-spinner fa-spin me-2"></i>Recognizing face...');
}

// Hide recognition status
function hideRecognitionStatus() {
    $('.recognition-status').addClass('d-none');
}

// Check camera permissions
async function checkCameraPermissions() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            return false;
        }
        
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach(track => track.stop()); // Stop immediately
        return true;
    } catch (error) {
        console.log('Camera permission check failed:', error.message);
        return false;
    }
}

// Capture image from video to canvas
function captureImage(video, canvas, callback) {
    if (!video || !canvas) {
        console.error('Video or canvas element not found');
        return;
    }
    
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(callback, 'image/jpeg', 0.8);
}

// Recognize face from blob
async function recognizeFace(blob) {
    try {
        // Convert blob to base64
        const base64 = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });
        
        const response = await fetch('/terminal/api/authenticate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                method: 'face_recognition',
                image_data: base64,
                terminal_id: terminalId || 'default'
            })
        });
        
        return await response.json();
    } catch (error) {
        console.error('Face recognition API error:', error);
        return { success: false, message: 'Face recognition failed' };
    }
}

// Start inactivity timer
function startInactivityTimer() {
    let inactivityTimer;
    const inactivityTimeout = 60000; // 1 minute
    
    function resetTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(() => {
            if (currentEmployee) {
                resetToAuthMode();
                showAlert('info', 'Session timeout due to inactivity');
            }
        }, inactivityTimeout);
    }
    
    // Reset timer on user activity
    $(document).on('click keypress mousemove touchstart', resetTimer);
    resetTimer();
}

// Perform health check
function performHealthCheck() {
    // Simple health check - verify key elements exist
    const checks = {
        video: !!document.getElementById('cameraVideo'),
        canvas: !!document.getElementById('captureCanvas'),
        pinForm: !!document.getElementById('pinForm'),
        idForm: !!document.getElementById('idForm'),
        clockButtons: !!document.getElementById('clockInBtn')
    };
    
    const allGood = Object.values(checks).every(check => check);
    
    console.log('Terminal health check:', checks);
    
    if (!allGood) {
        console.warn('Some terminal elements are missing');
    }
    
    return allGood;
}

// Demo mode functionality - NEW FUNCTIONS ADDED

// Start demo mode
async function startDemoMode() {
    console.log('🎭 Starting Demo Mode - No Camera Available');
    
    const video = document.getElementById('cameraVideo');
    if (!video) {
        showAlert('error', 'Video element not found.');
        return;
    }

    // Hide video element and show demo message
    video.style.display = 'none';
    
    // Create demo canvas to show face tracking simulation
    const demoCanvas = document.createElement('canvas');
    demoCanvas.id = 'demoCanvas';
    demoCanvas.width = 640;
    demoCanvas.height = 480;
    demoCanvas.style.width = '100%';
    demoCanvas.style.height = 'auto';
    demoCanvas.style.backgroundColor = '#2c3e50';
    demoCanvas.style.border = '2px solid #3498db';
    demoCanvas.style.borderRadius = '8px';
    
    // Insert demo canvas
    const container = video.parentElement;
    container.appendChild(demoCanvas);
    
    const ctx = demoCanvas.getContext('2d');
    
    // Update UI buttons
    $('#startCamera').addClass('d-none');
    $('#captureImage, #stopCamera').removeClass('d-none');
    faceRecognitionActive = true;
    
    // Show demo message
    showAlert('info', 'Demo Mode: Simulating face tracking markers (no camera required)', 5000);
    
    // Start demo face tracking animation
    simulateFaceTracking(ctx, demoCanvas);
}

// Simulate face tracking markers for demo
function simulateFaceTracking(ctx, canvas) {
    let frameCount = 0;
    const demoInterval = setInterval(() => {
        if (!faceRecognitionActive) {
            clearInterval(demoInterval);
            return;
        }
        
        // Clear canvas
        ctx.fillStyle = '#2c3e50';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw demo background text
        ctx.fillStyle = '#7f8c8d';
        ctx.font = '24px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('DEMO MODE', canvas.width / 2, 50);
        ctx.font = '16px Arial';
        ctx.fillText('No Camera Required', canvas.width / 2, 80);
        
        // Simulate face detection with animated bounding box
        const time = frameCount * 0.1;
        const centerX = canvas.width / 2 + Math.sin(time) * 20;
        const centerY = canvas.height / 2 + Math.cos(time * 0.7) * 10;
        const boxWidth = 180 + Math.sin(time * 2) * 10;
        const boxHeight = 220 + Math.cos(time * 1.5) * 10;
        
        // Draw face bounding box
        ctx.strokeStyle = '#27ae60';
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(centerX - boxWidth/2, centerY - boxHeight/2, boxWidth, boxHeight);
        
        // Draw face detection points
        const landmarks = [
            [centerX - 30, centerY - 30], // Left eye
            [centerX + 30, centerY - 30], // Right eye
            [centerX, centerY - 10],      // Nose
            [centerX, centerY + 30]       // Mouth
        ];
        
        ctx.fillStyle = '#e74c3c';
        landmarks.forEach(([x, y]) => {
            ctx.beginPath();
            ctx.arc(x + Math.sin(time * 3) * 2, y + Math.cos(time * 2) * 2, 4, 0, 2 * Math.PI);
            ctx.fill();
        });
        
        // Draw confidence indicator
        const confidence = 0.85 + Math.sin(time) * 0.1;
        ctx.fillStyle = '#3498db';
        ctx.font = '14px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(`Confidence: ${(confidence * 100).toFixed(1)}%`, 20, canvas.height - 60);
        ctx.fillText(`Quality: Good`, 20, canvas.height - 40);
        ctx.fillText(`Status: Face Detected`, 20, canvas.height - 20);
        
        // Draw quality indicators
        ctx.strokeStyle = confidence > 0.8 ? '#27ae60' : '#f39c12';
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.strokeRect(centerX - boxWidth/2 - 10, centerY - boxHeight/2 - 10, boxWidth + 20, boxHeight + 20);
        
        frameCount++;
    }, 100); // 10 FPS for smooth animation
}

// Add global function for testing
window.testDemoMode = function() {
    console.log('🧪 Manual demo mode test triggered');
    checkCameraAvailability();
};

window.forceDemoMode = function() {
    console.log('🎭 Forcing demo mode activation');
    const startCameraBtn = $('#startCamera');
    startCameraBtn.html('<i class="fas fa-video me-2"></i>Start Demo');
    startCameraBtn.removeClass('btn-primary').addClass('btn-info');
    startCameraBtn.attr('title', 'Demo Mode - Click to see face tracking simulation');
    console.log('✅ Demo mode button activated');
};

// --- Fix syntax errors in face tracking debug block ---
window.testFaceTracking = function() {
    console.log('🧪 Testing face tracking integration...');
    console.log('📋 System Status:');
    console.log('- MediaPipe FaceDetection:', typeof FaceDetection !== 'undefined');
    console.log('- window.faceTracker:', !!window.faceTracker);
    console.log('- faceTracker.mediaPipeEnabled:', window.faceTracker?.mediaPipeEnabled);
    console.log('- faceTracker.isTracking:', window.faceTracker?.isTracking);

    const video = document.getElementById('cameraVideo');
    if (video) {
        console.log('📹 Video Element:');
        console.log('- videoWidth:', video.videoWidth);
        console.log('- videoHeight:', video.videoHeight);
        console.log('- readyState:', video.readyState);
        console.log('- srcObject:', !!video.srcObject);
    }

    const overlay = document.getElementById('faceTrackingOverlay');
    if (overlay) {
        console.log('🎨 Tracking Overlay:');
        console.log('- width:', overlay.width);
        console.log('- height:', overlay.height);
        console.log('- style:', overlay.style.cssText);
        console.log('- parent:', overlay.parentElement ? overlay.parentElement.tagName : null);
    } else {
        console.log('❌ No face tracking overlay found');
    }
};

// Stop face tracking function
window.stopFaceTrackingTest = function() {
    console.log('🛑 Stopping face tracking test...');
    
    if (window.faceTracker) {
        window.faceTracker.stopTracking();
        console.log('✅ Face tracking stopped');
    }
    
    // Hide face tracking info
    $('#faceTrackingInfo').slideUp();
    
    // Update status
    updateTrackingStatus('inactive', 'Face tracking stopped');
    
    // Reset button states
    $('#testFaceTrackingBtn').removeClass('d-none');
    $('#stopFaceTrackingBtn').addClass('d-none');
    
    showAlert('info', 'Face tracking stopped');
};

// Helper function to update tracking status
function updateTrackingStatus(state, message) {
    const statusDiv = $('#faceTrackingStatus');
    const statusText = $('#trackingStatusText');
    const spinner = $('#trackingSpinner');
    const activeIcon = $('#trackingActiveIcon');
    
    // Show the status div
    statusDiv.removeClass('d-none');
    
    // Update text
    statusText.text(message);
    
    // Update styling and icons based on state
    statusDiv.removeClass('alert-secondary alert-info alert-success alert-warning alert-danger');
    spinner.hide();
    activeIcon.hide();
      switch(state) {
        case 'starting':
            statusDiv.addClass('alert-info');
            spinner.show();
            break;
        case 'active':
            statusDiv.addClass('alert-success');
            activeIcon.show();
            break;
        case 'inactive':
            statusDiv.addClass('alert-secondary');
            break;
        case 'warning':
            statusDiv.addClass('alert-warning');
            break;
        case 'error':
            statusDiv.addClass('alert-danger');
            break;
        default:
            statusDiv.addClass('alert-secondary');
    }
}

// Face tracking test button event listeners are handled in setupTerminalEventListeners()

// --- AUTO RESET COUNTDOWN FOR NEXT EMPLOYEE ---

function startAutoResetCountdown() {
    console.log('🕐 Starting auto-reset countdown for next employee');
    // Clear any existing timers
    if (autoResetTimer) clearTimeout(autoResetTimer);
    if (autoResetCountdownInterval) clearInterval(autoResetCountdownInterval);
    
    showAutoResetCountdown();
    let remainingSeconds = Math.ceil(AUTO_RESET_DELAY / 1000);
    updateCountdownDisplay(remainingSeconds);
    autoResetCountdownInterval = setInterval(() => {
        remainingSeconds--;
        updateCountdownDisplay(remainingSeconds);
        if (remainingSeconds <= 0) {
            clearInterval(autoResetCountdownInterval);
            autoResetCountdownInterval = null;
        }
    }, 1000);
    autoResetTimer = setTimeout(() => {
        console.log('⏰ Auto-reset timer expired - resetting terminal');
        clearInterval(autoResetCountdownInterval);
        autoResetCountdownInterval = null;
        autoResetTimer = null;
        resetToAuthMode();
        $('#autoResetCountdown').remove();
    }, AUTO_RESET_DELAY);
}

function showAutoResetCountdown() {
    console.log('📋 Showing auto-reset countdown UI');
    const countdownHtml = `
        <div class="alert alert-info d-flex align-items-center justify-content-between mt-3 shadow" id="autoResetCountdown">
            <div class="d-flex align-items-center">
                <i class="fas fa-clock me-2"></i>
                <span id="countdownText">Terminal will reset in <strong><span id="countdownSeconds">7</span></strong> seconds for the next employee</span>
            </div>
            <button class="btn btn-primary btn-lg fw-bold" onclick="continueToNextEmployee()" id="continueBtn">
                <i class="fas fa-arrow-right me-1"></i>
                Continue
            </button>
        </div>
    `;
    $('#autoResetCountdown').remove();
    $('#employeeStatus').after(countdownHtml);
    console.log('✅ Countdown UI added to DOM');
    setTimeout(() => {
        $('#continueBtn').addClass('btn-pulse');
        console.log('💫 Added pulse animation to continue button');
    }, 1000);
}

function updateCountdownDisplay(seconds) {
    const countdownElement = document.getElementById('countdownSeconds');
    if (countdownElement) {
        countdownElement.textContent = seconds;
    }
}

function continueToNextEmployee() {
    console.log('🔄 Continue button clicked - resetting terminal for next employee');
    if (autoResetTimer) {
        clearTimeout(autoResetTimer);
        autoResetTimer = null;
    }
    if (autoResetCountdownInterval) {
        clearInterval(autoResetCountdownInterval);
        autoResetCountdownInterval = null;
    }
    $('#autoResetCountdown').fadeOut(200, function() { $(this).remove(); });
    resetToAuthMode();
    showAlert('success', 'Ready for next employee!');
    setTimeout(() => { $('#pinInput').focus(); }, 300);
}

// Make function globally accessible
window.continueToNextEmployee = continueToNextEmployee;

// Add pulse animation CSS for continue button
(function addPulseStyle(){
    const css = `@keyframes btn-pulse {0%{transform:scale(1);}50%{transform:scale(1.07);}100%{transform:scale(1);}}.btn-pulse{animation:btn-pulse 1.2s infinite;}`;
    const style = document.createElement('style');
    style.innerHTML = css;
    document.head.appendChild(style);
})();

// Export terminal-specific functions
window.Terminal = {
    startFaceRecognition,
    stopFaceRecognition,
    resetAuthState,
    performHealthCheck
};

// --- Ensure Shift Info Button handler is registered after DOM is ready ---
$(document).ready(function() {
    // Shift Info Button handler
    $('#shiftInfoBtn').off('click').on('click', async function() {
        if (!currentEmployee || !currentEmployee.employee_id) {
            showAlert('warning', 'Authenticate first to view shift info.');
            return;
        }
        try {
            const response = await fetch(`/terminal/api/status/${currentEmployee.employee_id}`);
            const data = await response.json();
            if (response.ok && data.success && data.shift) {
                const shift = data.shift;
                let info = `<strong>Shift Info</strong><br>`;
                info += `Employee: ${currentEmployee.full_name || currentEmployee.name || 'Unknown'}<br>`;
                info += `Shift Name: ${shift.name || 'N/A'}<br>`;
                info += `Start: ${shift.start_time || 'N/A'}<br>`;
                info += `End: ${shift.end_time || 'N/A'}<br>`;
                info += `Terminal: ${currentEmployee.terminal_id || 'N/A'}<br>`;
                showAlert('info', info);
            } else {
                showAlert('warning', 'No shift info found for this employee.');
            }
        } catch (err) {
            showAlert('error', 'Error loading shift info.');
        }
    });
});
