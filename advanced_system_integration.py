"""
Integration Script for Advanced Multi-Angle Enrollment and Zone-Based Attendance
Sets up and tests the complete system with 4-camera CCTV integration
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import services
from attendance.services.database import DatabaseService
from attendance.services.advanced_enrollment import AdvancedEnrollmentService
from attendance.services.zone_attendance import ZoneAttendanceService
from attendance.services.cctv_integration import CCTVIntegrationService, CameraConfig
from attendance.services.face_recognition import face_service
from attendance.models.employee import Employee
from attendance.models.camera import Camera

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('advanced_system.log')
    ]
)
logger = logging.getLogger(__name__)

class AdvancedAttendanceSystem:
    """Complete advanced attendance system integration"""
    
    def __init__(self):
        self.db_service = None
        self.enrollment_service = None
        self.zone_service = None
        self.cctv_service = None
        self.face_service = None
        
        # System status
        self.initialized = False
        self.running = False
    
    def initialize_system(self):
        """Initialize all services and components"""
        try:
            logger.info("Initializing Advanced Attendance System...")
            
            # Initialize database service
            self.db_service = DatabaseService()
            logger.info("Database service initialized")
            
            # Initialize advanced enrollment service
            self.enrollment_service = AdvancedEnrollmentService()
            logger.info("Advanced enrollment service initialized")
            
            # Initialize zone attendance service
            self.zone_service = ZoneAttendanceService(self.db_service, self.enrollment_service)
            logger.info("Zone attendance service initialized")
            
            # Initialize CCTV integration service
            self.cctv_service = CCTVIntegrationService(
                self.db_service, 
                self.enrollment_service, 
                self.zone_service
            )
            logger.info("CCTV integration service initialized")
            
            # Connect face recognition service
            self.face_service = face_service
            self.face_service.set_enrollment_service(self.enrollment_service)
            logger.info("Face recognition service connected")
            
            # Setup detection callbacks
            self.cctv_service.add_detection_callback(self._on_detection)
            self.cctv_service.add_enrollment_callback(self._on_enrollment_event)
            
            self.initialized = True
            logger.info("Advanced Attendance System initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    def setup_demo_cameras(self):
        """Setup demo cameras for testing"""
        try:
            logger.info("Setting up demo cameras...")
            
            demo_cameras = [
                {
                    'camera_id': 'camera_01',
                    'name': 'Main Entrance',
                    'url': '0',  # Use webcam for demo
                    'location': 'main_entrance',
                    'enabled': True,
                    'detection_enabled': True
                },
                {
                    'camera_id': 'camera_02', 
                    'name': 'Lobby Camera',
                    'url': '0',  # Use same webcam for demo
                    'location': 'lobby',
                    'enabled': True,
                    'detection_enabled': True
                },
                {
                    'camera_id': 'camera_03',
                    'name': 'Corridor Camera', 
                    'url': '0',  # Use same webcam for demo
                    'location': 'corridor',
                    'enabled': True,
                    'detection_enabled': True
                },
                {
                    'camera_id': 'camera_04',
                    'name': 'Exit Camera',
                    'url': '0',  # Use same webcam for demo
                    'location': 'exit',
                    'enabled': True,
                    'detection_enabled': True
                }
            ]
            
            # Save cameras to database
            for cam_data in demo_cameras:
                camera = Camera(
                    camera_id=cam_data['camera_id'],
                    name=cam_data['name'],
                    url=cam_data['url'],
                    location=cam_data['location'],
                    enabled=cam_data['enabled'],
                    detection_enabled=cam_data['detection_enabled']
                )
                self.db_service.save(camera)
            
            # Configure CCTV service cameras
            for cam_data in demo_cameras:
                camera_config = CameraConfig(
                    camera_id=cam_data['camera_id'],
                    name=cam_data['name'],
                    url=cam_data['url'],
                    location=cam_data['location'],
                    enabled=cam_data['enabled'],
                    detection_enabled=cam_data['detection_enabled']
                )
                self.cctv_service.configure_camera(camera_config)
            
            logger.info(f"Demo cameras setup complete: {len(demo_cameras)} cameras configured")
            
        except Exception as e:
            logger.error(f"Failed to setup demo cameras: {e}")
            raise
    
    def create_demo_employees(self):
        """Create demo employees for testing"""
        try:
            logger.info("Creating demo employees...")
            
            demo_employees = [
                {
                    'employee_id': 'EMP001',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john.doe@company.com',
                    'department': 'Engineering',
                    'position': 'Software Developer'
                },
                {
                    'employee_id': 'EMP002',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'email': 'jane.smith@company.com',
                    'department': 'HR',
                    'position': 'HR Manager'
                },
                {
                    'employee_id': 'EMP003',
                    'first_name': 'Mike',
                    'last_name': 'Johnson',
                    'email': 'mike.johnson@company.com',
                    'department': 'Sales',
                    'position': 'Sales Representative'
                }
            ]
            
            for emp_data in demo_employees:
                employee = Employee(**emp_data)
                self.db_service.save(employee)
                logger.info(f"Created demo employee: {employee.full_name}")
            
            logger.info(f"Demo employees created: {len(demo_employees)} employees")
            
        except Exception as e:
            logger.error(f"Failed to create demo employees: {e}")
            raise
    
    def start_system(self):
        """Start the complete system"""
        try:
            if not self.initialized:
                raise Exception("System not initialized. Call initialize_system() first.")
            
            logger.info("Starting Advanced Attendance System...")
            
            # Start CCTV monitoring
            self.cctv_service.start_camera_monitoring()
            
            self.running = True
            logger.info("Advanced Attendance System is now running")
            
            # Display system status
            self.display_system_status()
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            raise
    
    def stop_system(self):
        """Stop the complete system"""
        try:
            logger.info("Stopping Advanced Attendance System...")
            
            if self.cctv_service:
                self.cctv_service.stop_camera_monitoring()
            
            self.running = False
            logger.info("Advanced Attendance System stopped")
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    def display_system_status(self):
        """Display current system status"""
        try:
            print("\n" + "="*60)
            print("ADVANCED ATTENDANCE SYSTEM STATUS")
            print("="*60)
            
            # Camera status
            camera_stats = self.cctv_service.get_camera_stats()
            print(f"\n📹 CAMERAS ({len(camera_stats)} total):")
            for camera_id, stats in camera_stats.items():
                status = "🟢 CONNECTED" if stats['connected'] else "🔴 DISCONNECTED"
                print(f"  {camera_id}: {status} | FPS: {stats['fps']} | Detections: {stats['detection_count']}")
            
            # Zone status
            zone_overview = self.cctv_service.get_zone_overview()
            print(f"\n🏢 ZONES ({len(zone_overview['zones'])} total):")
            for zone_id, zone_info in zone_overview['zones'].items():
                employees = zone_info['employees_present']
                action = zone_info['triggers_action'] or 'None'
                print(f"  {zone_info['zone_name']}: {employees} employees | Action: {action}")
            
            # Detection stats
            detection_stats = self.cctv_service.get_detection_stats()
            print(f"\n🎯 DETECTION STATISTICS:")
            print(f"  Total Detections: {detection_stats['total_detections']}")
            print(f"  Successful: {detection_stats['successful_recognitions']}")
            print(f"  Failed: {detection_stats['failed_recognitions']}")
            print(f"  Success Rate: {detection_stats['success_rate']:.1f}%")
            
            # Services status
            print(f"\n⚙️ SERVICES STATUS:")
            print(f"  Database: {'🟢 Active' if self.db_service else '🔴 Inactive'}")
            print(f"  Enrollment: {'🟢 Active' if self.enrollment_service else '🔴 Inactive'}")
            print(f"  Zone Tracking: {'🟢 Active' if self.zone_service and self.zone_service.running else '🔴 Inactive'}")
            print(f"  CCTV Integration: {'🟢 Active' if self.cctv_service else '🔴 Inactive'}")
            
            print("\n" + "="*60)
            
        except Exception as e:
            logger.error(f"Error displaying system status: {e}")
    
    def run_enrollment_demo(self, employee_id: str = 'EMP001'):
        """Run a demonstration of the enrollment process"""
        try:
            logger.info(f"Starting enrollment demo for employee {employee_id}")
            
            # Get employee
            employees = self.db_service.find_all(Employee)
            employee = next((e for e in employees if e.employee_id == employee_id), None)
            
            if not employee:
                logger.error(f"Employee {employee_id} not found")
                return
            
            # Start enrollment session
            session_id = self.cctv_service.start_enrollment_session(employee_id, employee.full_name)
            
            print(f"\n🎓 ENROLLMENT DEMO STARTED")
            print(f"Employee: {employee.full_name} ({employee_id})")
            print(f"Session ID: {session_id}")
            print("\nInstructions:")
            print("1. Look directly at the camera")
            print("2. Turn your head slowly left and right")
            print("3. Move closer and farther from camera")
            print("4. Try different expressions (smile, neutral, talking)")
            print("5. Test in different lighting conditions")
            print("\nPress Ctrl+C to stop enrollment demo\n")
            
            # Monitor enrollment progress
            start_time = time.time()
            max_duration = 300  # 5 minutes max
            
            while time.time() - start_time < max_duration:
                try:
                    # Process enrollment frame
                    result = self.cctv_service.process_enrollment_frame('camera_01', session_id)
                    
                    if result.get('enrollment_complete'):
                        print("🎉 ENROLLMENT COMPLETED SUCCESSFULLY!")
                        break
                    
                    # Display progress
                    progress = result.get('progress', 0)
                    captures_added = result.get('captures_added', 0)
                    
                    if captures_added > 0:
                        print(f"📸 Capture added! Progress: {progress:.1f}% | Instructions: {result.get('instructions', 'N/A')}")
                    
                    time.sleep(2)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Enrollment demo stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in enrollment demo: {e}")
                    time.sleep(1)
            
            logger.info("Enrollment demo completed")
            
        except Exception as e:
            logger.error(f"Failed to run enrollment demo: {e}")
    
    def _on_detection(self, detection_result):
        """Callback for detection events"""
        logger.info(f"🔍 Detection: {detection_result.employee_name} at {detection_result.camera_id} "
                   f"(confidence: {detection_result.confidence:.2f})")
    
    def _on_enrollment_event(self, event_type, event_data):
        """Callback for enrollment events"""
        logger.info(f"🎓 Enrollment event: {event_type} - {event_data}")

def main():
    """Main function to run the advanced system demo"""
    system = AdvancedAttendanceSystem()
    
    try:
        print("🚀 Initializing Advanced Multi-Angle Attendance System...")
        
        # Initialize system
        system.initialize_system()
        
        # Setup demo data
        system.setup_demo_cameras()
        system.create_demo_employees()
        
        # Start system
        system.start_system()
        
        print("\n✅ System is running! Available commands:")
        print("  'status' - Show system status")
        print("  'enroll <employee_id>' - Start enrollment demo")
        print("  'stop' - Stop system")
        print("  'help' - Show this help")
        
        # Interactive command loop
        while system.running:
            try:
                command = input("\n> ").strip().lower()
                
                if command == 'status':
                    system.display_system_status()
                elif command.startswith('enroll'):
                    parts = command.split()
                    employee_id = parts[1] if len(parts) > 1 else 'EMP001'
                    system.run_enrollment_demo(employee_id)
                elif command == 'stop':
                    break
                elif command == 'help':
                    print("\nAvailable commands:")
                    print("  'status' - Show system status")
                    print("  'enroll <employee_id>' - Start enrollment demo")
                    print("  'stop' - Stop system")
                    print("  'help' - Show this help")
                elif command == '':
                    continue
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n🛑 Stopping system...")
                break
            except EOFError:
                break
    
    except Exception as e:
        logger.error(f"System error: {e}")
        print(f"❌ System error: {e}")
    
    finally:
        # Clean shutdown
        system.stop_system()
        print("👋 Advanced Attendance System shutdown complete")

if __name__ == "__main__":
    main()
