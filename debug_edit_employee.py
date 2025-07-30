#!/usr/bin/env python3
"""
Debug script to test the edit employee functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from attendance.services.database import db
from attendance.models.employee import Employee

def test_get_employee():
    """Test getting an employee from the database"""
    try:
        # Test if we can get an employee by ID
        employee = db.get_employee_by_employee_id("EMP01")
        print(f"Found employee: {employee}")
        if employee:
            print(f"Employee details: {employee.__dict__}")
        else:
            print("Employee EMP01 not found")
            
        # List all employees to see what we have
        all_employees = db.get_all('employees')
        print(f"\nAll employees ({len(all_employees)}):")
        for emp in all_employees:
            print(f"  - {emp.employee_id}: {emp.full_name}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_employee()
