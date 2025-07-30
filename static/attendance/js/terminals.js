// Terminals-related logic

async function loadTerminals() {
    try {
        const response = await fetch('/admin/terminal-management/api/terminals');
        const data = await response.json();

        if (data.terminals) {
            terminalsData = data.terminals;
            updateTerminalsTable();
            updateStatistics();
        }
    } catch (error) {
        console.error('Error loading terminals:', error);
        showAlert('error', 'Failed to load terminals');
    }
}

function updateTerminalsTable() {
    const tbody = document.getElementById('terminalsTableBody');

    if (terminalsData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    <i class="fas fa-desktop fa-3x mb-3 d-block"></i>
                    <h5>No terminals configured</h5>
                    <p>Add your first terminal to get started with attendance tracking</p>
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addTerminalModal">
                        <i class="fas fa-plus me-2"></i>Add Terminal
                    </button>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = terminalsData.map(terminal => {
        const statusBadge = getStatusBadge(terminal.status);
        const featureBadges = getFeatureBadges(terminal);

        return `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="me-3">
                            <i class="fas fa-desktop fa-2x text-primary"></i>
                        </div>
                        <div>
                            <div class="fw-bold">${terminal.name}</div>
                            <div class="text-muted small">${terminal.id}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="fw-bold">${terminal.location}</div>
                    <div class="text-muted small">${terminal.description || 'No description'}</div>
                </td>
                <td>
                    <span class="badge bg-secondary">${terminal.ip_address || 'Not Set'}</span>
                </td>
                <td>${statusBadge}</td>
                <td><div class="d-flex gap-1">${featureBadges}</div></td>
                <td>
                    <div class="text-muted small">
                        ${terminal.last_activity || 'Never'}
                    </div>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editTerminal('${terminal.id}')" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="pingTerminal('${terminal.id}')" title="Ping">
                            <i class="fas fa-wifi"></i>
                        </button>
                        <button class="btn btn-outline-warning" onclick="configureTerminal('${terminal.id}')" title="Configure">
                            <i class="fas fa-cog"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteTerminal('${terminal.id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function getStatusBadge(status) {
    switch(status) {
        case 'online':
            return '<span class="badge bg-success">Online</span>';
        case 'offline':
            return '<span class="badge bg-danger">Offline</span>';
        case 'unknown':
        default:
            return '<span class="badge bg-secondary">Unknown</span>';
    }
}

function getFeatureBadges(terminal) {
    const badges = [];

    if (terminal.face_recognition_enabled) {
        badges.push('<span class="badge bg-success" title="Face Recognition"><i class="fas fa-user-check"></i></span>');
    }
    if (terminal.pin_enabled) {
        badges.push('<span class="badge bg-info" title="PIN Support"><i class="fas fa-key"></i></span>');
    }
    if (terminal.card_enabled) {
        badges.push('<span class="badge bg-warning" title="Card/Password"><i class="fas fa-id-card"></i></span>');
    }

    return badges.join('');
}

function updateStatistics() {
    const total = terminalsData.length;
    const online = terminalsData.filter(t => t.status === 'online').length;
    const offline = terminalsData.filter(t => t.status === 'offline').length;
    const faceRecognition = terminalsData.filter(t => t.face_recognition_enabled).length;

    document.getElementById('totalTerminals').textContent = total;
    document.getElementById('onlineTerminals').textContent = online;
    document.getElementById('offlineTerminals').textContent = offline;
    document.getElementById('faceRecognitionTerminals').textContent = faceRecognition;
}
