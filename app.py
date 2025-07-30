"""
Time Attendance System - Main Application Entry Point
Standalone Flask application with optional RIS integration
"""

from flask import Flask, render_template, redirect, url_for, request, jsonify
from datetime import datetime
from urllib.parse import urlparse
import os
import requests
import re
import subprocess
from pathlib import Path
import json

from attendance import create_attendance_app
from config import Config
from api.refresh_arp_table import refresh_arp_table

# Define the path to the JSON file
JSON_FILE_PATH = os.path.join(os.getcwd(), 'network_settings.json')

# Ensure the JSON file exists
if not os.path.exists(JSON_FILE_PATH):
    with open(JSON_FILE_PATH, 'w') as f:
        json.dump({"network_settings": {}, "discovered_devices": []}, f)

def create_app(config_class=Config):
    """Application factory pattern for Time Attendance System"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize data directory
    data_dir = Path(app.config['DATA_DIR'])
    data_dir.mkdir(exist_ok=True)
    (data_dir / 'backups' / 'daily').mkdir(parents=True, exist_ok=True)
    (data_dir / 'backups' / 'weekly').mkdir(parents=True, exist_ok=True)

    # Initialize attendance module
    create_attendance_app(app)

    # Remove advanced services and database dependencies
    # Advanced services like zone-based attendance, enrollment, and live camera services are disabled

    # Initialize messaging system (outside try-except to ensure it always loads)
    try:
        from routes.messaging_routes import register_messaging_routes
        register_messaging_routes(app)
        app.logger.info("Employee messaging system enabled")
    except Exception as e:
        app.logger.warning(f"Could not initialize messaging system: {e}")

    # Initialize file sharing system
    try:
        from routes.file_sharing_routes import register_file_sharing_routes, file_sharing_bp, upload_file
        register_file_sharing_routes(app)
        app.logger.info("Medical file sharing system enabled")
    except Exception as e:
        app.logger.warning(f"Could not initialize file sharing system: {e}")

    # Alias for legacy file-sharing endpoint
    app.add_url_rule(
        '/api/file-sharing/upload',
        endpoint='upload_file_alias',
        view_func=upload_file,
        methods=['POST']
    )

    # Initialize folder sharing system
    try:
        from routes.folder_sharing_routes import folder_sharing_bp
        app.register_blueprint(folder_sharing_bp)
        app.logger.info("Large folder sharing system enabled")
    except Exception as e:
        app.logger.warning(f"Could not initialize folder sharing system: {e}")

    # Register LAN file sharing routes
    try:
        from routes.lan_sharing_routes import lan_sharing_bp
        app.register_blueprint(lan_sharing_bp)
        app.logger.info("LAN file sharing system enabled")
    except Exception as e:
        app.logger.warning(f"Could not initialize LAN file sharing system: {e}")

    # Terminal management system is handled automatically by create_attendance_app
    # The modular blueprints are registered in attendance/__init__.py
    app.logger.info("Terminal management system enabled")

    # Register the refresh ARP table route
    app.add_url_rule('/admin/terminal-management/api/refresh-arp-table', view_func=refresh_arp_table)

    # Register leave management routes
    try:
        from routes.leave_routes import register_leave_routes
        register_leave_routes(app)
        app.logger.info("Leave management system enabled")
    except Exception as e:
        app.logger.warning(f"Could not initialize leave management system: {e}")

    @app.route('/')
    def index():
        """Main landing page - redirect to terminal or admin based on user"""
        return render_template('attendance/index.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'mode': app.config['ATTENDANCE_MODE'],
            'ris_integration': app.config['RIS_INTEGRATION_ENABLED']
        }
    
    @app.route('/camera-test')
    def camera_test():
        """Camera test page for troubleshooting camera functionality"""
        return render_template('attendance/camera_test.html')
    
    @app.route('/debug-face-tracking')
    def debug_face_tracking():
        """Debug page for face tracking over HTTPS"""
        import os
        debug_file = os.path.join(os.path.dirname(__file__), 'debug_face_tracking_https.html')
        with open(debug_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    @app.route('/test-face-tracking')
    def test_face_tracking():
        """Visual test page for face tracking"""
        import os
        test_file = os.path.join(os.path.dirname(__file__), 'face_tracking_visual_test.html')
        with open(test_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    @app.route('/test-fix-validation')
    def test_fix_validation():
        """Face tracking fix validation test page"""
        import os
        test_file = os.path.join(os.path.dirname(__file__), 'test_face_tracking_fix.html')
        with open(test_file, 'r', encoding='utf-8') as f:
            return f.read()

    @app.route('/live-camera-tracking')
    def live_camera_tracking():
        """Live camera face tracking interface"""
        import os
        tracking_file = os.path.join(os.path.dirname(__file__), 'face_tracking_live_camera.html')
        with open(tracking_file, 'r', encoding='utf-8') as f:
            return f.read()

    @app.route('/test-api')
    def test_api():
        """Test page for API endpoints"""
        return """
        <html>
        <head><title>API Test Page</title></head>
        <body>
            <h1>Live Camera API Test</h1>
            <div id="results"></div>
            <script>
                async function testAPI() {
                    const results = document.getElementById('results');
                    results.innerHTML = '<p>Testing API endpoints...</p>';
                    
                    try {
                        // Test zones endpoint
                        const zonesResponse = await fetch('/api/live-camera/zones');
                        const zonesData = await zonesResponse.json();
                        results.innerHTML += '<p>Zones: ' + JSON.stringify(zonesData) + '</p>';
                        
                        // Test status endpoint
                        const statusResponse = await fetch('/api/live-camera/status');
                        const statusData = await statusResponse.json();
                        results.innerHTML += '<p>Status: ' + JSON.stringify(statusData) + '</p>';
                        
                    } catch (error) {
                        results.innerHTML += '<p>Error: ' + error.message + '</p>';
                    }
                }
                
                testAPI();
            </script>
        </body>
        </html>
        """

    @app.route('/test-camera-form')
    def test_camera_form():
        """Test page for camera form"""
        import os
        test_file = os.path.join(os.path.dirname(__file__), 'test_live_camera_form.html')
        with open(test_file, 'r', encoding='utf-8') as f:
            return f.read()

    @app.route('/test-camera-modal')
    def test_camera_modal():
        """Test page for camera modal"""
        import os
        test_file = os.path.join(os.path.dirname(__file__), 'test_camera_modal.html')
        with open(test_file, 'r', encoding='utf-8') as f:
            return f.read()

    @app.route('/comprehensive-test')
    def comprehensive_test():
        """Comprehensive test page for live camera system"""
        import os
        test_file = os.path.join(os.path.dirname(__file__), 'comprehensive_test.html')
        with open(test_file, 'r', encoding='utf-8') as f:
            return f.read()

    @app.route('/admin/camera-login', methods=['POST'])
    def camera_login():
        """Handle camera login and auto-detect streaming details"""
        data = request.json
        ip_address = data.get('ip_address')
        username = data.get('username', 'admin')
        password = data.get('password', '')

        # Extract IP address from URL if provided
        if ip_address:
            # If it's a full URL, extract the hostname/IP
            if ip_address.startswith(('http://', 'https://')):
                try:
                    parsed = urlparse(ip_address)
                    ip_address = parsed.hostname
                except:
                    pass
            
            # Remove any path or port information
            if ':' in ip_address and not ip_address.count(':') > 1:  # Not IPv6
                ip_address = ip_address.split(':')[0]
            if '/' in ip_address:
                ip_address = ip_address.split('/')[0]

        # Validate IP address format
        if not ip_address or not re.match(r'^\d{1,3}(\.\d{1,3}){3}$', ip_address):
            return jsonify({"error": f"Invalid IP address format. Got: {data.get('ip_address')}"}), 400

        detected_streams = {
            'rtsp': f'rtsp://{ip_address}/stream',
            'http': f'http://{ip_address}/video',
            'onvif': f'http://{ip_address}/onvif/device_service'
        }

        # Check if the camera's web interface is accessible
        try:
            response = requests.get(f'http://{ip_address}/webcamera.html', auth=(username, password), timeout=10)
            if response.status_code == 200:
                detected_streams['http'] = f'http://{ip_address}/webcamera.html'
            else:
                detected_streams['http'] = 'N/A'
        except Exception as e:
            detected_streams['http'] = 'N/A'
            print(f"Error accessing camera web interface: {e}")

        # Validate RTSP stream
        try:
            response = requests.get(detected_streams['rtsp'], auth=(username, password), timeout=5)
            if response.status_code != 200:
                detected_streams['rtsp'] = 'N/A'
        except Exception as e:
            detected_streams['rtsp'] = 'N/A'
            print(f"Error accessing RTSP stream: {e}")

        # Validate ONVIF service
        try:
            response = requests.get(detected_streams['onvif'], auth=(username, password), timeout=5)
            if response.status_code != 200:
                detected_streams['onvif'] = 'N/A'
        except Exception as e:
            detected_streams['onvif'] = 'N/A'
            print(f"Error accessing ONVIF service: {e}")

        return jsonify(detected_streams)

    @app.route('/admin/open-stream', methods=['POST'])
    def open_stream():
        """Open the stream URL in the selected browser."""
        data = request.json
        browser = data.get('browser')
        stream_url = data.get('stream_url')

        if not stream_url:
            return jsonify({"error": "Stream URL is required."}), 400

        command = None
        if browser == 'ie':
            command = f'start iexplore "{stream_url}"'
        elif browser == 'ie-edge':
            # Use Microsoft Edge in IE mode
            command = f'start msedge --ie-mode-file-url "{stream_url}"'
        elif browser == 'chrome':
            command = f'start chrome "{stream_url}"'
        elif browser == 'firefox':
            command = f'start firefox "{stream_url}"'
        else:
            return jsonify({"error": "Unsupported browser."}), 400

        try:
            subprocess.Popen(command, shell=True)
            return jsonify({"success": True, "message": f"Stream opened in {browser}."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # --- Network settings API endpoints ---
    @app.route('/api/network-settings', methods=['GET'])
    def get_network_settings():
        try:
            if not os.path.exists(JSON_FILE_PATH):
                raise FileNotFoundError("Network settings file not found.")

            with open(JSON_FILE_PATH, 'r') as f:
                data = json.load(f)
            return jsonify(data), 200
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except json.JSONDecodeError as e:
            return jsonify({"error": "Invalid JSON format in the settings file."}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/network-settings', methods=['POST'])
    def save_network_settings():
        try:
            new_settings = request.json
            with open(JSON_FILE_PATH, 'r') as f:
                data = json.load(f)
            data["network_settings"] = new_settings
            with open(JSON_FILE_PATH, 'w') as f:
                json.dump(data, f, indent=4)
            return jsonify({"success": True}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/network-discovery', methods=['POST'])
    def cache_discovered_devices():
        try:
            new_devices = request.json.get("devices", []) if request.json else []
            if not isinstance(new_devices, list):
                raise ValueError("Invalid data format. 'devices' should be a list.")

            if not os.path.exists(JSON_FILE_PATH):
                raise FileNotFoundError("Network settings file not found.")

            with open(JSON_FILE_PATH, 'r') as f:
                data = json.load(f)

            # Ensure discovered_devices key exists
            if "discovered_devices" not in data:
                data["discovered_devices"] = []

            # Prevent duplicates in discovered_devices by comparing IP addresses
            existing_devices = data.get("discovered_devices", [])
            existing_ips = set()
            
            # Build set of existing IPs, handling None values and non-dict entries
            for device in existing_devices:
                if isinstance(device, dict) and device.get("ip"):
                    ip_addr = device.get("ip")
                    if isinstance(ip_addr, str):
                        existing_ips.add(ip_addr)
            
            # Add new devices, avoiding duplicates
            for device in new_devices:
                if isinstance(device, dict) and device.get("ip"):
                    ip_addr = device.get("ip")
                    if isinstance(ip_addr, str) and ip_addr not in existing_ips:
                        data["discovered_devices"].append(device)
                        existing_ips.add(ip_addr)

            with open(JSON_FILE_PATH, 'w') as f:
                json.dump(data, f, indent=4)

            return jsonify({"success": True, "cached_devices": data["discovered_devices"]}), 200
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except json.JSONDecodeError as e:
            return jsonify({"error": "Invalid JSON format in the settings file."}), 500
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app

# --- Multiprocessing-safe server runners for Windows ---
def run_http(app, host, port, debug):
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,
        use_reloader=False,
        ssl_context=None
    )

def run_https(app, host, port, debug, cert_path, key_path):
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,
        use_reloader=False,
        ssl_context=(cert_path, key_path)
    )

if __name__ == '__main__':
    import multiprocessing

    # Get configuration from environment
    mode = os.environ.get('ATTENDANCE_MODE', 'standalone')
    port = int(os.environ.get('ATTENDANCE_PORT', 5002))
    host = os.environ.get('ATTENDANCE_HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    app = create_app()

    print("=" * 60)
    print("🕐 TIME ATTENDANCE SYSTEM STARTING")
    print("=" * 60)
    print(f"Mode: {mode.upper()}")
    print(f"HTTP URL:  http://localhost:{port}")
    print(f"Terminal:  http://localhost:{port}/terminal")
    print(f"Admin:     http://localhost:{port}/admin")
    if app.config['RIS_INTEGRATION_ENABLED']:
        print(f"RIS Integration: ENABLED")
        print(f"RIS URL: {app.config['RIS_URL']}")
    cert_path = os.path.join(os.path.dirname(__file__), 'cert.pem')
    key_path = os.path.join(os.path.dirname(__file__), 'key.pem')
    has_ssl = os.path.exists(cert_path) and os.path.exists(key_path)
    if has_ssl:
        print(f"HTTPS URL: https://localhost:{port+1}")
        print(f"SSL enabled: Using cert.pem and key.pem for HTTPS.")
    else:
        print("SSL not enabled: cert.pem and key.pem not found. Running in HTTP mode only.")
    print("=" * 60)

    # Only start HTTPS if certs exist, otherwise HTTP
    if has_ssl:
        print(f"Starting HTTPS server on https://{host}:{port+1}")
        run_https(app, host, port+1, debug, cert_path, key_path)
    else:
        print(f"Starting HTTP server on http://{host}:{port}")
        run_http(app, host, port, debug)
