console.log('=== Face Enrollment Button Test ===');

// Test if jQuery is loaded
console.log('jQuery loaded:', typeof $ !== 'undefined');

// Test if elements exist
console.log('Face enrollment modal exists:', $('#employeeFormFaceEnrollmentModal').length > 0);
console.log('Start camera button exists:', $('#employeeFormStartEnrollmentCamera').length > 0);
console.log('Capture photo button exists:', $('#employeeFormCaptureEnrollmentPhoto').length > 0);

// Test button click handlers
$(document).ready(function() {
    console.log('Document ready - testing button event handlers...');
    
    // Check if buttons have click handlers
    const startCameraEvents = $._data($('#employeeFormStartEnrollmentCamera')[0], 'events');
    const capturePhotoEvents = $._data($('#employeeFormCaptureEnrollmentPhoto')[0], 'events');
    
    console.log('Start camera button has click events:', startCameraEvents && startCameraEvents.click ? startCameraEvents.click.length : 0);
    console.log('Capture photo button has click events:', capturePhotoEvents && capturePhotoEvents.click ? capturePhotoEvents.click.length : 0);
    
    // Test manual trigger
    setTimeout(function() {
        console.log('=== Manual Button Test ===');
        console.log('Attempting to click start camera button...');
        $('#employeeFormStartEnrollmentCamera').trigger('click');
    }, 3000);
});
