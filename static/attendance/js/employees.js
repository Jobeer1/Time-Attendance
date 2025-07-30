/**
 * Employee Management JavaScript
 * Handles employee operations like search, filter, face enrollment, PIN reset, and deletion
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if employee_form.js is already loaded to prevent conflicts
    if (window.employeeFormPageLoaded) {
        console.log('[employees.js] Employee form page detected, skipping initialization to prevent conflicts');
        return;
    }
    
    // Initialize search and filter functionality
    initializeSearchAndFilter();
    
    // Initialize modal event handlers
    initializeModals();
});

function initializeSearchAndFilter() {
    const searchInput = document.getElementById('searchEmployee');
    const departmentFilter = document.getElementById('departmentFilter');
    const statusFilter = document.getElementById('statusFilter');
    const table = document.getElementById('employeeTable');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterEmployees);
    }
    
    if (departmentFilter) {
        departmentFilter.addEventListener('change', filterEmployees);
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', filterEmployees);
    }
    
    function filterEmployees() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const departmentValue = departmentFilter ? departmentFilter.value.toLowerCase() : '';
        const statusValue = statusFilter ? statusFilter.value.toLowerCase() : '';
        const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
        
        Array.from(rows).forEach(row => {
            if (row.cells.length < 8) return; // Skip empty state row
            
            const employeeId = row.cells[1].textContent.toLowerCase();
            const name = row.cells[2].textContent.toLowerCase();
            const department = row.cells[3].textContent.toLowerCase();
            const status = row.cells[6].textContent.toLowerCase();
            
            const matchesSearch = !searchTerm || 
                employeeId.includes(searchTerm) || 
                name.includes(searchTerm);
                
            const matchesDepartment = !departmentValue || 
                department.includes(departmentValue);
                
            const matchesStatus = !statusValue || 
                status.includes(statusValue);
            
            if (matchesSearch && matchesDepartment && matchesStatus) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
}

function initializeModals() {
    // Only initialize modals if the elements exist and bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.warn('Bootstrap not loaded, modals will not work');
        return;
    }
      // Face enrollment modal
    const faceEnrollModalEl = document.getElementById('faceEnrollmentModal');
    if (faceEnrollModalEl) {
        try {
            const faceEnrollModal = new bootstrap.Modal(faceEnrollModalEl);
        } catch (e) {
            console.warn('Could not initialize face enrollment modal:', e);
        }
    }
    
    // PIN reset modal
    const pinResetModalEl = document.getElementById('pinResetModal');
    const pinResetForm = document.getElementById('pinResetForm');
    
    if (pinResetModalEl) {
        try {
            const pinResetModal = new bootstrap.Modal(pinResetModalEl);
        } catch (e) {
            console.warn('Could not initialize PIN reset modal:', e);
        }
    }
    
    if (pinResetForm) {
        pinResetForm.addEventListener('submit', handlePinReset);
    }
    
    // Delete confirmation modal
    const deleteModalEl = document.getElementById('deleteEmployeeModal');
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    
    if (deleteModalEl) {
        try {
            const deleteModal = new bootstrap.Modal(deleteModalEl);
        } catch (e) {
            console.warn('Could not initialize delete modal:', e);
        }
    }
    
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', handleDeleteEmployee);
    }

    // Terminate employee modal
    const terminateModalEl = document.getElementById('terminateEmployeeModal');
    const confirmTerminateBtn = document.getElementById('confirmTerminate');
    
    if (terminateModalEl) {
        try {
            const terminateModal = new bootstrap.Modal(terminateModalEl);
        } catch (e) {
            console.warn('Could not initialize terminate modal:', e);
        }
    }
    
    if (confirmTerminateBtn) {
        confirmTerminateBtn.addEventListener('click', handleTerminateEmployee);
    }

    // Reactivate employee modal
    const reactivateModalEl = document.getElementById('reactivateEmployeeModal');
    const confirmReactivateBtn = document.getElementById('confirmReactivate');
    
    if (reactivateModalEl) {
        try {
            const reactivateModal = new bootstrap.Modal(reactivateModalEl);
        } catch (e) {
            console.warn('Could not initialize reactivate modal:', e);
        }
    }
    
    if (confirmReactivateBtn) {
        confirmReactivateBtn.addEventListener('click', handleReactivateEmployee);
    }
}

// Only define enrollFace if not on employee form page
if (!window.employeeFormPageLoaded) {
    function enrollFace(employeeId) {
        console.log('[employees.js] enrollFace called for employeeId:', employeeId);
        // Store employee ID globally for later use
        window.currentEnrollmentEmployeeId = employeeId;
        
        // Update the modal title with employee info
        const employeeNameElement = document.getElementById('enrollmentEmployeeName');
        if (employeeNameElement) {
            employeeNameElement.textContent = `Enrolling face for Employee ID: ${employeeId}`;
        }
        
        const faceEnrollmentModalEl = document.getElementById('faceEnrollmentModal');
        if (!faceEnrollmentModalEl) {
            console.error('[employees.js] Face enrollment modal element not found!');
            return;
        }

        // Get existing modal instance or create a new one
        let modal = bootstrap.Modal.getInstance(faceEnrollmentModalEl);
        if (!modal) {
        console.log('[employees.js] Creating new Bootstrap modal instance for faceEnrollmentModal');
        modal = new bootstrap.Modal(faceEnrollmentModalEl);
    }

    // Remove any previous 'shown.bs.modal' listeners to prevent multiple initializations
    faceEnrollmentModalEl.removeEventListener('shown.bs.modal', handleFaceEnrollmentModalShown);
    // Add a new listener that runs once after the modal is shown
    faceEnrollmentModalEl.addEventListener('shown.bs.modal', handleFaceEnrollmentModalShown, { once: true });    console.log('[employees.js] Showing faceEnrollmentModal');
    modal.show();
}
} // End of conditional block for employeeFormPageLoaded

// New handler function for when the modal is fully shown
if (!window.employeeFormPageLoaded) {
    function handleFaceEnrollmentModalShown() {
        console.log('[employees.js] faceEnrollmentModal event: shown.bs.modal. Calling initializeFaceEnrollmentCamera.');
        initializeFaceEnrollmentCamera();
    }
}

if (!window.employeeFormPageLoaded) {
    function initializeFaceEnrollmentCamera() {
    console.log('[employees.js] initializeFaceEnrollmentCamera called (direct button listeners version)');
    const modal = document.getElementById('faceEnrollmentModal');
    const video = document.getElementById('enrollmentVideo');
    const photosList = document.getElementById('photoThumbnails');
    const saveBtn = document.getElementById('saveEnrollment');
    const photoCountElement = document.getElementById('photoCount');
    const progressBar = document.getElementById('enrollmentProgress');
    let stream = null;
    let capturedPhotos = [];
    let cameraManager = null;

    if (!modal || !video || !photosList || !saveBtn || !photoCountElement || !progressBar) {
        console.error('[employees.js] Required elements not found for face enrollment.');
        return;
    }

    // Helper: update progress bar and count
    function updateEnrollmentProgress() {
        const progress = (capturedPhotos.length / 5) * 100;
        progressBar.style.width = `${progress}%`;
        photoCountElement.textContent = `${capturedPhotos.length} / 5`;
    }

    // Helper: remove photo
    window.removePhoto = function(index) {
        capturedPhotos.splice(index, 1);
        photosList.innerHTML = '';
        capturedPhotos.forEach((photo, i) => {
            const photoDiv = document.createElement('div');
            photoDiv.className = 'col-md-4 mb-2';
            photoDiv.innerHTML = `
                <div class="card">
                    <img src="${photo}" class="card-img-top" style="height: 120px; object-fit: cover;">
                    <div class="card-body p-2">
                        <button type="button" class="btn btn-sm btn-danger w-100" onclick="removePhoto(${i})">
                            Remove
                        </button>
                    </div>
                </div>
            `;
            photosList.appendChild(photoDiv);
        });
        updateEnrollmentProgress();
        saveBtn.disabled = capturedPhotos.length === 0;
        if (capturedPhotos.length === 0) {
            document.getElementById('capturedPhotos').classList.add('d-none');
        }
    };

    // Camera start logic
    async function startCamera(startCameraBtn, captureBtn) {
        if (!startCameraBtn || !captureBtn) return;
        startCameraBtn.disabled = true;
        startCameraBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting...';
        try {
            if (window.enhancedCameraManager) {
                cameraManager = window.enhancedCameraManager;
                const cameraResult = await cameraManager.detectAndInitializeCamera();
                if (cameraResult.success && cameraResult.stream) {
                    stream = cameraResult.stream;
                    video.srcObject = stream;
                    await new Promise((resolve) => {
                        video.addEventListener('loadedmetadata', resolve, { once: true });
                    });
                    await video.play();
                    captureBtn.disabled = false;
                    startCameraBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Camera Active';
                    showAlert('Camera started successfully with enhanced detection!', 'success');
                    return;
                }
            }
            // Fallback to standard camera
            const constraints = { 
                video: { 
                    width: { ideal: 640 }, 
                    height: { ideal: 480 },
                    facingMode: 'user'
                } 
            };
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
            await video.play();
            captureBtn.disabled = false;
            startCameraBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Camera Active';
            showAlert('Camera started successfully!', 'success');
        } catch (err) {
            console.error('Error accessing camera:', err);
            showAlert('Error accessing camera. Please check permissions.', 'danger');
            startCameraBtn.disabled = false;
            startCameraBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Start Camera';
        }
    }

    // Photo capture logic
    async function capturePhoto(captureBtn) {
        if (!video.videoWidth || !video.videoHeight) {
            showAlert('Camera not ready. Please wait.', 'warning');
            return;
        }
        captureBtn.disabled = true;
        captureBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Capturing...';
        try {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            const dataURL = canvas.toDataURL('image/jpeg', 0.8);
            if (window.faceRecognitionManager) {
                const qualityResult = await window.faceRecognitionManager.validateFaceQuality(dataURL);
                if (!qualityResult.valid) {
                    showAlert(`Photo quality check failed: ${qualityResult.message}. ${qualityResult.recommendations?.join(' ') || ''}`, 'warning');
                    captureBtn.disabled = false;
                    captureBtn.innerHTML = '<i class="fas fa-camera-retro me-2"></i>Capture Photo';
                    return;
                }
            }
            capturedPhotos.push(dataURL);
            // Add photo to preview
            const photoDiv = document.createElement('div');
            photoDiv.className = 'col-md-4 mb-2';
            photoDiv.innerHTML = `
                <div class="card">
                    <img src="${dataURL}" class="card-img-top" style="height: 120px; object-fit: cover;">
                    <div class="card-body p-2">
                        <button type="button" class="btn btn-sm btn-danger w-100" onclick="removePhoto(${capturedPhotos.length - 1})">
                            Remove
                        </button>
                    </div>
                </div>
            `;
            photosList.appendChild(photoDiv);
            updateEnrollmentProgress();
            document.getElementById('capturedPhotos').classList.remove('d-none');
            saveBtn.disabled = capturedPhotos.length === 0;
            showAlert(`Photo ${capturedPhotos.length} captured successfully!`, 'success');
        } catch (error) {
            console.error('Photo capture error:', error);
            showAlert('Failed to capture photo. Please try again.', 'danger');
        } finally {
            captureBtn.disabled = false;
            captureBtn.innerHTML = '<i class="fas fa-camera-retro me-2"></i>Capture Photo';
        }
    }

    // Remove previous listeners to avoid stacking
    const startCameraBtn = document.getElementById('startEnrollmentCamera');
    const captureBtn = document.getElementById('captureEnrollmentPhoto');
    if (startCameraBtn) {
        // Remove previous listener if any
        if (startCameraBtn._faceListener) {
            startCameraBtn.removeEventListener('click', startCameraBtn._faceListener);
        }
        const handler = function() {
            startCamera(startCameraBtn, captureBtn);
        };
        startCameraBtn.addEventListener('click', handler);
        startCameraBtn._faceListener = handler;
    }
    if (captureBtn) {
        if (captureBtn._faceListener) {
            captureBtn.removeEventListener('click', captureBtn._faceListener);
        }
        const handler = function() {
            capturePhoto(captureBtn);
        };
        captureBtn.addEventListener('click', handler);
        captureBtn._faceListener = handler;
    }

    // Modal close cleanup
    function cleanupOnClose() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        capturedPhotos = [];
        photosList.innerHTML = '';
        const captureBtn = document.getElementById('captureEnrollmentPhoto');
        const startCameraBtn = document.getElementById('startEnrollmentCamera');
        if (captureBtn) captureBtn.disabled = true;
        if (startCameraBtn) startCameraBtn.disabled = false;
        saveBtn.disabled = true;
        document.getElementById('capturedPhotos').classList.add('d-none');
        updateEnrollmentProgress();
    }
    // Remove previous close handler if any
    if (modal._faceCloseHandler) {
        modal.removeEventListener('hidden.bs.modal', modal._faceCloseHandler);
    }
    modal.addEventListener('hidden.bs.modal', cleanupOnClose);
    modal._faceCloseHandler = cleanupOnClose;

    // Save enrollment handler (no change)
    saveBtn.onclick = async function() {
        const employeeId = window.currentEnrollmentEmployeeId;
        if (!employeeId) {
            showAlert('Employee ID not found.', 'danger');
            return;
        }
        if (capturedPhotos.length === 0) {
            showAlert('Please capture at least one photo.', 'warning');
            return;
        }
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        try {
            let enrollmentResult;
            if (window.faceRecognitionManager) {
                enrollmentResult = await window.faceRecognitionManager.enrollFace(employeeId, capturedPhotos);
            } else {
                const response = await fetch(`/admin/api/employees/${employeeId}/enroll_face`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        photos: capturedPhotos
                    })
                });
                enrollmentResult = await response.json();
            }
            if (enrollmentResult.success) {
                showAlert(enrollmentResult.message || 'Face enrolled successfully!', 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showAlert(enrollmentResult.message || 'Face enrollment failed.', 'danger');
            }
        } catch (error) {
            console.error('Enrollment error:', error);
            showAlert('Error enrolling face recognition: ' + error.message, 'danger');
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save Enrollment';
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    };
    // Initial state    if (captureBtn) captureBtn.disabled = true;
    if (startCameraBtn) startCameraBtn.disabled = false;
    saveBtn.disabled = true;
    updateEnrollmentProgress();
    document.getElementById('capturedPhotos').classList.add('d-none');
}
} // End of conditional block for initializeFaceEnrollmentCamera

function resetPin(employeeId) {
    document.getElementById('resetEmployeeId').value = employeeId;
    const modal = new bootstrap.Modal(document.getElementById('pinResetModal'));
    modal.show();
}

function handlePinReset(event) {
    event.preventDefault();
    
    const employeeId = document.getElementById('resetEmployeeId').value;
    const newPin = document.getElementById('newPin').value;
    const confirmPin = document.getElementById('confirmPin').value;
    const requireChange = document.getElementById('requirePinChange').checked;
    
    if (newPin !== confirmPin) {
        showAlert('PINs do not match.', 'danger');
        return;
    }
    
    if (newPin.length < 4) {
        showAlert('PIN must be at least 4 digits.', 'danger');
        return;
    }
    
    // Submit PIN reset
    fetch(`/admin/api/employees/${employeeId}/reset_pin`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            new_pin: newPin,
            require_change: requireChange
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('pinResetModal'));
            modal.hide();
            document.getElementById('pinResetForm').reset();
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error resetting PIN.', 'danger');
    });
}

function deleteEmployee(employeeId) {
    document.getElementById('deleteEmployeeId').value = employeeId;
    
    // Try to get existing modal instance first
    const modalEl = document.getElementById('deleteEmployeeModal');
    let modal = bootstrap.Modal.getInstance(modalEl);
    
    if (!modal) {
        modal = new bootstrap.Modal(modalEl);
    }
    
    modal.show();
}

function terminateEmployee(employeeId) {
    document.getElementById('terminateEmployeeId').value = employeeId;
    document.getElementById('terminationReason').value = '';
    
    const modalEl = document.getElementById('terminateEmployeeModal');
    let modal = bootstrap.Modal.getInstance(modalEl);
    
    if (!modal) {
        modal = new bootstrap.Modal(modalEl);
    }
    
    modal.show();
}

function reactivateEmployee(employeeId) {
    document.getElementById('reactivateEmployeeId').value = employeeId;
    
    const modalEl = document.getElementById('reactivateEmployeeModal');
    let modal = bootstrap.Modal.getInstance(modalEl);
    
    if (!modal) {
        modal = new bootstrap.Modal(modalEl);
    }
    
    modal.show();
}

function handleDeleteEmployee() {
    const employeeId = document.getElementById('deleteEmployeeId').value;
    
    fetch(`/admin/api/employees/${employeeId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: 'permanent_delete'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error deleting employee.', 'danger');
    });
    
    // Hide modal
    const modalEl = document.getElementById('deleteEmployeeModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
}

function handleTerminateEmployee() {
    const employeeId = document.getElementById('terminateEmployeeId').value;
    const reason = document.getElementById('terminationReason').value;
    
    fetch(`/admin/api/employees/${employeeId}/terminate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error terminating employee.', 'danger');
    });
    
    // Hide modal
    const modalEl = document.getElementById('terminateEmployeeModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
}

function handleReactivateEmployee() {
    const employeeId = document.getElementById('reactivateEmployeeId').value;
    
    fetch(`/admin/api/employees/${employeeId}/reactivate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error reactivating employee.', 'danger');
    });
    
    // Hide modal
    const modalEl = document.getElementById('reactivateEmployeeModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
}

function showAlert(message, type) {
    // Create and show alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of page
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}
