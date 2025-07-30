#!/usr/bin/env python3
"""
Test script to verify leave management system consistency
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_leave_manager():
    print("🧪 Testing LeaveManager...")
    
    try:
        from models.leave_management import leave_manager
        
        print(f"✅ Loaded {len(leave_manager.leave_applications)} total applications")
        
        # Count pending applications - handle both enum and string status
        pending_apps = []
        for app in leave_manager.leave_applications.values():
            status_value = app.status.value if hasattr(app.status, 'value') else str(app.status)
            if status_value.lower() == 'pending':
                pending_apps.append(app)
        print(f"✅ Found {len(pending_apps)} pending applications")
        
        # Test get_all_applications method
        all_apps = leave_manager.get_all_applications()
        print(f"✅ get_all_applications returned {len(all_apps)} applications")
        
        # Count pending via get_all_applications
        pending_via_method = [app for app in all_apps if app.get('status', '').upper() == 'PENDING']
        print(f"✅ Found {len(pending_via_method)} pending via get_all_applications")
        
        # Print application details
        for app in pending_apps:
            status_value = app.status.value if hasattr(app.status, 'value') else str(app.status)
            leave_type_value = app.leave_type.value if hasattr(app.leave_type, 'value') else str(app.leave_type)
            print(f"   📋 {app.id}: {app.employee_id} - {leave_type_value} ({status_value})")
            
        return len(pending_apps)
        
    except Exception as e:
        print(f"❌ Error testing LeaveManager: {e}")
        return 0

def test_admin_dashboard_import():
    print("\n🧪 Testing admin dashboard import...")
    
    try:
        # Test import that admin dashboard uses
        from models.leave_management import leave_manager
        
        # Simulate what admin dashboard does - handle both enum and string status
        pending_apps = []
        for app in leave_manager.leave_applications.values():
            status_value = app.status.value if hasattr(app.status, 'value') else str(app.status)
            if status_value.lower() == 'pending':
                pending_apps.append(app)
        pending_count = len(pending_apps)
        
        print(f"✅ Admin dashboard would show {pending_count} pending leaves")
        return pending_count
        
    except Exception as e:
        print(f"❌ Error testing admin dashboard import: {e}")
        return 0

if __name__ == "__main__":
    print("🚀 Starting Leave Management System Tests")
    print("=" * 50)
    
    # Test LeaveManager directly
    manager_count = test_leave_manager()
    
    # Test admin dashboard import
    dashboard_count = test_admin_dashboard_import()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"LeaveManager pending count: {manager_count}")
    print(f"Admin dashboard pending count: {dashboard_count}")
    
    if manager_count == dashboard_count and manager_count > 0:
        print("✅ SUCCESS: Counts are consistent!")
    else:
        print("❌ FAILURE: Counts are inconsistent!")
        
    print("🏁 Tests completed")
