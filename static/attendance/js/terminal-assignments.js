/**
 * Terminal Assignment Management JavaScript
 * Handles CRUD operations for employee-terminal assignments
 */

class TerminalAssignmentManager {
    constructor() {
        this.assignments = [];
        this.filteredAssignments = [];
        this.currentEditAssignment = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadAssignments();
        this.loadSystemPolicy();
    }

    setupEventListeners() {
        // Add assignment form
        document.getElementById('saveAssignmentBtn').addEventListener('click', () => this.saveAssignment());
        
        // Update assignment form
        document.getElementById('updateAssignmentBtn').addEventListener('click', () => this.updateAssignment());
        
        // System policy
        document.getElementById('savePolicyBtn').addEventListener('click', () => this.saveSystemPolicy());
        
        // Refresh and filters
        document.getElementById('refreshAssignments').addEventListener('click', () => this.loadAssignments());
        document.getElementById('filterEmployee').addEventListener('change', () => this.applyFilters());
        document.getElementById('filterTerminal').addEventListener('change', () => this.applyFilters());
        
        // Modal reset handlers
        $('#addAssignmentModal').on('hidden.bs.modal', () => this.resetAddForm());
        $('#editAssignmentModal').on('hidden.bs.modal', () => this.resetEditForm());
    }

    async loadSystemPolicy() {
        try {
            const response = await fetch('/admin/api/system-config');
            if (response.ok) {
                const data = await response.json();
                const checkbox = document.getElementById('terminalsOpenByDefault');
                if (data.config && data.config.terminals_open_by_default !== undefined) {
                    checkbox.checked = data.config.terminals_open_by_default;
                }
            }
        } catch (error) {
            console.error('Error loading system policy:', error);
        }
    }

    async saveSystemPolicy() {
        try {
            const openByDefault = document.getElementById('terminalsOpenByDefault').checked;
            
            const response = await fetch('/admin/api/system-config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    terminals_open_by_default: openByDefault
                })
            });

            if (response.ok) {
                this.showToast('System policy updated successfully', 'success');
            } else {
                throw new Error('Failed to save policy');
            }
        } catch (error) {
            console.error('Error saving system policy:', error);
            this.showToast('Failed to save system policy', 'error');
        }
    }

    async loadAssignments() {
        try {
            const response = await fetch('/admin/terminal-management/api/assignments');
            if (response.ok) {
                const data = await response.json();
                this.assignments = data.assignments || [];
                this.applyFilters();
                this.showToast('Assignments loaded successfully', 'success');
            } else {
                throw new Error('Failed to load assignments');
            }
        } catch (error) {
            console.error('Error loading assignments:', error);
            this.showToast('Failed to load assignments', 'error');
            this.assignments = [];
            this.applyFilters();
        }
    }

    applyFilters() {
        const employeeFilter = document.getElementById('filterEmployee').value;
        const terminalFilter = document.getElementById('filterTerminal').value;

        this.filteredAssignments = this.assignments.filter(assignment => {
            const employeeMatch = !employeeFilter || assignment.employee_id === employeeFilter;
            const terminalMatch = !terminalFilter || assignment.terminal_id === terminalFilter;
            return employeeMatch && terminalMatch;
        });

        this.renderAssignments();
    }

    renderAssignments() {
        const tbody = document.getElementById('assignmentsTableBody');
        tbody.innerHTML = '';

        if (this.filteredAssignments.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted">
                        <i class="fas fa-inbox fa-2x mb-2"></i><br>
                        No assignments found
                    </td>
                </tr>
            `;
            return;
        }

        this.filteredAssignments.forEach(assignment => {
            const row = this.createAssignmentRow(assignment);
            tbody.appendChild(row);
        });
    }

    createAssignmentRow(assignment) {
        const row = document.createElement('tr');
        row.className = assignment.is_active ? '' : 'table-secondary';

        // Status badge
        const statusClass = assignment.is_active ? 'bg-success' : 'bg-secondary';
        const statusText = assignment.is_active ? 'Active' : 'Inactive';

        // Time restrictions
        let timeRestrictions = 'None';
        if (assignment.allowed_time_start && assignment.allowed_time_end) {
            timeRestrictions = `${assignment.allowed_time_start} - ${assignment.allowed_time_end}`;
        }

        // Days
        let days = 'All Days';
        if (assignment.allowed_days && assignment.allowed_days.length > 0) {
            days = assignment.allowed_days.map(day => day.charAt(0).toUpperCase() + day.slice(1)).join(', ');
        }

        row.innerHTML = `
            <td>
                <div class="fw-bold">${assignment.employee_name || 'Unknown'}</div>
                <small class="text-muted">${assignment.employee_id}</small>
            </td>
            <td>
                <div class="fw-bold">${assignment.terminal_name || 'Unknown'}</div>
                <small class="text-muted">${assignment.terminal_location || ''}</small>
            </td>
            <td>
                <span class="badge ${assignment.assignment_type === 'exclusive' ? 'bg-primary' : 'bg-info'}">
                    ${assignment.assignment_type || 'Shared'}
                </span>
                ${assignment.priority > 1 ? `<br><small class="text-muted">Priority: ${assignment.priority}</small>` : ''}
            </td>
            <td><small>${timeRestrictions}</small></td>
            <td><small>${days}</small></td>
            <td>
                <span class="badge ${statusClass}">${statusText}</span>
                ${assignment.expiry_date ? `<br><small class="text-muted">Expires: ${new Date(assignment.expiry_date).toLocaleDateString()}</small>` : ''}
            </td>
            <td>
                <div>${assignment.assigned_by || 'System'}</div>
                <small class="text-muted">${new Date(assignment.assigned_date).toLocaleDateString()}</small>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary btn-sm" onclick="assignmentManager.editAssignment('${assignment.assignment_id}')" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-success btn-sm" onclick="assignmentManager.testAccess('${assignment.employee_id}', '${assignment.terminal_id}')" title="Test Access">
                        <i class="fas fa-check-circle"></i>
                    </button>
                    <button class="btn btn-outline-danger btn-sm" onclick="assignmentManager.deleteAssignment('${assignment.assignment_id}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;

        return row;
    }

    async saveAssignment() {
        try {
            const formData = this.getFormData('addAssignmentForm');
            
            if (!formData.employee_id || !formData.terminal_id) {
                this.showToast('Please select both employee and terminal', 'error');
                return;
            }

            const response = await fetch('/admin/terminal-management/api/assignments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const data = await response.json();
                this.showToast('Assignment created successfully', 'success');
                $('#addAssignmentModal').modal('hide');
                this.loadAssignments();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create assignment');
            }
        } catch (error) {
            console.error('Error saving assignment:', error);
            this.showToast('Failed to create assignment: ' + error.message, 'error');
        }
    }

    async editAssignment(assignmentId) {
        try {
            const response = await fetch(`/admin/terminal-management/api/assignments/${assignmentId}`);
            if (response.ok) {
                const data = await response.json();
                this.currentEditAssignment = data.assignment;
                this.populateEditForm(data.assignment);
                $('#editAssignmentModal').modal('show');
            } else {
                throw new Error('Failed to load assignment');
            }
        } catch (error) {
            console.error('Error loading assignment:', error);
            this.showToast('Failed to load assignment for editing', 'error');
        }
    }

    async updateAssignment() {
        try {
            if (!this.currentEditAssignment) {
                throw new Error('No assignment selected for editing');
            }

            const formData = this.getFormData('editAssignmentForm');
            
            const response = await fetch(`/admin/terminal-management/api/assignments/${this.currentEditAssignment.assignment_id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showToast('Assignment updated successfully', 'success');
                $('#editAssignmentModal').modal('hide');
                this.loadAssignments();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to update assignment');
            }
        } catch (error) {
            console.error('Error updating assignment:', error);
            this.showToast('Failed to update assignment: ' + error.message, 'error');
        }
    }

    async deleteAssignment(assignmentId) {
        if (!confirm('Are you sure you want to delete this assignment?')) {
            return;
        }

        try {
            const response = await fetch(`/admin/terminal-management/api/assignments/${assignmentId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showToast('Assignment deleted successfully', 'success');
                this.loadAssignments();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete assignment');
            }
        } catch (error) {
            console.error('Error deleting assignment:', error);
            this.showToast('Failed to delete assignment: ' + error.message, 'error');
        }
    }

    async testAccess(employeeId, terminalId) {
        try {
            const response = await fetch('/admin/terminal-management/api/check-access', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    employee_id: employeeId,
                    terminal_id: terminalId
                })
            });

            if (response.ok) {
                const data = await response.json();
                const message = data.has_access 
                    ? 'Employee has access to this terminal' 
                    : `Access denied: ${data.message || 'Employee is not authorized'}`;
                const type = data.has_access ? 'success' : 'warning';
                this.showToast(message, type);
            } else {
                throw new Error('Failed to test access');
            }
        } catch (error) {
            console.error('Error testing access:', error);
            this.showToast('Failed to test access', 'error');
        }
    }

    getFormData(formId) {
        const form = document.getElementById(formId);
        const formData = new FormData(form);
        const data = {};

        // Handle regular fields
        for (let [key, value] of formData.entries()) {
            if (key !== 'allowed_days') {
                data[key] = value;
            }
        }

        // Handle checkboxes for allowed_days
        const allowedDays = [];
        const dayCheckboxes = form.querySelectorAll('input[name="allowed_days"]:checked');
        dayCheckboxes.forEach(checkbox => {
            allowedDays.push(checkbox.value);
        });
        data.allowed_days = allowedDays;

        return data;
    }

    populateEditForm(assignment) {
        // Populate basic fields
        document.getElementById('editAssignmentId').value = assignment.assignment_id;
        document.getElementById('editEmployeeSelect').value = assignment.employee_id;
        document.getElementById('editTerminalSelect').value = assignment.terminal_id;
        document.getElementById('editAssignmentType').value = assignment.assignment_type || 'exclusive';
        document.getElementById('editPriority').value = assignment.priority || 1;
        document.getElementById('editIsActive').checked = assignment.is_active !== false;
        
        // Time restrictions
        document.getElementById('editAllowedTimeStart').value = assignment.allowed_time_start || '';
        document.getElementById('editAllowedTimeEnd').value = assignment.allowed_time_end || '';
        
        // Days
        const dayCheckboxes = document.querySelectorAll('#editAllowedDays input[type="checkbox"]');
        dayCheckboxes.forEach(checkbox => {
            checkbox.checked = assignment.allowed_days && assignment.allowed_days.includes(checkbox.value);
        });
        
        // Other fields
        document.getElementById('editExpiryDate').value = assignment.expiry_date || '';
        document.getElementById('editReason').value = assignment.reason || '';
        document.getElementById('editNotes').value = assignment.notes || '';
    }

    resetAddForm() {
        document.getElementById('addAssignmentForm').reset();
    }

    resetEditForm() {
        document.getElementById('editAssignmentForm').reset();
        this.currentEditAssignment = null;
    }

    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to toast container or create one
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        toastContainer.appendChild(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.assignmentManager = new TerminalAssignmentManager();
});

// Global functions for onclick handlers
function editAssignment(assignmentId) {
    window.assignmentManager.editAssignment(assignmentId);
}

function deleteAssignment(assignmentId) {
    window.assignmentManager.deleteAssignment(assignmentId);
}

function testAccess(employeeId, terminalId) {
    window.assignmentManager.testAccess(employeeId, terminalId);
}
