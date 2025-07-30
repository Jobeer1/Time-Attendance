#!/usr/bin/env python3
"""
Manual Terminal Countdown Test
Creates a test page to debug countdown functionality
"""

import os
import webbrowser
import time

def create_debug_terminal_page():
    """Create a debug page to test countdown functionality"""
    
    debug_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminal Countdown Debug</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .debug-container { max-width: 800px; margin: 2rem auto; padding: 2rem; }
        .test-section { background: #f8f9fa; border-radius: 0.5rem; padding: 1.5rem; margin: 1rem 0; }
        .log-output { background: #212529; color: #00ff00; padding: 1rem; border-radius: 0.25rem; 
                     font-family: monospace; font-size: 0.9rem; max-height: 300px; overflow-y: auto; }
        #employeeStatus { background: white; border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; }
        .employee-info { display: flex; align-items: center; margin-bottom: 1rem; }
        .employee-avatar { margin-right: 1rem; }
        .btn-pulse { animation: btn-pulse 1.2s infinite; }
        @keyframes btn-pulse { 0%{transform:scale(1);} 50%{transform:scale(1.07);} 100%{transform:scale(1);} }
    </style>
</head>
<body>
    <div class="debug-container">
        <h1 class="text-center mb-4">
            <i class="fas fa-bug me-2"></i>
            Terminal Countdown Debug
        </h1>
        
        <div class="test-section">
            <h3>Test Controls</h3>
            <div class="d-flex gap-2 flex-wrap">
                <button class="btn btn-primary" onclick="simulateAuthentication()">
                    1. Simulate Authentication
                </button>
                <button class="btn btn-success" onclick="simulateClockIn()" id="clockInBtn" disabled>
                    2. Simulate Clock In
                </button>
                <button class="btn btn-danger" onclick="simulateClockOut()" id="clockOutBtn" disabled>
                    3. Simulate Clock Out
                </button>
                <button class="btn btn-warning" onclick="testCountdownDirectly()">
                    4. Test Countdown Directly
                </button>
                <button class="btn btn-info" onclick="clearLogs()">Clear Logs</button>
            </div>
        </div>
        
        <!-- Simulated Employee Status (matches terminal.html structure) -->
        <div id="employeeStatus" class="d-none">
            <div class="employee-info">
                <div class="employee-avatar">
                    <i class="fas fa-user-circle fa-3x text-primary"></i>
                </div>
                <div class="employee-details">
                    <h4 id="employeeName">Demo Employee</h4>
                    <p id="employeeId">DEMO001</p>
                    <p id="employeeDepartment">IT Department</p>
                </div>
            </div>
            <div class="current-status">
                <div class="badge bg-secondary" id="statusBadge">
                    <i class="fas fa-clock me-1"></i>
                    <span id="statusText">Not Clocked In</span>
                </div>
                <div class="text-muted" id="lastAction">Ready for action</div>
            </div>
        </div>
        
        <!-- This is where countdown should appear after employeeStatus -->
        
        <div class="test-section">
            <h3>Console Logs</h3>
            <div id="logOutput" class="log-output">
                <div>Debug console ready...</div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    
    <script>
        // Global variables (matching terminal.js)
        let currentEmployee = null;
        let isProcessing = false;
        let autoResetTimer = null;
        let autoResetCountdownInterval = null;
        const AUTO_RESET_DELAY = 7000; // 7 seconds
        
        // Logging function
        function log(message) {
            const now = new Date().toLocaleTimeString();
            const logDiv = document.getElementById('logOutput');
            logDiv.innerHTML += `<div>[${now}] ${message}</div>`;
            logDiv.scrollTop = logDiv.scrollHeight;
            console.log(message);
        }
        
        function clearLogs() {
            document.getElementById('logOutput').innerHTML = '<div>Debug console cleared...</div>';
        }
        
        // Simulate authentication
        function simulateAuthentication() {
            log('🔐 Simulating employee authentication...');
            currentEmployee = {
                employee_id: 'DEMO001',
                name: 'Demo Employee',
                department: 'IT Department',
                auth_method: 'demo'
            };
            
            $('#employeeStatus').removeClass('d-none');
            $('#clockInBtn').prop('disabled', false);
            log('✅ Authentication successful - employee status shown');
        }
        
        // Simulate clock in
        function simulateClockIn() {
            if (!currentEmployee) {
                log('❌ No employee authenticated');
                return;
            }
            
            log('⏰ Simulating clock in action...');
            isProcessing = true;
            
            // Update status
            $('#statusBadge').removeClass('bg-secondary').addClass('bg-success');
            $('#statusText').text('Clocked In');
            $('#lastAction').text('Clocked in at ' + new Date().toLocaleTimeString());
            
            // Update buttons
            $('#clockInBtn').prop('disabled', true);
            $('#clockOutBtn').prop('disabled', false);
            
            log('✅ Clock in successful - starting countdown...');
            
            // This is the key function that should show countdown
            startAutoResetCountdown();
        }
        
        // Simulate clock out
        function simulateClockOut() {
            if (!currentEmployee) {
                log('❌ No employee authenticated');
                return;
            }
            
            log('🏁 Simulating clock out action...');
            
            // Update status
            $('#statusBadge').removeClass('bg-success').addClass('bg-danger');
            $('#statusText').text('Clocked Out');
            $('#lastAction').text('Clocked out at ' + new Date().toLocaleTimeString());
            
            // Reset buttons
            $('#clockInBtn').prop('disabled', false);
            $('#clockOutBtn').prop('disabled', true);
            
            log('✅ Clock out successful - starting countdown...');
            
            // Start countdown
            startAutoResetCountdown();
        }
        
        // Test countdown directly
        function testCountdownDirectly() {
            log('🧪 Testing countdown functionality directly...');
            startAutoResetCountdown();
        }
        
        // === COUNTDOWN FUNCTIONS (copied from terminal.js) ===
        
        function startAutoResetCountdown() {
            log('🕐 Starting auto-reset countdown for next employee');
            // Clear any existing timers
            if (autoResetTimer) clearTimeout(autoResetTimer);
            if (autoResetCountdownInterval) clearInterval(autoResetCountdownInterval);
            
            showAutoResetCountdown();
            let remainingSeconds = Math.ceil(AUTO_RESET_DELAY / 1000);
            updateCountdownDisplay(remainingSeconds);
            autoResetCountdownInterval = setInterval(() => {
                remainingSeconds--;
                updateCountdownDisplay(remainingSeconds);
                if (remainingSeconds <= 0) {
                    clearInterval(autoResetCountdownInterval);
                    autoResetCountdownInterval = null;
                }
            }, 1000);
            autoResetTimer = setTimeout(() => {
                log('⏰ Auto-reset timer expired - resetting terminal');
                clearInterval(autoResetCountdownInterval);
                autoResetCountdownInterval = null;
                autoResetTimer = null;
                resetToAuthMode();
                $('#autoResetCountdown').remove();
            }, AUTO_RESET_DELAY);
        }

        function showAutoResetCountdown() {
            log('📋 Showing auto-reset countdown UI');
            const countdownHtml = `
                <div class="alert alert-info d-flex align-items-center justify-content-between mt-3 shadow" id="autoResetCountdown">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-clock me-2"></i>
                        <span id="countdownText">Terminal will reset in <strong><span id="countdownSeconds">7</span></strong> seconds for the next employee</span>
                    </div>
                    <button class="btn btn-primary btn-lg fw-bold" onclick="continueToNextEmployee()" id="continueBtn">
                        <i class="fas fa-arrow-right me-1"></i>
                        Continue
                    </button>
                </div>
            `;
            $('#autoResetCountdown').remove();
            $('#employeeStatus').after(countdownHtml);
            log('✅ Countdown UI added to DOM');
            setTimeout(() => {
                $('#continueBtn').addClass('btn-pulse');
                log('💫 Added pulse animation to continue button');
            }, 1000);
        }

        function updateCountdownDisplay(seconds) {
            const countdownElement = document.getElementById('countdownSeconds');
            if (countdownElement) {
                countdownElement.textContent = seconds;
                log(`🕐 Countdown: ${seconds} seconds remaining`);
            } else {
                log('❌ Countdown element not found for update');
            }
        }

        function continueToNextEmployee() {
            log('🔄 Continue button clicked - resetting terminal for next employee');
            if (autoResetTimer) {
                clearTimeout(autoResetTimer);
                autoResetTimer = null;
            }
            if (autoResetCountdownInterval) {
                clearInterval(autoResetCountdownInterval);
                autoResetCountdownInterval = null;
            }
            $('#autoResetCountdown').fadeOut(200, function() { $(this).remove(); });
            resetToAuthMode();
            log('✅ Terminal reset for next employee');
        }
        
        function resetToAuthMode() {
            log('🔄 Resetting to authentication mode');
            currentEmployee = null;
            isProcessing = false;
            $('#employeeStatus').addClass('d-none');
            $('#clockInBtn').prop('disabled', true);
            $('#clockOutBtn').prop('disabled', true);
            log('✅ Reset complete - ready for next employee');
        }
        
        // Make functions globally accessible
        window.continueToNextEmployee = continueToNextEmployee;
        
        // Initialize
        $(document).ready(function() {
            log('🚀 Debug page initialized');
            log('📋 Click "1. Simulate Authentication" to start testing');
        });
    </script>
</body>
</html>
"""
    
    # Write debug file
    debug_file = os.path.join(os.getcwd(), "debug_terminal_countdown.html")
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(debug_html)
    
    print(f"✅ Debug page created: {debug_file}")
    return debug_file

def test_terminal_countdown():
    """Run manual test for terminal countdown"""
    print("🚀 Creating Terminal Countdown Debug Test")
    print("=" * 50)
    
    # Create debug page
    debug_file = create_debug_terminal_page()
    
    print("\n📋 Manual Test Instructions:")
    print("1. Open the debug page in your browser")
    print("2. Open browser Developer Tools (F12)")
    print("3. Go to Console tab to see detailed logs")
    print("4. Follow the numbered buttons in order:")
    print("   - Click '1. Simulate Authentication'")
    print("   - Click '2. Simulate Clock In'")
    print("   - Observe if countdown appears below employee status")
    print("   - Test the 'Continue' button")
    print("5. Check console for any JavaScript errors")
    
    print(f"\n🌐 Opening debug page: {debug_file}")
    
    # Try to open in browser
    try:
        webbrowser.open(f"file://{os.path.abspath(debug_file)}")
        print("✅ Debug page opened in browser")
    except Exception as e:
        print(f"❌ Could not auto-open browser: {e}")
        print(f"📁 Manually open: {os.path.abspath(debug_file)}")
    
    print("\n💡 If countdown doesn't appear, check:")
    print("- Browser console for JavaScript errors")
    print("- Verify jQuery is loaded")
    print("- Check CSS for display/visibility issues")
    print("- Ensure #employeeStatus element exists")
    
    return debug_file

if __name__ == "__main__":
    test_terminal_countdown()
