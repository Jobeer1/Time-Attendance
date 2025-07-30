#!/usr/bin/env python3
"""
Test leave rejection functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_rejection():
    print("🧪 Testing Leave Rejection...")
    
    try:
        from models.leave_management import leave_manager
        
        # Check initial state
        print(f"Initial applications: {len(leave_manager.leave_applications)}")
        pending_before = [app for app in leave_manager.leave_applications.values() 
                         if (app.status.value if hasattr(app.status, 'value') else str(app.status)).lower() == 'pending']
        print(f"Pending before rejection: {len(pending_before)}")
        
        if pending_before:
            # Try to reject the first pending application
            app_to_reject = pending_before[0]
            print(f"Attempting to reject: {app_to_reject.id}")
            
            success = leave_manager.reject_leave(app_to_reject.id, "admin", "Testing rejection")
            print(f"Rejection success: {success}")
            
            # Check status after rejection
            rejected_app = leave_manager.leave_applications[app_to_reject.id]
            status_after = rejected_app.status.value if hasattr(rejected_app.status, 'value') else str(rejected_app.status)
            print(f"Status after rejection: {status_after}")
            
            # Check pending count after rejection
            pending_after = [app for app in leave_manager.leave_applications.values() 
                           if (app.status.value if hasattr(app.status, 'value') else str(app.status)).lower() == 'pending']
            print(f"Pending after rejection: {len(pending_after)}")
            
            return len(pending_after)
        else:
            print("No pending applications to reject")
            return 0
            
    except Exception as e:
        print(f"❌ Error testing rejection: {e}")
        return -1

if __name__ == "__main__":
    print("🚀 Testing Leave Rejection")
    print("=" * 40)
    
    result = test_rejection()
    
    print("\n" + "=" * 40)
    if result >= 0:
        print(f"✅ Test completed. Remaining pending: {result}")
    else:
        print("❌ Test failed")
    print("🏁 Test finished")
