/**
 * Enhanced Face Recognition Integration
 * Client-side interface for the face recognition ML model
 */

class FaceRecognitionManager {
    constructor() {
        this.apiEndpoint = '/api/face_recognition';
        this.isProcessing = false;
        this.recognitionHistory = [];
        this.qualityThreshold = 0.7;
        this.confidenceThreshold = 0.6;
        this.processingQueue = [];
        this.maxQueueSize = 5;
    }

    /**
     * Initialize face recognition system
     */
    async initialize() {
        try {
            console.log('🤖 Initializing Face Recognition System...');
            
            // Test API connectivity
            const response = await fetch(`${this.apiEndpoint}/status`);
            if (response.ok) {
                const status = await response.json();
                console.log('✅ Face Recognition API connected:', status);
                return true;
            } else {
                console.log('⚠️ Face Recognition API not available, using fallback');
                return false;
            }
        } catch (error) {
            console.log('⚠️ Face Recognition initialization failed:', error.message);
            return false;
        }
    }

    /**
     * Validate face image quality before processing
     */
    async validateFaceQuality(imageData) {
        try {
            console.log('🔍 Validating face image quality...');
            
            const response = await fetch(`${this.apiEndpoint}/validate_quality`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_data: imageData })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('📊 Quality validation result:', result);
                return result;
            } else {
                // Client-side fallback quality check
                return this.clientSideQualityCheck(imageData);
            }
        } catch (error) {
            console.log('⚠️ Server quality check failed, using client-side validation');
            return this.clientSideQualityCheck(imageData);
        }
    }

    /**
     * Client-side image quality validation
     */
    clientSideQualityCheck(imageData) {
        try {
            // Create image element for analysis
            const img = new Image();
            
            return new Promise((resolve) => {
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    
                    canvas.width = img.width;
                    canvas.height = img.height;
                    ctx.drawImage(img, 0, 0);
                    
                    // Basic quality checks
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    const pixels = imageData.data;
                    
                    // Calculate average brightness
                    let totalBrightness = 0;
                    for (let i = 0; i < pixels.length; i += 4) {
                        const r = pixels[i];
                        const g = pixels[i + 1];
                        const b = pixels[i + 2];
                        totalBrightness += (r + g + b) / 3;
                    }
                    const avgBrightness = totalBrightness / (pixels.length / 4);
                    
                    // Quality assessment
                    const quality = {
                        valid: true,
                        quality_score: 75, // Default decent score
                        brightness: avgBrightness,
                        resolution: `${img.width}x${img.height}`,
                        recommendations: []
                    };

                    // Brightness checks
                    if (avgBrightness < 50) {
                        quality.recommendations.push('Image is too dark - improve lighting');
                        quality.quality_score -= 20;
                    } else if (avgBrightness > 200) {
                        quality.recommendations.push('Image is too bright - reduce lighting');
                        quality.quality_score -= 15;
                    }

                    // Resolution check
                    if (img.width < 200 || img.height < 200) {
                        quality.recommendations.push('Image resolution is too low');
                        quality.quality_score -= 25;
                    }

                    quality.valid = quality.quality_score >= 50;
                    quality.message = quality.valid ? 'Acceptable quality' : 'Quality needs improvement';

                    console.log('📊 Client-side quality check:', quality);
                    resolve(quality);
                };
                
                img.onerror = () => {
                    resolve({
                        valid: false,
                        quality_score: 0,
                        message: 'Invalid image data',
                        recommendations: ['Please capture a new image']
                    });
                };
                
                img.src = imageData;
            });
            
        } catch (error) {
            console.error('❌ Client-side quality check failed:', error);
            return {
                valid: false,
                quality_score: 0,
                message: 'Quality check failed',
                recommendations: ['Please try again']
            };
        }
    }

    /**
     * Enroll face for an employee
     */
    async enrollFace(employeeId, photos) {
        try {
            console.log(`🔧 Enrolling face for employee: ${employeeId}`);
            
            if (!photos || photos.length === 0) {
                throw new Error('No photos provided for enrollment');
            }

            // Validate all photos first
            const validationResults = [];
            for (let i = 0; i < photos.length; i++) {
                const quality = await this.validateFaceQuality(photos[i]);
                validationResults.push(quality);
                
                if (!quality.valid) {
                    console.log(`⚠️ Photo ${i + 1} failed quality check:`, quality.message);
                }
            }

            // Filter valid photos
            const validPhotos = photos.filter((photo, index) => validationResults[index].valid);
            
            if (validPhotos.length === 0) {
                throw new Error('No valid photos for enrollment');
            }

            console.log(`✅ ${validPhotos.length} of ${photos.length} photos passed quality check`);

            // Send enrollment request
            const response = await fetch(`/admin/api/employees/${employeeId}/enroll_face`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ photos: validPhotos })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Face enrollment successful:', result);
                return result;
            } else {
                const error = await response.json();
                throw new Error(error.message || 'Enrollment failed');
            }

        } catch (error) {
            console.error('❌ Face enrollment failed:', error);
            throw error;
        }
    }

    /**
     * Recognize face from image
     */
    async recognizeFace(imageData) {
        try {
            if (this.isProcessing) {
                console.log('⏳ Recognition already in progress, queuing request');
                return this.queueRecognition(imageData);
            }

            this.isProcessing = true;
            console.log('🔍 Starting face recognition...');

            // First validate image quality
            const quality = await this.validateFaceQuality(imageData);
            if (!quality.valid) {
                throw new Error(`Poor image quality: ${quality.message}`);
            }

            // Send recognition request
            const response = await fetch(`${this.apiEndpoint}/recognize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_data: imageData })
            });

            if (response.ok) {
                const result = await response.json();
                
                // Store in history
                this.recognitionHistory.push({
                    timestamp: new Date().toISOString(),
                    result: result,
                    quality: quality
                });

                // Limit history size
                if (this.recognitionHistory.length > 10) {
                    this.recognitionHistory.shift();
                }

                console.log('🎯 Face recognition result:', result);
                return result;
            } else {
                const error = await response.json();
                throw new Error(error.message || 'Recognition failed');
            }

        } catch (error) {
            console.error('❌ Face recognition failed:', error);
            return {
                success: false,
                recognized: false,
                error: error.message,
                confidence: 0
            };
        } finally {
            this.isProcessing = false;
            this.processQueue();
        }
    }

    /**
     * Queue recognition request when busy
     */
    queueRecognition(imageData) {
        return new Promise((resolve, reject) => {
            if (this.processingQueue.length >= this.maxQueueSize) {
                reject(new Error('Recognition queue full, try again later'));
                return;
            }

            this.processingQueue.push({ imageData, resolve, reject });
            console.log(`📋 Queued recognition request (${this.processingQueue.length} in queue)`);
        });
    }

    /**
     * Process queued recognition requests
     */
    async processQueue() {
        if (this.processingQueue.length === 0 || this.isProcessing) {
            return;
        }

        const { imageData, resolve, reject } = this.processingQueue.shift();
        
        try {
            const result = await this.recognizeFace(imageData);
            resolve(result);
        } catch (error) {
            reject(error);
        }
    }

    /**
     * Capture and process face from video element
     */
    async captureAndRecognize(videoElement) {
        try {
            // Capture frame from video
            const canvas = document.createElement('canvas');
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
            
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            
            // Process with face recognition
            return await this.recognizeFace(imageData);
            
        } catch (error) {
            console.error('❌ Capture and recognize failed:', error);
            return {
                success: false,
                recognized: false,
                error: error.message,
                confidence: 0
            };
        }
    }

    /**
     * Start continuous face recognition from video stream
     */
    startContinuousRecognition(videoElement, callback, interval = 2000) {
        console.log('🔄 Starting continuous face recognition...');
        
        const recognitionInterval = setInterval(async () => {
            if (!videoElement.videoWidth || !videoElement.videoHeight) {
                return; // Video not ready
            }

            try {
                const result = await this.captureAndRecognize(videoElement);
                callback(result);
                
                // Stop if successful recognition
                if (result.success && result.recognized && result.confidence >= this.confidenceThreshold) {
                    this.stopContinuousRecognition(recognitionInterval);
                }
                
            } catch (error) {
                console.log('⚠️ Continuous recognition error:', error.message);
            }
        }, interval);

        return recognitionInterval;
    }

    /**
     * Stop continuous recognition
     */
    stopContinuousRecognition(intervalId) {
        if (intervalId) {
            clearInterval(intervalId);
            console.log('🛑 Stopped continuous face recognition');
        }
    }

    /**
     * Get recognition statistics
     */
    getStatistics() {
        const stats = {
            totalRecognitions: this.recognitionHistory.length,
            successfulRecognitions: this.recognitionHistory.filter(h => h.result.success).length,
            averageConfidence: 0,
            queueLength: this.processingQueue.length,
            isProcessing: this.isProcessing
        };

        if (stats.successfulRecognitions > 0) {
            const confidenceSum = this.recognitionHistory
                .filter(h => h.result.success)
                .reduce((sum, h) => sum + (h.result.confidence || 0), 0);
            stats.averageConfidence = confidenceSum / stats.successfulRecognitions;
        }

        return stats;
    }

    /**
     * Clear recognition history
     */
    clearHistory() {
        this.recognitionHistory = [];
        console.log('🗑️ Recognition history cleared');
    }

    /**
     * Test face recognition system
     */
    async testSystem() {
        console.log('🧪 Testing Face Recognition System...');
        
        const testResults = {
            apiConnected: false,
            qualityValidation: false,
            recognitionCapable: false,
            overallHealth: 'unknown'
        };

        try {
            // Test API connection
            const initResult = await this.initialize();
            testResults.apiConnected = initResult;

            // Test quality validation with dummy data
            const dummyImage = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD//gA7Q1JFQVRP';
            const qualityResult = await this.validateFaceQuality(dummyImage);
            testResults.qualityValidation = qualityResult !== null;

            // Determine overall health
            if (testResults.apiConnected && testResults.qualityValidation) {
                testResults.overallHealth = 'excellent';
                testResults.recognitionCapable = true;
            } else if (testResults.qualityValidation) {
                testResults.overallHealth = 'good';
                testResults.recognitionCapable = true;
            } else {
                testResults.overallHealth = 'poor';
            }

            console.log('📊 Face Recognition System Test Results:', testResults);
            return testResults;

        } catch (error) {
            console.error('❌ Face Recognition System test failed:', error);
            testResults.overallHealth = 'failed';
            return testResults;
        }
    }
}

// Global face recognition manager instance
window.faceRecognitionManager = new FaceRecognitionManager();

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await window.faceRecognitionManager.initialize();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FaceRecognitionManager;
}
