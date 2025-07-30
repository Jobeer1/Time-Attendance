/**
 * Progress tracking JavaScript for PDF to Excel/CSV Converter
 */

// Global variables for progress tracking
let progressInterval = null;

/**
 * Generic handler for form submissions with progress bar and polling
 */
function handleFormSubmission(form, progressContainerId, progressFillId, progressTextId, buttonId, originalButtonText) {
    const formData = new FormData(form);
    const button = document.getElementById(buttonId);
    const progressContainer = document.getElementById(progressContainerId);
    const progressFill = document.getElementById(progressFillId);
    const progressText = document.getElementById(progressTextId);

    // Show progress bar
    progressContainer.style.display = 'block';
    button.disabled = true;
    button.textContent = originalButtonText + '...';
    progressFill.style.width = '0%';
    progressText.textContent = 'Starting...';

    // Determine endpoint based on form id
    let endpoint = '';
    if (form.id === 'image-to-csv-form') {
        endpoint = '/image_to_csv';
    } else if (form.id === 'batch-image-to-csv-form') {
        endpoint = '/batch_image_to_csv';
    } else if (form.id === 'pdf-to-csv-form') {
        endpoint = '/pdf_to_csv';
    } else if (form.id === 'batch-pdf-to-csv-form-new') {
        endpoint = '/batch_pdf_to_csv';
    } else {
        progressText.textContent = 'Unknown form submission.';
        button.disabled = false;
        button.textContent = originalButtonText;
        return;
    }

    fetch(endpoint, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.task_id) {
            startProgressPolling(data.task_id, progressFill, progressText, button, originalButtonText);
        } else {
            throw new Error('No task ID received');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        progressText.textContent = 'Error starting conversion';
        progressText.classList.add('error');
        button.disabled = false;
        button.textContent = originalButtonText;
    });
}

/**
 * Start progress polling for a background task
 */
function startProgressPolling(taskId, progressFill, progressText, button, originalButtonText) {
    let pollCount = 0;
    let lastProgress = 0;
    let stuckCount = 0;
    let lastProgressTime = Date.now();
    
    // Add processing animation to progress bar
    progressFill.classList.add('processing');
    
    progressInterval = setInterval(() => {
        pollCount++;
        
        fetch(`/progress/${taskId}`)
        .then(response => response.json())
        .then(data => {
            // Update progress bar
            progressFill.style.width = Math.max(data.progress, 0) + '%';
            
            // Enhanced progress text with emojis and detailed status
            let displayMessage = data.message;
            
            // Calculate elapsed time
            const elapsedMinutes = Math.floor(pollCount * 2 / 60);
            const elapsedSeconds = (pollCount * 2) % 60;
            const timeDisplay = elapsedMinutes > 0 
                ? `${elapsedMinutes}:${elapsedSeconds.toString().padStart(2, '0')}` 
                : `${elapsedSeconds}s`;
            
            // Check if progress is stuck - more lenient for intensive operations
            if (data.progress === lastProgress && data.progress > 0 && data.progress < 100) {
                stuckCount++;
                if (stuckCount >= 10) { // 20 seconds without progress change
                    displayMessage += " <span style='color: #f39c12;'>(Testing multiple OCR configurations...)</span>";
                }
                if (stuckCount >= 20) { // 40 seconds without progress change
                    displayMessage += " <span style='color: #e67e22;'>(This may take 2-5 minutes per page)</span>";
                }
            } else if (data.progress > lastProgress) {
                stuckCount = 0;
                lastProgressTime = Date.now();
            }
            
            // Always show time indicator for running processes
            if (data.progress > 0 && data.progress < 100) {
                displayMessage += ` <span style='color: #6c757d; font-size: 0.9em;'>[${timeDisplay}]</span>`;
            }
            
            // Show animated working indicator 
            if (data.progress > 0 && data.progress < 100) {
                const workingIcons = ['⚙️', '🔄', '⏳', '🔍'];
                const iconIndex = Math.floor(pollCount / 3) % workingIcons.length;
                displayMessage += ` <span class="working-spinner">${workingIcons[iconIndex]}</span>`;
            }
            
            // Add helpful context based on progress level
            if (data.progress >= 10 && data.progress < 90 && pollCount > 10) {
                if (displayMessage.includes('Processing image')) {
                    displayMessage += " <span style='color: #17a2b8; font-size: 0.85em;'>(OCR analysis in progress...)</span>";
                } else if (displayMessage.includes('Converting')) {
                    displayMessage += " <span style='color: #17a2b8; font-size: 0.85em;'>(PDF conversion active...)</span>";
                }
            }
            lastProgress = data.progress;
            
            progressText.innerHTML = displayMessage;
            
            // Check if complete or error
            if (data.progress >= 100 || data.message.includes('Completed!')) {
                clearInterval(progressInterval);
                button.disabled = false;
                button.textContent = originalButtonText;
                
                // Success state
                progressFill.classList.remove('processing');
                progressFill.classList.add('success');
                progressText.classList.add('success');
                
                // Check if there's a download link in the message
                if (data.message.includes('File saved to Downloads:')) {
                    const filename = data.message.split('File saved to Downloads: ')[1];
                    progressText.innerHTML = `🎉 Completed! File saved to: <strong>E:\\Downloads\\${filename}</strong>`;
                } else if (data.message.includes('Download:')) {
                    const filename = data.message.split('Download: ')[1];
                    progressText.innerHTML = `🎉 <a href="/download/${filename}" style="color: #28a745; text-decoration: none; font-weight: bold;">📥 Download ${filename}</a>`;
                }
            } else if (data.progress === 0 && data.message.includes('Error')) {
                // Error state
                clearInterval(progressInterval);
                button.disabled = false;
                button.textContent = originalButtonText;
                progressFill.classList.remove('processing');
                progressFill.classList.add('error');
                progressText.classList.add('error');
            }
            
            // Extended timeout check - if no progress for too long (5 minutes for intensive operations)
            if (Date.now() - lastProgressTime > 300000) { // 5 minutes without any progress
                clearInterval(progressInterval);
                button.disabled = false;
                button.textContent = originalButtonText;
                progressFill.classList.remove('processing');
                progressText.innerHTML = '⚠️ Processing seems to have stalled. <a href="javascript:location.reload()" style="color: #0078d4;">Refresh page</a> and try again.';
                progressText.classList.add('error');
            }
        })
        .catch(error => {
            console.error('Progress polling error:', error);
            
            // Don't stop polling immediately on network errors
            if (pollCount > 150) { // Stop after 5 minutes of errors
                clearInterval(progressInterval);
                button.disabled = false;
                button.textContent = originalButtonText;
                progressFill.classList.remove('processing');
                progressText.textContent = '❌ Connection lost. Please refresh and try again.';
                progressText.classList.add('error');
            } else if (pollCount % 5 === 0) { // Show warning every 5 failed polls
                progressText.innerHTML = `${displayMessage || 'Processing...'} <span style="color: #f39c12;">(Connection issues...)</span>`;
            }
        });
    }, 2000); // Poll every 2 seconds
}

/**
 * Show progress bar for traditional form submissions
 */
function showProgressBar(containerId, buttonId, buttonText, messages) {
    // Show progress bar
    document.getElementById(containerId).style.display = 'block';
    const button = document.getElementById(buttonId);
    const progressFill = document.querySelector(`#${containerId} .progress-fill`);
    const progressText = document.querySelector(`#${containerId} .progress-text`);
    
    button.disabled = true;
    button.textContent = buttonText;
    progressFill.classList.add('processing');
    
    // Animate progress (simulation for traditional forms)
    let progress = 0;
    let messageIndex = 0;
    
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90; // Don't go to 100% until complete
        
        progressFill.style.width = progress + '%';
        
        // Update message based on progress
        const targetIndex = Math.floor((progress / 90) * messages.length);
        if (targetIndex !== messageIndex && targetIndex < messages.length) {
            messageIndex = targetIndex;
            progressText.textContent = messages[messageIndex];
        }
    }, 1000);
    
    // Clean up interval when form submits
    setTimeout(() => clearInterval(interval), 100);
}

/**
 * Initialize event listeners when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Handle PDF to Images form submission
    const pdfToImagesForm = document.getElementById('pdf-to-images-form');
    if (pdfToImagesForm) {
        pdfToImagesForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const button = document.getElementById('pdf-to-images-button');
            const progressContainer = document.getElementById('progress-container-1');
            const progressFill = document.getElementById('progress-fill-1');
            const progressText = document.getElementById('progress-text-1');
            
            // Show progress bar
            progressContainer.style.display = 'block';
            button.disabled = true;
            button.textContent = 'Converting PDF...';
            progressFill.style.width = '0%';
            progressText.textContent = 'Starting PDF conversion...';
            
            // Submit form and get task ID
            fetch('/pdf_to_images', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.task_id) {
                    startProgressPolling(data.task_id, progressFill, progressText, button, 'Convert PDF to Images');
                } else {
                    throw new Error('No task ID received');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                progressText.textContent = 'Error starting PDF conversion';
                progressText.classList.add('error');
                button.disabled = false;
                button.textContent = 'Convert PDF to Images';
            });
        });
    }

    // Handle PDF to CSV form submission (NEW)
    const pdfToCsvForm = document.getElementById('pdf-to-csv-form');
    if (pdfToCsvForm) {
        pdfToCsvForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const button = document.getElementById('pdf-to-csv-button');
            const progressContainer = document.getElementById('progress-container-csv');
            const progressFill = document.getElementById('progress-fill-csv');
            const progressText = document.getElementById('progress-text-csv');
            
            // Show progress bar
            progressContainer.style.display = 'block';
            button.disabled = true;
            button.textContent = 'Converting to CSV...';
            progressFill.style.width = '0%';
            progressText.textContent = 'Starting PDF to CSV conversion with enhanced OCR...';
            
            // Submit form and get task ID
            fetch('/pdf_to_csv', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.task_id) {
                    startProgressPolling(data.task_id, progressFill, progressText, button, 'Convert PDF to CSV');
                } else {
                    throw new Error('No task ID received');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                progressText.textContent = 'Error starting PDF to CSV conversion';
                progressText.classList.add('error');
                button.disabled = false;
                button.textContent = 'Convert PDF to CSV';
            });
        });
    }

    // Handle Batch PDF to CSV form submission (NEW)
    const batchPdfToCsvForm = document.getElementById('batch-pdf-to-csv-form');
    if (batchPdfToCsvForm) {
        batchPdfToCsvForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const button = document.getElementById('batch-pdf-to-csv-button');
            const progressContainer = document.getElementById('progress-container-csv-batch');
            const progressFill = document.getElementById('progress-fill-csv-batch');
            const progressText = document.getElementById('progress-text-csv-batch');
            
            // Show progress bar
            progressContainer.style.display = 'block';
            button.disabled = true;
            button.textContent = 'Converting Multiple PDFs...';
            progressFill.style.width = '0%';
            progressText.textContent = 'Starting batch PDF to CSV conversion...';
            
            // Submit form and get task ID
            fetch('/batch_pdf_to_csv', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.task_id) {
                    startProgressPolling(data.task_id, progressFill, progressText, button, 'Convert All PDFs to CSV');
                } else {
                    throw new Error('No task ID received');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                progressText.textContent = 'Error starting batch PDF to CSV conversion';
                progressText.classList.add('error');
                button.disabled = false;
                button.textContent = 'Convert All PDFs to CSV';
            });
        });
    }

    // Handle Batch PDF to Images form submission
    const batchPdfForm = document.getElementById('batch-pdf-form');
    if (batchPdfForm) {
        batchPdfForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const button = document.getElementById('batch-pdf-button');
            const progressContainer = document.getElementById('progress-container-batch1');
            const progressFill = document.getElementById('progress-fill-batch1');
            const progressText = document.getElementById('progress-text-batch1');
            
            // Show progress bar
            progressContainer.style.display = 'block';
            button.disabled = true;
            button.textContent = 'Converting PDFs...';
            progressFill.style.width = '0%';
            progressText.textContent = 'Starting batch PDF conversion...';
            
            // Submit form and get task ID
            fetch('/batch_pdf_to_images', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.task_id) {
                    startProgressPolling(data.task_id, progressFill, progressText, button, 'Convert All PDFs to Images');
                } else {
                    throw new Error('No task ID received');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                progressText.textContent = 'Error starting batch PDF conversion';
                progressText.classList.add('error');
                button.disabled = false;
                button.textContent = 'Convert All PDFs to Images';
            });
        });
    }

    // Handle Batch Images form submission
    const batchImagesForm = document.getElementById('batch-images-form');
    if (batchImagesForm) {
        batchImagesForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const button = document.getElementById('batch-images-button');
            const progressContainer = document.getElementById('progress-container-batch3');
            const progressFill = document.getElementById('progress-fill-batch3');
            const progressText = document.getElementById('progress-text-batch3');
            
            // Show progress bar
            progressContainer.style.display = 'block';
            button.disabled = true;
            button.textContent = 'Processing Images...';
            progressFill.style.width = '0%';
            progressText.textContent = 'Starting batch image processing...';
            
            // Submit form and get task ID
            fetch('/batch_extract_text_from_images', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.task_id) {
                    startProgressPolling(data.task_id, progressFill, progressText, button, 'Extract Text from All Images');
                } else {
                    throw new Error('No task ID received');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                progressText.textContent = 'Error starting batch image processing';
                progressText.classList.add('error');
                button.disabled = false;
                button.textContent = 'Extract Text from All Images';
            });
        });
    }

    // Image to CSV form handler
    const imageToCSVForm = document.getElementById('image-to-csv-form');
    if (imageToCSVForm) {
        imageToCSVForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleFormSubmission(
                this, 
                'progress-container-image', 
                'progress-fill-image', 
                'progress-text-image', 
                'image-to-csv-button',
                'Convert Image to CSV'
            );
        });
    }

    // Batch Image to CSV form handler
    const batchImageToCSVForm = document.getElementById('batch-image-to-csv-form');
    if (batchImageToCSVForm) {
        batchImageToCSVForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleFormSubmission(
                this, 
                'progress-container-image-batch', 
                'progress-fill-image-batch', 
                'progress-text-image-batch', 
                'batch-image-to-csv-button',
                'Convert All Images to CSV'
            );
        });
    }

    // New PDF to CSV form handler
    const pdfToCSVNewForm = document.getElementById('pdf-to-csv-form');
    if (pdfToCSVNewForm) {
        pdfToCSVNewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleFormSubmission(
                this, 
                'progress-container-csv-new', 
                'progress-fill-csv-new', 
                'progress-text-csv-new', 
                'pdf-to-csv-new-button',
                'Convert PDF to CSV'
            );
        });
    }

    // New Batch PDF to CSV form handler
    const batchPDFToCSVNewForm = document.getElementById('batch-pdf-to-csv-form-new');
    if (batchPDFToCSVNewForm) {
        batchPDFToCSVNewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleFormSubmission(
                this, 
                'progress-container-csv-batch-new', 
                'progress-fill-csv-batch-new', 
                'progress-text-csv-batch-new', 
                'batch-pdf-to-csv-new-button',
                'Convert All PDFs to CSV'
            );
        });
    }
});

// Clean up intervals when page unloads
window.addEventListener('beforeunload', function() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
});
