/**
 * Enhanced Camera Detection and Management
 * Comprehensive camera handling with multiple fallback strategies
 */

class EnhancedCameraManager {
    constructor() {
        this.devices = [];
        this.activeStreams = new Map();
        this.constraints = {
            primary: { video: { width: 1280, height: 720, facingMode: 'user' } },
            fallback1: { video: { width: 640, height: 480, facingMode: 'user' } },
            fallback2: { video: { width: 320, height: 240, facingMode: 'user' } },
            fallback3: { video: { deviceId: 'default' } },
            fallback4: { video: true },
            basic: { video: {} }
        };
        this.permissionGranted = false;
        this.detectionInProgress = false;
    }

    /**
     * Comprehensive camera detection with multiple strategies
     */
    async detectCameras() {
        if (this.detectionInProgress) {
            return this.devices;
        }
        
        this.detectionInProgress = true;
        console.log('🔍 Starting enhanced camera detection...');
        
        try {
            // Strategy 1: Standard MediaDevices API
            const devices = await this.detectStandardDevices();
            if (devices.length > 0) {
                this.devices = devices;
                console.log(`✅ Standard detection found ${devices.length} camera(s)`);
                return devices;
            }

            // Strategy 2: Request permission first, then enumerate
            const permissionDevices = await this.detectWithPermissionRequest();
            if (permissionDevices.length > 0) {
                this.devices = permissionDevices;
                console.log(`✅ Permission-first detection found ${permissionDevices.length} camera(s)`);
                return permissionDevices;
            }

            // Strategy 3: Probe for camera access without enumeration
            const probeResult = await this.probeForCameras();
            if (probeResult.hasCamera) {
                this.devices = [{ deviceId: 'default', label: 'Default Camera', kind: 'videoinput' }];
                console.log('✅ Camera probe successful - found at least one camera');
                return this.devices;
            }

            // Strategy 4: Check for legacy camera APIs
            const legacyResult = await this.checkLegacyAPIs();
            if (legacyResult.hasCamera) {
                this.devices = [{ deviceId: 'legacy', label: 'Legacy Camera', kind: 'videoinput' }];
                console.log('✅ Legacy camera API detected');
                return this.devices;
            }

            console.log('❌ No cameras detected with any method');
            return [];

        } catch (error) {
            console.error('❌ Camera detection failed:', error);
            return [];
        } finally {
            this.detectionInProgress = false;
        }
    }

    /**
     * Standard MediaDevices enumeration
     */
    async detectStandardDevices() {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                throw new Error('MediaDevices API not supported');
            }

            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            console.log(`📹 Standard enumeration: ${devices.length} total, ${videoDevices.length} video`);
            
            return videoDevices.map(device => ({
                deviceId: device.deviceId,
                label: device.label || `Camera ${videoDevices.indexOf(device) + 1}`,
                kind: device.kind
            }));

        } catch (error) {
            console.log('⚠️ Standard device enumeration failed:', error.message);
            return [];
        }
    }

    /**
     * Request camera permission first, then enumerate
     */
    async detectWithPermissionRequest() {
        try {
            console.log('🔐 Requesting camera permissions...');
            
            // Request basic camera access to trigger permission dialog
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            
            // Stop the stream immediately
            stream.getTracks().forEach(track => track.stop());
            this.permissionGranted = true;
            
            // Now enumerate devices with permissions granted
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            console.log(`📹 Post-permission enumeration: ${videoDevices.length} video devices`);
            
            return videoDevices.map((device, index) => ({
                deviceId: device.deviceId,
                label: device.label || `Camera ${index + 1}`,
                kind: device.kind
            }));

        } catch (error) {
            console.log('⚠️ Permission-based detection failed:', error.message);
            return [];
        }
    }

    /**
     * Probe for camera access without device enumeration
     */
    async probeForCameras() {
        const strategies = Object.entries(this.constraints);
        
        for (const [name, constraint] of strategies) {
            try {
                console.log(`🔍 Probing with ${name} constraints...`);
                
                const stream = await navigator.mediaDevices.getUserMedia(constraint);
                
                // Success! Camera exists
                stream.getTracks().forEach(track => track.stop());
                console.log(`✅ Probe successful with ${name}`);
                
                return { hasCamera: true, workingConstraint: constraint };
                
            } catch (error) {
                console.log(`❌ Probe failed with ${name}:`, error.message);
                continue;
            }
        }
        
        return { hasCamera: false };
    }

    /**
     * Check for legacy camera APIs
     */
    async checkLegacyAPIs() {
        // Check for deprecated getUserMedia
        const legacyGetUserMedia = navigator.getUserMedia ||
                                 navigator.webkitGetUserMedia ||
                                 navigator.mozGetUserMedia ||
                                 navigator.msGetUserMedia;

        if (legacyGetUserMedia) {
            return new Promise((resolve) => {
                console.log('🔍 Trying legacy getUserMedia...');
                
                legacyGetUserMedia.call(navigator, { video: true },
                    (stream) => {
                        // Success
                        stream.getTracks().forEach(track => track.stop());
                        console.log('✅ Legacy camera API works');
                        resolve({ hasCamera: true });
                    },
                    (error) => {
                        console.log('❌ Legacy camera API failed:', error.message);
                        resolve({ hasCamera: false });
                    }
                );
            });
        }

        return { hasCamera: false };
    }

    /**
     * Get camera stream with enhanced error handling
     */
    async getStream(deviceId = null, videoElement = null) {
        console.log(`📹 Getting camera stream for device: ${deviceId || 'default'}`);
        
        // Try different constraint strategies
        const strategies = Object.entries(this.constraints);
        
        if (deviceId && deviceId !== 'default') {
            // Add device-specific constraints
            strategies.unshift(['specific', { 
                video: { deviceId: { exact: deviceId } } 
            }]);
        }

        for (const [name, constraint] of strategies) {
            try {
                console.log(`🔄 Trying ${name} constraints...`);
                
                const stream = await navigator.mediaDevices.getUserMedia(constraint);
                
                // Store active stream
                const streamId = deviceId || 'default';
                if (this.activeStreams.has(streamId)) {
                    this.stopStream(streamId);
                }
                this.activeStreams.set(streamId, stream);
                
                // Configure video element if provided
                if (videoElement) {
                    videoElement.srcObject = stream;
                    videoElement.onloadedmetadata = () => {
                        console.log(`📹 Video ready: ${videoElement.videoWidth}x${videoElement.videoHeight}`);
                    };
                }
                
                console.log(`✅ Stream acquired with ${name} constraints`);
                return stream;
                
            } catch (error) {
                console.log(`❌ ${name} constraints failed:`, error.message);
                continue;
            }
        }
        
        throw new Error('All camera access strategies failed');
    }

    /**
     * Stop a specific stream
     */
    stopStream(streamId = 'default') {
        if (this.activeStreams.has(streamId)) {
            const stream = this.activeStreams.get(streamId);
            stream.getTracks().forEach(track => track.stop());
            this.activeStreams.delete(streamId);
            console.log(`🛑 Stopped stream: ${streamId}`);
        }
    }

    /**
     * Stop all active streams
     */
    stopAllStreams() {
        for (const [streamId] of this.activeStreams) {
            this.stopStream(streamId);
        }
        console.log('🛑 All streams stopped');
    }

    /**
     * Get detailed camera information
     */
    async getCameraInfo() {
        const devices = await this.detectCameras();
        const info = {
            camerasDetected: devices.length,
            permissionGranted: this.permissionGranted,
            devices: devices,
            capabilities: await this.getCapabilities(),
            browserInfo: this.getBrowserInfo()
        };
        
        console.log('📊 Camera info:', info);
        return info;
    }

    /**
     * Get browser and device capabilities
     */
    async getCapabilities() {
        const capabilities = {
            mediaDevices: !!navigator.mediaDevices,
            getUserMedia: !!navigator.mediaDevices?.getUserMedia,
            enumerateDevices: !!navigator.mediaDevices?.enumerateDevices,
            legacyGetUserMedia: !!(navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia),
            isSecureContext: window.isSecureContext,
            protocol: window.location.protocol
        };

        return capabilities;
    }

    /**
     * Get browser information
     */
    getBrowserInfo() {
        const userAgent = navigator.userAgent;
        let browserName = 'Unknown';
        
        if (userAgent.includes('Chrome')) browserName = 'Chrome';
        else if (userAgent.includes('Firefox')) browserName = 'Firefox';
        else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) browserName = 'Safari';
        else if (userAgent.includes('Edge')) browserName = 'Edge';
        
        return {
            name: browserName,
            userAgent: userAgent,
            platform: navigator.platform,
            language: navigator.language
        };
    }

    /**
     * Test camera functionality
     */
    async testCamera(deviceId = null) {
        console.log('🧪 Testing camera functionality...');
        
        try {
            const stream = await this.getStream(deviceId);
            
            // Create temporary video element for testing
            const video = document.createElement('video');
            video.srcObject = stream;
            video.muted = true;
            
            return new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    const result = {
                        success: true,
                        resolution: `${video.videoWidth}x${video.videoHeight}`,
                        frameRate: stream.getVideoTracks()[0].getSettings().frameRate || 'unknown'
                    };
                    
                    // Clean up
                    this.stopStream(deviceId || 'default');
                    
                    console.log('✅ Camera test successful:', result);
                    resolve(result);
                };
                
                video.onerror = () => {
                    this.stopStream(deviceId || 'default');
                    resolve({ success: false, error: 'Video element error' });
                };
                
                video.play().catch(e => {
                    this.stopStream(deviceId || 'default');
                    resolve({ success: false, error: e.message });
                });
            });
            
        } catch (error) {
            console.log('❌ Camera test failed:', error.message);
            return { success: false, error: error.message };
        }
    }

    /**
     * Auto-detect streaming details for a camera
     */
    async autoDetectStream() {
        const ipAddress = document.getElementById('cameraLoginIP').value;
        const username = document.getElementById('cameraLoginUsername').value;
        const password = document.getElementById('cameraLoginPassword').value;

        if (!ipAddress) {
            alert('Please enter the camera IP address.');
            return;
        }

        try {
            const response = await fetch('/admin/camera-login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip_address: ipAddress, username, password })
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || 'Failed to auto-detect streaming details.');
                return;
            }

            // Update the UI with detected details
            document.getElementById('detectedRTSP').textContent = data.rtsp || 'N/A';
            document.getElementById('detectedHTTP').textContent = data.http || 'N/A';
            document.getElementById('detectedONVIF').textContent = data.onvif || 'N/A';
            document.getElementById('streamDetails').style.display = 'block';

            // Indicate browser-specific compatibility
            if (data.http === 'N/A') {
                document.getElementById('httpWarning').textContent = 'HTTP stream may require Internet Explorer.';
                document.getElementById('httpWarning').style.display = 'block';
            } else {
                document.getElementById('httpWarning').style.display = 'none';
            }

        } catch (error) {
            console.error('Error during auto-detection:', error);
            alert('An error occurred while detecting streaming details. Please try again.');
        }
    }
}

/**
 * Open the detected stream in the selected browser
 */
async function openStreamInBrowser() {
    const browser = document.getElementById('browserSelection').value;
    const streamUrl = document.getElementById('detectedHTTP').textContent;

    if (streamUrl === 'N/A') {
        alert('No valid stream URL detected. Please auto-detect the stream first.');
        return;
    }

    try {
        const response = await fetch('/admin/open-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ browser, stream_url: streamUrl })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || 'Failed to open the stream in the selected browser.');
            return;
        }

        alert(data.message || 'Stream opened successfully.');
    } catch (error) {
        console.error('Error opening stream:', error);
        alert('An unexpected error occurred while opening the stream.');
    }
}

// Global camera manager instance
window.enhancedCameraManager = new EnhancedCameraManager();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedCameraManager;
}
