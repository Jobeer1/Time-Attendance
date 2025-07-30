#!/usr/bin/env python3
"""
Debug employee status and filtering
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from attendance.services.database import db

print('=== Checking Employee Status ===')

# Get all employees regardless of status
all_employees = db.get_all('employees')
print(f'Total employees: {len(all_employees)}')
for emp in all_employees:
    status = getattr(emp, 'employment_status', 'N/A')
    print(f'  - {emp.employee_id}: {emp.full_name} (Status: {status}) (UUID: {emp.id})')

print('\n=== Checking Active Employees Query ===')
active_employees = db.find('employees', {'status': 'active'})
print(f'Active employees with status=active: {len(active_employees)}')

# Try employment_status instead
active_employees2 = db.find('employees', {'employment_status': 'active'})
print(f'Active employees with employment_status=active: {len(active_employees2)}')

print('\n=== Checking Attendance Records ===')
records = db.get_all('attendance_records')
print(f'Total attendance records: {len(records)}')
for record in records[:3]:
    print(f'  - Record {record.id}: employee_id={record.employee_id}, date={record.date}')

print('\n=== Testing Filter Logic ===')
if all_employees:
    test_employee = all_employees[0]
    print(f'Testing filter for: {test_employee.employee_id} (UUID: {test_employee.id})')
    
    # Test both ways - by employee_id string and by UUID
    filtered_count_by_string = 0
    filtered_count_by_uuid = 0
    
    for record in records:
        if record.employee_id == test_employee.employee_id:
            filtered_count_by_string += 1
        if record.employee_id == test_employee.id:
            filtered_count_by_uuid += 1
    
    print(f'Records found by employee_id string: {filtered_count_by_string}')
    print(f'Records found by UUID: {filtered_count_by_uuid}')
