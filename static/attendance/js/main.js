// Time Attendance System - Main JavaScript

// Global variables
let currentStream = null;
let currentEmployee = null;
let isProcessing = false;

// Network settings global variable with defaults
// Global network settings stored on window to share across scripts
window.networkSettings = {
    ip_range_start: '10.0.0.1',
    ip_range_end: '10.0.0.255',
    scan_timeout: 5,
    concurrent_scans: 20
};

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatTimeSpan(startTime, endTime) {
    if (!startTime || !endTime) return 'N/A';
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end - start;
    const diffHours = diffMs / (1000 * 60 * 60);
    
    const hours = Math.floor(diffHours);
    const minutes = Math.floor((diffHours - hours) * 60);
    
    return `${hours}h ${minutes}m`;
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-ZA', {
        style: 'currency',
        currency: 'ZAR'
    }).format(amount);
}

// Initialize the application
$(document).ready(function() {
    initializeApp();
    setupEventListeners();
    startTimeUpdates();
});

// Initialize application
function initializeApp() {
    // Hide loading overlay after page load
    setTimeout(() => {
        $('#loadingOverlay').addClass('d-none');
    }, 500);

    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();

    // Initialize popovers  
    $('[data-bs-toggle="popover"]').popover();

    // Auto-dismiss alerts after 5 seconds
    setTimeout(() => {
        $('.alert-dismissible').alert('close');
    }, 5000);
    
    // Check camera availability on pages that need it
    if (window.location.pathname.includes('terminal') || 
        window.location.pathname.includes('camera') ||
        document.getElementById('cameraVideo') ||
        document.getElementById('photoCaptureVideo')) {
        
        console.log('Checking camera permissions for this page...');
        checkCameraPermissions().then(hasCamera => {
            if (hasCamera) {
                console.log('Camera is available and accessible');
            } else {
                console.warn('Camera is not available or accessible');
            }
        });
    }
}

// Setup event listeners
function setupEventListeners() {
    // Loading overlay for forms
    $('form').on('submit', function() {
        if (!$(this).hasClass('no-loading')) {
            showLoading();
        }
    });

    // AJAX setup
    $.ajaxSetup({
        beforeSend: function() {
            showLoading();
        },
        complete: function() {
            hideLoading();
        },
        error: function(xhr, status, error) {
            console.error('AJAX Error:', error);
            showAlert('error', 'An error occurred. Please try again.');
        }
    });

    // IP Address Click Handler - Redirect to Terminal Management
    setupIPAddressClickHandler();

    // Search functionality
    $('#searchEmployee').on('input', debounce(filterEmployees, 300));
    $('#departmentFilter, #statusFilter').on('change', filterEmployees);    // Camera permissions
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Check camera permissions on page load
        checkCameraPermissions().then(hasCamera => {
            if (!hasCamera) {
                // Show warning about camera availability
                const cameraButtons = $('[data-bs-target="#cameraModal"], .camera-btn');
                if (cameraButtons.length > 0) {
                    cameraButtons.addClass('disabled').prop('disabled', true);
                    cameraButtons.attr('title', 'Camera not available or access denied');
                    
                    // Add visual indicator
                    cameraButtons.append(' <i class="fas fa-exclamation-triangle text-warning" title="Camera unavailable"></i>');
                }
            }
        });
    } else {
        console.warn('Camera API not supported in this browser');
        // Disable camera-related features
        $('[data-bs-target="#cameraModal"], .camera-btn').addClass('disabled').prop('disabled', true);
    }
}

// Time updates
function startTimeUpdates() {
    updateTime();
    setInterval(updateTime, 1000);
}

function updateTime() {
    const now = new Date();
    const timeOptions = { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
    };
    const dateOptions = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };

    const timeString = now.toLocaleTimeString('en-US', timeOptions);
    const dateString = now.toLocaleDateString('en-US', dateOptions);

    // Update all time displays
    $('#currentTime, #terminalTime, #dashboardTime').text(timeString);
    $('#terminalDate, #dashboardDate').text(dateString);
}

// Loading functions
function showLoading() {
    $('#loadingOverlay').removeClass('d-none');
}

function hideLoading() {
    $('#loadingOverlay').addClass('d-none');
}

// Alert functions
function showAlert(type, message, title = '') {
    try {
        const alertTypes = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        };

        const alertClass = alertTypes[type] || 'alert-info';
        const alertTitle = title ? `<strong>${title}:</strong> ` : '';
        
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${alertTitle}${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        // Find the best container for the alert
        let container = $('.container-fluid').first();
        if (!container.length) {
            container = $('main');
            if (!container.length) {
                container = $('body');
            }
        }

        // Remove existing alerts to avoid clutter
        container.find('.alert').remove();
        
        // Add new alert
        container.prepend(alertHtml);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            container.find('.alert').fadeOut(500, function() {
                if ($(this).length) {
                    $(this).remove();
                }
            });
        }, 5000);
        
    } catch (error) {
        console.error('Error showing alert:', error);
        // Fallback to console if alert fails
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Camera functions
async function checkCameraPermissions() {
    console.log('=== Starting Camera Permission Check ===');

    try {
        // Enforce secure context: getUserMedia requires HTTPS or localhost
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            console.error('Insecure context, HTTPS is required for camera access');
            alert('Camera access requires a secure (HTTPS) connection. Please access this page via HTTPS.');
            return false;
        }
        // Check basic browser support
        if (!navigator.mediaDevices) {
            console.error('navigator.mediaDevices not available');
            alert('Your browser does not support camera access. Please update your browser or try a different one.');
            return false;
        }

        if (!navigator.mediaDevices.getUserMedia) {
            console.error('getUserMedia not supported');
            alert('Your browser does not support camera access. Please update your browser or try a different one.');
            return false;
        }

        if (!navigator.mediaDevices.enumerateDevices) {
            console.error('enumerateDevices not supported');
            alert('Your browser does not support device enumeration. Please update your browser or try a different one.');
            return false;
        }

        console.log('Browser APIs supported - checking devices...');

        // Enumerate devices WITHOUT requesting permission
        let devices = [];
        let videoInputs = [];

        try {
            console.log('Enumerating devices (no permission request)...');
            devices = await navigator.mediaDevices.enumerateDevices();
            videoInputs = devices.filter(device => device.kind === 'videoinput');

            console.log(`Found ${devices.length} total devices:`);
            devices.forEach((device, index) => {
                console.log(`  Device ${index}: ${device.kind} - ${device.label || 'No label (permissions needed)'}`);
            });

            console.log(`Video input devices: ${videoInputs.length}`);
            
            // If no video inputs found, try requesting permission first
            if (videoInputs.length === 0) {
                console.log('No video devices found, requesting camera permission...');
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    console.log('Camera permission granted, re-enumerating devices...');
                    
                    // Stop the stream immediately
                    stream.getTracks().forEach(track => track.stop());
                    
                    // Re-enumerate devices now that we have permission
                    devices = await navigator.mediaDevices.enumerateDevices();
                    videoInputs = devices.filter(device => device.kind === 'videoinput');
                    
                    console.log(`After permission: Found ${videoInputs.length} video input devices`);
                } catch (error) {
                    console.error('Camera access error:', error);
                    // Handle different error types for clarity
                    if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
                        alert('Camera permission is required. Please allow camera access and refresh the page.');
                    } else if (error.name === 'NotFoundError' || error.name === 'OverconstrainedError') {
                        alert('No camera device found. Please connect a camera and try again.');
                    } else {
                        alert('Unable to access camera: ' + (error.message || error.name));
                    }
                    return false;
                }
            }
            
            if (videoInputs.length === 0) {
                alert('No cameras detected. Please ensure your camera is connected and try again.');
                return false;
            }
        } catch (enumError) {
            console.error('Device enumeration failed:', enumError);
            alert('Failed to enumerate devices. Please check your browser settings and permissions.');
            return false;
        }

        // Try different camera access strategies
        let cameraWorking = false;
        let lastError = null;

        const strategies = [
            {
                name: 'Basic video request',
                constraints: { video: true }
            },
            {
                name: 'User-facing camera with size constraints',
                constraints: {
                    video: {
                        width: { ideal: 640, min: 320 },
                        height: { ideal: 480, min: 240 },
                        facingMode: 'user'
                    }
                }
            },
            {
                name: 'Minimal constraints',
                constraints: {
                    video: {
                        width: { min: 320 },
                        height: { min: 240 }
                    }
                }
            },
            {
                name: 'No constraints fallback',
                constraints: { video: {} }
            }
        ];

        for (const strategy of strategies) {
            console.log(`Trying strategy: ${strategy.name}`);
            console.log('Constraints:', strategy.constraints);

            try {
                const stream = await navigator.mediaDevices.getUserMedia(strategy.constraints);
                console.log(`✅ Strategy succeeded: ${strategy.name}`);
                stream.getTracks().forEach(track => track.stop()); // Stop the stream
                cameraWorking = true;
                break;
            } catch (error) {
                console.error(`✗ Failed strategy: ${strategy.name} -`, error);
                lastError = error;
            }
        }

        if (!cameraWorking) {
            console.error('Camera is not available or accessible');
            alert('Camera is not available or accessible. Please check your browser settings and permissions.');
            console.error('Last error:', lastError);
            return false;
        }

        console.log('Camera permission check completed successfully.');
        return true;

    } catch (error) {
        console.error('Unexpected error during camera permission check:', error);
        alert('An unexpected error occurred while checking camera permissions. Please try again.');
        return false;
    }
}

async function startCamera(videoElement, onSuccess = null) {
    console.log('=== Starting Camera ===');
    
    try {
        if (currentStream) {
            console.log('Stopping existing camera stream...');
            stopCamera();
        }

        // Check if we have the required APIs
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera API not supported in this browser');
        }

        function isMobile() {
            return /Android|iPhone|iPad|iPod|Opera Mini|IEMobile|WPDesktop/i.test(navigator.userAgent);
        }

        console.log('Device type:', isMobile() ? 'Mobile' : 'Desktop');

        // Enhanced constraints with more fallback options
        const constraintSets = [
            // Best quality attempts
            { 
                name: 'High Quality User Camera',
                video: { 
                    facingMode: 'user', 
                    width: { ideal: 1280, min: 640 }, 
                    height: { ideal: 720, min: 480 },
                    frameRate: { ideal: 30, min: 15 }
                } 
            },
            { 
                name: 'Medium Quality User Camera',
                video: { 
                    facingMode: 'user', 
                    width: { ideal: 640, min: 320 }, 
                    height: { ideal: 480, min: 240 }
                } 
            },
            // Mobile-specific attempts
            ...(isMobile() ? [
                { 
                    name: 'Rear Camera (Environment)',
                    video: { 
                        facingMode: { exact: 'environment' }, 
                        width: { ideal: 640 }, 
                        height: { ideal: 480 }
                    } 
                },
                { 
                    name: 'Any Rear Camera',
                    video: { 
                        facingMode: 'environment' 
                    } 
                }
            ] : []),
            // Fallback attempts
            { 
                name: 'Any Camera with Size',
                video: { 
                    width: { min: 320, max: 1920 }, 
                    height: { min: 240, max: 1080 }
                } 
            },
            { 
                name: 'Minimal Constraints',
                video: { 
                    width: { min: 320 }, 
                    height: { min: 240 }
                } 
            },
            { 
                name: 'Basic Video Only',
                video: true 
            },
            { 
                name: 'Empty Video Constraints',
                video: {} 
            }
        ];

        // First, try to get available devices to select specific camera if needed
        let availableVideoDevices = [];
        try {
            console.log('Enumerating available devices...');
            const devices = await navigator.mediaDevices.enumerateDevices();
            availableVideoDevices = devices.filter(device => device.kind === 'videoinput');
            console.log(`Found ${availableVideoDevices.length} video input devices`);
            
            if (availableVideoDevices.length === 0) {
                console.warn('No video input devices found during enumeration');
            } else {
                availableVideoDevices.forEach((device, index) => {
                    console.log(`  Device ${index}: ${device.label || 'Unknown'} (${device.deviceId.substring(0, 8)}...)`);
                });
            }
        } catch (enumError) {
            console.warn('Could not enumerate devices:', enumError);
        }

        // Add device-specific constraints if we found devices
        if (availableVideoDevices.length > 0) {
            // Try each available device
            availableVideoDevices.forEach((device, index) => {
                constraintSets.push({
                    name: `Specific Device ${index + 1}: ${device.label || 'Unknown'}`,
                    video: { 
                        deviceId: device.deviceId,
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    }
                });
            });
        }

        let stream = null;
        let lastError = null;
        
        console.log(`Trying ${constraintSets.length} different camera configurations...`);
        
        for (let i = 0; i < constraintSets.length; i++) {
            const constraintSet = constraintSets[i];
            try {
                console.log(`Attempt ${i + 1}: ${constraintSet.name}`);
                console.log('Constraints:', JSON.stringify(constraintSet, null, 2));
                
                stream = await navigator.mediaDevices.getUserMedia(constraintSet);
                
                if (stream && stream.getVideoTracks().length > 0) {
                    const videoTrack = stream.getVideoTracks()[0];
                    console.log(`✓ SUCCESS: ${constraintSet.name}`);
                    console.log('Video track:', {
                        label: videoTrack.label,
                        settings: videoTrack.getSettings ? videoTrack.getSettings() : 'Not available',
                        enabled: videoTrack.enabled,
                        muted: videoTrack.muted,
                        readyState: videoTrack.readyState
                    });
                    break;
                } else {
                    console.warn(`Stream created but no video tracks for: ${constraintSet.name}`);
                    if (stream) {
                        stream.getTracks().forEach(track => track.stop());
                        stream = null;
                    }
                }
            } catch (constraintError) {
                console.warn(`✗ Failed: ${constraintSet.name} - ${constraintError.name}: ${constraintError.message}`);
                lastError = constraintError;
            }
        }

        if (!stream) {
            console.error('All camera attempts failed');
            throw lastError || new Error('No camera constraints worked');
        }

        console.log('Setting up video element...');
        currentStream = stream;
        videoElement.srcObject = currentStream;

        return new Promise((resolve, reject) => {
            videoElement.onloadedmetadata = () => {
                console.log('Video metadata loaded, starting playback...');
                videoElement.play().then(() => {
                    console.log('✓ Camera started successfully');
                    console.log('Video dimensions:', {
                        videoWidth: videoElement.videoWidth,
                        videoHeight: videoElement.videoHeight,
                        clientWidth: videoElement.clientWidth,
                        clientHeight: videoElement.clientHeight
                    });
                    
                    if (onSuccess) onSuccess();
                    resolve(true);
                }).catch(playError => {
                    console.error('Error playing video:', playError);
                    showAlert('error', 'Unable to display camera feed: ' + playError.message);
                    reject(playError);
                });
            };
            
            videoElement.onerror = (error) => {
                console.error('Video element error:', error);
                reject(new Error('Video element failed to load'));
            };
            
            // Add timeout for metadata loading
            setTimeout(() => {
                if (videoElement.readyState < 2) { // HAVE_CURRENT_DATA
                    console.warn('Video metadata loading timeout');
                    reject(new Error('Camera loading timeout'));
                }
            }, 10000); // 10 second timeout
        });

    } catch (error) {
        console.error('=== Camera Start Failed ===');
        console.error('Error:', error);
        
        let errorMessage = 'Unable to access camera. ';
        let troubleshootingTip = '';
        
        switch (error.name) {
            case 'NotFoundError':
                errorMessage += 'No camera device found.';
                troubleshootingTip = 'Please connect a camera or check Windows camera privacy settings.';
                break;
            case 'NotAllowedError':
                errorMessage += 'Camera access denied.';
                troubleshootingTip = 'Please click "Allow" when prompted for camera permission, or check browser camera settings.';
                break;
            case 'NotSupportedError':
                errorMessage += 'Camera not supported by this browser.';
                troubleshootingTip = 'Try using Chrome, Firefox, or Edge browser.';
                break;
            case 'NotReadableError':
                errorMessage += 'Camera is already in use by another application.';
                troubleshootingTip = 'Close other applications that might be using the camera (Skype, Teams, etc.).';
                break;
            case 'OverconstrainedError':
                errorMessage += 'Camera settings not supported.';
                troubleshootingTip = 'Your camera might not support the requested video quality.';
                break;
            case 'SecurityError':
                errorMessage += 'Security error accessing camera.';
                troubleshootingTip = 'Make sure you\'re using HTTPS and the site is trusted.';
                break;
            default:
                errorMessage += 'Unknown camera error.';
                troubleshootingTip = 'Try refreshing the page or restarting your browser.';
        }
        
        showAlert('error', errorMessage + ' ' + troubleshootingTip);
        
        // Provide detailed error info in console for debugging
        console.error('Detailed error info:', {
            name: error.name,
            message: error.message,
            constraint: error.constraint,
            stack: error.stack
        });
        
        return false;
    }
}

function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
}

function captureImage(videoElement, canvasElement, callback) {
    const context = canvasElement.getContext('2d');
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    
    context.drawImage(videoElement, 0, 0);
    
    canvasElement.toBlob(callback, 'image/jpeg', 0.9);
}

// Face recognition functions
async function recognizeFace(imageBlob) {
    const formData = new FormData();
    formData.append('image', imageBlob);

    try {
        const response = await fetch('/terminal/recognize_face', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Face recognition error:', error);
        throw error;
    }
}

// Employee authentication
async function authenticateEmployee(method, data) {
    try {
        const response = await fetch('/terminal/authenticate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                method: method,
                data: data
            })
        });

        const result = await response.json();
        
        if (result.success) {
            currentEmployee = result.employee;
            showEmployeeStatus(result.employee);
            return true;
        } else {
            showAlert('error', result.message || 'Authentication failed');
            return false;
        }
    } catch (error) {
        console.error('Authentication error:', error);
        showAlert('error', 'Authentication failed. Please try again.');
        return false;
    }
}

// Clock in/out functions
async function clockAction(action) {
    if (!currentEmployee || isProcessing) return;

    isProcessing = true;

    try {
        const response = await fetch('/terminal/clock_action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                employee_id: currentEmployee.employee_id,
                action: action
            })
        });

        const result = await response.json();
        
        if (result.success) {
            showActionResult(result.message, action);
            updateEmployeeStatus(result.status);
        } else {
            showAlert('error', result.message || 'Action failed');
        }
    } catch (error) {
        console.error('Clock action error:', error);
        showAlert('error', 'Action failed. Please try again.');
    } finally {
        isProcessing = false;
    }
}

// UI update functions
function showEmployeeStatus(employee) {
    $('#employeeName').text(employee.name);
    $('#employeeId').text(employee.employee_id);
    $('#employeeDepartment').text(employee.department);
    
    if (employee.photo) {
        $('#employeePhoto').attr('src', employee.photo).show();
        $('#employeePhotoPlaceholder').hide();
    } else {
        $('#employeePhoto').hide();
        $('#employeePhotoPlaceholder').show();
    }

    updateEmployeeStatus(employee.status);
    $('#employeeStatus').removeClass('d-none');
    $('#clockActions').removeClass('d-none');
}

function updateEmployeeStatus(status) {
    const statusBadge = $('#statusBadge');
    const statusText = $('#statusText');
    const lastAction = $('#lastAction');

    // Remove all status classes
    statusBadge.removeClass('clocked-in clocked-out on-break');

    switch (status.current_status) {
        case 'clocked_in':
            statusBadge.addClass('clocked-in');
            statusText.html('<i class="fas fa-check-circle me-1"></i>Clocked In');
            break;
        case 'on_break':
            statusBadge.addClass('on-break');
            statusText.html('<i class="fas fa-coffee me-1"></i>On Break');
            break;
        default:
            statusBadge.addClass('clocked-out');
            statusText.html('<i class="fas fa-clock me-1"></i>Not Clocked In');
    }

    if (status.last_action) {
        lastAction.text(`Last action: ${status.last_action}`);
    }

    // Update button states
    updateClockButtons(status.current_status);
}

function updateClockButtons(status) {
    const clockInBtn = $('#clockInBtn');
    const clockOutBtn = $('#clockOutBtn');
    const breakStartBtn = $('#breakStartBtn');
    const breakEndBtn = $('#breakEndBtn');

    // Reset all buttons
    $('[id$="Btn"]').prop('disabled', false);

    switch (status) {
        case 'clocked_in':
            clockInBtn.prop('disabled', true);
            breakEndBtn.prop('disabled', true);
            break;
        case 'on_break':
            clockInBtn.prop('disabled', true);
            breakStartBtn.prop('disabled', true);
            break;
        default:
            clockOutBtn.prop('disabled', true);
            breakStartBtn.prop('disabled', true);
            breakEndBtn.prop('disabled', true);
    }
}

function showActionResult(message, action) {
    $('#actionMessage').text(message);
    $('#actionResult').removeClass('d-none');
    $('#clockActions').addClass('d-none');
    
    // Auto-reset after 5 seconds
    setTimeout(() => {
        resetToAuthMode();
    }, 5000);
}

function resetToAuthMode() {
    currentEmployee = null;
    $('#employeeStatus').addClass('d-none');
    $('#clockActions').addClass('d-none');
    $('#actionResult').addClass('d-none');
    
    // Reset authentication tabs
    $('#face-tab').tab('show');
    $('#pinInput').val('');
    $('#employeeIdInput').val('');
    
    stopCamera();
}

// Employee filtering
function filterEmployees() {
    const searchTerm = $('#searchEmployee').val().toLowerCase();
    const departmentFilter = $('#departmentFilter').val();
    const statusFilter = $('#statusFilter').val();

    $('#employeeTable tbody tr').each(function() {
        const row = $(this);
        const name = row.find('td:nth-child(3)').text().toLowerCase();
        const employeeId = row.find('td:nth-child(2)').text().toLowerCase();
        const department = row.find('td:nth-child(4)').text();
        const status = row.find('td:nth-child(7) .badge').hasClass('bg-success') ? 'active' : 'inactive';

        let showRow = true;

        // Text search
        if (searchTerm && !name.includes(searchTerm) && !employeeId.includes(searchTerm)) {
            showRow = false;
        }

        // Department filter
        if (departmentFilter && department !== departmentFilter) {
            showRow = false;
        }

        // Status filter
        if (statusFilter && status !== statusFilter) {
            showRow = false;
        }

        row.toggle(showRow);
    });
}

// Function to update the discovered devices table
function updateDiscoveredDevicesTable(devices) {
    console.log('updateDiscoveredDevicesTable called with:', devices);
    
    // If no devices parameter provided, try to use global discoveredDevices variable
    if (devices === undefined && typeof discoveredDevices !== 'undefined') {
        devices = discoveredDevices;
        console.log('Using global discoveredDevices:', devices);
    }
    
    // Handle different possible data structures
    let deviceArray = devices;
    
    // Check for nested data structures
    if (devices && Array.isArray(devices.found_devices)) {
        deviceArray = devices.found_devices;
        console.log('Using nested found_devices array');
    } else if (devices && Array.isArray(devices.devices)) {
        deviceArray = devices.devices;
        console.log('Using nested devices array');
    } else if (Array.isArray(devices)) {
        deviceArray = devices;
        console.log('Using devices array directly');
    }
    
    if (!Array.isArray(deviceArray)) {
        console.error('Invalid devices data structure:', devices);
        console.log('Expected an array or object with found_devices/devices array');
        deviceArray = []; // Default to empty array
    }

    const tableBody = document.getElementById('discoveredDevicesTableBody');
    if (!tableBody) {
        console.error('Discovered devices table body not found');
        return;
    }

    // Clear existing rows
    tableBody.innerHTML = '';

    // Populate table with new data
    deviceArray.forEach((device, index) => {
        const row = document.createElement('tr');
        
        // Create unique device ID based on MAC address (safer than IP)
        const deviceId = device.mac_address ? 
            device.mac_address.replace(/[:\-]/g, '').toLowerCase() : 
            `device-${index}`;

        // Determine device status and badge
        const statusBadge = device.online !== false ? 
            '<span class="badge bg-success">Online</span>' : 
            '<span class="badge bg-secondary">Unknown</span>';
        
        // Determine device type and icon
        const deviceType = device.type || 'unknown';
        const deviceIcon = getDeviceIcon(deviceType);
        const deviceTypeBadge = getDeviceTypeBadge(deviceType);
        
        // Custom name or default (use MAC-based lookup if available)
        const customName = device.custom_name || device.hostname || 'Unnamed Device';

        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <i class="fas fa-${deviceIcon} fa-lg me-2 text-primary"></i>
                    <div>
                        <div class="fw-bold">${customName}</div>
                        <div class="text-muted small">${device.hostname || 'Unknown hostname'}</div>
                    </div>
                </div>
            </td>
            <td>
                <span class="font-monospace">${device.ip_address || 'N/A'}</span>
            </td>
            <td>
                <span class="font-monospace small">${device.mac_address || 'N/A'}</span>
            </td>
            <td>
                <span id="status-${deviceId}">${statusBadge}</span>
            </td>
            <td>${deviceTypeBadge}</td>
            <td>
                <input type="text" class="form-control form-control-sm" 
                       value="${device.custom_name || ''}" 
                       placeholder="Enter device name"
                       onchange="updateDeviceNameByMAC('${device.mac_address}', this.value)"
                       style="min-width: 150px;">
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-success ping-btn" 
                            onclick="pingDeviceWithLocalResult('${device.ip_address}', '${deviceId}')" 
                            title="Ping Device"
                            id="ping-btn-${deviceId}">
                        <i class="fas fa-wifi"></i>
                    </button>
                    <button class="btn btn-outline-primary" 
                            onclick="nameDevice('${device.ip_address}', '${device.mac_address}', '${customName}')" 
                            title="Name Device">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-info" 
                            onclick="addDeviceAsTerminal('${device.ip_address}', '${device.mac_address}', '${customName}')" 
                            title="Add as Terminal">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
                <!-- Ping result will be displayed here -->
                <div id="ping-result-${deviceId}" class="mt-1 small"></div>
            </td>
        `;

        tableBody.appendChild(row);
    });

    console.log(`Discovered devices table updated with ${deviceArray.length} devices`);
}

// Device management helper functions
function getDeviceIcon(type) {
    const icons = {
        'terminal': 'desktop',
        'computer': 'laptop',
        'printer': 'print',
        'router': 'network-wired',
        'switch': 'network-wired',
        'camera': 'camera',
        'phone': 'mobile-alt',
        'tablet': 'tablet-alt',
        'server': 'server',
        'access_point': 'wifi',
        'iot': 'microchip',
        'unknown': 'question-circle'
    };
    return icons[type] || icons['unknown'];
}

function getDeviceTypeBadge(type) {
    const badges = {
        'terminal': '<span class="badge bg-primary">Terminal</span>',
        'computer': '<span class="badge bg-info">Computer</span>',
        'printer': '<span class="badge bg-warning">Printer</span>',
        'router': '<span class="badge bg-success">Router</span>',
        'switch': '<span class="badge bg-success">Switch</span>',
        'camera': '<span class="badge bg-danger">Camera</span>',
        'phone': '<span class="badge bg-secondary">Phone</span>',
        'tablet': '<span class="badge bg-secondary">Tablet</span>',
        'server': '<span class="badge bg-dark">Server</span>',
        'access_point': '<span class="badge bg-info">AP</span>',
        'iot': '<span class="badge bg-purple">IoT</span>',
        'unknown': '<span class="badge bg-light text-dark">Unknown</span>'
    };
    return badges[type] || badges['unknown'];
}

// Update device name function
async function updateDeviceName(ipAddress, macAddress, newName) {
    if (!newName || newName.trim() === '') {
        return; // Don't update if name is empty
    }
    
    try {
        const response = await fetch('/admin/terminal-management/api/save-device-name', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ip_address: ipAddress,
                mac_address: macAddress,
                device_name: newName.trim(),
                device_type: 'unknown' // Default type, can be changed via modal
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', `Device name updated to "${newName}"`);
            
            // Update the global discovered devices array
            if (typeof discoveredDevices !== 'undefined') {
                const deviceIndex = discoveredDevices.findIndex(d => d.ip_address === ipAddress);
                if (deviceIndex !== -1) {
                    discoveredDevices[deviceIndex].custom_name = newName;
                }
            }
        } else {
            showAlert('error', result.error || 'Failed to update device name');
        }
        
    } catch (error) {
        console.error('Error updating device name:', error);
        showAlert('error', 'Failed to update device name');
    }
}

// Ping device function
async function pingDevice(ipAddress) {
    try {
        showAlert('info', `Pinging ${ipAddress}...`);
        
        const response = await fetch('/admin/terminal-management/api/ping-device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip_address: ipAddress })
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (result.online) {
                const responseTime = result.response_time ? ` (${result.response_time}ms)` : '';
                showAlert('success', `${ipAddress} is online${responseTime}`);
            } else {
                showAlert('warning', `${ipAddress} is offline or unreachable`);
            }
        } else {
            showAlert('error', result.error || 'Failed to ping device');
        }
        
    } catch (error) {
        console.error('Error pinging device:', error);
        showAlert('error', 'Failed to ping device');
    }
}

// Enhanced ping function with local result display
async function pingDeviceWithLocalResult(ipAddress, deviceId) {
    const pingBtn = document.getElementById(`ping-btn-${deviceId}`);
    const pingResult = document.getElementById(`ping-result-${deviceId}`);
    const statusElement = document.getElementById(`status-${deviceId}`);
    
    if (!pingBtn || !pingResult) {
        console.error('Ping elements not found for device:', deviceId);
        return;
    }
    
    // Show loading state
    const originalBtnContent = pingBtn.innerHTML;
    pingBtn.disabled = true;
    pingBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    pingResult.innerHTML = '<span class="text-info"><i class="fas fa-spinner fa-spin"></i> Pinging...</span>';
    
    try {
        console.log(`Pinging device ${ipAddress}...`);
        
        const response = await fetch('/admin/terminal-management/api/ping-device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                ip_address: ipAddress,
                timeout: 3, // 3 second timeout for faster response
                count: 2    // Send 2 ping packets for better accuracy
            })
        });
        
        const result = await response.json();
        console.log(`Ping result for ${ipAddress}:`, result);
        
        if (result.success) {
            if (result.online) {
                const responseTime = result.response_time ? ` (${result.response_time}ms)` : '';
                pingResult.innerHTML = `<span class="text-success"><i class="fas fa-check-circle"></i> Online${responseTime}</span>`;
                if (statusElement) {
                    statusElement.innerHTML = '<span class="badge bg-success">Online</span>';
                }
            } else {
                pingResult.innerHTML = `<span class="text-danger"><i class="fas fa-times-circle"></i> Offline</span>`;
                if (statusElement) {
                    statusElement.innerHTML = '<span class="badge bg-danger">Offline</span>';
                }
            }
        } else {
            pingResult.innerHTML = `<span class="text-warning"><i class="fas fa-exclamation-triangle"></i> ${result.error || 'Ping failed'}</span>`;
        }
        
        // Clear result after 5 seconds
        setTimeout(() => {
            if (pingResult) {
                pingResult.innerHTML = '';
            }
        }, 5000);
        
    } catch (error) {
        console.error('Error pinging device:', error);
        pingResult.innerHTML = `<span class="text-danger"><i class="fas fa-exclamation-triangle"></i> Error: ${error.message}</span>`;
        
        // Clear error after 5 seconds
        setTimeout(() => {
            if (pingResult) {
                pingResult.innerHTML = '';
            }
        }, 5000);
    } finally {
        // Restore button state
        pingBtn.disabled = false;
        pingBtn.innerHTML = originalBtnContent;
    }
}

// Update device name using MAC address as primary key
async function updateDeviceNameByMAC(macAddress, deviceName) {
    if (!macAddress || !deviceName.trim()) {
        return;
    }
    
    try {
        console.log(`Updating device name for MAC ${macAddress} to "${deviceName}"`);
        
        const response = await fetch('/admin/terminal-management/api/save-device-name', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mac_address: macAddress,
                device_name: deviceName.trim(),
                // Include additional metadata if available
                device_type: 'unknown',
                device_description: `Named device with MAC: ${macAddress}`
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Device name saved successfully');
            
            // Update the discovered devices array if it exists
            if (typeof discoveredDevices !== 'undefined' && Array.isArray(discoveredDevices)) {
                const deviceIndex = discoveredDevices.findIndex(d => d.mac_address === macAddress);
                if (deviceIndex !== -1) {
                    discoveredDevices[deviceIndex].custom_name = deviceName;
                }
            }
            
            // Show a small success indicator near the input field
            const inputField = event.target;
            if (inputField) {
                const originalBorder = inputField.style.border;
                inputField.style.border = '2px solid #28a745';
                setTimeout(() => {
                    inputField.style.border = originalBorder;
                }, 1000);
            }
        } else {
            console.error('Failed to save device name:', result.error);
            showAlert('error', result.error || 'Failed to save device name');
        }
        
    } catch (error) {
        console.error('Error saving device name:', error);
        showAlert('error', 'Failed to save device name: ' + error.message);
    }
}

// Get device name by MAC address (for loading saved names)
async function getDeviceNameByMAC(macAddress) {
    try {
        const response = await fetch(`/admin/terminal-management/api/get-device-name/${macAddress}`);
        const result = await response.json();
        
        if (result.success && result.device_name) {
            return result.device_name;
        }
        
        return null;
    } catch (error) {
        console.error('Error getting device name:', error);
        return null;
    }
}

// Enhanced device icon function with more device types
function getDeviceIcon(type) {
    const icons = {
        'terminal': 'desktop',
        'computer': 'laptop',
        'printer': 'print',
        'router': 'network-wired',
        'switch': 'network-wired',
        'camera': 'camera',
        'phone': 'mobile-alt',
        'tablet': 'tablet-alt',
        'server': 'server',
        'access_point': 'wifi',
        'iot': 'microchip',
        'unknown': 'question-circle'
    };
    return icons[type] || icons['unknown'];
}

// Enhanced device type badge function
function getDeviceTypeBadge(type) {
    const badges = {
        'terminal': '<span class="badge bg-primary">Terminal</span>',
        'computer': '<span class="badge bg-info">Computer</span>',
        'printer': '<span class="badge bg-warning">Printer</span>',
        'router': '<span class="badge bg-success">Router</span>',
        'switch': '<span class="badge bg-success">Switch</span>',
        'camera': '<span class="badge bg-danger">Camera</span>',
        'phone': '<span class="badge bg-secondary">Phone</span>',
        'tablet': '<span class="badge bg-secondary">Tablet</span>',
        'server': '<span class="badge bg-dark">Server</span>',
        'access_point': '<span class="badge bg-info">AP</span>',
        'iot': '<span class="badge bg-purple">IoT</span>',
        'unknown': '<span class="badge bg-light text-dark">Unknown</span>'
    };
    return badges[type] || badges['unknown'];
}

// Export functions for global access
window.TimeAttendance = {
    showAlert,
    showLoading,
    hideLoading,
    startCamera,
    stopCamera,
    captureImage,
    recognizeFace,
    authenticateEmployee,
    clockAction,
    resetToAuthMode,
    formatTime,
    formatCurrency
};

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    
    // Filter out common non-critical errors
    if (event.error && event.error.message) {
        const errorMsg = event.error.message;
        const skipErrors = [
            'Cannot read properties of null',
            'Cannot read properties of undefined',
            'Bootstrap',
            'backdrop',
            'serviceWorker'
        ];
        
        if (skipErrors.some(skip => errorMsg.includes(skip))) {
            return; // Don't show these errors to user
        }
        
        if (typeof showAlert === 'function') {
            showAlert('An unexpected error occurred. Please refresh the page.', 'danger');
        }
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Only show significant promise rejections
    if (event.reason && event.reason.message && 
        !event.reason.message.includes('Cannot read properties of null')) {
        if (typeof showAlert === 'function') {
            showAlert('error', 'An error occurred while processing your request.');
        }
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopCamera();
});

// IP Address Click Handler - Navigate to Terminal Management
function setupIPAddressClickHandler() {
    // Check if we're in admin interface
    if (!window.location.pathname.includes('/admin')) {
        return; // Only enable in admin interface
    }

    // IP address regex pattern
    const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    
    // Function to check if text looks like an IP address
    function isIPAddress(text) {
        return ipPattern.test(text.trim());
    }
    
    // Function to make IP addresses clickable
    function makeIPAddressesClickable() {
        // Find all text nodes and check for IP addresses
        $('*').contents().filter(function() {
            return this.nodeType === 3; // Text node
        }).each(function() {
            const textNode = this;
            const text = textNode.textContent;
            
            // Skip if parent already has IP click handler
            if ($(textNode.parentNode).hasClass('ip-clickable')) {
                return;
            }
            
            // Check if text contains IP address pattern
            const ipMatches = text.match(/\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/g);
            
            if (ipMatches && ipMatches.length > 0) {
                // Replace text with clickable IP addresses
                let newHTML = text;
                ipMatches.forEach(ip => {
                    newHTML = newHTML.replace(
                        new RegExp('\\b' + ip.replace(/\./g, '\\.') + '\\b', 'g'),
                        `<span class="ip-address-clickable" data-ip="${ip}" style="color: #0066cc; cursor: pointer; text-decoration: underline; font-weight: 500;" title="Click to go to Terminal Management">${ip}</span>`
                    );
                });
                
                // Replace the text node with HTML
                $(textNode).replaceWith(newHTML);
            }
        });
        
        // Add click handlers to IP addresses
        $('.ip-address-clickable').off('click.ipHandler').on('click.ipHandler', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const ip = $(this).data('ip');
            
            // Show confirmation
            if (confirm(`Navigate to Terminal Management to manage terminal with IP: ${ip}?`)) {
                // Navigate to terminal management with IP filter
                const terminalManagementUrl = '/admin/terminal-management/terminals';
                window.location.href = terminalManagementUrl + '?filter_ip=' + encodeURIComponent(ip);
            }
        });
    }
    
    // Initial scan for IP addresses
    makeIPAddressesClickable();
    
    // Re-scan when DOM changes (for dynamically loaded content)
    let scanTimeout;
    const observer = new MutationObserver(function(mutations) {
        clearTimeout(scanTimeout);
        scanTimeout = setTimeout(makeIPAddressesClickable, 500);
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
    
    console.log('✅ IP Address Click Handler initialized - IP addresses in admin interface are now clickable');
}

// Service worker registration disabled for now due to HTTPS issues
// TODO: Re-enable when deploying to production with proper SSL
/*
if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/attendance/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed: ', error);
                // Don't show error to user as this is not critical
            });
    });
} else if (window.location.protocol !== 'https:') {
    console.log('ServiceWorker requires HTTPS');
}
*/

function showRejectedApplications() {
    // Show loading indicator
    showLoading();

    // Fetch rejected leave applications from the backend
    $.ajax({
        url: '/api/leave/applications/rejected',
        method: 'GET',
        success: function(response) {
            hideLoading();

            if (response.success) {
                // Display rejected applications in a modal or table
                const rejectedApplications = response.data;
                let html = '<ul class="list-group">';

                rejectedApplications.forEach(app => {
                    html += `<li class="list-group-item">
                                <strong>Employee ID:</strong> ${app.employee_id}<br>
                                <strong>Reason:</strong> ${app.reason}<br>
                                <strong>Start Date:</strong> ${app.start_date}<br>
                                <strong>End Date:</strong> ${app.end_date}
                            </li>`;
                });

                html += '</ul>';
                $('#alertContent').html(html);
            } else {
                showAlert('error', response.error || 'Failed to fetch rejected applications.');
            }
        },
        error: function() {
            hideLoading();
            showAlert('error', 'An error occurred while fetching rejected applications.');
        }
    });
}
