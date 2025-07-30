/**
 * Attendance Records Management JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] Attendance records page loaded');
    
    // Initialize functionality
    initializeFilters();
    initializeModals();
    initializeExport();
    
    // Auto-apply filters when changed
    const filterForm = document.getElementById('attendanceFilters');
    if (filterForm) {
        const inputs = filterForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', applyFilters);
        });
    }
});

/**
 * Initialize filter functionality
 */
function initializeFilters() {
    const filterForm = document.getElementById('attendanceFilters');
    if (!filterForm) return;
    
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        applyFilters();
    });
    
    // Add clear filters button functionality
    const clearBtn = document.getElementById('clearFilters');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearFilters);
    }
}

/**
 * Apply current filter settings
 */
function applyFilters() {
    const form = document.getElementById('attendanceFilters');
    if (!form) return;
    
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    // Build query parameters
    for (let [key, value] of formData.entries()) {
        if (value.trim()) {
            params.append(key, value);
        }
    }
    
    // Reload page with filters
    const baseUrl = window.location.pathname;
    const newUrl = params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;
    window.location.href = newUrl;
}

/**
 * Clear all filters
 */
function clearFilters() {
    const form = document.getElementById('attendanceFilters');
    if (!form) return;
    
    // Clear all form inputs
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        if (input.type === 'date' || input.type === 'text') {
            input.value = '';
        } else if (input.type === 'select-one') {
            input.selectedIndex = 0;
        }
    });
    
    // Reload page without filters
    window.location.href = window.location.pathname;
}

/**
 * Initialize modal functionality
 */
function initializeModals() {
    // Record details modal
    const detailsModal = new bootstrap.Modal(document.getElementById('recordDetailsModal'));
    
    // Edit record modal
    const editModal = new bootstrap.Modal(document.getElementById('editRecordModal'));
    
    // Edit form submission
    const editForm = document.getElementById('editRecordForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveRecordEdit();
        });
    }
}

/**
 * View record details
 */
function viewRecord(recordId) {
    console.log('[DEBUG] Viewing record:', recordId);
    
    fetch(`/admin/api/attendance_record/${recordId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.record) {
                displayRecordDetails(data.record);
                const modal = new bootstrap.Modal(document.getElementById('recordDetailsModal'));
                modal.show();
            } else {
                showAlert('error', 'Failed to load record details');
            }
        })
        .catch(error => {
            console.error('[ERROR] Failed to fetch record details:', error);
            showAlert('error', 'Failed to load record details');
        });
}

/**
 * Display record details in modal
 */
function displayRecordDetails(record) {
    const content = document.getElementById('recordDetailsContent');
    if (!content) return;
    
    const timestamp = new Date(record.timestamp);
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <div class="text-center mb-3">
                    <img src="${record.employee.photo}" alt="${record.employee.name}" 
                         class="rounded-circle" style="width: 80px; height: 80px; object-fit: cover;">
                    <h6 class="mt-2">${record.employee.name}</h6>
                    <small class="text-muted">${record.employee.employee_id}</small>
                </div>
            </div>
            <div class="col-md-8">
                <table class="table table-borderless">
                    <tr>
                        <td><strong>Date:</strong></td>
                        <td>${timestamp.toLocaleDateString()}</td>
                    </tr>
                    <tr>
                        <td><strong>Time:</strong></td>
                        <td>${timestamp.toLocaleTimeString()}</td>
                    </tr>
                    <tr>
                        <td><strong>Action:</strong></td>
                        <td><span class="badge bg-${getActionColor(record.action_type)}">${record.action_type}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Terminal:</strong></td>
                        <td>${record.terminal_name || 'Unknown'}</td>
                    </tr>
                    <tr>
                        <td><strong>Department:</strong></td>
                        <td>${record.employee.department || 'Not specified'}</td>
                    </tr>
                </table>
            </div>
        </div>
    `;
}

/**
 * Edit record
 */
function editRecord(recordId) {
    console.log('[DEBUG] Editing record:', recordId);
    
    fetch(`/admin/api/attendance_record/${recordId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.record) {
                populateEditForm(data.record);
                const modal = new bootstrap.Modal(document.getElementById('editRecordModal'));
                modal.show();
            } else {
                showAlert('error', 'Failed to load record for editing');
            }
        })
        .catch(error => {
            console.error('[ERROR] Failed to fetch record for editing:', error);
            showAlert('error', 'Failed to load record for editing');
        });
}

/**
 * Populate edit form with record data
 */
function populateEditForm(record) {
    const form = document.getElementById('editRecordForm');
    if (!form) return;
    
    const timestamp = new Date(record.timestamp);
    
    // Set form values
    document.getElementById('editRecordId').value = record.record_id;
    document.getElementById('editTimestamp').value = timestamp.toISOString().slice(0, 16);
    document.getElementById('editActionType').value = record.action_type;
    document.getElementById('editNotes').value = record.notes || '';
}

/**
 * Save record edit
 */
function saveRecordEdit() {
    const form = document.getElementById('editRecordForm');
    if (!form) return;
    
    const recordId = document.getElementById('editRecordId').value;
    const timestamp = document.getElementById('editTimestamp').value;
    const actionType = document.getElementById('editActionType').value;
    const notes = document.getElementById('editNotes').value;
    
    if (!timestamp || !actionType) {
        showAlert('error', 'Please fill in all required fields');
        return;
    }
    
    const data = {
        timestamp: timestamp,
        action_type: actionType,
        notes: notes
    };
    
    fetch(`/admin/api/attendance_record/${recordId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Record updated successfully');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editRecordModal'));
            modal.hide();
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showAlert('error', data.error || 'Failed to update record');
        }
    })
    .catch(error => {
        console.error('[ERROR] Failed to update record:', error);
        showAlert('error', 'Failed to update record');
    });
}

/**
 * Delete record
 */
function deleteRecord(recordId) {
    if (!confirm('Are you sure you want to delete this attendance record? This action cannot be undone.')) {
        return;
    }
    
    console.log('[DEBUG] Deleting record:', recordId);
    
    fetch(`/admin/api/attendance_record/${recordId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Record deleted successfully');
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showAlert('error', data.error || 'Failed to delete record');
        }
    })
    .catch(error => {
        console.error('[ERROR] Failed to delete record:', error);
        showAlert('error', 'Failed to delete record');
    });
}

/**
 * Initialize export functionality
 */
function initializeExport() {
    const exportBtn = document.getElementById('exportAttendance');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportAttendance);
    }
}

/**
 * Export attendance records
 */
function exportAttendance() {
    console.log('[DEBUG] Exporting attendance records');
    
    // Get current filter values
    const form = document.getElementById('attendanceFilters');
    const params = new URLSearchParams();
    
    if (form) {
        const formData = new FormData(form);
        for (let [key, value] of formData.entries()) {
            if (value.trim()) {
                params.append(key, value);
            }
        }
    }
    
    const exportUrl = `/admin/api/export_attendance?${params.toString()}`;
    
    fetch(exportUrl)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Create and download CSV file
                const blob = new Blob([data.csv_data], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('success', 'Records exported successfully');
            } else {
                showAlert('error', data.error || 'Failed to export records');
            }
        })
        .catch(error => {
            console.error('[ERROR] Failed to export records:', error);
            showAlert('error', 'Failed to export records');
        });
}

/**
 * Get action color for badges
 */
function getActionColor(actionType) {
    switch (actionType.toLowerCase()) {
        case 'clock_in':
            return 'success';
        case 'clock_out':
            return 'danger';
        default:
            return 'secondary';
    }
}

/**
 * Show alert message
 */
function showAlert(type, message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of container
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}
