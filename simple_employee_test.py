#!/usr/bin/env python3
"""
Simple test to check employee data loading
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting employee test...")

try:
    import json
    with open('attendance_data/employees.json', 'r') as f:
        raw_data = json.load(f)
    print(f"Raw JSON: {len(raw_data)} employees")
    
    # Show first 3 employees
    for i, emp in enumerate(raw_data[:3]):
        emp_id = emp.get('employee_id', 'NO_ID')
        name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
        status = emp.get('employment_status', 'unknown')
        print(f"  {emp_id}: {name} ({status})")
        
except Exception as e:
    print(f"Raw JSON error: {e}")

try:
    from attendance.models.employee import Employee
    employees = Employee.get_all_employees()
    print(f"Employee model: {len(employees)} employees")
    
    # Show first 3 employees  
    for i, emp in enumerate(employees[:3]):
        emp_id = getattr(emp, 'employee_id', 'NO_ID')
        first = getattr(emp, 'first_name', '')
        last = getattr(emp, 'last_name', '')
        status = getattr(emp, 'employment_status', 'unknown')
        print(f"  {emp_id}: {first} {last} ({status})")
        
except Exception as e:
    print(f"Employee model error: {e}")

print("Test complete.")
