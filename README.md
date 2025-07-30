# 🕐 Dr Stoyanov Time Attendance System

A comprehensive enterprise-grade time attendance and workforce management system with advanced features for modern workplaces.

## 🌟 Overview

This is a sophisticated Flask-based time attendance system designed for enterprise environments. It combines traditional time tracking with modern features like biometric authentication, employee messaging, large file sharing, and advanced reporting capabilities.

## ✨ Key Features

### 🔐 Authentication & Security
- **Multi-factor Authentication**: PIN, face recognition, and biometric verification
- **Role-based Access Control**: Admin, employee, and department-specific permissions
- **LAN-only Security**: Network-restricted access for sensitive operations
- **Audit Trails**: Complete logging of all system activities

### 👥 Employee Management
- **Comprehensive Employee Profiles**: Full employee data management with photos
- **Department Organization**: Hierarchical department and team structures
- **Face Recognition**: Advanced biometric authentication using face encodings
- **Employee Messaging**: Internal communication system with file attachments

### ⏰ Time Tracking
- **Multiple Clock-in Methods**: PIN entry, face recognition, or manual entry
- **Terminal Management**: Support for multiple physical terminals across locations
- **Real-time Tracking**: Live monitoring of employee presence and activities
- **Overtime Management**: Automatic overtime calculation and alerts

### 📋 Shift Management
- **Flexible Shift Patterns**: Support for various shift types and rotations
- **Shift Assignments**: Easy assignment of employees to shifts
- **Schedule Optimization**: Intelligent scheduling based on business needs
- **Conflict Detection**: Automatic detection of scheduling conflicts

### 🏥 Leave Management
- **Leave Request System**: Employee self-service leave applications
- **Multiple Leave Types**: Annual, sick, emergency, and custom leave types
- **Approval Workflows**: Hierarchical approval processes
- **BCEA Compliance**: South African labor law compliance features
- **Leave Balance Tracking**: Real-time tracking of leave entitlements

### 📊 Advanced Reporting
- **Real-time Dashboards**: Live attendance and productivity metrics
- **Comprehensive Reports**: Attendance, overtime, leave, and productivity reports
- **Data Export**: Excel and CSV export capabilities
- **Analytics**: Trend analysis and workforce insights

### 💬 Communication Systems

#### Employee Messaging
- **Internal Messaging**: Secure employee-to-employee communication
- **File Attachments**: Support for document and image sharing
- **Broadcast Messages**: Company-wide announcements
- **Message Threading**: Organized conversation management

#### Medical File Sharing (5GB Support)
- **DICOM Support**: Specialized for medical imaging files
- **Large File Handling**: Up to 5GB per file for CT scans, MRIs
- **Medical Categories**: CT, MRI, X-ray, ultrasound, pathology, etc.
- **Secure Sharing**: HIPAA-compliant file sharing features
- **Compression**: Automatic compression for large medical files

#### Enterprise LAN Large File Sharing (50GB Support)
- **Massive File Support**: Up to 50GB per file for enterprise needs
- **Enterprise File Types**: VM images, databases, CAD assemblies, large media
- **Folder Sharing**: Compressed folder archives for large datasets
- **LAN Optimization**: Network-optimized transfers with resume capability
- **Project-based Organization**: File organization by projects and teams

### 🔧 System Administration
- **Multi-terminal Support**: Manage multiple attendance terminals
- **Camera Integration**: IP camera support for enhanced security
- **Network Discovery**: Automatic discovery of network devices
- **System Configuration**: Comprehensive admin controls
- **Backup & Recovery**: Automated data backup systems

### 📱 Modern Interface
- **Responsive Design**: Mobile-friendly web interface
- **Real-time Updates**: Live data updates without page refresh
- **Intuitive Navigation**: User-friendly interface design
- **Dark/Light Themes**: Customizable interface themes

## 🏗️ Technical Architecture

### Backend Technologies
- **Framework**: Flask (Python)
- **Database**: JSON-based storage with SQLite option
- **Authentication**: Custom multi-factor authentication
- **File Storage**: Local file system with enterprise-grade organization
- **Security**: HTTPS with SSL certificates, IP-based access control

### Frontend Technologies
- **UI Framework**: Bootstrap 5 with custom CSS
- **JavaScript**: Vanilla JS with modern ES6+ features
- **Real-time Updates**: Server-sent events and AJAX
- **Responsive Design**: Mobile-first approach

### Infrastructure
- **Deployment**: Standalone Flask application
- **Network**: LAN-optimized with external access options
- **File Systems**: Hierarchical storage for different file types
- **Backup**: Automated backup systems with versioning

## 📁 Project Structure

```
Time Attendance/
├── 📁 attendance/                    # Core attendance module
│   ├── 📁 models/                   # Data models
│   ├── 📁 services/                 # Business logic services
│   └── 📁 views/                    # View controllers
├── 📁 models/                       # Shared models
│   ├── 📄 employee_messaging.py     # Employee messaging system
│   ├── 📄 medical_file_sharing.py   # Medical file sharing (5GB)
│   ├── 📄 lan_file_sharing.py       # Enterprise large files (50GB)
│   └── 📄 leave_management.py       # Leave management system
├── 📁 routes/                       # API routes
│   ├── 📄 messaging_routes.py       # Employee messaging API
│   ├── 📄 file_sharing_routes.py    # Medical file sharing API
│   ├── 📄 lan_sharing_routes.py     # Enterprise file sharing API
│   └── 📄 leave_routes.py           # Leave management API
├── 📁 templates/                    # HTML templates
│   └── 📁 attendance/               # Attendance-specific templates
├── 📁 static/                       # Static assets (CSS, JS, images)
├── 📁 attendance_data/              # Employee and attendance data
├── 📁 file_storage/                 # Medical file storage
├── 📁 enterprise_lan_storage/       # Enterprise large file storage
├── 📄 app.py                        # Main application
├── 📄 config.py                     # Configuration settings
└── 📄 requirements.txt              # Python dependencies
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Windows/Linux/macOS
- Network access for LAN features
- Camera hardware (optional, for face recognition)

### Quick Start

1. **Clone and Setup**
   ```bash
   cd "Time Attendance"
   pip install -r requirements.txt
   ```

2. **Generate SSL Certificates**
   ```bash
   python generate_ssl_certs.py
   ```

3. **Create Admin User**
   ```bash
   python create_admin_user.py
   ```

4. **Start the Application**
   ```bash
   python app.py
   ```

5. **Access the System**
   - HTTP: `http://localhost:5002`
   - HTTPS: `https://localhost:5003`
   - Admin: `https://localhost:5003/admin`
   - Terminal: `https://localhost:5003/terminal`

## 🔧 Configuration

### Environment Settings
- **Standalone Mode**: Self-contained operation
- **Network Discovery**: Automatic device detection
- **SSL/HTTPS**: Secure connections with custom certificates
- **File Storage**: Configurable storage paths and limits

### Default Access URLs
| Service | URL | Description |
|---------|-----|-------------|
| Main Dashboard | `https://localhost:5003/admin` | Admin interface |
| Employee Terminal | `https://localhost:5003/terminal` | Employee check-in |
| Employee Messaging | `https://localhost:5003/api/messaging/interface` | Internal messaging |
| Medical File Sharing | `https://localhost:5003/api/files/interface` | Medical imaging files |
| Enterprise File Sharing | `https://localhost:5003/api/lan-sharing/interface` | Large enterprise files |
| Leave Management | `https://localhost:5003/api/leave/employee-leave` | Leave applications |

## 👥 User Roles & Permissions

### 🔑 Administrator
- **Full System Access**: Complete control over all features
- **Employee Management**: Add, edit, delete employee records
- **Shift Management**: Create and assign shifts
- **Report Generation**: Access to all reports and analytics
- **System Configuration**: Modify system settings
- **File Sharing Admin**: Manage all file sharing activities

### 👤 Employee
- **Time Tracking**: Clock in/out, view attendance history
- **Leave Requests**: Apply for and track leave requests
- **Messaging**: Send/receive messages with colleagues
- **File Sharing**: Upload and share files within permissions
- **Profile Management**: Update personal information

### 🏢 Department Manager
- **Department Reports**: View team attendance and productivity
- **Leave Approval**: Approve/reject leave requests for team
- **Team Messaging**: Broadcast messages to department
- **File Access**: Access department-shared files

## 💾 Data Storage

### Employee Data
- **Personal Information**: Names, contact details, departments
- **Biometric Data**: Face encodings for recognition
- **Employment Details**: Hire dates, positions, salary information
- **Attendance Records**: Complete time tracking history

### File Storage Systems

#### Medical Files (`file_storage/`)
- **Purpose**: Medical imaging files (DICOM, CT, MRI)
- **Capacity**: Up to 5GB per file
- **Features**: Compression, virus scanning, retention policies
- **Security**: Medical-grade privacy and access controls

#### Enterprise Files (`enterprise_lan_storage/`)
- **Purpose**: Large enterprise files (VMs, databases, CAD)
- **Capacity**: Up to 50GB per file
- **Features**: Chunked uploads, resume capability, network mounting
- **Organization**: Project-based file organization

### Configuration Storage
- **System Settings**: JSON-based configuration files
- **User Preferences**: Personalized settings per user
- **Audit Logs**: Complete activity tracking
- **Backup Data**: Automated backup with versioning

## 🔒 Security Features

### Network Security
- **LAN-only Operations**: Critical operations restricted to local network
- **IP Validation**: Automatic validation of source IP addresses
- **SSL/TLS Encryption**: All communications encrypted
- **Certificate Management**: Custom SSL certificate generation

### Authentication Security
- **Multi-factor Authentication**: PIN + Biometric verification
- **Session Management**: Secure session handling
- **Password Policies**: Enforced password complexity
- **Account Lockout**: Protection against brute force attacks

### Data Security
- **File Integrity**: MD5 hash verification for all files
- **Access Logging**: Complete audit trail of file access
- **Permission Controls**: Granular access permissions
- **Data Retention**: Configurable retention policies

## 📈 Reporting & Analytics

### Real-time Dashboards
- **Live Attendance**: Current employee status
- **Today's Activity**: Clock-ins, break times, overtime
- **System Health**: Server status and performance metrics
- **File Usage**: Storage utilization and transfer statistics

### Comprehensive Reports
- **Attendance Reports**: Daily, weekly, monthly attendance summaries
- **Overtime Analysis**: Overtime hours and cost analysis
- **Leave Reports**: Leave utilization and balance reports
- **Productivity Metrics**: Employee productivity and efficiency metrics

### Export Capabilities
- **Excel Export**: Formatted spreadsheet reports
- **CSV Export**: Raw data for external analysis
- **PDF Reports**: Professional formatted reports
- **API Access**: RESTful API for system integration

## 🛠️ Administration

### Employee Management
```python
# Create sample employees
python create_sample_employees.py

# Ensure employees exist
python ensure_sample_employees.py

# Check employee data
python check_employee_data.py
```

### System Maintenance
```python
# Check system health
python quick_test.py

# Advanced system test
python quick_test_advanced.py

# Verify messaging system
python verify_messaging_system.py
```

### File Management
```python
# Test file uploads
python test_enhanced_messaging.py

# Test folder sharing
python test_folder_sharing.py

# Convert CSV to Excel
python csv_to_excel_converter.py
```

## 🌐 Network Integration

### Terminal Support
- **Multiple Terminals**: Support for distributed terminals
- **Network Discovery**: Automatic discovery of network devices
- **ARP Table Integration**: Network device detection and monitoring
- **Remote Management**: Centralized management of all terminals

### Camera Integration
- **IP Camera Support**: Integration with network cameras
- **Face Recognition**: Real-time face detection and recognition
- **Security Monitoring**: Visual verification of attendance events
- **Stream Management**: Multiple camera stream handling

### LAN Optimization
- **Local Network Priority**: Optimized for LAN performance
- **Bandwidth Management**: Intelligent bandwidth utilization
- **Resume Capabilities**: Interrupted transfer recovery
- **Network Mount Points**: Seamless folder sharing across network

## 🔧 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python --version

# Install dependencies
pip install -r requirements.txt

# Check port availability
netstat -an | findstr :5003
```

#### Face Recognition Issues
```bash
# Install face recognition dependencies
pip install face-recognition

# Check camera availability
python simple_camera_test.py

# Test face recognition
python setup_face_recognition.py
```

#### File Upload Issues
- **Check file size limits**: Medical (5GB), Enterprise (50GB)
- **Verify network connection**: Ensure LAN connectivity
- **Check storage space**: Monitor available disk space
- **Review permissions**: Verify user access levels

### Log Files
- **Application Logs**: Console output during application runtime
- **Access Logs**: File access and download logs
- **Error Logs**: System error tracking and debugging
- **Audit Trails**: Complete user activity logging

## 🤝 Contributing

### Development Setup
1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes**: Implement your feature
4. **Test thoroughly**: Run all test scripts
5. **Submit pull request**: Document your changes

### Code Standards
- **Python PEP 8**: Follow Python coding standards
- **Type Hints**: Use type annotations where possible
- **Documentation**: Comment complex logic thoroughly
- **Testing**: Include tests for new features

## 📄 License

This project is proprietary software developed for enterprise time attendance management. All rights reserved.

## 👨‍💻 Authors & Contributors

- **Lead Developer**: Time Attendance System Team
- **Architecture**: Enterprise-grade system design
- **Security**: Advanced security implementation
- **UI/UX**: Modern responsive interface design

## 🔮 Future Roadmap

### Planned Features
- **Mobile Application**: Native mobile apps for iOS and Android
- **Advanced Analytics**: Machine learning-powered insights
- **API Gateway**: RESTful API for third-party integrations
- **Cloud Integration**: Optional cloud backup and sync
- **Advanced Biometrics**: Fingerprint and iris recognition
- **Workflow Automation**: Advanced approval workflows
- **Real-time Notifications**: Push notifications for important events

### Performance Improvements
- **Database Optimization**: Migration to high-performance databases
- **Caching Layer**: Redis integration for improved performance
- **Load Balancing**: Multi-server deployment support
- **CDN Integration**: Content delivery network for static assets

---

# Dr Stoyanov Time Attendance System

## Overview
AI-powered face recognition time attendance system for modern workplaces. Standalone, secure, and easy to use.

## Features
- Face recognition attendance tracking
- Web-based interface (works in any browser)
- Employee management
- Shift scheduling
- Leave request management
- Real-time attendance monitoring
- Network camera support
- SSL/HTTPS encryption
- Administrative dashboard
- Terminal interface for advanced users

## Quick Start
1. Clone this repository:
   ```sh
git clone https://github.com/Jobeer1/Time-Attendance.git
   ```
2. Install dependencies:
   ```sh
pip install -r requirements.txt
   ```
3. Run the application:
   ```sh
python app.py
   ```
4. Access the system in your browser:
   - HTTPS: https://localhost:5003
   - HTTP:  http://localhost:5002

## Distribution
For standalone use, run `DrStoyanovTimeAttendance.exe` (no Python required).

## System Requirements
- Windows 10/11 (64-bit)
- RAM: Minimum 4GB (8GB recommended)
- Storage: 500MB free space

## Default Login
- Username: `admin`
- Password: `admin123`

## License
MIT License

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Support
For technical support, refer to the documentation or contact your system administrator.

---

*This README represents the current state of the Dr Stoyanov Time Attendance System - a comprehensive workforce management solution designed for modern enterprise environments.*
- **Multiple Clock-in Methods**: 
  - Face recognition (primary)
  - PIN-based authentication
  - Password authentication
- **Real-time Attendance**: Live clock-in/out with timestamp validation
- **Shift Validation**: Automatic verification against scheduled shifts
- **Location Tracking**: Terminal-based location logging

### 3. Face Recognition System
- **Advanced Face Encoding**: Uses `face_recognition` library with multiple encoding support
- **Quality Validation**: Image quality assessment before encoding
- **Real-time Recognition**: Live camera feed processing
- **Confidence Scoring**: Adjustable similarity thresholds

### 4. Multi-Terminal Support
- **Distributed Terminals**: Multiple attendance terminals across locations
- **IP-based Security**: Allowed terminal IP validation
- **Terminal Management**: Administrative control over terminal access
- **Session Management**: Secure terminal sessions with timeout

### 5. Shift Management
- **Flexible Scheduling**: Custom shift definitions with start/end times
- **Employee Assignment**: Individual or group shift assignments
- **Overtime Calculation**: Automatic overtime detection and calculation
- **Break Time Tracking**: Configurable break periods

---

## ⚙️ Backend Code Structure (Modularized)

- All backend routes are now split into domain-specific files under `attendance/routes/` for maintainability:
  - `admin_dashboard.py`, `employee_management.py`, `shift_management.py`, `camera_management.py`, `reports.py`, `user_management.py`, `terminal_management.py`, `human_detection.py`, `absent_employees.py`, and shared `admin_helpers.py`.
- Shared helpers and authentication logic are in `attendance/utils/`.
- Register all blueprints in your Flask app using `from attendance.routes import register_blueprints; register_blueprints(app)`.
