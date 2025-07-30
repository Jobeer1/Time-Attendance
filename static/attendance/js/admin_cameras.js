/// Camera Management JavaScript - Fixed Version

console.log('Camera management script loaded');

$(document).ready(function() {
    console.log('Document ready');
    initializeCameraManagement();
    initializeCameraSetupWizard();
});

// Camera Setup Wizard Variables
let currentStep = 1;
let discoveredStreams = [];
let selectedStreamUrl = '';

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
        var cameraId = $(this).data('camera-id');
        
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
    });

    // Modal handlers
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
    });

    // Camera access confirmation handler
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
        
        console.log('Opening camera URL:', finalUrl.replace(/:[^:]*@/, ':***@'));
        console.log('Camera ID:', cameraId);
        
        // Close the confirmation modal
        $('#cameraAccessModal').modal('hide');
        
        // Open in new window/tab with standalone camera view
        try {
            const popupFeatures = 'width=1100,height=700,noopener,noreferrer';
            const viewUrl = '/admin/view/camera/' + cameraId;
            console.log('[DEBUG] Opening camera view URL:', viewUrl);
            
            const cameraWindow = window.open(viewUrl, '_blank', popupFeatures);
            
            if (!cameraWindow) {
                alert('Popup blocked or failed to open! Please allow popups for this site.');
                return;
            }
            
            // Focus on the new window
            cameraWindow.focus();
        } catch (error) {
            console.error('Error opening camera view:', error);
        }
    });
    
    // Refresh stream button handler
    $('#refreshStream').on('click', function() {
        console.log('Refreshing camera stream');
        const video = document.getElementById('testCameraVideo');
        const image = document.getElementById('testCameraImage');
        
        if (video && video.style.display !== 'none') {
            video.load();
        }
        if (image && image.style.display !== 'none') {
            const src = image.src;
            image.src = '';
            setTimeout(() => image.src = src + '?t=' + Date.now(), 100);
        }
    });
}

function initializeCameraSetupWizard() {
    // Location dropdown handler
    $('#cameraLocation').on('change', function() {
        if ($(this).val() === 'custom') {
            $('#customLocationDiv').show();
        } else {
            $('#customLocationDiv').hide();
        }
    });
}

// Step Navigation Functions
function nextStep(step) {
    // Hide current step
    $('.camera-setup-step').hide();
    
    // Show target step
    $('#step' + step).show();
    currentStep = step;
}

function prevStep(step) {
    // Hide current step
    $('.camera-setup-step').hide();
    
    // Show target step
    $('#step' + step).show();
    currentStep = step;
}

// Stream Discovery Functions
function discoverStreams() {
    const ip = $('#cameraIp').val();
    const username = $('#cameraUsername').val();
    const password = $('#cameraPassword').val();
    const port = $('#cameraPort').val();
    const protocol = $('#cameraProtocol').val();
    
    if (!ip) {
        alert('Please enter camera IP address');
        return;
    }
    
    // Build base URL
    let baseUrl = `${protocol}://${ip}`;
    if (port) {
        baseUrl += `:${port}`;
    }
    
    // Show discovery progress
    $('#discoveryProgress').show();
    $('#discoveryResults').hide();
    $('#discoveryError').hide();
    
    // Create temporary camera object for discovery
    const tempCamera = {
        url: baseUrl,
        username: username,
        password: password
    };
    
    startStreamDiscovery(tempCamera);
    nextStep(3);
}

function startStreamDiscovery(cameraData) {
    // Reset results
    discoveredStreams = [];
    selectedStreamUrl = '';
    
    // Show progress
    $('#discoveryProgress').show();
    $('#discoveryResults').hide();
    $('#discoveryError').hide();
    $('#continueToTestBtn').prop('disabled', true);
    
    // Update progress
    updateDiscoveryProgress(0, 'Starting stream discovery...');
    
    // Create a temporary camera first
    $.ajax({
        url: '/admin/api/cameras',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            name: 'temp_discovery_camera',
            location: 'temp',
            url: cameraData.url,
            username: cameraData.username,
            password: cameraData.password,
            is_active: false,
            temp: true
        }),
        success: function(response) {
            if (response.success) {
                const tempCameraId = response.camera.id;
                updateDiscoveryProgress(25, 'Camera created, discovering streams...');
                
                // Now discover streams
                $.ajax({
                    url: `/admin/api/cameras/${tempCameraId}/discover-streams`,
                    method: 'POST',
                    success: function(discoveryResponse) {
                        updateDiscoveryProgress(75, 'Analyzing discovered streams...');
                        
                        if (discoveryResponse.success) {
                            discoveredStreams = discoveryResponse.streams || [];
                            updateDiscoveryProgress(100, 'Discovery complete!');
                            
                            setTimeout(() => {
                                showDiscoveryResults();
                                // Clean up temp camera
                                deleteTempCamera(tempCameraId);
                            }, 1000);
                        } else {
                            showDiscoveryError(discoveryResponse.error || 'No streams found');
                            deleteTempCamera(tempCameraId);
                        }
                    },
                    error: function() {
                        showDiscoveryError('Discovery request failed');
                        deleteTempCamera(tempCameraId);
                    }
                });
            } else {
                showDiscoveryError('Failed to create temporary camera for discovery');
            }
        },
        error: function() {
            showDiscoveryError('Failed to prepare camera for discovery');
        }
    });
}

function deleteTempCamera(cameraId) {
    $.ajax({
        url: `/admin/api/cameras/${cameraId}`,
        method: 'DELETE',
        success: function() {
            console.log('Temporary camera cleaned up');
        },
        error: function() {
            console.log('Failed to clean up temporary camera');
        }
    });
}

function updateDiscoveryProgress(percent, status) {
    $('#discoveryProgressBar').css('width', percent + '%');
    $('#discoveryStatus').text(status);
}

function showDiscoveryResults() {
    $('#discoveryProgress').hide();
    
    if (discoveredStreams.length > 0) {
        $('#discoveryResults').show();
        $('#discoveryCount').text(discoveredStreams.length);
        
        // Build streams list
        const streamsList = $('#streamsList');
        streamsList.empty();
        
        discoveredStreams.forEach((stream, index) => {
            const statusBadge = getStreamStatusBadge(stream.status);
            const streamItem = $(`
                <div class="list-group-item list-group-item-action stream-item" data-stream-index="${index}">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${stream.endpoint}</h6>
                        ${statusBadge}
                    </div>
                    <p class="mb-1">
                        <strong>Content Type:</strong> ${stream.content_type}<br>
                        <strong>Method:</strong> ${stream.method}
                        ${stream.note ? '<br><strong>Note:</strong> ' + stream.note : ''}
                    </p>
                    <small class="text-muted">${stream.url}</small>
                </div>
            `);
            
            streamItem.on('click', function() {
                selectStream(index);
            });
            
            streamsList.append(streamItem);
        });
        
        $('#continueToTestBtn').prop('disabled', false);
    } else {
        showDiscoveryError('No video streams found');
    }
}

function getStreamStatusBadge(status) {
    switch (status) {
        case 'success':
            return '<span class="badge bg-success">✓ Working</span>';
        case 'possible':
            return '<span class="badge bg-warning">? Possible</span>';
        case 'auth_required':
            return '<span class="badge bg-info">🔐 Auth Required</span>';
        default:
            return '<span class="badge bg-secondary">Unknown</span>';
    }
}

function selectStream(index) {
    // Remove previous selection
    $('.stream-item').removeClass('active');
    
    // Select current stream
    $(`.stream-item[data-stream-index="${index}"]`).addClass('active');
    
    // Store selected stream
    const stream = discoveredStreams[index];
    selectedStreamUrl = stream.url;
    
    // Update step 4 with selected stream info
    $('#selectedStreamUrl').text(stream.url);
    $('#selectedStreamType').text(stream.content_type);
    $('#selectedStreamStatus').removeClass().addClass('badge').addClass(getStatusClass(stream.status)).text(stream.status);
}

function getStatusClass(status) {
    switch (status) {
        case 'success': return 'bg-success';
        case 'possible': return 'bg-warning';
        case 'auth_required': return 'bg-info';
        default: return 'bg-secondary';
    }
}

function showDiscoveryError(errorMessage) {
    $('#discoveryProgress').hide();
    $('#discoveryResults').hide();
    $('#discoveryError').show();
    $('#errorMessage').text(errorMessage);
}

function rediscoverStreams() {
    // Restart discovery with current form data
    discoverStreams();
}

function testSelectedStream() {
    if (!selectedStreamUrl) {
        alert('Please select a stream first');
        return;
    }
    
    // Show stream preview
    const previewDiv = $('#streamPreview');
    previewDiv.html(`
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Testing stream...</span>
            </div>
            <p class="mt-2 text-white">Testing stream connection...</p>
        </div>
    `);
    
    // Test stream with a simple image load
    const testImg = new Image();
    testImg.onload = function() {
        previewDiv.html(`
            <img src="${selectedStreamUrl}" class="img-fluid" style="max-height: 200px;" alt="Stream Preview">
            <div class="text-success mt-2">✓ Stream test successful!</div>
        `);
        $('#integrateCameraBtn').prop('disabled', false);
    };
    
    testImg.onerror = function() {
        previewDiv.html(`
            <div class="text-warning">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <p>Stream preview failed, but URL might still work for video players</p>
                <small>Some streams don't support direct browser preview</small>
            </div>
        `);
        $('#integrateCameraBtn').prop('disabled', false);
    };
    
    testImg.src = selectedStreamUrl;
}

function integrateCamera() {
    if (!selectedStreamUrl) {
        alert('Please select and test a stream first');
        return;
    }
    
    // Get form data
    const formData = {
        name: $('#cameraName').val(),
        location: $('#cameraLocation').val() === 'custom' ? $('#customLocation').val() : $('#cameraLocation').val(),
        url: selectedStreamUrl,
        username: $('#cameraUsername').val(),
        password: $('#cameraPassword').val(),
        description: `Auto-discovered stream: ${selectedStreamUrl}`,
        is_active: true
    };
    
    // Create camera
    $.ajax({
        url: '/admin/api/cameras',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            if (response.success) {
                nextStep(5);
                // Refresh the cameras table
                setTimeout(() => {
                    location.reload();
                }, 3000);
            } else {
                alert('Failed to create camera: ' + (response.error || 'Unknown error'));
            }
        },
        error: function() {
            alert('Failed to create camera');
        }
    });
}

function viewCamera() {
    $('#addCameraModal').modal('hide');
    // Redirect to cameras page or refresh
    setTimeout(() => {
        location.reload();
    }, 500);
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

function handleEditCamera(e) {
    e.preventDefault();
    console.log('Edit camera form submitted');
    
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
    
    var cameraId = formData.get('camera_id');

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

function viewCamera(element) {
    console.log('View camera called');
    
    const cameraUrl = element.data('camera-url');
    const cameraUsername = element.data('camera-username');
    const cameraPassword = element.data('camera-password');
    const cameraId = element.data('camera-id');
    
    if (!cameraUrl) {
        alert('Camera URL not configured');
        return;
    }

    // Get camera name and location from the table row
    const $row = element.closest('tr');
    const cameraName = element.clone().children().remove().end().text().trim() || 'Unknown Camera';
    const cameraLocation = $row.find('td:nth-child(2)').text().trim() || 'Unknown Location';
    
    // Build URL with authentication if credentials are provided
    let finalUrl = cameraUrl;
    let displayUrl = cameraUrl;
    
    if (cameraUsername && cameraPassword) {
        try {
            const url = new URL(cameraUrl);
            
            if (url.protocol === 'http:' || url.protocol === 'https:') {
                url.username = encodeURIComponent(cameraUsername);
                url.password = encodeURIComponent(cameraPassword);
                finalUrl = url.toString();
                displayUrl = url.protocol + '//' + cameraUsername + ':***@' + url.host + url.pathname + url.search + url.hash;
            } else if (url.protocol === 'rtsp:') {
                url.username = encodeURIComponent(cameraUsername);
                url.password = encodeURIComponent(cameraPassword);
                finalUrl = url.toString();
                displayUrl = url.protocol + '//' + cameraUsername + ':***@' + url.host + url.pathname + url.search + url.hash;
            }
        } catch (error) {
            console.warn('Could not parse camera URL, opening without credentials:', error);
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
    console.log('Edit camera:', cameraId);
    
    // Fetch camera data
    fetch('/admin/api/cameras/' + cameraId)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (!data || data.error) {
                alert('Error fetching camera data: ' + (data.error || 'Unknown error'));
                return;
            }
            
            // Fill form fields
            $('#editCameraForm input[name="camera_id"]').val(cameraId);
            $('#editCameraForm input[name="name"]').val(data.name || '');
            $('#editCameraForm input[name="location"]').val(data.location || '');
            $('#editCameraForm input[name="url"]').val(data.url || '');
            $('#editCameraForm input[name="username"]').val(data.username || '');
            $('#editCameraForm input[name="password"]').val('');  // Don't show password for security reasons
            $('#editCameraForm textarea[name="description"]').val(data.description || '');
            $('#editCameraForm input[name="is_active"]').prop('checked', data.is_active || false);
            
            // Show edit modal
            $('#editCameraModal').modal('show');
        })
        .catch(function(error) {
            console.error('Error fetching camera data:', error);
            alert('Failed to fetch camera data');
        });
}

function testCamera(cameraId) {
    console.log('Testing camera:', cameraId);
    
    // Fetch camera data
    fetch('/admin/api/cameras/' + cameraId)
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (!data || data.error) {
                alert('Error fetching camera data: ' + (data.error || 'Unknown error'));
                return;
            }
            
            $('#testCameraLabel').text('Test Camera: ' + (data.name || 'Unknown'));
            
            const cameraUrl = data.url;
            let authUrl = cameraUrl;
            
            // Add auth to URL if present
            if (data.username && data.password) {
                try {
                    const url = new URL(cameraUrl);
                    url.username = encodeURIComponent(data.username);
                    url.password = encodeURIComponent(data.password);
                    authUrl = url.toString();
                } catch (error) {
                    console.warn('Could not parse camera URL for testing:', error);
                    if (cameraUrl.match(/^https?:\/\//)) {
                        authUrl = cameraUrl.replace(/^(https?:\/\/)/, '$1' + encodeURIComponent(data.username) + ':' + encodeURIComponent(data.password) + '@');
                    }
                }
            }
            
            // Set up test stream
            const video = document.getElementById('testCameraVideo');
            const image = document.getElementById('testCameraImage');
            
            // Hide both by default
            video.style.display = 'none';
            image.style.display = 'none';
            
            if (cameraUrl.startsWith('webcam://')) {
                // For webcam URLs, use the user's webcam
                video.style.display = 'block';
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    navigator.mediaDevices.getUserMedia({ video: true })
                        .then(function(stream) {
                            video.srcObject = stream;
                            video.play();
                        })
                        .catch(function(err) {
                            console.error('Error accessing webcam:', err);
                            $('#testCameraStatus').html('<div class="alert alert-danger">Error accessing webcam</div>');
                        });
                } else {
                    $('#testCameraStatus').html('<div class="alert alert-danger">Webcam access not supported in this browser</div>');
                }
            } else if (cameraUrl.startsWith('rtsp://')) {
                // For RTSP streams, use a snapshot image as a test
                $('#testCameraStatus').html('<div class="alert alert-info">RTSP streams can only be viewed in the camera view</div>');
                image.style.display = 'block';
                image.src = '/admin/proxy/camera/' + cameraId + '/snapshot';
            } else {
                // For HTTP(S) streams, use a snapshot
                image.style.display = 'block';
                image.src = '/admin/proxy/camera/' + cameraId + '/snapshot?t=' + Date.now();
            }
            
            // Show test modal
            $('#testCameraModal').modal('show');
        })
        .catch(function(error) {
            console.error('Error testing camera:', error);
            alert('Failed to test camera');
        });
}

function deleteCamera(cameraId) {
    console.log('Delete camera:', cameraId);
    
    if (!confirm('Are you sure you want to delete this camera?')) {
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
