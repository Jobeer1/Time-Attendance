// Ensure global networkSettings object exists
if (typeof window.networkSettings === 'undefined') {
    window.networkSettings = {
        ip_range_start: '10.0.0.1',
        ip_range_end: '10.0.0.255',
        scan_timeout: 5,
        concurrent_scans: 10
    };
}

// Network settings-related logic

// Global flag to prevent unwanted modal displays after save
let preventModalDisplay = false;

async function showNetworkSettings() {
    try {
        console.log('showNetworkSettings called explicitly by user');
        // Reset the prevention flag since this is a user-initiated request
        preventModalDisplay = false;
        // Load current settings from backend and show modal
        await loadAndShowNetworkSettings();
        
    } catch (error) {
        console.error('Error loading network settings:', error);
        
        // Fall back to default settings
        document.getElementById('ipRangeStart').value = networkSettings.ip_range_start;
        document.getElementById('ipRangeEnd').value = networkSettings.ip_range_end;
        document.getElementById('scanTimeout').value = networkSettings.scan_timeout;
        document.getElementById('concurrentScans').value = networkSettings.concurrent_scans;
        
        new bootstrap.Modal(document.getElementById('networkSettingsModal')).show();
    }
}

async function loadNetworkSettings() {
    try {
        console.log('Loading network settings from backend API...');
        const response = await fetch('/admin/terminal-management/api/network-settings');
        if (!response.ok) {
            throw new Error(`Failed to load network settings: ${response.statusText}`);
        }
        const result = await response.json();
        console.log('Network settings loaded from backend API:', result);

        // Update the global networkSettings object
        if (result.success && result.settings) {
            networkSettings = result.settings;
            return result.settings;
        }
        throw new Error(result.error || 'Failed to retrieve settings');
    } catch (error) {
        console.error('Error loading network settings:', error);
        throw error;
    }
}

async function loadNetworkSettingsQuietly() {
    try {
        console.log('Quietly loading network settings from backend API...');
        const response = await fetch('/admin/terminal-management/api/network-settings');
        if (!response.ok) {
            console.warn(`Failed to load network settings: ${response.statusText}`);
            return;
        }
        const result = await response.json();
        console.log('Network settings loaded quietly:', result);

        // Update the global networkSettings object only - NEVER show modal from this function
        if (result.success && result.settings) {
            networkSettings = result.settings;
        }
    } catch (error) {
        console.warn('Error loading network settings quietly:', error);
        // Don't throw error, just continue with defaults
    }
}

async function loadAndShowNetworkSettings() {
    try {
        console.log('Loading and showing network settings...');
        const settings = await loadNetworkSettings();
        
        // Populate the UI with the loaded settings
        document.getElementById('ipRangeStart').value = settings.ip_range_start || '155.235.81.1';
        document.getElementById('ipRangeEnd').value = settings.ip_range_end || '155.235.81.254';
        document.getElementById('scanTimeout').value = settings.scan_timeout || 5;
        document.getElementById('concurrentScans').value = settings.concurrent_scans || 10;

        // Only show modal if not prevented (i.e., not called after a save operation)
        const modal = document.getElementById('networkSettingsModal');
        if (!preventModalDisplay && !modal.classList.contains('show')) {
            new bootstrap.Modal(modal).show();
            console.log('Network settings modal was shown');
        } else {
            console.log('Network settings modal display prevented or already visible');
        }
    } catch (error) {
        console.error('Error loading network settings:', error);
        if (!preventModalDisplay) {
            showAlert('error', 'Failed to load network settings. Using defaults.');
            
            // Fall back to defaults
            document.getElementById('ipRangeStart').value = '155.235.81.1';
            document.getElementById('ipRangeEnd').value = '155.235.81.254';
            document.getElementById('scanTimeout').value = 5;
            document.getElementById('concurrentScans').value = 10;
            
            new bootstrap.Modal(document.getElementById('networkSettingsModal')).show();
        }
    }
}

async function saveNetworkSettings() {
    try {
        showLoading(); // Explicitly show loading

        const form = document.getElementById('networkSettingsForm');
        const formData = new FormData(form);

        const settings = {
            ip_range_start: formData.get('ip_range_start'),
            ip_range_end: formData.get('ip_range_end'),
            scan_timeout: parseInt(formData.get('scan_timeout')),
            concurrent_scans: parseInt(formData.get('concurrent_scans'))
        };

        const response = await fetch('/admin/terminal-management/api/network-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        const result = await response.json();
        if (!response.ok || result.success === false) {
            let errorMsg = result.error || `HTTP ${response.status}`;
            if (errorMsg.includes('outside your local subnet')) {
                showAlert('error', errorMsg);
            } else {
                showAlert('error', `Failed to save: ${errorMsg}`);
            }
            throw new Error(errorMsg);
        }
        if (result.settings) {
            networkSettings = result.settings;
        }

        // Close modal and show success
        $('#networkSettingsModal').modal('hide');
        showAlert('success', 'Network settings saved successfully.');
        
    } catch (error) {
        console.error('Save error:', error);
        // Error alert already shown above
    } finally {
        hideLoading(); // Always hide loading regardless of success/failure
    }
}

// Initialize form handler when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('networkSettingsForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveNetworkSettings();
        });
    }
});
