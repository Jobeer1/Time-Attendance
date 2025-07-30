// Discovery-related logic


function updateDiscoveryStatus(message) {
    const statusElement = document.getElementById('discoveryStatus');
    if (statusElement) {
        statusElement.textContent = message;
    }
}

async function discoverStaticDevices() {
    try {
        // Show progress bar
        showDiscoveryProgress('Static Discovery', 'Fetching cached devices and ARP table...');

        // Fetch cached devices and ARP table findings
        let cachedDevices = [];
        let arpTable = [];
        try {
            const response = await fetch('/admin/terminal-management/api/cached-devices');
            if (response.ok) {
                const data = await response.json();
                cachedDevices = data.cached_devices || [];
                arpTable = data.arp_table || [];
            } else {
                console.error('Failed to load cached devices and ARP table:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading cached devices and ARP table:', error);
        }

        // Display ARP devices and other devices in the same table
        updateDiscoveredDevicesTable(cachedDevices, arpTable);

        // Show progress bar at 10% to indicate start
        const progressBar = document.getElementById('discoveryProgressBar');
        const progressText = document.getElementById('discoveryProgressText');
        progressBar.style.width = '10%';
        progressText.textContent = '10%';

        // Get network settings with proper error handling
        let settings = {};
        try {
            const response = await fetch('/admin/terminal-management/api/network-settings');
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.settings) {
                    settings = result.settings;
                } else {
                    console.error('Failed to load network settings:', result.error);
                }
            } else {
                console.error('Failed to load network settings:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading network settings:', error);
        }

        // Provide defaults if settings are missing
        const ip_range_start = settings.ip_range_start || '192.168.1.1';
        const ip_range_end = settings.ip_range_end || '192.168.1.254';
        const scan_timeout = settings.scan_timeout || 5;
        const concurrent_scans = settings.concurrent_scans || 10;

        // Show loading state
        showLoading();
        
        // Start discovery with the parameters
        const response = await fetch('/admin/terminal-management/api/discover-static-devices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ip_range_start,
                ip_range_end,
                scan_timeout,
                concurrent_scans
            })
        });

        // Show progress bar at 30% after request sent
        progressBar.style.width = '30%';
        progressText.textContent = '30%';
        updateDiscoveryStatus('Scanning network...');

        if (!response.ok) {
            throw new Error(`Discovery failed: ${response.statusText}`);
        }

        const result = await response.json();

        // Show progress bar at 80% after response received
        progressBar.style.width = '80%';
        progressText.textContent = '80%';
        updateDiscoveryStatus('Processing results...');

        // Finalize progress bar
        setTimeout(() => {
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            updateDiscoveryStatus('Discovery completed!');
            setTimeout(() => {
                hideDiscoveryProgress();
                if (result.devices) {
                    updateDiscoveredDevicesTable(result.devices);
                    // Add DHCP recommendation
                    const allDHCP = result.devices.every(d => d.discovery_method === 'arp' || d.discovery_method === 'cache');
                    if (allDHCP) {
                        showAlert('info', `Found ${result.devices.length} DHCP devices. For full network scan, use DHCP Discovery.`);
                    } else {
                        showAlert('success', `Static discovery completed. Found ${result.devices.length} devices.`);
                    }
                }
            }, 1000);
        }, 500);

        return result;
        
    } catch (error) {
        console.error('Error in static discovery:', error);
        showAlert('error', `Static discovery failed: ${error.message}`);
        throw error;
    } finally {
        hideLoading();
    }
}

// Ensure discoverStaticDevices is globally accessible
window.discoverStaticDevices = discoverStaticDevices;

async function discoverDHCPDevices() {
    const btn = document.getElementById('discoverDHCPBtn');
    const originalText = btn.innerHTML;

    try {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting...';

        // Show progress bar
        showDiscoveryProgress('DHCP Discovery', 'Initializing DHCP device scan...');

        console.log('Sending DHCP discovery request');

        const response = await fetch('/admin/terminal-management/api/discover-dhcp-devices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        console.log('DHCP discovery response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('DHCP discovery result:', result);

        if (result.success && result.session_id) {
            // Start polling for progress
            await pollDiscoveryProgress(result.session_id);
        } else {
            showAlert('error', result.error || 'Failed to start DHCP device discovery');
            hideDiscoveryProgress();
        }

    } catch (error) {
        console.error('Error in DHCP discovery:', error);
        showAlert('error', 'Error starting DHCP device discovery: ' + error.message);
        hideDiscoveryProgress();
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function showDiscoveryProgress(title, status) {
    const progressContainer = document.getElementById('discoveryProgressContainer');
    const progressTitle = document.getElementById('discoveryProgressTitle');
    const progressBar = document.getElementById('discoveryProgressBar');
    const progressText = document.getElementById('discoveryProgressText');
    const discoveryStatus = document.getElementById('discoveryStatus');
    const foundCount = document.getElementById('discoveryFoundCount');

    // Reset progress
    progressBar.style.width = '0%';
    progressText.textContent = '0%';
    discoveryStatus.textContent = status;
    foundCount.textContent = '0';
    progressTitle.textContent = title;

    // Show progress container
    progressContainer.style.display = 'block';

    // Show discovered devices card
    document.getElementById('discoveredDevicesCard').style.display = 'block';
}

function hideDiscoveryProgress() {
    document.getElementById('discoveryProgressContainer').style.display = 'none';
    if (discoveryPollingInterval) {
        clearInterval(discoveryPollingInterval);
        discoveryPollingInterval = null;
    }
    currentDiscoverySession = null;
}

let discoveryPollingInterval = null;

async function pollDiscoveryProgress(sessionId) {
    try {
        discoveryPollingInterval = setInterval(async () => {
            console.log(`Polling progress for session: ${sessionId}`);

            const response = await fetch(`/admin/terminal-management/api/discovery-progress/${sessionId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            let data = await response.json();
            console.log('Discovery progress data received:', data);

            if (data.success && data.discovery) {
                const discovery = data.discovery;
                const percentage = discovery.progress || 0;
                const status = discovery.message || discovery.status || '';
                const foundDevices = data.device_count || 0;
                const complete = discovery.status === 'completed' || discovery.status === 'error';

                console.log(`Progress: ${percentage}%, Status: ${status}, Found Devices: ${foundDevices}`);

                // Update progress bar and status
                const progressBar = document.getElementById('discoveryProgressBar');
                const progressText = document.getElementById('discoveryProgressText');
                const discoveryStatus = document.getElementById('discoveryStatus');
                const foundCount = document.getElementById('discoveryFoundCount');

                progressBar.style.width = `${percentage}%`;
                progressText.textContent = `${percentage}%`;
                discoveryStatus.textContent = status;
                foundCount.textContent = foundDevices;

                // Real-time device display: Show devices as they're discovered
                const currentDevices = data.discovery.found_devices || [];
                const arpDevices = currentDevices.filter(d => d.discovery_method === 'arp');
                const otherDevices = currentDevices.filter(d => d.discovery_method !== 'arp');
                updateDiscoveredDevicesTable(otherDevices, arpDevices);

                if (complete) {
                    clearInterval(discoveryPollingInterval);
                    discoveryPollingInterval = null;

                    hideDiscoveryProgress();
                    showAlert('success', `Discovery completed successfully! Found ${currentDevices.length} devices.`);
                }
            }
        }, 2000);
    } catch (error) {
        console.error('Error polling discovery progress:', error);
        clearInterval(discoveryPollingInterval);
        discoveryPollingInterval = null;
        hideDiscoveryProgress();
        showAlert('error', 'Error polling discovery progress: ' + error.message);
    }
}

// Render ARP table in its own section
function renderArpTable(devices) {
    const arpSection = document.getElementById('arpTableSection');
    const arpTableBody = document.getElementById('arpTableBody');
    if (!arpSection || !arpTableBody) return;

    arpSection.style.display = 'block';
    arpTableBody.innerHTML = '';

    if (!devices || devices.length === 0) {
        arpTableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No ARP devices found. Please try refreshing the ARP table.</td></tr>`;
        return;
    }

    devices.forEach(device => {
        const customName = device.custom_name || 'Unnamed'; // Default to 'Unnamed' if no custom name is set
        console.log(`Rendering device: IP=${device.ip_address}, Name=${customName}`); // Debugging log
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${device.ip_address || '<span class="text-muted">N/A</span>'}</td>
            <td>${device.mac_address || '<span class="text-muted">N/A</span>'}</td>
            <td>${device.status && device.status.toLowerCase() === 'online'
                ? '<span class="badge badge-success-persistent">Online</span>'
                : device.status && device.status.toLowerCase() === 'offline'
                    ? '<span class="badge badge-danger-persistent">Offline</span>'
                    : '<span class="text-muted">N/A</span>'}
            </td>
            <td><span class="text-primary">${customName}</span></td>
            <td>${device.device_type || '<span class="text-muted">N/A</span>'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editArpDeviceName('${device.ip_address || ''}', '${device.mac_address || ''}', '${customName}')">Edit</button>
                <button class="btn btn-sm btn-info" onclick="pingDevice('${device.ip_address || ''}')">Ping</button>
                <button class="btn btn-sm btn-success" onclick="addAsTerminal('${device.ip_address || ''}', '${customName}')">Add as Terminal</button>
            </td>
        `;
        arpTableBody.appendChild(row);
    });
}

async function fetchArpDevices() {
    try {
        const response = await fetch('/admin/terminal-management/api/cached-devices');
        if (response.ok) {
            const data = await response.json();
            const arpTable = data.arp_table || [];
            const cachedDevices = data.cached_devices || [];
            // Build map of custom names by IP and MAC (normalize MAC to lowercase)
            const nameMap = {};
            cachedDevices.forEach(device => {
                const ip = device.ip_address;
                const mac = (device.mac_address || '').toLowerCase();
                const key = `${ip}_${mac}`;
                if (device.custom_name) {
                    nameMap[key] = device.custom_name;
                }
            });
            // Merge custom_name into ARP entries
            const merged = arpTable.map(device => {
                const ip = device.ip_address;
                const mac = (device.mac_address || '').toLowerCase();
                const key = `${ip}_${mac}`;
                const custom = nameMap[key] || device.custom_name || '';
                return {
                    ...device,
                    custom_name: custom
                };
            });
            console.log('Fetched and merged ARP devices with names:', merged);
            return merged;
        } else {
            console.error('Failed to fetch ARP devices and cache:', response.statusText);
            return [];
        }
    } catch (error) {
        console.error('Error fetching ARP devices:', error);
        return [];
    }
}

async function renderArpTableFromJson() {
    const devices = await fetchArpDevices();
    renderArpTable(devices);
}

// Call refreshArpTable to initialize the ARP table on page load
document.addEventListener('DOMContentLoaded', refreshArpTable);

async function refreshArpTable() {
    try {
        const response = await fetch('/admin/terminal-management/api/refresh-arp-table');
        if (!response.ok) {
            throw new Error(`Failed to refresh ARP table: ${response.statusText}`);
        }
        const data = await response.json();
        // Merge custom names from cache
        let arpTable = data.arp_table || [];
        // Fetch cached devices for custom names
        const cacheResp = await fetch('/admin/terminal-management/api/cached-devices');
        let cachedDevices = [];
        if (cacheResp.ok) {
            const cacheData = await cacheResp.json();
            cachedDevices = cacheData.cached_devices || [];
        }
        // Build name map by ip_mac key (normalize MAC to lowercase)
        const nameMap = {};
        cachedDevices.forEach(d => {
            const ip = d.ip_address;
            const mac = (d.mac_address || '').toLowerCase();
            const key = `${ip}_${mac}`;
            if (d.custom_name) nameMap[key] = d.custom_name;
        });
        console.log('Custom name map:', nameMap);
        // Merge into ARP entries
        const merged = arpTable.map(device => {
            const ip = device.ip_address;
            const mac = (device.mac_address || '').toLowerCase();
            const key = `${ip}_${mac}`;
            const custom = nameMap[key] || device.custom_name || '';
            return { ...device, custom_name: custom };
        });
        console.log('Merged ARP entries:', merged);
        // Render table with merged names
        if (merged.length > 0) {
            renderArpTable(merged);
            showAlert('success', `ARP table refreshed successfully. Found ${merged.length} entries.`);
        } else {
            renderArpTable([]);
            showAlert('warning', 'ARP table is empty. Please try again or check your network settings.');
        }
    } catch (error) {
        console.error('Error refreshing ARP table:', error);
        showAlert('error', `Error refreshing ARP table: ${error.message}`);
    }
}

function updateDiscoveredDevicesTable(devices, arpDevices = []) {
    console.log('Real-time updating device table with', devices.length, 'devices');

    // Update found count in progress bar
    const foundCount = document.getElementById('discoveryFoundCount');
    if (foundCount) {
        foundCount.textContent = devices.length + arpDevices.length;
    }

    // Get the table body and ARP header row
    const tableBody = document.getElementById('discoveredDevicesTableBody');
    const arpHeaderRow = document.getElementById('arpTableHeaderRow');

    // Clear existing content
    tableBody.innerHTML = '';

    // Show ARP devices first, if any
    if (arpDevices.length > 0) {
        arpHeaderRow.style.display = '';
        arpDevices.forEach(device => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>ARP TABLE</td>
                <td>${device.ip_address || '<span class="text-muted">N/A</span>'}</td>
                <td>${device.mac_address || '<span class="text-muted">N/A</span>'}</td>
                <td><span class="text-muted">Not available for ARP</span></td>
                <td><span class="text-muted">Not available for ARP</span></td>
                <td><span class="text-muted">Not available for ARP</span></td>
                <td><span class="text-muted">Not available for ARP</span></td>
            `;
            tableBody.appendChild(row);
        });
    } else {
        arpHeaderRow.style.display = 'none';
    }

    // Show all other devices (including those without MAC addresses)
    if (devices.length === 0 && arpDevices.length === 0) {
        const noDevicesRow = document.createElement('tr');
        noDevicesRow.innerHTML = `<td colspan="7" class="text-center text-muted">No devices found.<br><span class="text-warning">No static IPs found in ARP table. <strong>Try DHCP discovery for better results.</strong></span></td>`;
        tableBody.appendChild(noDevicesRow);
        return;
    }

    devices.forEach(device => {
        const row = document.createElement('tr');
        // Show custom_name as primary name; fallback to hostname
        row.innerHTML = `
            <td>${device.custom_name ? `<span class="text-primary">${device.custom_name}</span>` : (device.hostname || '<span class="text-muted">N/A</span>')}</td>
            <td>${device.ip_address || '<span class="text-muted">N/A</span>'}</td>
            <td>${device.mac_address || '<span class="text-muted">N/A</span>'}</td>
            <td>${device.online ? '<span class="badge badge-success">Online</span>' : '<span class="badge badge-secondary">Offline</span>'}</td>
            <td>${device.device_type || '<span class="text-muted">unknown</span>'}</td>
            <td>${device.custom_name ? `<span class="text-primary">${device.custom_name}</span>` : '<span class="text-muted">-</span>'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editDevice('${device.ip_address || ''}')">Edit</button>
                <button class="btn btn-sm btn-info" onclick="pingDevice('${device.ip_address || ''}')">Ping</button>
                <button class="btn btn-sm btn-success" onclick="addAsTerminal('${device.ip_address || ''}')">Add as Terminal</button>
            </td>
        `;
        tableBody.appendChild(row);
    });

    console.log(`Displayed ${arpDevices.length} ARP devices and ${devices.length} other devices in table`);
}

function displayDiscoveredDevices(devices) {
    console.log('Final display of discovered devices:', devices);
    
    // Show the discovered devices card
    document.getElementById('discoveredDevicesCard').style.display = 'block';
    
    // Use the real-time update function for final display
    updateDiscoveredDevicesTable(devices);
}

// Helper functions for device actions
function editDevice(ipAddress) {
    console.log('Edit device:', ipAddress);
    
    // Find the device row by matching IP in the IP Address column
    const rows = document.querySelectorAll('#discoveredDevicesTableBody tr');
    const deviceRow = Array.from(rows).find(row => row.children[1]?.textContent.trim() === ipAddress);
    if (!deviceRow) {
        showAlert('error', `Could not find device ${ipAddress} in table`);
        return;
    }
    
    // Get current device info from the row columns
    const deviceNameCell = deviceRow.children[0]; // Device Name column
    const macAddressCell = deviceRow.children[2]; // MAC Address column
    const customNameCell = deviceRow.children[5]; // Custom Name column
    const currentName = deviceNameCell.textContent.trim();
    const macAddress = macAddressCell.textContent.trim();
    
    // Create a simple prompt for editing the device name
    const newName = prompt(`Edit device name for ${ipAddress} (MAC: ${macAddress}):`, currentName);
    
    if (newName !== null && newName.trim() !== '' && newName.trim() !== currentName) {
        // User entered a new name and it's different
        const updatedName = newName.trim();
        
        // Update the device name in the table immediately
        deviceNameCell.textContent = updatedName;
        
        // Also update the custom name column (6th column)
        const customNameCell = deviceRow.children[5];
        customNameCell.innerHTML = `<span class="text-primary">${updatedName}</span>`;
        
        showAlert('info', `Saving device name "${updatedName}" for ${ipAddress} (MAC: ${macAddress})...`);
        
        // Send update to backend with both IP and MAC address
        // Use device-cache API to update custom name by MAC
        fetch('/admin/terminal-management/api/device-cache/update-name', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                ip_address: ipAddress,
                mac_address: macAddress,
                custom_name: updatedName
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', `Device name updated successfully for ${ipAddress} (MAC: ${macAddress})`);
            } else {
                // Revert the name if save failed
                deviceNameCell.textContent = currentName;
                customNameCell.innerHTML = currentName !== 'Unknown' ? `<span class="text-muted">${currentName}</span>` : '<span class="text-muted">-</span>';
                showAlert('error', `Failed to save device name: ${data.error || 'Unknown error'}`);
            }
        })
        .catch(error => {
            console.error('Error updating device name:', error);
            // Revert the name if network error
            deviceNameCell.textContent = currentName;
            customNameCell.innerHTML = currentName !== 'Unknown' ? `<span class="text-muted">${currentName}</span>` : '<span class="text-muted">-</span>';
            showAlert('error', `Network error updating device name: ${error.message}`);
        });
        
    } else if (newName !== null && newName.trim() === '') {
        showAlert('warning', 'Device name cannot be empty');
    }
}

function pingDevice(ipAddress) {
    console.log('Ping device:', ipAddress);

    // Find the device row by IP in IP Address column of discovered devices
    const rows = document.querySelectorAll('#discoveredDevicesTableBody tr');
    const deviceRow = Array.from(rows).find(row => row.children[1]?.textContent.trim() === ipAddress);
    if (!deviceRow) {
        showAlert('error', `Could not find device ${ipAddress} in table`);
        return;
    }
    // Status is in the 4th column (index 3)
    const statusCell = deviceRow.children[3];
    const originalStatusHTML = statusCell.innerHTML;

    // Show pinging status
    statusCell.innerHTML = '<span class="badge badge-warning">Pinging...</span>';
    showAlert('info', `Pinging ${ipAddress}...`);

    // Extract discovery badge if it exists
    let discoveryBadge = '';
    if (originalStatusHTML.includes('Cached')) {
        discoveryBadge = '<span class="badge badge-info ml-1">Cached</span>';
    } else if (originalStatusHTML.includes('New')) {
        discoveryBadge = '<span class="badge badge-primary ml-1">New</span>';
    } else if (originalStatusHTML.includes('ARP')) {
        discoveryBadge = '<span class="badge badge-warning ml-1">ARP</span>';
    }

    // Make actual ping request to backend
    fetch(`/admin/terminal-management/api/ping-device`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip_address: ipAddress })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const isOnline = data.online;
            const responseTime = data.response_time;

            if (isOnline) {
                // Device is online - flash green and keep it green
                statusCell.innerHTML = '<span class="badge badge-success ping-flash-green">Online</span>';
                showAlert('success', `${ipAddress} is online! Response time: ${responseTime ? responseTime.toFixed(2) + 'ms' : 'N/A'}`);

                // Add green flash animation
                statusCell.querySelector('.badge').classList.add('ping-flash-green');

                // After flash, keep it green with persistent class
                setTimeout(() => {
                    statusCell.innerHTML = '<span class="badge badge-success-persistent">Online</span>' + discoveryBadge;
                }, 2000);

                // Update ARP table row status if present
                const arpRows = document.querySelectorAll('#arpTableBody tr');
                arpRows.forEach(row => {
                    const ipCell = row.children[0];
                    if (ipCell && ipCell.textContent.trim() === ipAddress) {
                        row.children[2].innerHTML = '<span class="badge badge-success-persistent">Online</span>';
                    }
                });

            } else {
                // Device is offline - flash red and keep it red
                statusCell.innerHTML = '<span class="badge badge-danger ping-flash-red">Offline</span>';
                showAlert('error', `${ipAddress} is offline or unreachable`);

                // Add red flash animation
                statusCell.querySelector('.badge').classList.add('ping-flash-red');

                // After flash, keep it red with persistent class
                setTimeout(() => {
                    statusCell.innerHTML = '<span class="badge badge-danger-persistent">Offline</span>' + discoveryBadge;
                }, 2000);

                // Update ARP table row status if present
                const arpRows = document.querySelectorAll('#arpTableBody tr');
                arpRows.forEach(row => {
                    const ipCell = row.children[0];
                    if (ipCell && ipCell.textContent.trim() === ipAddress) {
                        row.children[2].innerHTML = '<span class="badge badge-danger-persistent">Offline</span>';
                    }
                });
            }
        } else {
            // Error in ping request
            statusCell.innerHTML = '<span class="badge badge-danger ping-flash-red">Error</span>';
            showAlert('error', `Error pinging ${ipAddress}: ${data.error || 'Unknown error'}`);

            // Flash red for error and keep it red
            statusCell.querySelector('.badge').classList.add('ping-flash-red');
            setTimeout(() => {
                statusCell.innerHTML = '<span class="badge badge-danger-persistent">Error</span>' + discoveryBadge;
            }, 2000);
        }
    })
    .catch(error => {
        console.error('Error pinging device:', error);

        // Network error - flash red and keep it red
        statusCell.innerHTML = '<span class="badge badge-danger ping-flash-red">Error</span>';
        showAlert('error', `Network error pinging ${ipAddress}: ${error.message}`);

        // Flash red for network error and keep it red
        statusCell.querySelector('.badge').classList.add('ping-flash-red');
        setTimeout(() => {
            statusCell.innerHTML = '<span class="badge badge-danger-persistent">Error</span>' + discoveryBadge;
        }, 2000);
    });
}

function addAsTerminal(ipAddress, hostname) {
    console.log('Add as terminal:', ipAddress, hostname);
    
    // Pre-fill the add terminal modal with device info
    document.getElementById('terminalName').value = hostname || `Terminal-${ipAddress.replace(/\./g, '-')}`;
    document.getElementById('terminalLocation').value = `Network Device (${ipAddress})`;
    document.getElementById('terminalDescription').value = `Auto-discovered network device at ${ipAddress}`;
    
    // Show the add terminal modal
    const modal = new bootstrap.Modal(document.getElementById('addTerminalModal'));
    modal.show();
}

function hideDiscoveredDevices() {
    document.getElementById('discoveredDevicesCard').style.display = 'none';
}

async function refreshArpTable() {
    try {
        const response = await fetch('/admin/terminal-management/api/refresh-arp-table');
        if (!response.ok) {
            throw new Error(`Failed to refresh ARP table: ${response.statusText}`);
        }
        const data = await response.json();
        // Merge custom names from cache
        let arpTable = data.arp_table || [];
        // Fetch cached devices for custom names
        const cacheResp = await fetch('/admin/terminal-management/api/cached-devices');
        let cachedDevices = [];
        if (cacheResp.ok) {
            const cacheData = await cacheResp.json();
            cachedDevices = cacheData.cached_devices || [];
        }
        // Build name map by ip_mac key (normalize MAC to lowercase)
        const nameMap = {};
        cachedDevices.forEach(d => {
            const ip = d.ip_address;
            const mac = (d.mac_address || '').toLowerCase();
            const key = `${ip}_${mac}`;
            if (d.custom_name) nameMap[key] = d.custom_name;
        });
        console.log('Custom name map:', nameMap);
        // Merge into ARP entries
        const merged = arpTable.map(device => {
            const ip = device.ip_address;
            const mac = (device.mac_address || '').toLowerCase();
            const key = `${ip}_${mac}`;
            const custom = nameMap[key] || device.custom_name || '';
            return { ...device, custom_name: custom };
        });
        console.log('Merged ARP entries:', merged);
        // Render table with merged names
        if (merged.length > 0) {
            renderArpTable(merged);
            showAlert('success', `ARP table refreshed successfully. Found ${merged.length} entries.`);
        } else {
            renderArpTable([]);
            showAlert('warning', 'ARP table is empty. Please try again or check your network settings.');
        }
    } catch (error) {
        console.error('Error refreshing ARP table:', error);
        showAlert('error', `Error refreshing ARP table: ${error.message}`);
    }
}
window.refreshArpTable = refreshArpTable;

function cancelDiscovery() {
    console.log('Cancelling discovery process...');
    
    // Stop polling
    if (discoveryPollingInterval) {
        clearInterval(discoveryPollingInterval);
        discoveryPollingInterval = null;
    }
    
    // Hide progress
    hideDiscoveryProgress();
    
    // Show cancellation message
    showAlert('info', 'Discovery process cancelled by user.');
    
    // TODO: Add API call to cancel server-side discovery if needed
}

// Ensure editArpDeviceName is globally accessible
window.editArpDeviceName = function(ipAddress, macAddress, currentName) {
    const newName = prompt(`Edit device name for ${ipAddress} (MAC: ${macAddress}):`, currentName);
    if (newName !== null && newName.trim() !== '' && newName.trim() !== currentName) {
        const updatedName = newName.trim();
        showAlert('info', `Saving device name "${updatedName}" for ${ipAddress} (MAC: ${macAddress})...`);
        fetch('/admin/terminal-management/api/update-device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ip_address: ipAddress,
                mac_address: macAddress,
                custom_name: updatedName
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', `Device name updated successfully for ${ipAddress} (MAC: ${macAddress})`);
                renderArpTableFromJson(); // Refresh the table to reflect changes
            } else {
                showAlert('error', `Failed to save device name: ${data.error || 'Unknown error'}`);
            }
        })
        .catch(error => {
            showAlert('error', `Network error updating device name: ${error.message}`);
        });
    } else if (newName !== null && newName.trim() === '') {
        showAlert('warning', 'Device name cannot be empty');
    }
};
