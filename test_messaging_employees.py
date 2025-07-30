#!/usr/bin/env python3
"""
Test script to check messaging system and employee data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=== Testing Employee Messaging System ===")

# Test 1: Check if messaging system is working
try:
    from models.employee_messaging import EmployeeMessagingManager
    messaging_manager = EmployeeMessagingManager()
    print("✅ Successfully created EmployeeMessagingManager")
except Exception as e:
    print(f"❌ Error creating messaging manager: {e}")
    sys.exit(1)

# Test 2: Check employee database
try:
    from attendance.services.database import db
    all_employees = db.get_all('employees')
    print(f"✅ Found {len(all_employees)} total employees in database")
    
    # Show employee details
    if all_employees:
        print("\n📋 Current employees:")
        for i, emp in enumerate(all_employees[:10]):  # Show first 10
            status = getattr(emp, 'employment_status', getattr(emp, 'status', 'unknown'))
            print(f"  {i+1}. ID: {emp.employee_id}, Name: {emp.full_name}, Status: {status}")
    else:
        print("⚠️  No employees found in database")
        
except Exception as e:
    print(f"❌ Error accessing employee database: {e}")

# Test 3: Check messaging route functionality
try:
    from routes.messaging_routes import messaging_bp
    print("✅ Successfully imported messaging routes")
except Exception as e:
    print(f"❌ Error importing messaging routes: {e}")

# Test 4: Test the employee list endpoint logic
try:
    print("\n🔍 Testing employee list logic...")
    from attendance.models.employee import Employee
    
    # Try to get employees using the messaging route method
    try:
        employees = Employee.get_all_employees()
        print(f"✅ Found {len(employees)} employees using Employee.get_all_employees()")
        
        # Filter active employees
        active_employees = [emp for emp in employees if getattr(emp, 'is_active', True)]
        print(f"✅ Found {len(active_employees)} active employees")
        
        if active_employees:
            print("\n📝 Active employees for messaging:")
            for emp in active_employees[:5]:  # Show first 5
                name = getattr(emp, 'name', getattr(emp, 'full_name', 'Unknown'))
                dept = getattr(emp, 'department', 'Unknown')
                print(f"  - ID: {emp.employee_id}, Name: {name}, Dept: {dept}")
        
    except AttributeError as ae:
        print(f"⚠️  Employee.get_all_employees() method not found: {ae}")
        print("   Trying alternative method...")
        
        # Try direct database access
        all_employees = db.get_all('employees')
        active_employees = [emp for emp in all_employees if getattr(emp, 'employment_status', 'active') == 'active']
        print(f"✅ Found {len(active_employees)} active employees using direct DB access")
        
except Exception as e:
    print(f"❌ Error testing employee list logic: {e}")

# Test 5: Check if sample employees exist
print("\n🔍 Checking for sample employees...")
sample_ids = ['EMP01', 'EMP02', 'EMP03', 'ADMIN']
for emp_id in sample_ids:
    try:
        emp = db.get_employee_by_employee_id(emp_id)
        if emp:
            print(f"✅ Found {emp_id}: {emp.full_name}")
        else:
            print(f"❌ Employee {emp_id} not found")
    except Exception as e:
        print(f"❌ Error checking {emp_id}: {e}")

print("\n=== Test Complete ===")
