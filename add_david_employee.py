#!/usr/bin/env python3
"""
Add David Wilson employee to the database
"""
import json
import os
from datetime import datetime

def add_david_employee():
    """Add David Wilson to employees database"""
    file_path = 'attendance_data/employees.json'
    
    # Read current employees
    with open(file_path, 'r') as f:
        employees = json.load(f)
    
    print(f'Current employees count: {len(employees)}')
    
    # Check current employees
    for i, emp in enumerate(employees[:5]):
        emp_id = emp.get('employee_id', 'NO_ID')
        first_name = emp.get('first_name', '')
        last_name = emp.get('last_name', '')
        status = emp.get('employment_status', 'unknown')
        print(f'  {i+1}. {emp_id}: {first_name} {last_name} ({status})')
    
    # Check if David Wilson already exists
    david_exists = any(
        emp.get('first_name') == 'David' and emp.get('last_name') == 'Wilson' 
        for emp in employees
    )
    
    if not david_exists:
        # Add David Wilson
        david = {
            'id': f'david-{datetime.now().timestamp()}',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'employee_id': 'EMP_DAVID',
            'first_name': 'David',
            'last_name': 'Wilson',
            'email': 'david.wilson@company.com',
            'phone': '+27123456789',
            'department': 'IT Department',
            'position': 'Developer',
            'hire_date': '2023-01-01',
            'employment_status': 'active',
            'employment_type': 'full_time',
            'salary': 50000.0,
            'password_hash': '',
            'pin': '5678',
            'face_encodings': [],
            'face_recognition_enabled': True,
            'face_photos': [],
            'photo': '',
            'require_face_recognition': False,
            'require_pin': True,
            'can_work_overtime': True,
            'default_shift_id': '',
            'current_shift_assignments': [],
            'is_admin': False,
            'can_manage_employees': False,
            'can_view_reports': False,
            'notification_preferences': {
                'email_notifications': True,
                'overtime_alerts': True,
                'schedule_reminders': True
            },
            'notes': 'Added for messaging system testing'
        }
        
        employees.append(david)
        print('Added David Wilson')
        
        # Save back to file
        with open(file_path, 'w') as f:
            json.dump(employees, f, indent=2)
        
        print(f'Updated employees count: {len(employees)}')
    else:
        print('David Wilson already exists')

if __name__ == '__main__':
    add_david_employee()
