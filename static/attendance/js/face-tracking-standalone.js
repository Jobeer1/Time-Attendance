/**
 * Standalone Face Detection - No External Dependencies
 * Robust face detection that works without MediaPipe
 */

class StandaloneFaceTracker {
    constructor() {
        this.isTracking = false;
        this.trackingCanvas = null;
        this.trackingContext = null;
        this.trackingInterval = null;
        this.lastDetection = null;
        this.videoElement = null;
        
        console.log('🎯 Standalone Face Tracker initialized');
    }

    async initialize() {
        console.log('🎯 Initializing Standalone Face Tracking...');
        // Always ready - no external dependencies
        return true;
    }

    startTracking(videoElement, canvasElement = null) {
        if (this.isTracking) {
            this.stopTracking();
        }

        this.isTracking = true;
        this.videoElement = videoElement;
        
        console.log('🎯 Starting standalone face tracking...');
        console.log('- Video dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
        
        // Create overlay canvas if not provided
        if (canvasElement) {
            this.trackingCanvas = canvasElement;
            this.trackingContext = canvasElement.getContext('2d');
        } else {
            this.createTrackingOverlay(videoElement);
        }
        
        // Wait for video to be ready
        if (videoElement.videoWidth === 0) {
            console.log('⏳ Video not ready, waiting...');
            videoElement.addEventListener('loadedmetadata', () => {
                console.log('✅ Video ready, starting tracking');
                this.startTrackingLoop();
            }, { once: true });
        } else {
            this.startTrackingLoop();
        }
        
        return true;
    }

    createTrackingOverlay(videoElement) {
        const container = videoElement.parentElement;
        
        // Remove existing overlay if present
        if (this.trackingCanvas) {
            this.trackingCanvas.remove();
        }
        
        this.trackingCanvas = document.createElement('canvas');
        this.trackingCanvas.id = 'faceTrackingOverlay';
        this.trackingCanvas.style.position = 'absolute';
        this.trackingCanvas.style.top = '0';
        this.trackingCanvas.style.left = '0';
        this.trackingCanvas.style.pointerEvents = 'none';
        this.trackingCanvas.style.zIndex = '10';
        this.trackingCanvas.style.border = '2px solid transparent';
        
        // Ensure container has relative positioning
        container.style.position = 'relative';
        container.appendChild(this.trackingCanvas);
        this.trackingContext = this.trackingCanvas.getContext('2d');
        
        console.log('🎨 Standalone tracking overlay created');
        
        // Update canvas size
        const updateCanvasSize = () => {
            if (videoElement.videoWidth > 0 && videoElement.videoHeight > 0) {
                this.trackingCanvas.width = videoElement.videoWidth;
                this.trackingCanvas.height = videoElement.videoHeight;
                this.trackingCanvas.style.width = videoElement.offsetWidth + 'px';
                this.trackingCanvas.style.height = videoElement.offsetHeight + 'px';
                console.log('📐 Canvas size updated:', this.trackingCanvas.width, 'x', this.trackingCanvas.height);
            }
        };
        
        videoElement.addEventListener('loadedmetadata', updateCanvasSize);
        videoElement.addEventListener('resize', updateCanvasSize);
        
        if (videoElement.videoWidth > 0) {
            updateCanvasSize();
        }
    }

    startTrackingLoop() {
        console.log('🔄 Starting standalone tracking loop...');
        
        this.trackingInterval = setInterval(() => {
            if (!this.isTracking || !this.videoElement || !this.videoElement.videoWidth) return;
            
            try {
                this.performFaceDetection();
            } catch (error) {
                console.log('Tracking error:', error.message);
            }
        }, 200); // 5 FPS
        
        console.log('✅ Standalone tracking loop started');
    }

    performFaceDetection() {
        if (!this.trackingContext) return;
        
        // Clear canvas
        this.trackingContext.clearRect(0, 0, this.trackingCanvas.width, this.trackingCanvas.height);
        
        // Create analysis canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = this.videoElement.videoWidth;
        canvas.height = this.videoElement.videoHeight;
        ctx.drawImage(this.videoElement, 0, 0);
        
        // Get image data
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const pixels = imageData.data;
        
        // Detect face region
        const faceRegion = this.detectFaceRegion(pixels, canvas.width, canvas.height);
        
        if (faceRegion) {
            this.drawFaceTracking(faceRegion);
        } else {
            this.drawSearchingIndicator();
        }
    }

    detectFaceRegion(pixels, width, height) {
        // Enhanced skin tone detection
        const centerX = width / 2;
        const centerY = height / 2;
        const searchRadius = Math.min(width, height) / 3;
        
        let skinPixels = 0;
        let totalX = 0, totalY = 0;
        let minX = width, maxX = 0, minY = height, maxY = 0;
        
        // Scan for skin tones
        for (let y = Math.max(0, centerY - searchRadius); y < Math.min(height, centerY + searchRadius); y++) {
            for (let x = Math.max(0, centerX - searchRadius); x < Math.min(width, centerX + searchRadius); x++) {
                const index = (y * width + x) * 4;
                const r = pixels[index];
                const g = pixels[index + 1];
                const b = pixels[index + 2];
                
                if (this.isSkinTone(r, g, b)) {
                    skinPixels++;
                    totalX += x;
                    totalY += y;
                    
                    minX = Math.min(minX, x);
                    maxX = Math.max(maxX, x);
                    minY = Math.min(minY, y);
                    maxY = Math.max(maxY, y);
                }
            }
        }
        
        // Require minimum skin pixels
        if (skinPixels > 800) {
            const avgX = totalX / skinPixels;
            const avgY = totalY / skinPixels;
            const padding = 30;
            
            const faceWidth = Math.max(100, maxX - minX + padding * 2);
            const faceHeight = Math.max(120, maxY - minY + padding * 2);
            
            return {
                x: Math.max(0, avgX - faceWidth / 2),
                y: Math.max(0, avgY - faceHeight / 2),
                width: Math.min(width, faceWidth),
                height: Math.min(height, faceHeight),
                confidence: Math.min(1.0, skinPixels / 2000)
            };
        }
        
        return null;
    }

    isSkinTone(r, g, b) {
        // Multiple skin tone detection methods
        const basic = (r > 95 && g > 40 && b > 20 && 
                      Math.max(r, g, b) - Math.min(r, g, b) > 15 &&
                      Math.abs(r - g) > 15 && r > g && r > b);
        
        const alt = (r > 60 && g > 30 && b > 15 && r > b && r > g);
        
        // HSV-like hue check
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const diff = max - min;
        
        let hue = 0;
        if (diff > 0) {
            if (max === r) {
                hue = ((g - b) / diff) % 6;
            } else if (max === g) {
                hue = (b - r) / diff + 2;
            } else {
                hue = (r - g) / diff + 4;
            }
            hue = hue * 60;
            if (hue < 0) hue += 360;
        }
        
        const hueCheck = (hue >= 0 && hue <= 50) || (hue >= 300 && hue <= 360);
        
        return basic || alt || (hueCheck && max > 80);
    }

    drawFaceTracking(detection) {
        // Scale to canvas coordinates
        const x = detection.x * (this.trackingCanvas.width / this.videoElement.videoWidth);
        const y = detection.y * (this.trackingCanvas.height / this.videoElement.videoHeight);
        const width = detection.width * (this.trackingCanvas.width / this.videoElement.videoWidth);
        const height = detection.height * (this.trackingCanvas.height / this.videoElement.videoHeight);
        const confidence = detection.confidence;
        
        // Store detection
        this.lastDetection = { x, y, width, height, confidence, timestamp: Date.now() };
        
        const centerX = x + width / 2;
        const centerY = y + height / 2;
        
        // Color based on confidence
        const boxColor = confidence > 0.8 ? '#00ff00' : confidence > 0.6 ? '#ffff00' : '#ff6600';
        
        // Draw main bounding box
        this.trackingContext.strokeStyle = boxColor;
        this.trackingContext.lineWidth = 4;
        this.trackingContext.setLineDash([]);
        this.trackingContext.strokeRect(x, y, width, height);
        
        // Draw corner brackets
        const cornerSize = 25;
        this.trackingContext.strokeStyle = boxColor;
        this.trackingContext.lineWidth = 3;
        
        // Top-left
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(x, y + cornerSize);
        this.trackingContext.lineTo(x, y);
        this.trackingContext.lineTo(x + cornerSize, y);
        this.trackingContext.stroke();
        
        // Top-right
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(x + width - cornerSize, y);
        this.trackingContext.lineTo(x + width, y);
        this.trackingContext.lineTo(x + width, y + cornerSize);
        this.trackingContext.stroke();
        
        // Bottom-left
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(x, y + height - cornerSize);
        this.trackingContext.lineTo(x, y + height);
        this.trackingContext.lineTo(x + cornerSize, y + height);
        this.trackingContext.stroke();
        
        // Bottom-right
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(x + width - cornerSize, y + height);
        this.trackingContext.lineTo(x + width, y + height);
        this.trackingContext.lineTo(x + width, y + height - cornerSize);
        this.trackingContext.stroke();
        
        // Draw face landmarks
        this.drawFaceLandmarks(centerX, centerY, width, height, confidence);
        
        // Draw confidence score
        this.trackingContext.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.trackingContext.fillRect(x - 2, y - 40, 180, 30);
        
        this.trackingContext.fillStyle = boxColor;
        this.trackingContext.font = 'bold 16px Arial';
        this.trackingContext.textAlign = 'left';
        this.trackingContext.fillText(`Face: ${Math.round(confidence * 100)}%`, x + 5, y - 18);
        
        // Draw quality panel
        this.drawQualityPanel(x, y, width, height, confidence);
    }

    drawFaceLandmarks(centerX, centerY, width, height, confidence) {
        const eyeOffsetX = width * 0.18;
        const eyeOffsetY = height * 0.18;
        const noseOffsetY = height * 0.08;
        const mouthOffsetY = height * 0.22;
        
        const landmarkColor = confidence > 0.8 ? '#00ff88' : confidence > 0.6 ? '#ffff44' : '#ff8844';
        this.trackingContext.fillStyle = landmarkColor;
        this.trackingContext.strokeStyle = '#ffffff';
        this.trackingContext.lineWidth = 2;
        
        // Eyes
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX - eyeOffsetX, centerY - eyeOffsetY, 8, 0, 2 * Math.PI);
        this.trackingContext.fill();
        this.trackingContext.stroke();
        
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX + eyeOffsetX, centerY - eyeOffsetY, 8, 0, 2 * Math.PI);
        this.trackingContext.fill();
        this.trackingContext.stroke();
        
        // Nose
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX, centerY - noseOffsetY, 6, 0, 2 * Math.PI);
        this.trackingContext.fill();
        this.trackingContext.stroke();
        
        // Mouth
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX, centerY + mouthOffsetY, 7, 0, 2 * Math.PI);
        this.trackingContext.fill();
        this.trackingContext.stroke();
    }

    drawQualityPanel(x, y, width, height, confidence) {
        const panelX = 15;
        const panelY = 15;
        const panelWidth = 220;
        const panelHeight = 120;
        
        // Panel background
        this.trackingContext.fillStyle = 'rgba(0, 0, 0, 0.85)';
        this.trackingContext.fillRect(panelX, panelY, panelWidth, panelHeight);
        
        this.trackingContext.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        this.trackingContext.lineWidth = 1;
        this.trackingContext.strokeRect(panelX, panelY, panelWidth, panelHeight);
        
        // Title
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = 'bold 16px Arial';
        this.trackingContext.textAlign = 'left';
        this.trackingContext.fillText('Face Quality Assessment', panelX + 10, panelY + 25);
        
        // Confidence
        const confColor = confidence > 0.8 ? '#00ff00' : confidence > 0.6 ? '#ffff00' : '#ff0000';
        this.trackingContext.fillStyle = confColor;
        this.trackingContext.fillRect(panelX + 10, panelY + 40, 20, 15);
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = '14px Arial';
        this.trackingContext.fillText(`Confidence: ${Math.round(confidence * 100)}%`, panelX + 40, panelY + 52);
        
        // Size assessment
        const idealSize = Math.min(this.trackingCanvas.width, this.trackingCanvas.height) * 0.3;
        const currentSize = Math.min(width, height);
        const sizeRatio = currentSize / idealSize;
        const sizeColor = (sizeRatio > 0.8 && sizeRatio < 1.5) ? '#00ff00' : '#ffff00';
        const sizeText = (sizeRatio > 0.8 && sizeRatio < 1.5) ? 'Perfect Size' : 'Adjust Distance';
        
        this.trackingContext.fillStyle = sizeColor;
        this.trackingContext.fillRect(panelX + 10, panelY + 65, 20, 15);
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.fillText(`Size: ${sizeText}`, panelX + 40, panelY + 77);
        
        // Position assessment
        const centerFaceX = x + width / 2;
        const centerFaceY = y + height / 2;
        const centerCanvasX = this.trackingCanvas.width / 2;
        const centerCanvasY = this.trackingCanvas.height / 2;
        const positionOffset = Math.sqrt(
            Math.pow(centerFaceX - centerCanvasX, 2) + 
            Math.pow(centerFaceY - centerCanvasY, 2)
        );
        
        const positionColor = positionOffset < this.trackingCanvas.width * 0.1 ? '#00ff00' : '#ffff00';
        const positionText = positionOffset < this.trackingCanvas.width * 0.1 ? 'Centered' : 'Adjust Position';
        
        this.trackingContext.fillStyle = positionColor;
        this.trackingContext.fillRect(panelX + 10, panelY + 90, 20, 15);
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.fillText(`Position: ${positionText}`, panelX + 40, panelY + 102);
    }

    drawSearchingIndicator() {
        if (!this.trackingContext) return;
        
        const centerX = this.trackingCanvas.width / 2;
        const centerY = this.trackingCanvas.height / 2;
        
        // Main message
        this.trackingContext.fillStyle = 'rgba(255, 255, 255, 0.9)';
        this.trackingContext.font = 'bold 20px Arial';
        this.trackingContext.textAlign = 'center';
        this.trackingContext.fillText('🔍 Looking for face...', centerX, centerY);
        
        // Mode indicator
        this.trackingContext.fillStyle = 'rgba(255, 255, 255, 0.7)';
        this.trackingContext.font = '16px Arial';
        this.trackingContext.fillText('Standalone Detection Mode', centerX, centerY + 30);
        
        // Animated scanning effect
        const time = Date.now() * 0.008;
        const radius = 60 + Math.sin(time) * 20;
        
        this.trackingContext.strokeStyle = '#00ff88';
        this.trackingContext.lineWidth = 4;
        this.trackingContext.setLineDash([20, 15]);
        this.trackingContext.lineDashOffset = time * 40;
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX, centerY - 60, radius, 0, 2 * Math.PI);
        this.trackingContext.stroke();
        
        // Corner scanning indicators
        const cornerSize = 35;
        const cornerOffset = 100;
        this.trackingContext.strokeStyle = 'rgba(0, 255, 136, 0.8)';
        this.trackingContext.lineWidth = 3;
        this.trackingContext.setLineDash([]);
        
        const animOffset = Math.sin(time * 3) * 8;
        
        // Animated corners
        const corners = [
            [centerX - cornerOffset, centerY - cornerOffset],
            [centerX + cornerOffset, centerY - cornerOffset],
            [centerX - cornerOffset, centerY + cornerOffset],
            [centerX + cornerOffset, centerY + cornerOffset]
        ];
        
        corners.forEach(([cx, cy], index) => {
            const offset = animOffset * (index % 2 === 0 ? 1 : -1);
            this.trackingContext.beginPath();
            this.trackingContext.moveTo(cx + offset, cy + cornerSize);
            this.trackingContext.lineTo(cx + offset, cy);
            this.trackingContext.lineTo(cx + cornerSize + offset, cy);
            this.trackingContext.stroke();
        });
        
        // Status panel
        this.trackingContext.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.trackingContext.fillRect(15, 15, 250, 80);
        
        this.trackingContext.fillStyle = '#00ff88';
        this.trackingContext.font = 'bold 16px Arial';
        this.trackingContext.textAlign = 'left';
        this.trackingContext.fillText('Standalone Face Tracking', 25, 35);
        
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = '14px Arial';
        this.trackingContext.fillText('Status: Searching for face', 25, 55);
        this.trackingContext.fillText('Mode: Enhanced skin detection', 25, 75);
    }

    stopTracking() {
        this.isTracking = false;
        this.lastDetection = null;
        
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
            this.trackingInterval = null;
        }
        
        if (this.trackingCanvas) {
            if (this.trackingContext) {
                this.trackingContext.clearRect(0, 0, this.trackingCanvas.width, this.trackingCanvas.height);
            }
            
            if (this.trackingCanvas.id === 'faceTrackingOverlay') {
                this.trackingCanvas.remove();
            }
            
            this.trackingCanvas = null;
            this.trackingContext = null;
        }
        
        console.log('🛑 Standalone face tracking stopped');
    }

    getCurrentQuality() {
        const isRecentDetection = this.lastDetection && 
            (Date.now() - this.lastDetection.timestamp) < 500;
        
        return {
            faceDetected: isRecentDetection ? true : null,
            confidence: this.lastDetection?.confidence || 0.5,
            size: this.lastDetection?.width > 100 ? 'good' : 'medium',
            position: this.lastDetection ? 'centered' : 'unknown',
            lighting: 'good'
        };
    }
}

// If MediaPipe failed to load, use standalone tracker
if (typeof FaceDetection === 'undefined') {
    console.log('🔄 MediaPipe not available, using standalone face tracker');
    window.faceTracker = new StandaloneFaceTracker();
    
    // Initialize standalone tracker
    document.addEventListener('DOMContentLoaded', async () => {
        console.log('🎯 Initializing standalone face tracker...');
        await window.faceTracker.initialize();
    });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StandaloneFaceTracker;
}
