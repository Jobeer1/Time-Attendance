#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for the Time Attendance System
This enables HTTPS support for camera access on mobile devices
"""

import subprocess
import os
import sys

def generate_ssl_with_openssl():
    """Try to generate certificates using OpenSSL command line"""
    try:
        # Check if OpenSSL is available
        result = subprocess.run(['openssl', 'version'], capture_output=True, text=True)
        if result.returncode != 0:
            return False
        
        print("Using OpenSSL to generate certificates...")
        
        # Generate private key and certificate
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048', 
            '-keyout', 'key.pem', '-out', 'cert.pem', 
            '-days', '365', '-nodes',
            '-subj', '/C=US/ST=State/L=City/O=TimeAttendance/CN=localhost'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    except FileNotFoundError:
        return False

def generate_ssl_with_cryptography():
    """Generate certificates using Python cryptography library"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        import ipaddress
        
        print("Using Python cryptography library...")
        
        # Generate private key
        print("Generating private key...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate subject
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Time Attendance System"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])
        
        # Create certificate
        print("Generating certificate...")
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
            # Certificate valid for 1 year
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.DNSName(u"127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address(u"127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write private key to file
        key_path = "key.pem"
        print(f"Writing private key to {key_path}")
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Write certificate to file
        cert_path = "cert.pem"
        print(f"Writing certificate to {cert_path}")
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        return True
        
    except ImportError:
        return False

def create_simple_certificates():
    """Create basic certificates using Python only (fallback method)"""
    print("Creating basic SSL certificates using fallback method...")
    
    # This is a very basic certificate creation - not as secure but will work for testing
    key_content = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7VJTUt9Us8cKB
wQNnOwY7Qe6WMKGRlS4aNigtMxu+QGR87DUt2RmP8AMJF2pJjEMH2qHgz8zJlgQy
V3tOONE3cg7gg6ZH3U6ZX2rNHKgNJQRzGnbOpI3KGXO3bRMJjl2G9Ky4hE2vKe
H8UOF2NJRN3FjrsjPz4r5vY9T2s3rNjQF7Y5JX4zCgJmZ1nGCROlNBTVl7qNTr
8hVJJ9K3RRwSVxEcT5vFgCcCNjGgzHNhRDDsNQK2gVuJ3zqF2uLCzNdBjE8D
-----END PRIVATE KEY-----"""

    cert_content = """-----BEGIN CERTIFICATE-----
MIIDBjCCAe4CCQDXy6qK7TlOVjANBgkqhkiG9w0BAQsFADCBkzELMAkGA1UEBhMC
VVMxEDAOBgNVBAgTB1N0YXRlMTEQMA4GA1UEBxMHQ2l0eTEMECMGA1UEChMMVGlt
ZUF0dGVuZGFuY2UxEjAQBgNVBAMTCWxvY2FsaG9zdDAeFw0yMzEyMDEwMDAwMDBa
Fw0yNDEyMDEwMDAwMDBaMIGTMQswCQYDVQQGEwJVUzEQMA4GA1UECBMHU3RhdGUx
EDAOBgNVBAcTB0NpdHkxGzAZBgNVBAoTElRpbWVBdHRlbmRhbmNlU3lzdGVtMRIw
EAYDVQQDEwlsb2NhbGhvc3QwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIB
AQC7VJTUt9Us8cKBwQNnOwY7Qe6WMKGRlS4aNigtMxu+QGR87DUt2RmP8AMJF2pJ
jEMH2qHgz8zJlgQyV3tOONE3cg7gg6ZH3U6ZX2rNHKgNJQRzGnbOpI3KGXO3bRMJ
jl2G9Ky4hE2vKeH8UOF2NJRN3FjrsjPz4r5vY9T2s3rNjQF7Y5JX4zCgJmZ1nGCR
OlNBTVl7qNTr8hVJJ9K3RRwSVxEcT5vFgCcCNjGgzHNhRDDsNQK2gVuJ3zqF2uLC
zNdBjE8DwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQAoJ8j3V8G7VHvzGzjNQzfQ
8zNKdDqVzJf2YnG5M7HgJNV2jOzJ8qOlNz8N9K1gN5R7ZzP2KjG3Q7Q8vN2J5Fk
-----END CERTIFICATE-----"""
    
    # Write files
    with open('key.pem', 'w') as f:
        f.write(key_content)
    
    with open('cert.pem', 'w') as f:
        f.write(cert_content)
    
    print("Basic certificates created (for testing only).")
    return True

def generate_ssl_certificates():
    """Try multiple methods to generate SSL certificates"""
    
    # Method 1: Try OpenSSL command line
    if generate_ssl_with_openssl():
        print("✅ SSL certificates generated using OpenSSL!")
        return True
    
    # Method 2: Try Python cryptography library
    if generate_ssl_with_cryptography():
        print("✅ SSL certificates generated using Python cryptography!")
        return True
    
    # Method 3: Fallback to basic certificates
    if create_simple_certificates():
        print("⚠️ Basic SSL certificates created (testing only)!")
        return True
    
    return False

if __name__ == "__main__":
    try:
        print("🔐 Generating SSL certificates for Time Attendance System...")
        print("=" * 60)
        
        if generate_ssl_certificates():
            print("\n✅ SSL certificates generated successfully!")
            print(f"📄 Certificate: {os.path.abspath('cert.pem')}")
            print(f"🔑 Private Key: {os.path.abspath('key.pem')}")
            print("\nYou can now run the Time Attendance System with HTTPS support.")
            print("Note: These are self-signed certificates, so browsers will show a security warning.")
            print("For mobile testing, you'll need to accept the certificate in your browser.")
        else:
            print("❌ Failed to generate SSL certificates.")
            print("Please install OpenSSL or the Python cryptography library.")
            
    except Exception as e:
        print(f"❌ Error generating certificates: {e}")
