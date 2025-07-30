#!/usr/bin/env python3
"""
Test script to verify leave application submission is properly saved
"""

import sys
import os
import requests
import json
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_leave_application_submission():
    """Test that new leave applications are properly saved and visible in admin dashboard"""
    
    base_url = "https://localhost:5003"
    
    print("🧪 Testing Leave Application Submission and Persistence")
    print("=" * 60)
    
    # Test data
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    day_after = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    
    test_application = {
        "employee_id": "EMP001",
        "leave_type": "annual",
        "start_date": tomorrow,
        "end_date": day_after,
        "reason": "Test leave application - verification"
    }
    
    try:
        # 1. Get initial pending count
        print("1. Getting initial pending applications...")
        response = requests.get(f"{base_url}/api/leave/applications/pending", verify=False)
        if response.status_code == 200:
            initial_data = response.json()
            initial_count = len(initial_data.get('applications', []))
            print(f"   ✅ Initial pending applications: {initial_count}")
        else:
            print(f"   ❌ Failed to get initial count: {response.status_code}")
            return
        
        # 2. Submit new leave application
        print("2. Submitting new leave application...")
        response = requests.post(
            f"{base_url}/api/leave/apply",
            json=test_application,
            headers={'Content-Type': 'application/json'},
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                app_id = result.get('application_id')
                print(f"   ✅ Leave application submitted successfully: {app_id}")
            else:
                print(f"   ❌ Leave application failed: {result.get('error')}")
                return
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            return
        
        # 3. Verify pending count increased
        print("3. Verifying pending applications count...")
        response = requests.get(f"{base_url}/api/leave/applications/pending", verify=False)
        if response.status_code == 200:
            updated_data = response.json()
            updated_count = len(updated_data.get('applications', []))
            print(f"   ✅ Updated pending applications: {updated_count}")
            
            if updated_count > initial_count:
                print(f"   ✅ SUCCESS: Pending count increased by {updated_count - initial_count}")
                
                # Show the new application
                for app in updated_data.get('applications', []):
                    if app.get('id') == app_id:
                        print(f"   📋 New application found: {app.get('id')} - {app.get('leave_type')} - {app.get('status')}")
                        break
            else:
                print(f"   ❌ FAILED: Pending count did not increase (expected > {initial_count}, got {updated_count})")
        else:
            print(f"   ❌ Failed to get updated count: {response.status_code}")
        
        # 4. Verify all applications endpoint
        print("4. Verifying all applications endpoint...")
        response = requests.get(f"{base_url}/api/leave/applications/all", verify=False)
        if response.status_code == 200:
            all_data = response.json()
            all_count = len(all_data.get('applications', []))
            print(f"   ✅ Total applications in system: {all_count}")
            
            # Find our new application
            found_app = None
            for app in all_data.get('applications', []):
                if app.get('id') == app_id:
                    found_app = app
                    break
            
            if found_app:
                print(f"   ✅ New application visible in all applications list")
                print(f"      ID: {found_app.get('id')}")
                print(f"      Employee: {found_app.get('employee_id')}")
                print(f"      Type: {found_app.get('leave_type')}")
                print(f"      Status: {found_app.get('status')}")
            else:
                print(f"   ❌ New application NOT found in all applications list")
        else:
            print(f"   ❌ Failed to get all applications: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed. Check the results above.")

if __name__ == "__main__":
    test_leave_application_submission()
