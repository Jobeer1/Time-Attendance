#!/usr/bin/env python3
"""
Test script to debug Employee.get_all_employees() method
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_employee_loading():
    """Test the Employee.get_all_employees method directly"""
    print("=== Testing Employee Loading ===")
    
    try:
        # Import the Employee model
        from attendance.models.employee import Employee
        print("✓ Successfully imported Employee model")
        
        # Call get_all_employees
        employees = Employee.get_all_employees()
        print(f"✓ Employee.get_all_employees() returned {type(employees)}")
        print(f"✓ Number of employees: {len(employees) if employees else 0}")
        
        if employees:
            print("\n--- Employee Details ---")
            for i, emp in enumerate(employees[:10]):  # Show first 10
                try:
                    emp_id = getattr(emp, 'employee_id', 'NO_ID')
                    first_name = getattr(emp, 'first_name', 'NO_FIRST')
                    last_name = getattr(emp, 'last_name', 'NO_LAST')
                    status = getattr(emp, 'employment_status', 'NO_STATUS')
                    print(f"  {i+1}. {emp_id}: {first_name} {last_name} ({status})")
                except Exception as e:
                    print(f"  {i+1}. Error reading employee: {e}")
        else:
            print("❌ No employees returned")
            
    except Exception as e:
        print(f"❌ Error testing Employee model: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing Database Service ===")
    try:
        # Test database service directly
        from attendance.services.database import db
        print("✓ Successfully imported database service")
        
        employees_db = db.get_all('employees')
        print(f"✓ db.get_all('employees') returned {type(employees_db)}")
        print(f"✓ Number of employees from DB: {len(employees_db) if employees_db else 0}")
        
        if employees_db:
            print("\n--- Database Employee Details ---")
            for i, emp in enumerate(employees_db[:10]):  # Show first 10
                try:
                    emp_id = getattr(emp, 'employee_id', 'NO_ID')
                    first_name = getattr(emp, 'first_name', 'NO_FIRST')
                    last_name = getattr(emp, 'last_name', 'NO_LAST')
                    status = getattr(emp, 'employment_status', 'NO_STATUS')
                    print(f"  {i+1}. {emp_id}: {first_name} {last_name} ({status})")
                except Exception as e:
                    print(f"  {i+1}. Error reading employee: {e}")
        else:
            print("❌ No employees returned from database")
            
    except Exception as e:
        print(f"❌ Error testing database service: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing Raw JSON Loading ===")
    try:
        import json
        from pathlib import Path
        
        employees_file = Path('attendance_data/employees.json')
        print(f"✓ employees.json exists: {employees_file.exists()}")
        
        if employees_file.exists():
            print(f"✓ File size: {employees_file.stat().st_size} bytes")
            
            with open(employees_file, 'r') as f:
                raw_data = json.load(f)
            
            print(f"✓ Raw JSON loaded: {len(raw_data)} records")
            
            print("\n--- Raw JSON Employee Details ---")
            for i, emp in enumerate(raw_data[:10]):  # Show first 10
                emp_id = emp.get('employee_id', 'NO_ID')
                first_name = emp.get('first_name', 'NO_FIRST')
                last_name = emp.get('last_name', 'NO_LAST')
                status = emp.get('employment_status', 'NO_STATUS')
                print(f"  {i+1}. {emp_id}: {first_name} {last_name} ({status})")
        else:
            print("❌ employees.json file not found")
            
    except Exception as e:
        print(f"❌ Error testing raw JSON: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_employee_loading()
