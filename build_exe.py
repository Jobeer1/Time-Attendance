#!/usr/bin/env python3
"""
Build script for creating standalone .exe distribution of Dr Stoyanov Time Attendance System
This script packages the entire Flask application with all dependencies into a single executable.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_icon():
    """Create a professional icon for the time attendance system"""
    
    # 🎨 CUSTOM ICON: Place your custom icon here and uncomment the lines below
    # custom_icon_path = "my_custom_icon.ico"  # Your custom icon file
    # if os.path.exists(custom_icon_path):
    #     print(f"✅ Using custom icon: {custom_icon_path}")
    #     return custom_icon_path
    
    icon_content = """
    Creates a professional clock/attendance themed icon using PIL
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create a 256x256 icon with professional design
        size = 256
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Background circle - professional blue
        circle_color = (41, 128, 185)  # Professional blue
        draw.ellipse([10, 10, size-10, size-10], fill=circle_color, outline=(52, 152, 219), width=4)
        
        # Clock face - white background
        clock_size = int(size * 0.7)
        clock_offset = (size - clock_size) // 2
        draw.ellipse([clock_offset, clock_offset, clock_offset + clock_size, clock_offset + clock_size], 
                    fill=(255, 255, 255), outline=(44, 62, 80), width=3)
        
        # Clock numbers (12, 3, 6, 9)
        center_x, center_y = size // 2, size // 2
        radius = clock_size // 2 - 20
        
        # Draw clock numbers
        for i, (angle, num) in enumerate([(0, '12'), (90, '3'), (180, '6'), (270, '9')]):
            import math
            angle_rad = math.radians(angle - 90)  # Start from top
            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            
            # Draw number
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), num, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text((x - text_width//2, y - text_height//2), num, 
                     fill=(44, 62, 80), font=font)
        
        # Clock hands pointing to 9:00 (work time)
        # Hour hand (short, thick)
        hour_length = radius * 0.5
        hour_angle = math.radians(270 - 90)  # 9 o'clock
        hour_x = center_x + hour_length * math.cos(hour_angle)
        hour_y = center_y + hour_length * math.sin(hour_angle)
        draw.line([center_x, center_y, hour_x, hour_y], fill=(231, 76, 60), width=6)
        
        # Minute hand (long, thin)
        minute_length = radius * 0.8
        minute_angle = math.radians(0 - 90)  # 12 o'clock
        minute_x = center_x + minute_length * math.cos(minute_angle)
        minute_y = center_y + minute_length * math.sin(minute_angle)
        draw.line([center_x, center_y, minute_x, minute_y], fill=(231, 76, 60), width=4)
        
        # Center dot
        dot_size = 8
        draw.ellipse([center_x - dot_size, center_y - dot_size, 
                     center_x + dot_size, center_y + dot_size], 
                    fill=(231, 76, 60))
        
        # Attendance badge in corner
        badge_size = 40
        badge_x, badge_y = size - badge_size - 15, 15
        draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], 
                    fill=(46, 204, 113), outline=(39, 174, 96), width=2)
        
        # Checkmark in badge
        check_points = [
            (badge_x + 12, badge_y + 20),
            (badge_x + 18, badge_y + 26),
            (badge_x + 28, badge_y + 14)
        ]
        draw.line(check_points, fill=(255, 255, 255), width=3)
        
        # Save as ICO file
        icon_path = "time_attendance_icon.ico"
        # Convert to multiple sizes for ICO format
        sizes = [256, 128, 64, 48, 32, 16]
        images = []
        
        for ico_size in sizes:
            resized = img.resize((ico_size, ico_size), Image.Resampling.LANCZOS)
            images.append(resized)
        
        # Save as ICO with multiple sizes
        images[0].save(icon_path, format='ICO', sizes=[(img.width, img.height) for img in images])
        print(f"✅ Created professional icon: {icon_path}")
        return icon_path
        
    except ImportError:
        print("⚠️  PIL not available, creating simple icon...")
        # Create a simple text-based icon as fallback
        return create_simple_icon()
    except Exception as e:
        print(f"⚠️  Error creating icon: {e}")
        return create_simple_icon()

def create_simple_icon():
    """Create a simple icon using basic graphics"""
    try:
        from PIL import Image, ImageDraw
        
        size = 64
        img = Image.new('RGB', (size, size), (41, 128, 185))
        draw = ImageDraw.Draw(img)
        
        # Simple clock design
        draw.ellipse([8, 8, size-8, size-8], fill=(255, 255, 255), outline=(44, 62, 80), width=2)
        
        # Clock hands
        center = size // 2
        draw.line([center, center, center, center-15], fill=(231, 76, 60), width=2)  # Hour
        draw.line([center, center, center+10, center], fill=(231, 76, 60), width=1)   # Minute
        
        icon_path = "time_attendance_icon.ico"
        img.save(icon_path, format='ICO')
        print(f"✅ Created simple icon: {icon_path}")
        return icon_path
        
    except Exception as e:
        print(f"⚠️  Could not create icon: {e}")
        return None

def install_dependencies():
    """Install required dependencies for building"""
    dependencies = [
        'pyinstaller',
        'pillow',  # For icon creation
    ]
    
    print("📦 Installing build dependencies...")
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Failed to install {dep}")

def create_spec_file(icon_path):
    """Create PyInstaller spec file for advanced configuration"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files and folders to include
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('attendance_data', 'attendance_data'),
    ('file_storage', 'file_storage'),
    ('enterprise_lan_storage', 'enterprise_lan_storage'),
    ('models', 'models'),
    ('routes', 'routes'),
    ('attendance', 'attendance'),
    ('config.py', '.'),
    ('cert.pem', '.'),
    ('key.pem', '.'),
    ('network_settings.json', '.'),
]

# Hidden imports for Flask and related modules
hiddenimports = [
    'flask',
    'flask.templating',
    'flask.json',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.utils',
    'jinja2',
    'jinja2.ext',
    'jinja2.loaders',
    'markupsafe',
    'click',
    'itsdangerous',
    'cryptography',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'face_recognition',
    'cv2',
    'numpy',
    'json',
    'datetime',
    'os',
    'sys',
    'threading',
    'hashlib',
    'base64',
    'zipfile',
    'shutil',
    'socket',
    'subprocess',
    'time',
    'logging',
    'uuid',
    'pathlib',
    'mimetypes',
    'urllib',
    'requests',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.application',
    'smtplib',
    'ssl',
    'secrets',
    'functools',
    'collections',
]

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DrStoyanovTimeAttendance',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{icon_path if icon_path else "NONE"}',
    version_file='version_info.txt',
)
'''
    
    with open('time_attendance.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file")

def create_version_info():
    """Create version information file for Windows executable"""
    version_content = '''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 0, 0, 0),
    prodvers=(2, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Dr Stoyanov Time Attendance Systems'),
        StringStruct(u'FileDescription', u'Enterprise Time Attendance and Workforce Management System'),
        StringStruct(u'FileVersion', u'2.0.0.0'),
        StringStruct(u'InternalName', u'DrStoyanovTimeAttendance'),
        StringStruct(u'LegalCopyright', u'© 2025 Dr Stoyanov Time Attendance Systems. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'DrStoyanovTimeAttendance.exe'),
        StringStruct(u'ProductName', u'Dr Stoyanov Time Attendance System'),
        StringStruct(u'ProductVersion', u'2.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_content)
    
    print("✅ Created version information file")

def create_launcher_script():
    """Create a startup script that handles SSL certificates and data directories"""
    launcher_content = '''#!/usr/bin/env python3
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
        print("\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
    
    with open('launcher.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print("✅ Created launcher script")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    
    try:
        # Build using spec file
        subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'time_attendance.spec'
        ], check=True)
        
        print("✅ Executable built successfully!")
        
        # Check if build was successful
        exe_path = Path('dist/DrStoyanovTimeAttendance.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Executable size: {size_mb:.1f} MB")
            print(f"📁 Location: {exe_path.absolute()}")
            return True
        else:
            print("❌ Executable not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_distribution_package():
    """Create a complete distribution package"""
    print("📦 Creating distribution package...")
    
    dist_dir = Path('distribution')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir()
    
    # Copy executable
    exe_source = Path('dist/DrStoyanovTimeAttendance.exe')
    if exe_source.exists():
        shutil.copy2(exe_source, dist_dir / 'DrStoyanovTimeAttendance.exe')
        print("✅ Copied executable")
    
    # Copy essential files
    essential_files = [
        'README.md',
        'requirements.txt',
        'Setup_Desktop_Integration.bat',
        'Uninstall.bat',
    ]
    
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, dist_dir / file)
            print(f"✅ Copied {file}")
    
    # Create startup batch file
    batch_content = '''@echo off
title Dr Stoyanov Time Attendance System
echo.
echo ================================================
echo    Dr Stoyanov Time Attendance System v2.0
echo ================================================
echo.
echo Starting the system...
echo The browser will open automatically.
echo.
DrStoyanovTimeAttendance.exe
if %errorlevel% neq 0 (
    echo.
    echo Error starting the application.
    echo Please check if antivirus is blocking the exe.
    pause
)
'''
    
    with open(dist_dir / 'Start_Time_Attendance.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print("✅ Created startup batch file")
    
    # Create quick setup guide
    setup_guide = '''# Quick Setup Guide - Dr Stoyanov Time Attendance System

## 🚀 Getting Started

### **Option 1: Easy Setup with Desktop Integration (Recommended)**
1. **Run Setup**: Double-click `Setup_Desktop_Integration.bat`
2. **Choose Options**: Desktop shortcut and/or Start Menu integration
3. **Start System**: Option to start immediately after setup

### **Option 2: Direct Launch**
1. **Simple Start**: Double-click `Start_Time_Attendance.bat` OR
2. **Direct Launch**: Double-click `DrStoyanovTimeAttendance.exe`

## 🖥️ **Desktop Integration Features**

### **Desktop Shortcut**
- ✅ **Professional Icon**: Your custom icon appears on desktop
- ✅ **Quick Access**: Double-click to start system
- ✅ **Professional Name**: "Dr Stoyanov Time Attendance"

### **Start Menu Integration**
- ✅ **Start Menu Entry**: Find in Windows Start Menu
- ✅ **Professional Branding**: Organized under program folder
- ✅ **Uninstall Option**: Clean removal when needed

### **System Tray & Taskbar**
- ✅ **Custom Icon**: Your icon appears in taskbar when running
- ✅ **Professional Appearance**: Branded application presence

## 🔐 **First Time Setup**

The system will automatically:
1. **Create SSL certificates** for HTTPS security
2. **Initialize data directories** for storage
3. **Open browser** to admin panel (https://localhost:5003/admin)
4. **Guide you** through creating admin user

## 📍 **Access URLs**
- Main Admin Panel: https://localhost:5003/admin
- Employee Terminal: https://localhost:5003/terminal
- Employee Messaging: https://localhost:5003/api/messaging/interface
- Medical File Sharing: https://localhost:5003/api/files/interface
- Enterprise File Sharing: https://localhost:5003/api/lan-sharing/interface

## �️ **Uninstalling**

To remove desktop integration:
1. **Run**: `Uninstall.bat` (removes shortcuts only)
2. **Keep Data**: Your attendance data is preserved
3. **Complete Removal**: Delete entire folder if desired

## 🛠️ **System Requirements**

- Windows 7/8/10/11 (64-bit)
- 4GB RAM minimum
- 2GB free disk space
- Network connectivity for LAN features
- Camera (optional, for face recognition)

## 📞 **Support**

For technical support or questions, refer to the complete README.md file.

## 🎉 **Result**

After setup, you get:
- ✅ **Desktop shortcut** with your custom icon
- ✅ **Start Menu integration** for easy access
- ✅ **Professional Windows integration**
- ✅ **Complete workforce management system**
- ✅ **All features ready to use**

---
*Dr Stoyanov Time Attendance System - Enterprise v2.0*
'''
    
    with open(dist_dir / 'QUICK_SETUP.md', 'w', encoding='utf-8') as f:
        f.write(setup_guide)
    
    print("✅ Created quick setup guide")
    print(f"📁 Distribution package created in: {dist_dir.absolute()}")

def main():
    """Main build process"""
    print("🏗️  Dr Stoyanov Time Attendance System - Build Process")
    print("=" * 60)
    
    # Install dependencies
    install_dependencies()
    
    # Create icon
    icon_path = create_icon()
    
    # Create build files
    create_version_info()
    create_spec_file(icon_path)
    create_launcher_script()
    
    # Build executable
    if build_executable():
        create_distribution_package()
        
        print("\n🎉 BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📦 Your Dr Stoyanov Time Attendance System is ready for distribution!")
        print("📁 Check the 'distribution' folder for the complete package.")
        print("🚀 Users can run 'Start_Time_Attendance.bat' to start the system.")
        print("=" * 60)
    else:
        print("\n❌ BUILD FAILED!")
        print("Check the error messages above for details.")

if __name__ == "__main__":
    main()
