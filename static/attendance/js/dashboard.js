/**
 * Admin Dashboard JavaScript
 * Handles dashboard interactions and real-time updates
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Set up event listeners
    setupEventListeners();
    
    // Start real-time updates
    startRealTimeUpdates();
});

function initializeDashboard() {
    // Update current time display
    updateTimeDisplay();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    console.log('Dashboard initialized');
}

function setupEventListeners() {
    // Refresh activity button
    const refreshBtn = document.getElementById('refreshActivity');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshTodayActivity);
    }
    
    // Present Today card click
    const presentTodayCard = document.getElementById('presentTodayCard');
    if (presentTodayCard) {
        presentTodayCard.addEventListener('click', showPresentEmployees);
    }
      // Late Today card click
    const lateTodayCard = document.getElementById('lateTodayCard');
    if (lateTodayCard) {
        lateTodayCard.addEventListener('click', showLateEmployees);
    }
    
    // Absent Today card click
    const absentTodayCard = document.getElementById('absentTodayCard');
    if (absentTodayCard) {
        absentTodayCard.addEventListener('click', showAbsentEmployees);
    }
    
    // Export data button
    const exportBtn = document.getElementById('exportData');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportData);
    }
    
    // System health button
    const healthBtn = document.getElementById('systemHealth');
    if (healthBtn) {
        healthBtn.addEventListener('click', checkSystemHealth);
    }
}

function updateTimeDisplay() {
    const now = new Date();
    
    // Update time
    const timeElement = document.getElementById('dashboardTime');
    if (timeElement) {
        timeElement.textContent = now.toLocaleTimeString('en-ZA', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    }
    
    // Update date
    const dateElement = document.getElementById('dashboardDate');
    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('en-ZA', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

function startRealTimeUpdates() {
    // Update time every second
    setInterval(updateTimeDisplay, 1000);
    
    // Refresh activity every 30 seconds
    setInterval(refreshTodayActivity, 30000);
    
    // Check system status every 5 minutes
    setInterval(updateSystemStatus, 300000);
}

function refreshTodayActivity() {
    const tbody = document.getElementById('todayActivity');
    if (!tbody) return;
    
    // Add loading indicator
    const refreshBtn = document.getElementById('refreshActivity');
    if (refreshBtn) {
        const originalHtml = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        refreshBtn.disabled = true;
        
        // Restore button after delay
        setTimeout(() => {
            refreshBtn.innerHTML = originalHtml;
            refreshBtn.disabled = false;
        }, 1000);
    }
    
    // Show loading in activity table
    tbody.innerHTML = '<tr><td colspan="5" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Refreshing activity...</td></tr>';
    
    // Fetch latest activity
    fetch('/admin/api/today-activity')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateActivityTable(data.activity);
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No activity found</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error refreshing activity:', error);
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading activity data</td></tr>';
        });
}

function updateActivityTable(activities) {
    const tbody = document.getElementById('todayActivity');
    if (!tbody) return;
    
    // Reset the activity header title if it was changed
    const cardTitle = tbody.closest('.card').querySelector('.card-title');
    if (cardTitle) {
        cardTitle.innerHTML = '<i class="fas fa-clock me-2"></i>Today\'s Activity';
    }
    
    // Remove back button if exists
    const backBtn = tbody.closest('.card').querySelector('.back-to-activity-btn');
    if (backBtn) {
        backBtn.remove();
    }
    
    if (!activities || activities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No activity today</td></tr>';
        return;
    }
    
    let html = '';
    activities.forEach(record => {
        const statusBadge = record.is_late ? 
            '<span class="badge bg-warning">Late</span>' : 
            record.is_early ? 
            '<span class="badge bg-info">Early</span>' :
            '<span class="badge bg-success">On Time</span>';
        
        const photoHtml = record.employee.photo ? 
            `<img src="${record.employee.photo}" alt="${record.employee.name}" class="rounded-circle" width="32" height="32">` :
            '<i class="fas fa-user-circle fa-2x text-muted"></i>';
        
        html += `
        <tr>
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar me-2">${photoHtml}</div>
                    <div>
                        <div class="fw-bold">${record.employee.name}</div>
                        <small class="text-muted">${record.employee.employee_id}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-${record.action_color}">
                    <i class="fas fa-${record.action_icon} me-1"></i>
                    ${record.action_type}
                </span>
            </td>
            <td>${record.timestamp}</td>
            <td>
                <small class="text-muted">${record.ip_address}</small>
            </td>
            <td>${statusBadge}</td>
        </tr>`;
    });
      tbody.innerHTML = html;
}

function createActivityRow(activity) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            <div class="d-flex align-items-center">
                <div class="avatar me-2">
                    ${activity.employee.photo ? 
                        `<img src="${activity.employee.photo}" alt="${activity.employee.name}" class="rounded-circle" width="32" height="32">` :
                        '<i class="fas fa-user-circle fa-2x text-muted"></i>'
                    }
                </div>
                <div>
                    <div class="fw-bold">${activity.employee.name}</div>
                    <small class="text-muted">${activity.employee.employee_id}</small>
                </div>
            </div>
        </td>
        <td>
            <span class="badge bg-${activity.action_color}">
                <i class="fas fa-${activity.action_icon} me-1"></i>
                ${activity.action_type}
            </span>
        </td>
        <td>${activity.time}</td>
        <td>
            <span class="badge bg-${activity.status_color}">${activity.status}</span>
        </td>
    `;
    return row;
}

function exportData() {
    const exportBtn = document.getElementById('exportData');
    if (exportBtn) {
        const originalHtml = exportBtn.innerHTML;
        exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Exporting...';
        exportBtn.disabled = true;
        
        // Simulate export process
        setTimeout(() => {
            // Create download link for CSV export
            const csvData = generateCSVData();
            const blob = new Blob([csvData], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            // Restore button
            exportBtn.innerHTML = originalHtml;
            exportBtn.disabled = false;
            
            // Show success message
            showNotification('Data exported successfully', 'success');
        }, 2000);
    }
}

function generateCSVData() {
    // This would normally fetch real data from the server
    return `Employee ID,Name,Date,Time In,Time Out,Hours Worked,Status
EMP001,John Smith,${new Date().toISOString().split('T')[0]},08:00,17:00,9.0,Present
EMP002,Sarah Johnson,${new Date().toISOString().split('T')[0]},08:15,17:00,8.75,Late
EMP003,Michael Brown,${new Date().toISOString().split('T')[0]},18:00,06:00,10.0,Present`;
}

function checkSystemHealth() {
    const healthBtn = document.getElementById('systemHealth');
    if (healthBtn) {
        const originalHtml = healthBtn.innerHTML;
        healthBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Checking...';
        healthBtn.disabled = true;
        
        // Simulate health check
        setTimeout(() => {
            healthBtn.innerHTML = originalHtml;
            healthBtn.disabled = false;
            
            // Show health status
            showSystemHealthModal();
        }, 1500);
    }
}

function showSystemHealthModal() {
    // Create modal dynamically
    const modalHtml = `
        <div class="modal fade" id="systemHealthModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-heartbeat me-2"></i>System Health Check
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="health-item mb-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-database me-2"></i>Database Connection</span>
                                <span class="badge bg-success">Healthy</span>
                            </div>
                        </div>
                        <div class="health-item mb-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-camera me-2"></i>Face Recognition Service</span>
                                <span class="badge bg-success">Online</span>
                            </div>
                        </div>
                        <div class="health-item mb-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-memory me-2"></i>Memory Usage</span>
                                <span class="text-muted">65%</span>
                            </div>
                        </div>
                        <div class="health-item mb-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-hdd me-2"></i>Disk Space</span>
                                <span class="text-muted">42% used</span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('systemHealthModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add new modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('systemHealthModal'));
    modal.show();
}

function updateSystemStatus() {
    // Fetch system status from server
    fetch('/admin/api/system-status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update status indicators
                updateStatusIndicators(data.status);
            }
        })
        .catch(error => {
            console.error('Error updating system status:', error);
        });
}

function updateStatusIndicators(status) {
    // Update face recognition status
    const faceRecognitionStatus = document.querySelector('.system-status .face-recognition');
    if (faceRecognitionStatus && status.face_recognition !== undefined) {
        updateStatusBadge(faceRecognitionStatus, status.face_recognition);
    }
    
    // Update database status
    const databaseStatus = document.querySelector('.system-status .database');
    if (databaseStatus && status.database !== undefined) {
        updateStatusBadge(databaseStatus, status.database);
    }
}

function updateStatusBadge(element, isOnline) {
    const badge = element.querySelector('.badge');
    if (badge) {
        if (isOnline) {
            badge.className = 'badge bg-success';
            badge.innerHTML = '<i class="fas fa-check-circle"></i> Online';
        } else {
            badge.className = 'badge bg-danger';
            badge.innerHTML = '<i class="fas fa-times-circle"></i> Offline';
        }
    }
}

function showNotification(message, type = 'info') {
    // Create notification
    const notificationHtml = `
        <div class="alert alert-${type} alert-dismissible fade show notification" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Add to page
    document.body.insertAdjacentHTML('beforeend', notificationHtml);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        const notifications = document.querySelectorAll('.notification');
        if (notifications.length > 0) {
            notifications[notifications.length - 1].remove();
        }
    }, 5000);
}

function showPresentEmployees() {
    console.log('Present Today card clicked - showing detailed employee list');
    
    // Add visual feedback to the card
    const card = document.getElementById('presentTodayCard');
    if (card) {
        card.style.opacity = '0.8';
        setTimeout(() => {
            card.style.opacity = '1';
        }, 200);
    }
    
    // Show loading in activity table
    const tbody = document.getElementById('todayActivity');
    if (!tbody) {
        console.error('todayActivity table body not found!');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="5" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Loading present employees...</td></tr>';
    
    // Fetch present employees data
    console.log('Fetching present employees from API...');
    fetch('/admin/api/present-employees')
        .then(response => {
            console.log('API Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('API Response data:', data);
            if (data.success && data.present_employees) {
                console.log(`Found ${data.present_employees.length} present employees`);
                displayPresentEmployees(data.present_employees);
            } else {
                console.log('No present employees found or API error:', data);
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No employees currently present</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error fetching present employees:', error);
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading employee data: ' + error.message + '</td></tr>';
        });
}

function displayPresentEmployees(employees) {
    console.log('displayPresentEmployees called with:', employees);
    
    const tbody = document.getElementById('todayActivity');
    if (!tbody) {
        console.error('todayActivity table body not found in displayPresentEmployees!');
        return;
    }
    
    if (employees.length === 0) {
        console.log('No employees to display');
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No employees currently present</td></tr>';
        return;
    }
    
    console.log(`Displaying ${employees.length} present employees`);
    let html = '';
    employees.forEach((emp, index) => {
        console.log(`Processing employee ${index + 1}:`, emp);
        
        const statusBadge = emp.is_late ? 
            '<span class="badge bg-warning">Late</span>' : 
            '<span class="badge bg-success">Present</span>';
        
        const photoHtml = emp.employee.photo ? 
            `<img src="${emp.employee.photo}" alt="${emp.employee.name}" class="rounded-circle" width="32" height="32">` :
            '<i class="fas fa-user-circle fa-2x text-muted"></i>';
        
        html += `
        <tr class="present-employee-row">
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar me-2">${photoHtml}</div>
                    <div>
                        <div class="fw-bold">${emp.employee.name}</div>
                        <small class="text-muted">${emp.employee.employee_id} • ${emp.employee.department}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-${emp.action_color}">
                    <i class="fas fa-${emp.action_icon} me-1"></i>
                    ${emp.action_type}
                </span>
            </td>
            <td>
                <div class="fw-bold">${emp.timestamp}</div>
                <small class="text-muted">Clocked in</small>
            </td>
            <td>
                <div class="d-flex flex-column">
                    <small class="text-muted">${emp.ip_address}</small>
                    <small class="text-muted">${emp.terminal}</small>
                </div>
            </td>
            <td>${statusBadge}</td>
        </tr>`;
    });
    
    console.log('Generated HTML:', html);
    tbody.innerHTML = html;
    
    // Update the activity header to show we're viewing present employees
    const cardTitle = document.querySelector('#todayActivity').closest('.card').querySelector('.card-title');
    if (cardTitle) {
        const originalTitle = cardTitle.innerHTML;
        cardTitle.innerHTML = '<i class="fas fa-users me-2"></i>Currently Present Employees';
        
        // Add a button to go back to regular activity view
        const cardHeader = cardTitle.closest('.card-header');
        if (cardHeader && !cardHeader.querySelector('.back-to-activity-btn')) {
            const backBtn = document.createElement('button');
            backBtn.className = 'btn btn-sm btn-outline-secondary back-to-activity-btn ms-2';
            backBtn.innerHTML = '<i class="fas fa-arrow-left me-1"></i>Back to Activity';
            backBtn.onclick = () => {
                cardTitle.innerHTML = originalTitle;
                backBtn.remove();
                refreshTodayActivity();
            };
            cardTitle.parentNode.appendChild(backBtn);
        }
    }
      console.log(`Displayed ${employees.length} present employees`);
}

function showLateEmployees() {
    console.log('Late Today card clicked - showing detailed late employee list');
    
    // Add visual feedback to the card
    const card = document.getElementById('lateTodayCard');
    if (card) {
        card.style.opacity = '0.8';
        setTimeout(() => {
            card.style.opacity = '1';
        }, 200);
    }
    
    // Show loading in activity table
    const tbody = document.getElementById('todayActivity');
    if (!tbody) {
        console.error('todayActivity table body not found!');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="5" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Loading late employees...</td></tr>';
    
    // Fetch late employees data
    console.log('Fetching late employees from API...');
    fetch('/admin/api/late-employees')
        .then(response => {
            console.log('API Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('API Response data:', data);
            if (data.success && data.late_employees) {
                console.log(`Found ${data.late_employees.length} late employees`);
                displayLateEmployees(data.late_employees);
            } else {
                console.log('No late employees found or API error:', data);
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No employees were late today</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error fetching late employees:', error);
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading employee data: ' + error.message + '</td></tr>';
        });
}

function displayLateEmployees(employees) {
    console.log('displayLateEmployees called with:', employees);
    
    const tbody = document.getElementById('todayActivity');
    if (!tbody) {
        console.error('todayActivity table body not found in displayLateEmployees!');
        return;
    }
    
    if (employees.length === 0) {
        console.log('No late employees to display');
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No employees were late today</td></tr>';
        return;
    }
    
    console.log(`Displaying ${employees.length} late employees`);
    let html = '';
    employees.forEach((emp, index) => {
        console.log(`Processing late employee ${index + 1}:`, emp);
        
        const statusBadge = '<span class="badge bg-warning">Late</span>';
        
        const photoHtml = emp.employee.photo ? 
            `<img src="${emp.employee.photo}" alt="${emp.employee.name}" class="rounded-circle" width="32" height="32">` :
            '<i class="fas fa-user-circle fa-2x text-muted"></i>';
        
        // Calculate how late they were
        const lateText = emp.minutes_late ? `${emp.minutes_late} min late` : 'Late arrival';
        
        html += `
        <tr class="late-employee-row">
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar me-2">${photoHtml}</div>
                    <div>
                        <div class="fw-bold">${emp.employee.name}</div>
                        <small class="text-muted">${emp.employee.employee_id} • ${emp.employee.department}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-${emp.action_color}">
                    <i class="fas fa-${emp.action_icon} me-1"></i>
                    ${emp.action_type}
                </span>
            </td>
            <td>
                <div class="fw-bold">${emp.timestamp}</div>
                <small class="text-warning">${lateText}</small>
            </td>
            <td>
                <div class="d-flex flex-column">
                    <small class="text-muted">${emp.ip_address}</small>
                    <small class="text-muted">${emp.terminal}</small>
                </div>
            </td>
            <td>${statusBadge}</td>
        </tr>`;
    });
    
    console.log('Generated HTML:', html);
    tbody.innerHTML = html;
    
    // Update the activity header to show we're viewing late employees
    const cardTitle = document.querySelector('#todayActivity').closest('.card').querySelector('.card-title');
    if (cardTitle) {
        const originalTitle = cardTitle.innerHTML;
        cardTitle.innerHTML = '<i class="fas fa-clock me-2"></i>Late Employees Today';
        
        // Add a button to go back to regular activity view
        const cardHeader = cardTitle.closest('.card-header');
        if (cardHeader && !cardHeader.querySelector('.back-to-activity-btn')) {
            const backBtn = document.createElement('button');
            backBtn.className = 'btn btn-sm btn-outline-secondary back-to-activity-btn ms-2';
            backBtn.innerHTML = '<i class="fas fa-arrow-left me-1"></i>Back to Activity';
            backBtn.onclick = () => {
                cardTitle.innerHTML = originalTitle;
                backBtn.remove();
                refreshTodayActivity();
            };
            cardTitle.parentNode.appendChild(backBtn);
        }
    }
    
    console.log(`Displayed ${employees.length} late employees`);
}

// Utility functions
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('en-ZA', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function formatDate(timestamp) {
    return new Date(timestamp).toLocaleDateString('en-ZA');
}

function showAbsentEmployees() {
    console.log('Absent Today card clicked - showing detailed absent employee list');
    
    // Add visual feedback to the card
    const card = document.getElementById('absentTodayCard');
    if (card) {
        card.style.opacity = '0.8';
        setTimeout(() => {
            card.style.opacity = '1';
        }, 200);
    }
    
    // Show loading in activity table
    const tbody = document.getElementById('todayActivity');
    if (!tbody) {
        console.error('todayActivity table body not found!');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="5" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Loading absent employees...</td></tr>';
    
    // Fetch absent employees data
    console.log('Fetching absent employees from API...');
    fetch('/admin/api/absent-employees')
        .then(response => {
            console.log('API Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('API Response data:', data);
            if (data.success && data.absent_employees) {
                console.log(`Found ${data.absent_employees.length} absent employees`);
                displayAbsentEmployees(data.absent_employees);
            } else {
                console.log('No absent employees found or API error:', data);
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">All employees are present today</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error fetching absent employees:', error);
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading employee data: ' + error.message + '</td></tr>';
        });
}

function displayAbsentEmployees(employees) {
    console.log('displayAbsentEmployees called with:', employees);
    
    const tbody = document.getElementById('todayActivity');
    if (!tbody) {
        console.error('todayActivity table body not found in displayAbsentEmployees!');
        return;
    }
    
    if (employees.length === 0) {
        console.log('No absent employees to display');
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">All employees are present today</td></tr>';
        return;
    }
    
    console.log(`Displaying ${employees.length} absent employees`);
    let html = '';
    employees.forEach((emp, index) => {
        console.log(`Processing absent employee ${index + 1}:`, emp);
        
        const statusBadge = `<span class="badge bg-${emp.action_color}">Absent</span>`;
        
        html += `
        <tr class="absent-employee-row">
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar me-2"><img src="${emp.employee.photo}" alt="${emp.employee.name}" class="rounded-circle" width="32" height="32"></div>
                    <div>
                        <div class="fw-bold">${emp.employee.name}</div>
                        <small class="text-muted">${emp.employee.employee_id} • ${emp.employee.department}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-${emp.action_color}">
                    <i class="fas fa-${emp.action_icon} me-1"></i>
                    ${emp.action_type}
                </span>
            </td>
            <td>
                <div class="fw-bold">Last seen: ${emp.timestamp}</div>
                <small class="text-muted">${emp.days_absent > 0 ? emp.days_absent + ' day(s) absent' : 'Today'}</small>
            </td>
            <td>
                <div class="d-flex flex-column">
                    <small class="text-muted">${emp.ip_address}</small>
                    <small class="text-muted">${emp.terminal}</small>
                </div>
            </td>
            <td>${statusBadge}</td>
        </tr>
        `;
    });
    
    console.log('Generated HTML:', html);
    tbody.innerHTML = html;
    console.log(`Displayed ${employees.length} absent employees`);
}

// Export functions for external use
window.Dashboard = {
    refreshTodayActivity,
    exportData,
    checkSystemHealth,
    showNotification
};
