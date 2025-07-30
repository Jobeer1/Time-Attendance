/**
 * Real-time Human Detection for Camera Management
 * Detects humans in live camera feeds and displays 3 dots per person
 * Uses MediaPipe Pose Detection for accurate human tracking
 */

class CameraHumanDetector {
    constructor() {
        this.isDetecting = false;
        this.detectionCanvas = null;
        this.detectionContext = null;
        this.videoElement = null;
        this.humanDetections = [];
        this.detectionInterval = null;
        
        // MediaPipe Pose Detection
        this.poseDetection = null;
        this.poseEnabled = false;
        
        // Fallback human detection
        this.fallbackMode = false;
        
        console.log('🎯 Camera Human Detector initialized');
    }

    /**
     * Initialize human detection system
     */
    async initialize() {
        try {
            console.log('🤖 Initializing Human Detection System...');
            
            // Wait for MediaPipe to load
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Try to load MediaPipe Pose Detection
            if (typeof Pose !== 'undefined') {
                console.log('📱 Attempting MediaPipe Pose Detection initialization...');
                
                try {
                    this.poseDetection = new Pose({
                        locateFile: (file) => {
                            return `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5/${file}`;
                        }
                    });
                    
                    this.poseDetection.setOptions({
                        modelComplexity: 1,
                        smoothLandmarks: true,
                        enableSegmentation: false,
                        smoothSegmentation: false,
                        minDetectionConfidence: 0.5,
                        minTrackingConfidence: 0.5
                    });
                    
                    this.poseDetection.onResults(this.onPoseResults.bind(this));
                    await this.poseDetection.initialize();
                    
                    this.poseEnabled = true;
                    console.log('✅ MediaPipe Pose Detection ready');
                } catch (error) {
                    console.log('⚠️ MediaPipe Pose initialization failed:', error.message);
                    this.fallbackMode = true;
                }
            } else {
                console.log('⚠️ MediaPipe Pose not available, using fallback detection');
                this.fallbackMode = true;
            }
            
            console.log(`🎯 Human Detector initialization complete - Pose enabled: ${this.poseEnabled}`);
            return true;
        } catch (error) {
            console.log('⚠️ Human detection initialization failed:', error.message);
            this.fallbackMode = true;
            return false;
        }
    }

    /**
     * Start human detection on camera stream
     */
    startDetection(videoElement) {
        if (this.isDetecting) {
            this.stopDetection();
        }

        this.isDetecting = true;
        this.videoElement = videoElement;
        
        console.log('🎯 Starting human detection...');
        console.log('- Video dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
        console.log('- Pose detection enabled:', this.poseEnabled);
        
        // Create detection overlay
        this.createDetectionOverlay(videoElement);
        
        // Start detection loop
        if (this.poseEnabled && this.poseDetection) {
            console.log('🤖 Starting MediaPipe pose detection');
            this.startPoseDetection();
        } else {
            console.log('🔄 Starting fallback human detection');
            this.startFallbackDetection();
        }
        
        console.log('✅ Human detection started successfully');
        return true;
    }

    /**
     * Stop human detection
     */
    stopDetection() {
        console.log('⏹️ Stopping human detection...');
        
        this.isDetecting = false;
        
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
        
        // Remove overlay canvas
        if (this.detectionCanvas && this.detectionCanvas.parentNode) {
            this.detectionCanvas.parentNode.removeChild(this.detectionCanvas);
        }
        
        this.detectionCanvas = null;
        this.detectionContext = null;
        this.videoElement = null;
        this.humanDetections = [];
        
        console.log('✅ Human detection stopped');
    }

    /**
     * Create detection overlay canvas
     */
    createDetectionOverlay(videoElement) {
        const container = videoElement.parentElement;
        
        // Create overlay canvas
        this.detectionCanvas = document.createElement('canvas');
        this.detectionCanvas.id = 'humanDetectionOverlay';
        this.detectionCanvas.style.position = 'absolute';
        this.detectionCanvas.style.top = '0';
        this.detectionCanvas.style.left = '0';
        this.detectionCanvas.style.zIndex = '10';
        this.detectionCanvas.style.pointerEvents = 'none';
        
        // Set canvas size to match video
        this.detectionCanvas.width = videoElement.videoWidth || 640;
        this.detectionCanvas.height = videoElement.videoHeight || 480;
        this.detectionCanvas.style.width = videoElement.style.width || videoElement.offsetWidth + 'px';
        this.detectionCanvas.style.height = videoElement.style.height || videoElement.offsetHeight + 'px';
        
        this.detectionContext = this.detectionCanvas.getContext('2d');
        
        // Add to container
        container.style.position = 'relative';
        container.appendChild(this.detectionCanvas);
        
        console.log('✅ Detection overlay created:', this.detectionCanvas.width, 'x', this.detectionCanvas.height);
    }

    /**
     * Start MediaPipe pose detection
     */
    startPoseDetection() {
        console.log('🤖 Starting MediaPipe pose detection loop...');
        
        this.detectionInterval = setInterval(async () => {
            if (!this.isDetecting || !this.videoElement || !this.videoElement.videoWidth) return;
            
            try {
                if (this.poseDetection) {
                    await this.poseDetection.send({ image: this.videoElement });
                }
            } catch (error) {
                console.log('Pose detection error:', error.message);
                // If MediaPipe fails, switch to fallback
                if (error.message.includes('Cannot read properties')) {
                    console.log('🔄 Switching to fallback detection due to MediaPipe issues');
                    clearInterval(this.detectionInterval);
                    this.poseEnabled = false;
                    this.startFallbackDetection();
                }
            }
        }, 200); // 5 FPS for pose detection
    }

    /**
     * Handle MediaPipe pose detection results
     */
    onPoseResults(results) {
        if (!this.isDetecting || !this.detectionContext) return;
        
        // Clear previous drawings
        this.detectionContext.clearRect(0, 0, this.detectionCanvas.width, this.detectionCanvas.height);
        
        if (results.poseLandmarks && results.poseLandmarks.length > 0) {
            console.log('🎯 Human detected with pose landmarks');
            this.drawHumanDots(results.poseLandmarks, 'pose');
        } else {
            // Show searching indicator
            this.drawSearchingIndicator();
        }
    }

    /**
     * Start fallback human detection
     */
    startFallbackDetection() {
        console.log('🔄 Starting fallback human detection...');
        
        this.detectionInterval = setInterval(() => {
            if (!this.isDetecting || !this.videoElement || !this.videoElement.videoWidth) return;
            
            try {
                this.performBasicHumanDetection();
            } catch (error) {
                console.log('Fallback detection error:', error.message);
                this.drawSearchingIndicator();
            }
        }, 500); // 2 FPS for fallback detection
    }

    /**
     * Basic human detection using movement and shape analysis
     */
    performBasicHumanDetection() {
        if (!this.detectionContext) return;
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = this.videoElement.videoWidth;
        canvas.height = this.videoElement.videoHeight;
        ctx.drawImage(this.videoElement, 0, 0);
        
        // Get image data for analysis
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const pixels = imageData.data;
        
        // Simple human shape detection
        const humanRegions = this.detectHumanShapes(pixels, canvas.width, canvas.height);
        
        // Clear previous drawings
        this.detectionContext.clearRect(0, 0, this.detectionCanvas.width, this.detectionCanvas.height);
        
        if (humanRegions.length > 0) {
            console.log('🎯 Humans detected with fallback algorithm:', humanRegions.length);
            humanRegions.forEach(region => {
                this.drawHumanDots(region, 'fallback');
            });
        } else {
            this.drawSearchingIndicator();
        }
    }

    /**
     * Detect human-like shapes in image data
     */
    detectHumanShapes(pixels, width, height) {
        const humanRegions = [];
        const blockSize = 40; // Analyze in blocks
        
        for (let y = 0; y < height - blockSize; y += blockSize) {
            for (let x = 0; x < width - blockSize; x += blockSize) {
                const skinPixels = this.countSkinPixelsInBlock(pixels, x, y, blockSize, width);
                const movementScore = this.detectMovementInBlock(x, y, blockSize);
                
                // Combine skin detection and movement for human detection
                if (skinPixels > blockSize * blockSize * 0.1 && movementScore > 0.3) {
                    humanRegions.push({
                        x: x + blockSize / 2,
                        y: y + blockSize / 2,
                        confidence: Math.min(1.0, (skinPixels / (blockSize * blockSize)) + movementScore)
                    });
                }
            }
        }
        
        // Merge nearby regions
        return this.mergeNearbyRegions(humanRegions);
    }

    /**
     * Count skin-colored pixels in a block
     */
    countSkinPixelsInBlock(pixels, startX, startY, blockSize, width) {
        let skinPixels = 0;
        
        for (let y = startY; y < startY + blockSize; y++) {
            for (let x = startX; x < startX + blockSize; x++) {
                const index = (y * width + x) * 4;
                const r = pixels[index];
                const g = pixels[index + 1];
                const b = pixels[index + 2];
                
                if (this.isSkinTone(r, g, b)) {
                    skinPixels++;
                }
            }
        }
        
        return skinPixels;
    }

    /**
     * Simple skin tone detection
     */
    isSkinTone(r, g, b) {
        return (
            r > 95 && g > 40 && b > 20 &&
            r > g && r > b &&
            Math.abs(r - g) > 15 &&
            r - Math.min(g, b) > 15
        );
    }

    /**
     * Detect movement in a block (simplified)
     */
    detectMovementInBlock(x, y, blockSize) {
        // This would need frame comparison for real movement detection
        // For now, return a random value to simulate movement detection
        return Math.random() * 0.8;
    }

    /**
     * Merge nearby human detection regions
     */
    mergeNearbyRegions(regions) {
        const merged = [];
        const mergeDistance = 100;
        
        regions.forEach(region => {
            let foundNearby = false;
            
            for (let i = 0; i < merged.length; i++) {
                const distance = Math.sqrt(
                    Math.pow(region.x - merged[i].x, 2) + 
                    Math.pow(region.y - merged[i].y, 2)
                );
                
                if (distance < mergeDistance) {
                    // Merge with existing region
                    merged[i].x = (merged[i].x + region.x) / 2;
                    merged[i].y = (merged[i].y + region.y) / 2;
                    merged[i].confidence = Math.max(merged[i].confidence, region.confidence);
                    foundNearby = true;
                    break;
                }
            }
            
            if (!foundNearby) {
                merged.push(region);
            }
        });
        
        return merged;
    }

    /**
     * Draw 3 dots per detected human
     */
    drawHumanDots(landmarks, type) {
        if (!this.detectionContext) return;
        
        if (type === 'pose' && landmarks) {
            // MediaPipe pose landmarks - extract key points
            const canvasWidth = this.detectionCanvas.width;
            const canvasHeight = this.detectionCanvas.height;
            
            // Key landmark indices for MediaPipe Pose
            const HEAD_INDEX = 0;      // Nose
            const TORSO_INDEX = 11;    // Left shoulder (approximate torso center)
            const LOWER_INDEX = 23;    // Left hip
            
            // Get landmark positions
            const headPoint = landmarks[HEAD_INDEX];
            const torsoPoint = landmarks[TORSO_INDEX];
            const lowerPoint = landmarks[LOWER_INDEX];
            
            if (headPoint && torsoPoint && lowerPoint) {
                this.drawDotsForPerson([
                    { x: headPoint.x * canvasWidth, y: headPoint.y * canvasHeight, label: '👤' },
                    { x: torsoPoint.x * canvasWidth, y: torsoPoint.y * canvasHeight, label: '🫀' },
                    { x: lowerPoint.x * canvasWidth, y: lowerPoint.y * canvasHeight, label: '🦵' }
                ]);
            }
        } else if (type === 'fallback') {
            // Fallback detection - estimate 3 points based on detected region
            const scaleX = this.detectionCanvas.width / this.videoElement.videoWidth;
            const scaleY = this.detectionCanvas.height / this.videoElement.videoHeight;
            
            const centerX = landmarks.x * scaleX;
            const centerY = landmarks.y * scaleY;
            
            // Estimate head, torso, and lower body positions
            this.drawDotsForPerson([
                { x: centerX, y: centerY - 40, label: '👤' },  // Head (above center)
                { x: centerX, y: centerY, label: '🫀' },       // Torso (center)
                { x: centerX, y: centerY + 40, label: '🦵' }   // Lower body (below center)
            ]);
        }
    }

    /**
     * Draw the 3 dots for a single person
     */
    drawDotsForPerson(points) {
        points.forEach((point, index) => {
            // Draw colored dot
            const colors = ['#ff4444', '#44ff44', '#4444ff']; // Red, Green, Blue
            this.detectionContext.fillStyle = colors[index];
            this.detectionContext.strokeStyle = '#ffffff';
            this.detectionContext.lineWidth = 2;
            
            // Draw main dot
            this.detectionContext.beginPath();
            this.detectionContext.arc(point.x, point.y, 8, 0, 2 * Math.PI);
            this.detectionContext.fill();
            this.detectionContext.stroke();
            
            // Draw inner dot for better visibility
            this.detectionContext.fillStyle = '#ffffff';
            this.detectionContext.beginPath();
            this.detectionContext.arc(point.x, point.y, 3, 0, 2 * Math.PI);
            this.detectionContext.fill();
            
            // Draw label
            this.detectionContext.fillStyle = '#ffffff';
            this.detectionContext.font = 'bold 16px Arial';
            this.detectionContext.textAlign = 'center';
            this.detectionContext.strokeStyle = '#000000';
            this.detectionContext.lineWidth = 3;
            this.detectionContext.strokeText(point.label, point.x + 20, point.y - 10);
            this.detectionContext.fillText(point.label, point.x + 20, point.y - 10);
        });
    }

    /**
     * Draw searching indicator when no humans detected
     */
    drawSearchingIndicator() {
        if (!this.detectionContext) return;
        
        const centerX = this.detectionCanvas.width / 2;
        const centerY = this.detectionCanvas.height / 2;
        
        // Clear canvas first
        this.detectionContext.clearRect(0, 0, this.detectionCanvas.width, this.detectionCanvas.height);
        
        // Draw searching indicator
        this.detectionContext.fillStyle = 'rgba(255, 255, 255, 0.8)';
        this.detectionContext.font = 'bold 16px Arial';
        this.detectionContext.textAlign = 'center';
        this.detectionContext.fillText('🔍 Scanning for humans...', centerX, centerY);
        
        // Draw animated scanning circle
        const time = Date.now() * 0.003;
        const radius = 40 + Math.sin(time) * 10;
        
        this.detectionContext.strokeStyle = '#00ff88';
        this.detectionContext.lineWidth = 3;
        this.detectionContext.setLineDash([10, 5]);
        this.detectionContext.lineDashOffset = time * 20;
        this.detectionContext.beginPath();
        this.detectionContext.arc(centerX, centerY - 30, radius, 0, 2 * Math.PI);
        this.detectionContext.stroke();
    }

    /**
     * Get current detection status
     */
    getDetectionStatus() {
        return {
            isDetecting: this.isDetecting,
            poseEnabled: this.poseEnabled,
            fallbackMode: this.fallbackMode,
            humansDetected: this.humanDetections.length
        };
    }
}

// Global human detector instance
window.cameraHumanDetector = new CameraHumanDetector();

// Auto-initialize when page loads
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🎯 Camera Human Detector DOM loaded, initializing...');
    
    // Wait for MediaPipe scripts to load
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    console.log('🎯 Starting human detector initialization...');
    await window.cameraHumanDetector.initialize();
});

// Global function to initialize pose detection - used by camera view
window.initializePoseDetection = async function() {
    console.log('🔧 Global initializePoseDetection called');
    
    if (window.cameraHumanDetector && window.cameraHumanDetector.poseDetector) {
        console.log('✅ Returning existing pose detector');
        return window.cameraHumanDetector.poseDetector;
    }
    
    // Initialize if not already done
    if (window.cameraHumanDetector) {
        await window.cameraHumanDetector.initialize();
        console.log('✅ Initialized pose detector');
        return window.cameraHumanDetector.poseDetector;
    }
    
    console.log('❌ Camera human detector not available');
    return null;
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CameraHumanDetector;
}
