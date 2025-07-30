#!/usr/bin/env python3
"""
Optimized app.py for standalone executable deployment
Handles resource paths, SSL, and initialization for packaged environment
"""

import os
import sys
import tempfile
from pathlib import Path

# Handle PyInstaller frozen executable paths
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = Path(sys.executable).parent
    TEMP_DIR = Path(tempfile.gettempdir()) / "DrStoyanovTimeAttendance"
    TEMP_DIR.mkdir(exist_ok=True)
    
    # Set working directory to executable location
    os.chdir(BASE_DIR)
    
    # Add executable directory to Python path
    sys.path.insert(0, str(BASE_DIR))
    
else:
    # Running as Python script
    BASE_DIR = Path(__file__).parent
    TEMP_DIR = BASE_DIR

# Import Flask and other dependencies
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
    from werkzeug.security import generate_password_hash, check_password_hash
    from werkzeug.utils import secure_filename
    import json
    import datetime
    import uuid
    import threading
    import webbrowser
    import time
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)

# Initialize Flask app with proper configuration for executable
app = Flask(__name__,
           template_folder=str(BASE_DIR / 'templates'),
           static_folder=str(BASE_DIR / 'static'))

# Configure app for standalone deployment
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dr-stoyanov-time-attendance-secret-key-2025'),
    MAX_CONTENT_LENGTH=50 * 1024 * 1024 * 1024,  # 50GB max file size
    UPLOAD_FOLDER=str(BASE_DIR / 'file_storage'),
    ENTERPRISE_UPLOAD_FOLDER=str(BASE_DIR / 'enterprise_lan_storage'),
    ATTENDANCE_DATA_FOLDER=str(BASE_DIR / 'attendance_data'),
    SSL_CERT_PATH=str(BASE_DIR / 'cert.pem'),
    SSL_KEY_PATH=str(BASE_DIR / 'key.pem'),
    TEMPLATES_AUTO_RELOAD=False,  # Disable for production
    SEND_FILE_MAX_AGE_DEFAULT=0,  # Disable caching for development
)

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        app.config['UPLOAD_FOLDER'],
        app.config['ENTERPRISE_UPLOAD_FOLDER'],
        app.config['ATTENDANCE_DATA_FOLDER'],
        BASE_DIR / 'static' / 'uploads',
        BASE_DIR / 'logs',
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def generate_ssl_certificates():
    """Generate SSL certificates if they don't exist"""
    cert_path = Path(app.config['SSL_CERT_PATH'])
    key_path = Path(app.config['SSL_KEY_PATH'])
    
    if cert_path.exists() and key_path.exists():
        return True
    
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        
        print("🔒 Generating SSL certificates...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ZA"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Gauteng"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Johannesburg"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Dr Stoyanov Time Attendance"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress("127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate and key files
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print("✅ SSL certificates generated successfully")
        return True
        
    except ImportError:
        print("⚠️  Cryptography not available, SSL disabled")
        return False
    except Exception as e:
        print(f"⚠️  Error generating certificates: {e}")
        return False

# Import all route modules
try:
    # Core attendance routes
    from attendance.routes import register_blueprints
    register_blueprints(app)
    
    # Messaging routes
    from routes.messaging_routes import messaging_bp
    app.register_blueprint(messaging_bp)
    
    # File sharing routes
    from routes.file_sharing_routes import file_sharing_bp
    app.register_blueprint(file_sharing_bp)
    
    # LAN sharing routes
    from routes.lan_sharing_routes import lan_sharing_bp
    app.register_blueprint(lan_sharing_bp)
    
    # Leave management routes
    from routes.leave_routes import leave_bp
    app.register_blueprint(leave_bp)
    
    print("✅ All route modules loaded successfully")
    
except ImportError as e:
    print(f"⚠️  Warning: Could not import route module: {e}")
    print("Some features may not be available.")

# Main route
@app.route('/')
def index():
    """Main landing page"""
    return redirect(url_for('attendance.admin_dashboard'))

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('attendance/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('attendance/500.html'), 500

def open_browser_delayed(url, delay=3):
    """Open browser after a delay"""
    def open_browser():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"🌐 Opened browser at {url}")
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
    
    thread = threading.Thread(target=open_browser)
    thread.daemon = True
    thread.start()

def main():
    """Main application startup"""
    print("🕐 Dr Stoyanov Time Attendance System v2.0")
    print("=" * 50)
    
    # Initialize
    ensure_directories()
    has_ssl = generate_ssl_certificates()
    
    # Determine URLs and ports
    https_port = 5003
    http_port = 5002
    
    if has_ssl:
        primary_url = f"https://localhost:{https_port}"
        print(f"🔒 HTTPS Mode: {primary_url}")
    else:
        primary_url = f"http://localhost:{http_port}"
        print(f"🌐 HTTP Mode: {primary_url}")
    
    print(f"🔧 Admin Panel: {primary_url}/admin")
    print(f"⏰ Employee Terminal: {primary_url}/terminal")
    print(f"💬 Employee Messaging: {primary_url}/api/messaging/interface")
    print(f"🏥 Medical File Sharing: {primary_url}/api/files/interface")
    print(f"💼 Enterprise File Sharing: {primary_url}/api/lan-sharing/interface")
    print()
    print("💡 Browser will open automatically in 3 seconds...")
    print("📋 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Open browser
    open_browser_delayed(f"{primary_url}/admin")
    
    try:
        if has_ssl:
            # HTTPS mode
            app.run(
                host='0.0.0.0',
                port=https_port,
                debug=False,
                ssl_context=(app.config['SSL_CERT_PATH'], app.config['SSL_KEY_PATH']),
                threaded=True,
                use_reloader=False
            )
        else:
            # HTTP mode
            app.run(
                host='0.0.0.0',
                port=http_port,
                debug=False,
                threaded=True,
                use_reloader=False
            )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        if not getattr(sys, 'frozen', False):
            input("Press Enter to exit...")

if __name__ == "__main__":
    main()
