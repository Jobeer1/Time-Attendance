#!/usr/bin/env python3
"""
Dr Stoyanov Time Attendance System Launcher
Handles initialization, SSL certificates, and data directory setup.
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading
from pathlib import Path

def setup_directories():
    """Ensure all required directories exist"""
    directories = [
        'attendance_data',
        'file_storage',
        'enterprise_lan_storage',
        'static/uploads',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Data directories initialized")

def check_certificates():
    """Check if SSL certificates exist, create if needed"""
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("🔒 Generating SSL certificates...")
        try:
            # Import here to avoid issues if not available
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import datetime
            
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
            with open(cert_file, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(key_file, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            print("✅ SSL certificates generated successfully")
            
        except ImportError:
            print("⚠️  Cryptography library not available, using HTTP mode")
        except Exception as e:
            print(f"⚠️  Error generating certificates: {e}")

def start_browser(url, delay=3):
    """Start browser after a delay"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"🌐 Opened browser at {url}")
    except Exception as e:
        print(f"⚠️  Could not open browser: {e}")

def main():
    """Main launcher function"""
    print("🕐 Dr Stoyanov Time Attendance System")
    print("=" * 50)
    
    # Setup
    setup_directories()
    check_certificates()
    
    # Determine URLs
    https_url = "https://localhost:5003"
    http_url = "http://localhost:5002"
    
    # Check if we have SSL certificates
    has_ssl = os.path.exists('cert.pem') and os.path.exists('key.pem')
    primary_url = https_url if has_ssl else http_url
    
    print(f"🚀 Starting Time Attendance System...")
    print(f"📍 Primary URL: {primary_url}")
    print(f"🔧 Admin Panel: {primary_url}/admin")
    print(f"⏰ Employee Terminal: {primary_url}/terminal")
    print()
    print("💡 The browser will open automatically in 3 seconds...")
    print("📋 To stop the server, press Ctrl+C")
    print("=" * 50)
    
    # Start browser in background
    browser_thread = threading.Thread(target=start_browser, args=(f"{primary_url}/admin",))
    browser_thread.daemon = True
    browser_thread.start()
    
    # Import and start the Flask app
    try:
        from app import app
        
        if has_ssl:
            app.run(
                host='0.0.0.0',
                port=5003,
                debug=False,
                ssl_context=('cert.pem', 'key.pem'),
                threaded=True
            )
        else:
            app.run(
                host='0.0.0.0',
                port=5002,
                debug=False,
                threaded=True
            )
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
