"""
Quick Test of Advanced Multi-Angle Enrollment and Zone-Based Attendance
Tests the core functionality of the new system
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_zone_attendance():
    """Test zone-based attendance functionality"""
    print("🏢 Testing Zone-Based Attendance...")
    
    try:
        from attendance.services.database import DatabaseService
        from attendance.services.zone_attendance import ZoneAttendanceService, ZoneDefinition, AttendanceAction
        from attendance.models.employee import Employee
        
        # Create temp database
        temp_dir = tempfile.mkdtemp()
        db_service = DatabaseService(data_dir=temp_dir)
        zone_service = ZoneAttendanceService(db_service)
        
        # Test zone creation
        zone = ZoneDefinition(
            zone_id="test_zone",
            name="Test Zone",
            camera_ids=["camera_01"],
            zone_type="entry",
            triggers_action=AttendanceAction.CLOCK_IN
        )
        zone_service.add_zone(zone)
        
        # Test employee creation
        employee = Employee(
            employee_id="EMP001",
            first_name="Test",
            last_name="Employee"
        )
        db_service.save(employee)
        
        # Test detection processing
        zone_service.process_detection(
            camera_id="camera_01",
            employee_id="EMP001",
            employee_name="Test Employee",
            confidence=0.8
        )
        
        # Verify tracking
        assert "EMP001" in zone_service.employee_locations
        assert len(zone_service.movement_history["EMP001"]) > 0
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("   ✅ Zone attendance test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Zone attendance test failed: {e}")
        return False

def test_advanced_enrollment():
    """Test advanced enrollment functionality"""
    print("🎓 Testing Advanced Enrollment...")
    
    try:
        from attendance.services.advanced_enrollment import AdvancedEnrollmentService
        import numpy as np
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        enrollment_service = AdvancedEnrollmentService(data_dir=temp_dir)
        
        # Test session creation
        session_id = enrollment_service.start_employee_enrollment("EMP001", "Test Employee")
        assert session_id is not None
        assert "EMP001" in enrollment_service.employee_profiles
        
        # Test capture analysis
        dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        face_location = (100, 200, 300, 100)
        face_encoding = np.random.rand(128)
        
        analysis = enrollment_service._analyze_capture(
            dummy_frame, face_location, face_encoding, "camera_01"
        )
        
        assert 'quality_score' in analysis
        assert 0 <= analysis['quality_score'] <= 1
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("   ✅ Advanced enrollment test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Advanced enrollment test failed: {e}")
        return False

def test_system_integration():
    """Test system integration"""
    print("🔗 Testing System Integration...")
    
    try:
        from attendance.services.database import DatabaseService
        from attendance.services.advanced_enrollment import AdvancedEnrollmentService
        from attendance.services.zone_attendance import ZoneAttendanceService
        from attendance.services.cctv_integration import CCTVIntegrationService, CameraConfig
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        # Initialize services
        db_service = DatabaseService(data_dir=temp_dir)
        enrollment_service = AdvancedEnrollmentService(data_dir=temp_dir)
        zone_service = ZoneAttendanceService(db_service, enrollment_service)
        cctv_service = CCTVIntegrationService(db_service, enrollment_service, zone_service)
        
        # Test camera configuration
        camera_config = CameraConfig(
            camera_id="test_camera",
            name="Test Camera",
            url="test://url",
            location="test_location"
        )
        cctv_service.configure_camera(camera_config)
        
        assert "test_camera" in cctv_service.cameras
        
        # Test zone configuration
        camera_info = {
            'camera_01': {'name': 'Entrance', 'location': 'entrance'},
            'camera_02': {'name': 'Exit', 'location': 'exit'}
        }
        zone_service.configure_zones_for_cameras(camera_info)
        
        assert len(zone_service.zones) > 0
        
        # Test status reporting
        camera_stats = cctv_service.get_camera_stats()
        zone_status = cctv_service.get_zone_overview()
        
        assert isinstance(camera_stats, dict)
        assert isinstance(zone_status, dict)
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("   ✅ System integration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ System integration test failed: {e}")
        return False

def main():
    """Run all quick tests"""
    print("🧪 Quick Test Suite for Advanced Attendance System")
    print("=" * 60)
    
    tests = [
        test_zone_attendance,
        test_advanced_enrollment,
        test_system_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Advanced system is ready for deployment.")
        print("\n🚀 Next steps:")
        print("1. Run: python advanced_system_integration.py")
        print("2. Configure your 4 camera RTSP URLs")
        print("3. Start enrolling employees with multi-angle captures")
        print("4. Enable automatic zone-based attendance tracking")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
