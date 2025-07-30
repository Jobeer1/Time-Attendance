/**
 * Employee Form JavaScript - FIXED VERSION
 * Handles photo capture, camera functionality, and face enrollment
 */

// Global variables for camera streams
let photoStream = null;
let enrollmentStream = null;
let enrollmentPhotos = [];
let isEnrollmentActive = false; // Flag to prevent multiple enrollments

$(document).ready(function() {
    console.log('Employee form script loaded');
    
    // Mark that employee_form.js is loaded to prevent conflicts with employees.js
    window.employeeFormPageLoaded = true;
    
    // Photo capture functionality
    $('#capturePhotoBtn').on('click', function() {
        $('#photoCaptureModal').modal('show');
    });
    
    // Start camera for photo capture
    $('#startPhotoCaptureCamera').on('click', async function() {
        try {
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            };
            
            photoStream = await navigator.mediaDevices.getUserMedia(constraints);
            const video = document.getElementById('photoCaptureVideo');
            video.srcObject = photoStream;
              // Enable capture button
            $('#capturePhotoImage').prop('disabled', false);
            $('#startPhotoCaptureCamera').prop('disabled', true);
            
            // Wait for video to be ready and start face tracking
            video.addEventListener('loadedmetadata', () => {
                console.log('📹 Photo capture video metadata loaded');
                
                // Start face tracking if available
                if (window.faceTracker) {
                    console.log('🎯 Starting face tracking for photo capture...');
                    try {
                        window.faceTracker.initialize().then(() => {
                            window.faceTracker.startTracking(video);
                            console.log('✅ Face tracking started for photo capture');
                        }).catch((error) => {
                            console.log('⚠️ Face tracking initialization failed:', error.message);
                        });
                    } catch (error) {
                        console.log('⚠️ Face tracking failed to start:', error.message);
                    }
                } else {
                    console.log('⚠️ Face tracker not available for photo capture');
                }
            });
              console.log('✅ Photo capture camera started successfully');
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            showAlert('Error accessing camera. Please ensure camera permissions are granted.', 'danger');
        }
    });
      // Capture photo - Enhanced with face tracking integration
    $('#capturePhotoImage').off('click'); // Remove any existing handlers
    $('#capturePhotoImage').on('click', function() {
        console.log('=== PHOTO CAPTURE CLICKED (Photo Modal) ===');
        
        const video = document.getElementById('photoCaptureVideo');
        const canvas = document.getElementById('photoCaptureCanvas');
        
        if (!video || !canvas) {
            console.error('Video or canvas element not found');
            showAlert('Camera elements not found', 'danger');
            return;
        }
        
        if (!video.videoWidth || !video.videoHeight) {
            console.error('Video not ready:', video.videoWidth, 'x', video.videoHeight);
            showAlert('Camera not ready. Please wait for camera to load.', 'warning');
            return;
        }
        
        // Check face tracking quality if available
        if (window.faceTracker) {
            const quality = window.faceTracker.getCurrentQuality();
            console.log('📊 Face quality check:', quality);
            
            if (!quality.faceDetected) {
                showAlert('⚠️ No face detected! Please position your face in front of the camera.', 'warning');
                return;
            }
            
            if (quality.confidence < 0.7) {
                showAlert('⚠️ Face detection confidence low. Please improve lighting and positioning.', 'warning');
                return;
            }
        }
        
        const context = canvas.getContext('2d');
        
        // Set canvas dimensions to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Draw current video frame to canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Show captured image in place of video
        video.style.display = 'none';
        canvas.style.display = 'block';
        
        // Update button states
        $('#capturePhotoImage').prop('disabled', true);
        $('#retakePhoto').show();
        $('#usePhoto').show();
        
        console.log('✅ Photo captured successfully');
    });
    
    // Retake photo
    $('#retakePhoto').on('click', function() {
        const video = document.getElementById('photoCaptureVideo');
        const canvas = document.getElementById('photoCaptureCanvas');
        
        // Show video, hide canvas
        video.style.display = 'block';
        canvas.style.display = 'none';
        
        // Update button states
        $('#capturePhotoImage').prop('disabled', false);
        $('#retakePhoto').hide();
        $('#usePhoto').hide();
    });
    
    // Use captured photo
    $('#usePhoto').on('click', function() {
        const canvas = document.getElementById('photoCaptureCanvas');
        
        // Convert canvas to blob
        canvas.toBlob(function(blob) {
            // Create a file from the blob
            const file = new File([blob], 'captured_photo.jpg', { type: 'image/jpeg' });
            
            // Create a FileList-like object
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            
            // Set the file input
            document.getElementById('photo').files = dataTransfer.files;
            
            // Preview the image
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#employeePhotoPreview').attr('src', e.target.result).show();
                $('#employeePhotoPlaceholder').hide();
            };
            reader.readAsDataURL(file);
            
            // Close modal
            $('#photoCaptureModal').modal('hide');
            
        }, 'image/jpeg', 0.8);
    });
      // Clean up camera when modal is closed - Enhanced with face tracking cleanup
    $('#photoCaptureModal').on('hidden.bs.modal', function() {
        console.log('🎬 Photo capture modal closed - cleaning up...');
        
        if (photoStream) {
            photoStream.getTracks().forEach(track => track.stop());
            photoStream = null;
        }
        
        // Stop face tracking if active
        if (window.faceTracker) {
            console.log('🛑 Stopping face tracking for photo capture...');
            window.faceTracker.stopTracking();
        }
        
        // Reset modal state
        const video = document.getElementById('photoCaptureVideo');
        const canvas = document.getElementById('photoCaptureCanvas');
        video.style.display = 'block';
        canvas.style.display = 'none';
        
        $('#startPhotoCaptureCamera').prop('disabled', false);
        $('#capturePhotoImage').prop('disabled', true);
        $('#retakePhoto').hide();
        $('#usePhoto').hide();
        
        console.log('✅ Photo capture cleanup complete');
    });
    
    // Photo upload preview
    $('#photo').on('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#employeePhotoPreview').attr('src', e.target.result).show();
                $('#employeePhotoPlaceholder').hide();
            };
            reader.readAsDataURL(file);
        }
    });
    
    // Form validation
    $('#employeeForm').on('submit', function(e) {
        const employeeId = $('#employee_id').val().trim();
        const name = $('#name').val().trim();
        const department = $('#department').val();
        const pin = $('#pin').val();
        
        if (!employeeId) {
            e.preventDefault();
            showAlert('Employee ID is required', 'danger');
            return false;
        }
        
        if (!name) {
            e.preventDefault();
            showAlert('Employee name is required', 'danger');
            return false;
        }
        
        if (!department) {
            e.preventDefault();
            showAlert('Department selection is required', 'danger');
            return false;
        }
        
        if (pin && pin.length !== 4) {
            e.preventDefault();
            showAlert('PIN must be exactly 4 digits', 'danger');
            return false;
        }
        
        if (pin && !/^\d+$/.test(pin)) {
            e.preventDefault();
            showAlert('PIN must contain only numbers', 'danger');
            return false;
        }
        
        return true;
    });
    
    // PIN input validation
    $('#pin').on('input', function() {
        const pin = $(this).val();
        if (pin && (pin.length > 4 || !/^\d*$/.test(pin))) {
            $(this).val(pin.slice(0, 4).replace(/\D/g, ''));
        }
    });
    
    // Employee ID validation
    $('#employee_id').on('input', function() {
        const id = $(this).val().toUpperCase();
        $(this).val(id);
    });
    
    // Initialize face enrollment functionality
    initializeFaceEnrollment();
});

// Face enrollment functions (called from buttons)
function enrollFace(employeeId) {
    console.log('=== ENROLL FACE FUNCTION CALLED ===');
    console.log('Employee ID:', employeeId);
    
    // Reset adding photos flag unless specifically called via addMorePhotos
    if (!window.isAddingMorePhotos) {
        window.isAddingMorePhotos = false;
    }
    
    // Prevent multiple simultaneous enrollments
    if (isEnrollmentActive) {
        console.log('Enrollment already active, ignoring duplicate call');
        return;
    }
    
    if (!employeeId) {
        console.warn('No employee ID provided');
        showAlert('Employee must be saved before enrolling face recognition', 'warning');
        return;
    }
    
    isEnrollmentActive = true;
    
    // Store employee ID for enrollment
    window.currentEnrollmentEmployeeId = employeeId; 
    console.log('Stored employee ID:', window.currentEnrollmentEmployeeId);
    
    // Test if modal exists before showing
    const modal = $('#employeeFormFaceEnrollmentModal');
    console.log('Modal element found:', modal.length > 0);
    
    if (modal.length === 0) {
        console.error('Face enrollment modal not found in DOM');
        showAlert('Face enrollment modal not found', 'danger');
        return;
    }
    
    // Update modal title
    const employeeNameElement = $('#employeeFormEnrollmentEmployeeName');
    if (employeeNameElement.length > 0) {
        employeeNameElement.text(`Enrolling face for Employee ID: ${employeeId}`);
        console.log('Updated modal title');
    } else {
        console.warn('Employee name element not found');
    }
    
    // Show face enrollment modal
    console.log('About to show modal...');
    modal.modal('show');    console.log('Modal show command sent');
}

function addMorePhotos(employeeId) {
    console.log('Adding more photos for employee:', employeeId);
    
    // Set a flag to indicate we're adding photos (not replacing)
    window.isAddingMorePhotos = true;
    
    // Update modal title to indicate we're adding more photos
    const modal = $('#employeeFormFaceEnrollmentModal');
    modal.find('.modal-title').text('Add More Photos for Better Recognition');
    
    // Update employee name/ID in modal
    const employeeNameElement = $('#employeeFormEnrollmentEmployeeName');
    if (employeeNameElement.length > 0) {
        employeeNameElement.text(`Adding more photos for Employee ID: ${employeeId}`);
    }
    
    // Update instruction text
    modal.find('.text-muted').text('Adding more photos will improve recognition accuracy without removing existing data');
    
    // Store employee ID globally for the modal functions
    window.currentEnrollmentEmployeeId = employeeId;
    
    // Show face enrollment modal
    modal.modal('show');
}

function reEnrollFace(employeeId) {
    if (confirm('Are you sure you want to re-enroll face recognition? This will replace existing face data.')) {
        // Clear the flag for adding photos
        window.isAddingMorePhotos = false;
        enrollFace(employeeId);
    }
}

function removeFaceData(employeeId) {
    if (confirm('Are you sure you want to remove face recognition data? This cannot be undone.')) {
        $.ajax({
            url: `/admin/api/employees/${employeeId}/remove_face`,
            method: 'DELETE',
            success: function(response) {
                if (response.success) {
                    showAlert('Face recognition data removed successfully', 'success');
                    location.reload();
                } else {
                    showAlert(response.message || 'Failed to remove face data', 'danger');
                }
            },
            error: function() {
                showAlert('Failed to remove face data', 'danger');
            }
        });
    }
}

// Face enrollment initialization function
function initializeFaceEnrollment() {
    console.log('=== INITIALIZING FACE ENROLLMENT ===');
    
    // Wait for DOM to be fully ready
    setTimeout(() => {
        const modal = $('#employeeFormFaceEnrollmentModal');
        
        if (modal.length === 0) {
            console.log('Face enrollment modal not found - feature not available');
            return;
        }
        
        console.log('Face enrollment modal found, setting up functionality...');
          // Setup modal events
        modal.off('.faceEnrollment'); // Clear any existing events
        
        modal.on('shown.bs.modal.faceEnrollment', function() {
            console.log('Face enrollment modal shown event triggered');
            resetEnrollmentUI();
            setupButtonHandlers();
        });
          // Also setup handlers immediately in case modal events don't fire
        console.log('Setting up immediate button handlers as fallback...');
        setupButtonHandlers();
        
        modal.on('hidden.bs.modal.faceEnrollment', function() {
            console.log('Face enrollment modal hidden');
            isEnrollmentActive = false; // Reset enrollment flag
            stopEnrollmentCamera();
            resetEnrollmentUI();
        });
        
        console.log('Face enrollment initialization complete');
        
    }, 200);
}

// Setup button handlers when modal is shown
function setupButtonHandlers() {
    console.log('=== SETTING UP BUTTON HANDLERS ===');
    
    const startCameraBtn = $('#employeeFormStartEnrollmentCamera');
    const capturePhotoBtn = $('#employeeFormCaptureEnrollmentPhoto');
    const saveEnrollmentBtn = $('#employeeFormSaveEnrollment');
    const video = $('#employeeFormEnrollmentVideo');
    const canvas = $('#employeeFormEnrollmentCanvas');
    
    console.log('Button availability check:');
    console.log('- Start Camera:', startCameraBtn.length, startCameraBtn[0]);
    console.log('- Capture Photo:', capturePhotoBtn.length, capturePhotoBtn[0]);
    console.log('- Save Enrollment:', saveEnrollmentBtn.length, saveEnrollmentBtn[0]);
    
    if (startCameraBtn.length === 0 || capturePhotoBtn.length === 0 || saveEnrollmentBtn.length === 0) {
        console.error('Required buttons not found!');
        return;
    }
    
    // Clear existing handlers
    console.log('Clearing existing event handlers...');
    startCameraBtn.off('.faceEnrollment');
    capturePhotoBtn.off('.faceEnrollment');
    saveEnrollmentBtn.off('.faceEnrollment');
    
    // Test if button is clickable
    console.log('Button states:');
    console.log('- Start Camera disabled:', startCameraBtn.prop('disabled'));
    console.log('- Start Camera visible:', startCameraBtn.is(':visible'));
    
    // Start Camera button
    console.log('Attaching Start Camera click handler...');
    startCameraBtn.on('click.faceEnrollment', async function(e) {
        console.log('=== START CAMERA BUTTON CLICKED! ===');
        e.preventDefault();
        e.stopPropagation();
        
        const btn = $(this);
        btn.prop('disabled', true);
        btn.html('<i class="fas fa-spinner fa-spin me-2"></i>Starting Camera...');
        
        try {
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            };
            
            console.log('Requesting camera access...');
            enrollmentStream = await navigator.mediaDevices.getUserMedia(constraints);
              const videoElement = video[0];
            videoElement.srcObject = enrollmentStream;
              videoElement.onloadedmetadata = function() {
                console.log('Camera loaded successfully');
                console.log('Enabling Capture Photo button...');
                
                // Force enable the capture button with multiple methods
                capturePhotoBtn.prop('disabled', false);
                capturePhotoBtn.removeClass('disabled');
                capturePhotoBtn.removeAttr('disabled');
                capturePhotoBtn.attr('disabled', false);
                
                // Also try direct DOM manipulation
                const captureBtn = document.getElementById('employeeFormCaptureEnrollmentPhoto');
                if (captureBtn) {
                    captureBtn.disabled = false;
                    captureBtn.removeAttribute('disabled');
                }
                  console.log('Capture Photo button enabled (prop):', !capturePhotoBtn.prop('disabled'));
                console.log('Capture Photo button enabled (attr):', capturePhotoBtn.attr('disabled'));
                console.log('Capture Photo button enabled (DOM):', captureBtn ? !captureBtn.disabled : 'not found');
                
                btn.html('<i class="fas fa-check me-2"></i>Camera Active');
                
                // Start face tracking if available
                if (window.faceTracker) {
                    console.log('🎯 Starting face tracking for enrollment guidance...');
                    try {
                        window.faceTracker.startTracking(videoElement);
                        console.log('✅ Face tracking started successfully');
                    } catch (error) {
                        console.log('⚠️ Face tracking failed to start:', error.message);
                    }
                } else {
                    console.log('⚠️ Face tracker not available');
                }
                
                // Comprehensive button testing
                setTimeout(() => {
                    console.log('=== COMPREHENSIVE BUTTON TEST AFTER CAMERA LOAD ===');
                    
                    // Check event handlers
                    const clickEvents = $._data(capturePhotoBtn[0], 'events');
                    console.log('Capture button jQuery events:', clickEvents);
                    
                    // Check button position and visibility
                    const rect = captureBtn.getBoundingClientRect();
                    console.log('Button position:', rect);
                    console.log('Button visible:', rect.width > 0 && rect.height > 0);
                    
                    // Check for overlapping elements
                    const elementsAtCenter = document.elementsFromPoint(
                        rect.left + rect.width / 2, 
                        rect.top + rect.height / 2
                    );
                    console.log('Elements at button center:', elementsAtCenter.map(el => el.tagName + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ').join('.') : '')));
                    
                    // Check if button is the topmost element
                    const topElement = elementsAtCenter[0];
                    console.log('Top element at button position:', topElement.tagName + (topElement.id ? '#' + topElement.id : ''));
                    console.log('Is button topmost?', topElement === captureBtn);
                    
                    // Test programmatic click
                    console.log('Testing programmatic click...');
                    try {
                        capturePhotoBtn.trigger('click');
                        console.log('jQuery trigger click executed');
                    } catch (e) {
                        console.error('jQuery trigger click failed:', e);
                    }
                    
                    try {
                        captureBtn.click();
                        console.log('Native click executed');
                    } catch (e) {
                        console.error('Native click failed:', e);
                    }
                    
                }, 1000);
            };
              } catch (error) {
            console.error('Camera error:', error);
            showAlert('Error accessing camera. Please ensure camera permissions are granted.', 'danger');
            btn.prop('disabled', false);
            btn.html('<i class="fas fa-camera me-2"></i>Start Camera');
        }
    });
      // Add global processing flag to prevent duplicate captures
    let isCapturingPhoto = false;
      // Capture Photo button - Single unified handler with face tracking integration
    console.log('Attaching unified Capture Photo click handler...');
    capturePhotoBtn.on('click.faceEnrollment', async function(e) {
        console.log('=== CAPTURE PHOTO BUTTON CLICKED! ===');
        e.preventDefault();
        e.stopPropagation();
        
        // Check if already processing to prevent duplicates
        if (isCapturingPhoto) {
            console.log('Photo capture already in progress, skipping...');
            return;
        }
        
        isCapturingPhoto = true;
        console.log('Setting capture flag to prevent duplicates');
        
        // Reset flag after a short delay to allow for legitimate clicks
        setTimeout(() => {
            isCapturingPhoto = false;
            console.log('Capture flag reset');
        }, 1000);
        
        const videoElement = video[0];
        const canvasElement = canvas[0];
        
        if (!videoElement || !canvasElement) {
            showAlert('Video or canvas element not found', 'danger');
            isCapturingPhoto = false;
            return;
        }
        
        if (!videoElement.videoWidth || !videoElement.videoHeight) {
            showAlert('Camera not ready. Please wait for camera to load.', 'warning');
            isCapturingPhoto = false;
            return;
        }        // Check face tracking quality before capture (with permissive fallback)
        let qualityWarning = false;
        
        if (window.faceTracker) {
            const quality = window.faceTracker.getCurrentQuality();
            console.log('📊 Face quality check:', quality);
            
            // Only show warning, don't block capture
            if (quality.faceDetected === false && quality.confidence < 0.3) {
                console.log('⚠️ Low face detection confidence, but allowing capture');
                qualityWarning = true;
            }
        }
          // Always proceed with capture - user can decide if quality is acceptable
        console.log('📸 Proceeding with photo capture...');
          // Show capture feedback to user
        showAlert('📸 Capturing photo...', 'info');
        
        // Debug video and canvas elements
        console.log('🎥 Video element:', videoElement);
        console.log('📐 Video dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
        console.log('🖼️ Canvas element:', canvasElement);
        
        if (!videoElement.videoWidth || !videoElement.videoHeight) {
            console.error('❌ Video not ready for capture');
            showAlert('❌ Camera not ready. Please wait for video to load.', 'error');
            isCapturingPhoto = false;
            return;
        }
        
        const context = canvasElement.getContext('2d');
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        
        console.log('📏 Canvas set to:', canvasElement.width, 'x', canvasElement.height);
        
        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
        console.log('🎨 Image drawn to canvas');
        
        const imageData = canvasElement.toDataURL('image/jpeg', 0.8);
        console.log('📊 Image data length:', imageData.length, 'characters');
          // Simplified quality validation (non-blocking)
        if (window.faceRecognitionManager) {
            try {
                console.log('🔍 Validating photo quality (non-blocking)...');
                const qualityResult = await window.faceRecognitionManager.validateFaceQuality(imageData);
                
                if (!qualityResult.valid) {
                    console.log('⚠️ Quality check failed but continuing:', qualityResult.message);
                    // Show warning but don't block
                    showAlert(`⚠️ Photo quality: ${qualityResult.message}`, 'warning');
                } else {
                    console.log('✅ Photo quality validated successfully');
                }
            } catch (error) {
                console.log('⚠️ Quality validation failed:', error.message);
                // Continue with capture even if validation fails
            }
        }
        
        // Always add the photo to enrollment
        console.log('➕ Adding photo to enrollment photos...');
          enrollmentPhotos.push(imageData);
        
        console.log(`Photo captured! Total: ${enrollmentPhotos.length}`);
        showAlert('📸 Photo captured successfully!', 'success');
        
        updateEnrollmentProgress();
        addPhotoThumbnail(imageData, enrollmentPhotos.length);
        
        if (enrollmentPhotos.length >= 3) {
            saveEnrollmentBtn.prop('disabled', false);
        }
        
        // Stop face tracking when we have enough photos (5)
        if (enrollmentPhotos.length >= 5) {
            console.log('🎯 Maximum photos captured, stopping face tracking...');
            if (window.faceTracker) {
                window.faceTracker.stopTracking();
            }
            showAlert('✅ Enrollment complete! All 5 photos captured. You can now save the enrollment.', 'success');
        }
        
        if (enrollmentPhotos.length >= 5) {
            $(this).prop('disabled', true);
            $(this).html('<i class="fas fa-check me-2"></i>Photos Complete');
            showAlert('Maximum photos captured! You can now save the enrollment.', 'success');
            
            // Stop face tracking when enrollment is complete
            if (window.faceTracker) {
                window.faceTracker.stopTracking();
            }
        }
    });
      // Add comprehensive debugging for Capture Photo button
    console.log('=== CAPTURE PHOTO BUTTON DEBUGGING ===');
    
    // Optional: Add native event listener debugging without duplicate functionality
    const capturePhotoNative = document.getElementById('employeeFormCaptureEnrollmentPhoto');
    if (capturePhotoNative) {
        console.log('Capture Photo native element found');
        
        // Remove any existing onclick handlers to prevent conflicts
        capturePhotoNative.onclick = null;
        
        // Add debugging listeners only (not duplicate handlers)
        capturePhotoNative.addEventListener('mousedown', function(e) {
            console.log('=== CAPTURE PHOTO: mousedown detected ===');
            console.log('Button disabled:', this.disabled);
            console.log('Processing flag:', isCapturingPhoto);
        });
        
        capturePhotoNative.addEventListener('mouseup', function(e) {
            console.log('=== CAPTURE PHOTO: mouseup detected ===');
        });
        
        // Detailed button state debugging
        console.log('=== CAPTURE PHOTO BUTTON STATE DEBUG ===');
        console.log('Button element:', capturePhotoNative);
        console.log('Button disabled:', capturePhotoNative.disabled);
        console.log('Button position:', capturePhotoNative.getBoundingClientRect());
        console.log('Button computed style visibility:', window.getComputedStyle(capturePhotoNative).visibility);
        console.log('Button computed style display:', window.getComputedStyle(capturePhotoNative).display);
        console.log('Button computed style pointer-events:', window.getComputedStyle(capturePhotoNative).pointerEvents);
        console.log('Button computed style z-index:', window.getComputedStyle(capturePhotoNative).zIndex);
        
    } else {
        console.error('Capture Photo button not found for debugging!');
    }
      // Add debugging for button interactions  
    if (startCameraBtn.length > 0) {
        const btnElement = startCameraBtn[0];
        
        console.log('=== START CAMERA BUTTON DEBUGGING ===');
        console.log('Button element found');
        console.log('Button position:', btnElement.getBoundingClientRect());
        console.log('Button computed style visibility:', window.getComputedStyle(btnElement).visibility);
        console.log('Button computed style display:', window.getComputedStyle(btnElement).display);
        console.log('Button computed style pointer-events:', window.getComputedStyle(btnElement).pointerEvents);
        
        // Add event debugging listeners
        btnElement.addEventListener('mousedown', function() {
            console.log('Start Camera button: mousedown detected');
        });
        
        btnElement.addEventListener('mouseup', function() {
            console.log('Start Camera button: mouseup detected');
        });
        
        btnElement.addEventListener('click', function() {
            console.log('Start Camera button: native click detected');
        });
    }
    
    // Log all current events on the button
    const currentEvents = $._data(startCameraBtn[0], 'events');
    console.log('Current events on Start Camera button:', currentEvents);
    
    // Add debugging for Capture Photo button interactions
    if (capturePhotoBtn.length > 0) {
        const captureElement = capturePhotoBtn[0];
        
        console.log('=== CAPTURE PHOTO BUTTON DEBUGGING ===');
        console.log('Capture button element:', captureElement);
        console.log('Capture button position:', captureElement.getBoundingClientRect());
        console.log('Capture button computed style visibility:', window.getComputedStyle(captureElement).visibility);
        console.log('Capture button computed style display:', window.getComputedStyle(captureElement).display);
        console.log('Capture button computed style pointer-events:', window.getComputedStyle(captureElement).pointerEvents);
        console.log('Capture button disabled:', captureElement.disabled);
        console.log('Capture button offsetParent:', captureElement.offsetParent);
        
        // Add mousedown/mouseup listeners for debugging
        captureElement.addEventListener('mousedown', function() {
            console.log('Capture Photo button: mousedown detected');
        });
        
        captureElement.addEventListener('mouseup', function() {
            console.log('Capture Photo button: mouseup detected');
        });
          captureElement.addEventListener('click', function() {
            console.log('Capture Photo button: native click detected');
        });
    }
    
    // Log all current events on the capture button
    const captureEvents = $._data(capturePhotoBtn[0], 'events');
    console.log('Current events on Capture Photo button:', captureEvents);
    
    // Save Enrollment button
    saveEnrollmentBtn.on('click.faceEnrollment', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('SAVE ENROLLMENT BUTTON CLICKED!');
        
        if (enrollmentPhotos.length < 3) {
            showAlert('Please capture at least 3 photos for enrollment', 'warning');
            return;
        }
        
        const employeeId = window.currentEnrollmentEmployeeId;
        if (!employeeId) {
            showAlert('Employee ID not found', 'danger');
            return;
        }
        
        const btn = $(this);
        btn.prop('disabled', true);
        btn.html('<i class="fas fa-spinner fa-spin me-2"></i>Saving...');
        
        $.ajax({
            url: `/admin/api/employees/${employeeId}/enroll_face`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ photos: enrollmentPhotos }),
            timeout: 30000,            success: function(response) {
                console.log('Enrollment response:', response);
                
                if (response.success) {
                    // Show appropriate success message based on mode
                    const message = window.isAddingMorePhotos ? 
                        `Additional photos added successfully! Total encodings: ${response.total_encodings}` :
                        'Face enrollment completed successfully!';
                    showAlert(message, 'success');
                    $('#employeeFormFaceEnrollmentModal').modal('hide');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showAlert(response.message || 'Failed to save enrollment', 'danger');
                    btn.prop('disabled', false);
                    btn.html('<i class="fas fa-save me-2"></i>Save Enrollment');
                }
            },
            error: function(xhr, status, error) {
                console.error('Enrollment save error:', error);
                let errorMessage = 'Failed to save enrollment';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                }
                  showAlert(errorMessage, 'danger');
                btn.prop('disabled', false);
                btn.html('<i class="fas fa-save me-2"></i>Save Enrollment');
            }
        });
    });
    
    console.log('Button handlers setup complete');
      // Test if the event handler is actually attached (without triggering)
    console.log('Testing button handler attachment...');
    setTimeout(() => {
        const events = $._data(startCameraBtn[0], 'events');
        console.log('Events attached to Start Camera button:', events);
        
        // Check Capture Photo button state
        console.log('Capture Photo button state:');
        console.log('- Disabled:', capturePhotoBtn.prop('disabled'));
        console.log('- Visible:', capturePhotoBtn.is(':visible'));
        
        const captureEvents = $._data(capturePhotoBtn[0], 'events');
        console.log('Events attached to Capture Photo button:', captureEvents);
        
        // Add additional debugging for the Start Camera button
        console.log('=== START CAMERA BUTTON DETAILED DEBUG ===');
        const startBtn = startCameraBtn[0];
        if (startBtn) {
            console.log('Button element:', startBtn);
            console.log('Button offsetParent:', startBtn.offsetParent);
            console.log('Button style.display:', startBtn.style.display);
            console.log('Button style.visibility:', startBtn.style.visibility);
            console.log('Button computed style:', window.getComputedStyle(startBtn));            console.log('Button position:', startBtn.getBoundingClientRect());
        }
    }, 100);
}

// Utility functions
function resetEnrollmentUI() {
    console.log('Resetting enrollment UI...');
    
    enrollmentPhotos = [];
    
    const startBtn = $('#employeeFormStartEnrollmentCamera');
    const captureBtn = $('#employeeFormCaptureEnrollmentPhoto');
    const saveBtn = $('#employeeFormSaveEnrollment');
    
    startBtn.prop('disabled', false)
        .html('<i class="fas fa-camera me-2"></i>Start Camera');
    captureBtn.prop('disabled', true)
        .html('<i class="fas fa-camera-retro me-2"></i>Capture Photo');
    saveBtn.prop('disabled', true)
        .html('<i class="fas fa-save me-2"></i>Save Enrollment');
        
    console.log('Reset - Capture Photo button disabled:', captureBtn.prop('disabled'));
    
    $('#employeeFormEnrollmentProgress').css('width', '0%');
    $('#employeeFormPhotoCount').text('0 / 5');
    $('#employeeFormCapturedPhotos').addClass('d-none');
    $('#employeeFormPhotoThumbnails').empty();
    
    stopEnrollmentCamera();
}

function stopEnrollmentCamera() {
    if (enrollmentStream) {
        console.log('Stopping enrollment camera...');
        enrollmentStream.getTracks().forEach(track => track.stop());
        enrollmentStream = null;
        
        const video = document.getElementById('employeeFormEnrollmentVideo');
        if (video) {
            video.srcObject = null;
        }
    }
    
    // Stop face tracking when camera stops
    if (window.faceTracker) {
        console.log('🛑 Stopping face tracking...');
        window.faceTracker.stopTracking();
    }
}

function updateEnrollmentProgress() {
    const progress = (enrollmentPhotos.length / 5) * 100;
    $('#employeeFormEnrollmentProgress').css('width', `${progress}%`);
    $('#employeeFormPhotoCount').text(`${enrollmentPhotos.length} / 5`);
    
    if (enrollmentPhotos.length > 0) {
        $('#employeeFormCapturedPhotos').removeClass('d-none');
    }
}

function addPhotoThumbnail(imageData, index) {
    const thumbnail = `
        <div class="col-2 mb-2">
            <img src="${imageData}" class="img-thumbnail" style="width: 60px; height: 60px; object-fit: cover;">
            <small class="d-block text-center">${index}</small>
        </div>
    `;
    $('#employeeFormPhotoThumbnails').append(thumbnail);
}

function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('.alert').remove();
    $('#employeeForm').prepend(alertHtml);
    
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}

// Expose functions globally for button calls
window.enrollFace = enrollFace;
window.reEnrollFace = reEnrollFace;
window.removeFaceData = removeFaceData;
