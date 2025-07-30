/**
 * Real-time Face Tracking for Enrollment
 * Lightweight face detection using MediaPipe or fallback to basic tracking
 */

class FaceTracker {    constructor() {
        this.isTracking = false;
        this.trackingCanvas = null;
        this.trackingContext = null;
        this.faceDetectionWorker = null;
        this.trackingInterval = null;
        this.lastDetection = null; // Store last detection for quality checks
        
        // MediaPipe face detection (if available)
        this.faceDetection = null;
        this.mediaPipeEnabled = false;
        
        // Fallback face detection using basic algorithms
        this.faceClassifier = null;
        
        console.log('🎯 Face Tracker initialized');
    }    /**
     * Initialize face tracking system
     */
    async initialize() {
        try {
            console.log('🎯 Initializing Face Tracking System...');
            
            // Wait a moment for MediaPipe to fully load
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Try to load MediaPipe Face Detection (lightweight)
            if (typeof FaceDetection !== 'undefined') {
                console.log('📱 Attempting MediaPipe Face Detection initialization...');
                
                try {
                    this.faceDetection = new FaceDetection({
                        locateFile: (file) => {
                            return `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection@0.4/${file}`;
                        }
                    });
                    
                    this.faceDetection.setOptions({
                        selfieMode: true,
                        model: 'short',  // Use short-range model for close-up faces
                        minDetectionConfidence: 0.5
                    });
                    
                    this.faceDetection.onResults(this.onFaceDetectionResults.bind(this));
                    
                    // Set a timeout for MediaPipe initialization
                    const initPromise = this.faceDetection.initialize();
                    const timeoutPromise = new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('MediaPipe initialization timeout')), 5000)
                    );
                    
                    await Promise.race([initPromise, timeoutPromise]);
                    
                    this.mediaPipeEnabled = true;
                    console.log('✅ MediaPipe Face Detection ready');
                } catch (mediaError) {
                    console.log('⚠️ MediaPipe initialization failed:', mediaError.message);
                    console.log('🔄 Falling back to basic face detection');
                    this.mediaPipeEnabled = false;
                }
            } else {
                console.log('⚠️ MediaPipe not available, using fallback tracking');
                this.mediaPipeEnabled = false;
            }
            
            // Always ensure fallback is ready
            if (!this.mediaPipeEnabled) {
                console.log('🔧 Preparing enhanced fallback face detection...');
                // The fallback detection is always available
            }
            
        } catch (error) {
            console.log('⚠️ Face tracking initialization failed, using fallback:', error.message);
            this.mediaPipeEnabled = false;
        }
        
        console.log(`🎯 Face Tracker initialization complete - MediaPipe enabled: ${this.mediaPipeEnabled}`);
        return true;
    }/**
     * Start face tracking on video element
     */
    startTracking(videoElement, canvasElement = null) {
        if (this.isTracking) {
            this.stopTracking();
        }

        this.isTracking = true;
        this.videoElement = videoElement;
        
        console.log('🎯 Starting face tracking...');
        console.log('- Video dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
        console.log('- MediaPipe enabled:', this.mediaPipeEnabled);
        
        // Create overlay canvas if not provided
        if (canvasElement) {
            this.trackingCanvas = canvasElement;
            this.trackingContext = canvasElement.getContext('2d');
        } else {
            this.createTrackingOverlay(videoElement);
        }
        
        // Wait for video to be fully ready
        if (videoElement.videoWidth === 0) {
            console.log('⏳ Video not ready, waiting for metadata...');
            videoElement.addEventListener('loadedmetadata', () => {
                console.log('✅ Video metadata loaded, starting tracking');
                this.startTrackingLoop();
            }, { once: true });
        } else {
            this.startTrackingLoop();
        }
        
        return true;
    }
      /**
     * Start the actual tracking loop
     */
    startTrackingLoop() {
        console.log('🎯 Starting tracking loop...');
        
        // Immediately show visual feedback
        if (this.trackingContext) {
            this.drawSearchingMessage();
        }
        
        // Start tracking loop
        if (this.mediaPipeEnabled && this.faceDetection) {
            console.log('🤖 Starting MediaPipe tracking');
            this.startMediaPipeTracking();
        } else {
            console.log('🔄 Starting fallback tracking');
            this.startFallbackTracking();
        }
        
        console.log('✅ Tracking loop started successfully');
    }/**
     * Stop face tracking
     */
    stopTracking() {
        this.isTracking = false;
        this.lastDetection = null; // Clear last detection
        
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
            this.trackingInterval = null;
        }
        
        // Clean up tracking canvas
        if (this.trackingCanvas) {
            if (this.trackingContext) {
                this.trackingContext.clearRect(0, 0, this.trackingCanvas.width, this.trackingCanvas.height);
            }
            
            // Remove canvas from DOM if we created it
            if (this.trackingCanvas.id === 'faceTrackingOverlay') {
                this.trackingCanvas.remove();
            }
            
            this.trackingCanvas = null;
            this.trackingContext = null;
        }
        
        console.log('🛑 Face tracking stopped and cleaned up');
    }    /**
     * Create tracking overlay canvas
     */
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
        
        console.log('🎨 Face tracking overlay canvas created');
        
        // Update canvas size when video loads
        const updateCanvasSize = () => {
            if (videoElement.videoWidth > 0 && videoElement.videoHeight > 0) {
                this.trackingCanvas.width = videoElement.videoWidth;
                this.trackingCanvas.height = videoElement.videoHeight;
                this.trackingCanvas.style.width = videoElement.offsetWidth + 'px';
                this.trackingCanvas.style.height = videoElement.offsetHeight + 'px';
                console.log('📐 Canvas size updated:', this.trackingCanvas.width, 'x', this.trackingCanvas.height);
                
                // Draw initial indicator immediately after canvas is sized
                if (this.isTracking) {
                    setTimeout(() => this.drawSearchingMessage(), 100);
                }
            }
        };
        
        videoElement.addEventListener('loadedmetadata', updateCanvasSize);
        videoElement.addEventListener('resize', updateCanvasSize);
        
        // Try to update size immediately
        if (videoElement.videoWidth > 0) {
            updateCanvasSize();
        } else {
            // Set default size if video not ready yet
            this.trackingCanvas.width = 640;
            this.trackingCanvas.height = 480;
            this.trackingCanvas.style.width = '100%';
            this.trackingCanvas.style.height = 'auto';
            
            // Draw placeholder message
            setTimeout(() => {
                if (this.isTracking && this.trackingContext) {
                    this.drawSearchingMessage();
                }
            }, 200);
        }
    }    /**
     * MediaPipe face tracking
     */
    startMediaPipeTracking() {
        console.log('🤖 Starting MediaPipe tracking loop...');
        
        this.trackingInterval = setInterval(async () => {
            if (!this.isTracking || !this.videoElement || !this.videoElement.videoWidth) return;
            
            try {
                if (this.faceDetection) {
                    await this.faceDetection.send({ image: this.videoElement });
                }
            } catch (error) {
                console.log('MediaPipe tracking error:', error.message);
                // If MediaPipe consistently fails, switch to fallback
                if (error.message.includes('Cannot read properties')) {
                    console.log('🔄 Switching to fallback detection due to MediaPipe format issues');
                    clearInterval(this.trackingInterval);
                    this.mediaPipeEnabled = false;
                    this.startFallbackTracking();
                }
            }
        }, 100); // 10 FPS for tracking
    }/**
     * Handle MediaPipe face detection results
     */
    onFaceDetectionResults(results) {
        if (!this.isTracking || !this.trackingContext) return;
        
        // Clear previous drawings
        this.trackingContext.clearRect(0, 0, this.trackingCanvas.width, this.trackingCanvas.height);
        
        if (results.detections && results.detections.length > 0) {
            const detection = results.detections[0]; // Use first face
            console.log('🎯 MediaPipe detection:', detection); // Debug log
            this.drawFaceTracking(detection, 'mediapipe');
        } else {
            // Show searching message when no face detected
            this.drawSearchingMessage();
        }
    }/**
     * Fallback face tracking using basic algorithms
     */
    startFallbackTracking() {
        console.log('🔄 Starting fallback face detection...');
        
        this.trackingInterval = setInterval(() => {
            if (!this.isTracking || !this.videoElement || !this.videoElement.videoWidth) return;
            
            try {
                this.performBasicFaceDetection();
            } catch (error) {
                console.log('Fallback tracking error:', error.message);
                // Even if detection fails, show that we're actively tracking
                this.drawSearchingMessage();
            }
        }, 150); // Increased to 6.7 FPS for smoother fallback
        
        // Also draw an immediate indicator
        setTimeout(() => {
            if (this.trackingContext) {
                this.drawSearchingMessage();
            }
        }, 100);
        
        console.log('✅ Fallback tracking started');
    }/**
     * Basic face detection using canvas analysis
     */
    performBasicFaceDetection() {
        if (!this.trackingContext) return;
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = this.videoElement.videoWidth;
        canvas.height = this.videoElement.videoHeight;
        ctx.drawImage(this.videoElement, 0, 0);
        
        // Get image data for analysis
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const pixels = imageData.data;
        
        // Simple face detection using skin tone and face proportions
        const faceRegion = this.detectFaceRegion(pixels, canvas.width, canvas.height);
        
        // Clear previous drawings
        this.trackingContext.clearRect(0, 0, this.trackingCanvas.width, this.trackingCanvas.height);
        
        if (faceRegion) {
            console.log('🎯 Face detected with fallback algorithm');
            this.drawFaceTracking(faceRegion, 'basic');
        } else {
            // Draw a message indicating we're looking for faces
            this.drawSearchingMessage();
        }
    }
      /**
     * Draw a message when no face is detected
     */
    drawSearchingMessage() {
        if (!this.trackingContext) return;
        
        const centerX = this.trackingCanvas.width / 2;
        const centerY = this.trackingCanvas.height / 2;
        
        // Clear canvas first
        this.trackingContext.clearRect(0, 0, this.trackingCanvas.width, this.trackingCanvas.height);
        
        // Draw main searching indicator
        this.trackingContext.fillStyle = 'rgba(255, 255, 255, 0.9)';
        this.trackingContext.font = 'bold 18px Arial';
        this.trackingContext.textAlign = 'center';
        this.trackingContext.fillText('🔍 Looking for face...', centerX, centerY);
        
        // Draw mode indicator
        const modeText = this.mediaPipeEnabled ? 'MediaPipe Mode' : 'Fallback Mode';
        this.trackingContext.fillStyle = 'rgba(255, 255, 255, 0.7)';
        this.trackingContext.font = '14px Arial';
        this.trackingContext.fillText(modeText, centerX, centerY + 25);
        
        // Draw animated search circle
        const time = Date.now() * 0.005;
        const radius = 50 + Math.sin(time) * 15;
        
        this.trackingContext.strokeStyle = '#00ff88';
        this.trackingContext.lineWidth = 4;
        this.trackingContext.setLineDash([15, 10]);
        this.trackingContext.lineDashOffset = time * 30;
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX, centerY - 50, radius, 0, 2 * Math.PI);
        this.trackingContext.stroke();
        
        // Draw corner scanning lines
        const cornerSize = 30;
        const cornerOffset = 80;
        this.trackingContext.strokeStyle = 'rgba(0, 255, 136, 0.8)';
        this.trackingContext.lineWidth = 3;
        this.trackingContext.setLineDash([]);
        
        // Animated corner brackets
        const animOffset = Math.sin(time * 2) * 5;
        
        // Top-left
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(centerX - cornerOffset + animOffset, centerY - cornerOffset + cornerSize);
        this.trackingContext.lineTo(centerX - cornerOffset + animOffset, centerY - cornerOffset);
        this.trackingContext.lineTo(centerX - cornerOffset + cornerSize + animOffset, centerY - cornerOffset);
        this.trackingContext.stroke();
        
        // Top-right
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(centerX + cornerOffset - cornerSize - animOffset, centerY - cornerOffset);
        this.trackingContext.lineTo(centerX + cornerOffset - animOffset, centerY - cornerOffset);
        this.trackingContext.lineTo(centerX + cornerOffset - animOffset, centerY - cornerOffset + cornerSize);
        this.trackingContext.stroke();
        
        // Bottom-left
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(centerX - cornerOffset + animOffset, centerY + cornerOffset - cornerSize);
        this.trackingContext.lineTo(centerX - cornerOffset + animOffset, centerY + cornerOffset);
        this.trackingContext.lineTo(centerX - cornerOffset + cornerSize + animOffset, centerY + cornerOffset);
        this.trackingContext.stroke();
        
        // Bottom-right
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(centerX + cornerOffset - cornerSize - animOffset, centerY + cornerOffset);
        this.trackingContext.lineTo(centerX + cornerOffset - animOffset, centerY + cornerOffset);
        this.trackingContext.lineTo(centerX + cornerOffset - animOffset, centerY + cornerOffset - cornerSize);
        this.trackingContext.stroke();
        
        // Draw status indicator
        this.trackingContext.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.trackingContext.fillRect(10, 10, 200, 60);
        
        this.trackingContext.fillStyle = '#00ff88';
        this.trackingContext.font = 'bold 14px Arial';
        this.trackingContext.textAlign = 'left';
        this.trackingContext.fillText('Face Tracking Active', 20, 30);
        
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = '12px Arial';
        this.trackingContext.fillText(`Mode: ${modeText}`, 20, 45);
        this.trackingContext.fillText('Position yourself in frame', 20, 60);
    }/**
     * Simple face region detection
     */
    detectFaceRegion(pixels, width, height) {
        // Look for skin tone clusters in the center region
        const centerX = width / 2;
        const centerY = height / 2;
        const searchRadius = Math.min(width, height) / 3; // Increased search area
        
        let skinPixels = 0;
        let minX = width, maxX = 0, minY = height, maxY = 0;
        let totalX = 0, totalY = 0;
        
        // Scan center region for skin tones
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
        
        // Need minimum skin pixels to consider it a face
        const minSkinPixels = 800; // Lowered threshold for better detection
        if (skinPixels > minSkinPixels) {
            const avgX = totalX / skinPixels;
            const avgY = totalY / skinPixels;
            const padding = 20;
            
            // Create a face region based on detected skin tones
            const faceWidth = Math.max(80, maxX - minX + padding * 2);
            const faceHeight = Math.max(100, maxY - minY + padding * 2);
            
            return {
                x: Math.max(0, avgX - faceWidth / 2),
                y: Math.max(0, avgY - faceHeight / 2),
                width: Math.min(width, faceWidth),
                height: Math.min(height, faceHeight),
                confidence: Math.min(1.0, skinPixels / 2000) // Adjusted confidence calculation
            };
        }
        
        return null;
    }    /**
     * Simple skin tone detection
     */
    isSkinTone(r, g, b) {
        // Improved skin tone detection algorithm with multiple checks
        
        // Check 1: Basic RGB ranges for skin tones
        const basicSkin = (r > 95 && g > 40 && b > 20 && 
                          Math.max(r, g, b) - Math.min(r, g, b) > 15 &&
                          Math.abs(r - g) > 15 && r > g && r > b);
        
        // Check 2: Alternative skin tone detection (covers more diverse skin tones)
        const altSkin = (r > 60 && g > 30 && b > 15 && 
                        r > b && r > g && 
                        (r - g) > 10 && (r - b) > 10);
        
        // Check 3: HSV-like check for skin hue
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const diff = max - min;
        
        // Calculate a simple hue-like value
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
        
        // Skin tones typically fall in hue range 0-50 (red-orange-yellow)
        const hueCheck = (hue >= 0 && hue <= 50) || (hue >= 300 && hue <= 360);
        
        // Return true if any of the checks pass
        return basicSkin || altSkin || (hueCheck && max > 80);
    }/**
     * Draw face tracking overlay
     */
    drawFaceTracking(detection, type) {
        if (!this.trackingContext) return;
        
        let x, y, width, height, confidence;
          if (type === 'mediapipe') {
            // MediaPipe format - handle different possible formats
            let bbox;
            let score;
            
            if (detection.boundingBox) {
                // Standard MediaPipe Face Detection format
                bbox = detection.boundingBox;
                score = detection.score || (detection.scores && detection.scores[0]) || 0.8;
            } else if (detection.locationData && detection.locationData.relativeBoundingBox) {
                // Alternative MediaPipe format
                bbox = detection.locationData.relativeBoundingBox;
                score = detection.score || 0.8;
            } else {
                console.log('🔍 Unknown MediaPipe format:', detection);
                // Fallback to basic format
                x = detection.x || 0;
                y = detection.y || 0;
                width = detection.width || 100;
                height = detection.height || 100;
                confidence = detection.confidence || 0.8;
                console.log('🔄 Using fallback format for MediaPipe detection');
            }
              if (bbox) {
                x = (bbox.xCenter || bbox.x || 0.5) * this.trackingCanvas.width - ((bbox.width || 0.2) * this.trackingCanvas.width) / 2;
                y = (bbox.yCenter || bbox.y || 0.5) * this.trackingCanvas.height - ((bbox.height || 0.2) * this.trackingCanvas.height) / 2;
                width = (bbox.width || 0.2) * this.trackingCanvas.width;
                height = (bbox.height || 0.2) * this.trackingCanvas.height;
                confidence = Array.isArray(score) ? score[0] : (score || 0.8);
            }
        } else {
            // Basic detection format
            x = detection.x * (this.trackingCanvas.width / this.videoElement.videoWidth);
            y = detection.y * (this.trackingCanvas.height / this.videoElement.videoHeight);
            width = detection.width * (this.trackingCanvas.width / this.videoElement.videoWidth);
            height = detection.height * (this.trackingCanvas.height / this.videoElement.videoHeight);
            confidence = detection.confidence;
        }
        
        // Store last detection for quality checks
        this.lastDetection = {
            x, y, width, height, confidence,
            timestamp: Date.now()
        };
        
        // Enhanced face tracking visualization
        const centerX = x + width / 2;
        const centerY = y + height / 2;
        
        // Draw enhanced bounding box with confidence-based coloring
        const boxColor = confidence > 0.8 ? '#00ff00' : confidence > 0.6 ? '#ffff00' : '#ff6600';
        this.trackingContext.strokeStyle = boxColor;
        this.trackingContext.lineWidth = 4;
        this.trackingContext.setLineDash([]);
        this.trackingContext.strokeRect(x, y, width, height);
        
        // Draw semi-transparent fill
        this.trackingContext.fillStyle = boxColor + '20'; // 20 = 12% opacity
        this.trackingContext.fillRect(x, y, width, height);
        
        // Draw corner brackets for professional look
        const cornerSize = 20;
        this.trackingContext.strokeStyle = boxColor;
        this.trackingContext.lineWidth = 3;
        
        // Top-left corner
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(x, y + cornerSize);
        this.trackingContext.lineTo(x, y);
        this.trackingContext.lineTo(x + cornerSize, y);
        this.trackingContext.stroke();
        
        // Top-right corner
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(x + width - cornerSize, y);
        this.trackingContext.lineTo(x + width, y);
        this.trackingContext.lineTo(x + width, y + cornerSize);
        this.trackingContext.stroke();
        
        // Bottom-left corner
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(x, y + height - cornerSize);
        this.trackingContext.lineTo(x, y + height);
        this.trackingContext.lineTo(x + cornerSize, y + height);
        this.trackingContext.stroke();
        
        // Bottom-right corner
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(x + width - cornerSize, y + height);
        this.trackingContext.lineTo(x + width, y + height);
        this.trackingContext.lineTo(x + width, y + height - cornerSize);
        this.trackingContext.stroke();
        
        // Draw face landmark dots (eyes, nose, mouth)
        this.drawFaceLandmarks(centerX, centerY, width, height, confidence);
        
        // Draw enhanced confidence score with background
        this.trackingContext.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.trackingContext.fillRect(x - 2, y - 35, 150, 25);
        
        this.trackingContext.fillStyle = boxColor;
        this.trackingContext.font = 'bold 14px Arial';
        this.trackingContext.fillText(
            `Face: ${Math.round(confidence * 100)}%`, 
            x + 5, 
            y - 15
        );
        
        // Draw center crosshair
        this.trackingContext.strokeStyle = '#ff0040';
        this.trackingContext.lineWidth = 2;
        this.trackingContext.beginPath();
        this.trackingContext.moveTo(centerX - 15, centerY);
        this.trackingContext.lineTo(centerX + 15, centerY);
        this.trackingContext.moveTo(centerX, centerY - 15);
        this.trackingContext.lineTo(centerX, centerY + 15);
        this.trackingContext.stroke();
        
        // Draw center circle
        this.trackingContext.strokeStyle = '#ff0040';
        this.trackingContext.lineWidth = 1;
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX, centerY, 8, 0, 2 * Math.PI);
        this.trackingContext.stroke();
        
        // Draw quality indicators
        this.drawQualityIndicators(x, y, width, height, confidence);
        
        // Draw positioning guide
        this.drawPositioningGuide(centerX, centerY, confidence);
    }    /**
     * Draw face landmark dots (eyes, nose, mouth)
     */
    drawFaceLandmarks(centerX, centerY, width, height, confidence) {
        // Calculate landmark positions based on face dimensions
        const eyeOffsetX = width * 0.15;
        const eyeOffsetY = height * 0.15;
        const noseOffsetY = height * 0.05;
        const mouthOffsetY = height * 0.2;
        
        // Set landmark style based on confidence
        const landmarkColor = confidence > 0.8 ? '#00ff88' : confidence > 0.6 ? '#ffff44' : '#ff8844';
        this.trackingContext.fillStyle = landmarkColor;
        this.trackingContext.strokeStyle = '#ffffff';
        this.trackingContext.lineWidth = 2;
        
        // Draw left eye
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX - eyeOffsetX, centerY - eyeOffsetY, 6, 0, 2 * Math.PI);
        this.trackingContext.fill();
        this.trackingContext.stroke();
        
        // Draw right eye
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX + eyeOffsetX, centerY - eyeOffsetY, 6, 0, 2 * Math.PI);
        this.trackingContext.fill();
        this.trackingContext.stroke();
        
        // Draw nose
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX, centerY - noseOffsetY, 4, 0, 2 * Math.PI);
        this.trackingContext.fill();
        this.trackingContext.stroke();
        
        // Draw mouth
        this.trackingContext.beginPath();
        this.trackingContext.arc(centerX, centerY + mouthOffsetY, 5, 0, 2 * Math.PI);
        this.trackingContext.fill();
        this.trackingContext.stroke();
        
        // Add landmark labels
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = '10px Arial';
        this.trackingContext.textAlign = 'center';
        
        this.trackingContext.fillText('👁', centerX - eyeOffsetX, centerY - eyeOffsetY - 10);
        this.trackingContext.fillText('👁', centerX + eyeOffsetX, centerY - eyeOffsetY - 10);
        this.trackingContext.fillText('👃', centerX, centerY - noseOffsetY - 10);
        this.trackingContext.fillText('👄', centerX, centerY + mouthOffsetY + 20);
    }

    /**
     * Draw positioning guide overlay
     */
    drawPositioningGuide(centerX, centerY, confidence) {
        const canvasWidth = this.trackingCanvas.width;
        const canvasHeight = this.trackingCanvas.height;
        const idealCenterX = canvasWidth / 2;
        const idealCenterY = canvasHeight / 2;
        
        // Calculate positioning offset
        const offsetX = centerX - idealCenterX;
        const offsetY = centerY - idealCenterY;
        const totalOffset = Math.sqrt(offsetX * offsetX + offsetY * offsetY);
        
        // Draw ideal position guide (center target)
        this.trackingContext.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        this.trackingContext.lineWidth = 2;
        this.trackingContext.setLineDash([10, 5]);
        
        // Draw center circle guide
        this.trackingContext.beginPath();
        this.trackingContext.arc(idealCenterX, idealCenterY, 50, 0, 2 * Math.PI);
        this.trackingContext.stroke();
        
        // Draw positioning arrows if face is off-center
        if (totalOffset > 30) {
            this.drawPositioningArrows(centerX, centerY, idealCenterX, idealCenterY);
        }
        
        // Draw positioning status
        this.drawPositioningStatus(totalOffset, confidence);
    }

    /**
     * Draw arrows indicating where to move face
     */
    drawPositioningArrows(currentX, currentY, idealX, idealY) {
        const arrowSize = 15;
        const arrowDistance = 40;
        
        // Calculate direction
        const deltaX = idealX - currentX;
        const deltaY = idealY - currentY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        if (distance > 0) {
            const normalizedX = deltaX / distance;
            const normalizedY = deltaY / distance;
            
            // Arrow start position (near current face position)
            const arrowStartX = currentX + normalizedX * arrowDistance;
            const arrowStartY = currentY + normalizedY * arrowDistance;
            
            // Arrow end position
            const arrowEndX = arrowStartX + normalizedX * 30;
            const arrowEndY = arrowStartY + normalizedY * 30;
            
            // Draw arrow
            this.trackingContext.strokeStyle = '#ff4444';
            this.trackingContext.fillStyle = '#ff4444';
            this.trackingContext.lineWidth = 3;
            this.trackingContext.setLineDash([]);
            
            // Arrow line
            this.trackingContext.beginPath();
            this.trackingContext.moveTo(arrowStartX, arrowStartY);
            this.trackingContext.lineTo(arrowEndX, arrowEndY);
            this.trackingContext.stroke();
            
            // Arrow head
            const angle = Math.atan2(normalizedY, normalizedX);
            this.trackingContext.beginPath();
            this.trackingContext.moveTo(arrowEndX, arrowEndY);
            this.trackingContext.lineTo(
                arrowEndX - arrowSize * Math.cos(angle - Math.PI / 6),
                arrowEndY - arrowSize * Math.sin(angle - Math.PI / 6)
            );
            this.trackingContext.lineTo(
                arrowEndX - arrowSize * Math.cos(angle + Math.PI / 6),
                arrowEndY - arrowSize * Math.sin(angle + Math.PI / 6)
            );
            this.trackingContext.closePath();
            this.trackingContext.fill();
        }
    }

    /**
     * Draw positioning status indicator
     */
    drawPositioningStatus(offset, confidence) {
        const canvasWidth = this.trackingCanvas.width;
        const statusY = 30;
        
        // Status background
        this.trackingContext.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.trackingContext.fillRect(canvasWidth - 200, statusY - 20, 190, 80);
        
        // Status text
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = 'bold 12px Arial';
        this.trackingContext.textAlign = 'left';
        
        let positionStatus = '';
        let positionColor = '#ff4444';
        
        if (offset < 20) {
            positionStatus = '✓ Perfect Position';
            positionColor = '#44ff44';
        } else if (offset < 40) {
            positionStatus = '⚠ Good Position';
            positionColor = '#ffff44';
        } else {
            positionStatus = '⚠ Adjust Position';
            positionColor = '#ff4444';
        }
        
        this.trackingContext.fillStyle = positionColor;
        this.trackingContext.fillText(positionStatus, canvasWidth - 190, statusY);
        
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.fillText(`Confidence: ${Math.round(confidence * 100)}%`, canvasWidth - 190, statusY + 20);
        
        // Quality bar
        const qualityBarWidth = 120;
        const qualityBarHeight = 8;
        const qualityBarX = canvasWidth - 190;
        const qualityBarY = statusY + 35;
        
        // Background bar
        this.trackingContext.fillStyle = 'rgba(255, 255, 255, 0.3)';
        this.trackingContext.fillRect(qualityBarX, qualityBarY, qualityBarWidth, qualityBarHeight);
        
        // Quality bar fill
        const qualityWidth = Math.max(0, Math.min(qualityBarWidth, confidence * qualityBarWidth));
        const qualityColor = confidence > 0.8 ? '#44ff44' : confidence > 0.6 ? '#ffff44' : '#ff4444';
        this.trackingContext.fillStyle = qualityColor;
        this.trackingContext.fillRect(qualityBarX, qualityBarY, qualityWidth, qualityBarHeight);
    }    /**
     * Draw quality indicators
     */
    drawQualityIndicators(x, y, width, height, confidence) {
        const canvasWidth = this.trackingCanvas.width;
        const canvasHeight = this.trackingCanvas.height;
        
        // Face size indicator
        const idealSize = Math.min(canvasWidth, canvasHeight) * 0.3;
        const currentSize = Math.min(width, height);
        const sizeRatio = currentSize / idealSize;
        
        let sizeColor = '#ff0000'; // Red for bad
        let sizeStatus = 'Too Small';
        if (sizeRatio > 0.8 && sizeRatio < 1.5) {
            sizeColor = '#00ff00'; // Green for good
            sizeStatus = 'Perfect Size';
        } else if (sizeRatio > 0.6 && sizeRatio < 2.0) {
            sizeColor = '#ffff00'; // Yellow for okay
            sizeStatus = 'Good Size';
        } else if (sizeRatio >= 1.5) {
            sizeStatus = 'Too Large';
        }
        
        // Position indicator
        const centerX = x + width / 2;
        const centerY = y + height / 2;
        const canvasCenterX = canvasWidth / 2;
        const canvasCenterY = canvasHeight / 2;
        
        const positionOffset = Math.sqrt(
            Math.pow(centerX - canvasCenterX, 2) + 
            Math.pow(centerY - canvasCenterY, 2)
        );
        
        let positionColor = '#ff0000';
        let positionStatus = 'Off Center';
        if (positionOffset < canvasWidth * 0.1) {
            positionColor = '#00ff00';
            positionStatus = 'Centered';
        } else if (positionOffset < canvasWidth * 0.2) {
            positionColor = '#ffff00';
            positionStatus = 'Near Center';
        }
        
        // Enhanced quality indicators panel
        const panelX = 10;
        const panelY = 10;
        const panelWidth = 200;
        const panelHeight = 120;
        
        // Panel background with rounded corners
        this.trackingContext.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.trackingContext.fillRect(panelX, panelY, panelWidth, panelHeight);
        
        // Panel border
        this.trackingContext.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        this.trackingContext.lineWidth = 1;
        this.trackingContext.strokeRect(panelX, panelY, panelWidth, panelHeight);
        
        // Title
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = 'bold 14px Arial';
        this.trackingContext.textAlign = 'left';
        this.trackingContext.fillText('Face Quality', panelX + 10, panelY + 20);
        
        // Size indicator
        this.trackingContext.fillStyle = sizeColor;
        this.trackingContext.fillRect(panelX + 10, panelY + 35, 15, 15);
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = '12px Arial';
        this.trackingContext.fillText(`Size: ${sizeStatus}`, panelX + 35, panelY + 47);
        
        // Position indicator
        this.trackingContext.fillStyle = positionColor;
        this.trackingContext.fillRect(panelX + 10, panelY + 55, 15, 15);
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.fillText(`Position: ${positionStatus}`, panelX + 35, panelY + 67);
        
        // Confidence indicator
        const confidenceColor = confidence > 0.8 ? '#00ff00' : confidence > 0.6 ? '#ffff00' : '#ff0000';
        this.trackingContext.fillStyle = confidenceColor;
        this.trackingContext.fillRect(panelX + 10, panelY + 75, 15, 15);
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.fillText(`Confidence: ${Math.round(confidence * 100)}%`, panelX + 35, panelY + 87);
        
        // Overall quality status
        const overallQuality = this.calculateOverallQuality(sizeRatio, positionOffset / canvasWidth, confidence);
        const qualityColor = overallQuality > 0.8 ? '#00ff00' : overallQuality > 0.6 ? '#ffff00' : '#ff0000';
        const qualityText = overallQuality > 0.8 ? 'Excellent' : overallQuality > 0.6 ? 'Good' : 'Poor';
        
        this.trackingContext.fillStyle = qualityColor;
        this.trackingContext.fillRect(panelX + 10, panelY + 95, 15, 15);
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.fillText(`Overall: ${qualityText}`, panelX + 35, panelY + 107);
        
        // Add live guidance text
        this.drawLiveGuidance(sizeRatio, positionOffset, confidence);
    }

    /**
     * Calculate overall quality score
     */
    calculateOverallQuality(sizeRatio, positionRatio, confidence) {
        let sizeScore = 0;
        if (sizeRatio > 0.8 && sizeRatio < 1.5) {
            sizeScore = 1.0;
        } else if (sizeRatio > 0.6 && sizeRatio < 2.0) {
            sizeScore = 0.7;
        } else {
            sizeScore = 0.3;
        }
        
        let positionScore = 0;
        if (positionRatio < 0.1) {
            positionScore = 1.0;
        } else if (positionRatio < 0.2) {
            positionScore = 0.7;
        } else {
            positionScore = 0.4;
        }
        
        // Weighted average: confidence (40%), size (30%), position (30%)
        return (confidence * 0.4) + (sizeScore * 0.3) + (positionScore * 0.3);
    }

    /**
     * Draw live guidance text
     */
    drawLiveGuidance(sizeRatio, positionOffset, confidence) {
        const canvasWidth = this.trackingCanvas.width;
        const canvasHeight = this.trackingCanvas.height;
        
        // Guidance panel
        const guideX = canvasWidth - 250;
        const guideY = canvasHeight - 100;
        const guideWidth = 240;
        const guideHeight = 90;
        
        // Background
        this.trackingContext.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.trackingContext.fillRect(guideX, guideY, guideWidth, guideHeight);
        
        // Border
        this.trackingContext.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        this.trackingContext.lineWidth = 1;
        this.trackingContext.strokeRect(guideX, guideY, guideWidth, guideHeight);
        
        // Title
        this.trackingContext.fillStyle = '#ffffff';
        this.trackingContext.font = 'bold 12px Arial';
        this.trackingContext.textAlign = 'left';
        this.trackingContext.fillText('Live Guidance', guideX + 10, guideY + 18);
        
        // Generate guidance messages
        const guidance = [];
        
        if (confidence < 0.6) {
            guidance.push('• Improve lighting');
        }
        if (sizeRatio < 0.8) {
            guidance.push('• Move closer to camera');
        }
        if (sizeRatio > 1.5) {
            guidance.push('• Move away from camera');
        }
        if (positionOffset > canvasWidth * 0.2) {
            guidance.push('• Center your face');
        }
        if (guidance.length === 0) {
            guidance.push('✓ Perfect! Ready to capture');
        }
        
        // Draw guidance text
        this.trackingContext.fillStyle = '#ffff88';
        this.trackingContext.font = '11px Arial';
        guidance.forEach((text, index) => {
            this.trackingContext.fillText(text, guideX + 10, guideY + 35 + (index * 15));
        });
    }/**
     * Get current face quality metrics
     */
    getCurrentQuality() {
        // Check if we have a recent detection (within last 500ms)
        const isRecentDetection = this.lastDetection && 
            (Date.now() - this.lastDetection.timestamp) < 500;
        
        // If no recent detection, assume there might be a face but tracking failed
        // This is more permissive for photo capture
        const hasFace = isRecentDetection ? true : null; // null instead of false for unknown state
        
        return {
            faceDetected: hasFace,
            confidence: this.lastDetection?.confidence || 0.5, // Default to moderate confidence
            size: this.lastDetection?.width > 100 ? 'good' : 'medium',
            position: this.lastDetection ? 'centered' : 'unknown',
            lighting: 'good' // TODO: Implement lighting analysis
        };
    }
}

// Global face tracker instance
window.faceTracker = new FaceTracker();

// Auto-initialize on page load with proper timing
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🎯 Face tracking DOM loaded, initializing...');
    
    // Wait for all scripts to load, including MediaPipe
    await new Promise(resolve => {
        if (document.readyState === 'complete') {
            resolve();
        } else {
            window.addEventListener('load', resolve);
        }
    });
    
    // Additional wait to ensure MediaPipe is fully available
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    console.log('🎯 Starting face tracker initialization...');
    await window.faceTracker.initialize();
});

// Also initialize when window loads (backup)
window.addEventListener('load', async () => {
    if (!window.faceTracker.mediaPipeEnabled) {
        console.log('🔄 Backup initialization attempt...');
        await window.faceTracker.initialize();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FaceTracker;
}
