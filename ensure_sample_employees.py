#!/usr/bin/env python3
"""
Ensure sample employees exist for messaging system testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from attendance.services.database import db
from attendance.models.employee import Employee

def ensure_sample_employees():
    """Ensure we have some sample employees for testing"""
    print("🔧 Checking and creating sample employees...")
    
    # Check existing employees
    existing_employees = db.get_all('employees')
    existing_ids = [emp.employee_id for emp in existing_employees]
    
    print(f"Found {len(existing_employees)} existing employees: {existing_ids}")
    
    # Sample employees to ensure exist
    sample_employees = [
        {
            'employee_id': 'MSG01',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'email': 'alice.johnson@company.com',
            'department': 'Human Resources',
            'position': 'HR Specialist',
            'employment_status': 'active',
            'phone': '+27123456701',
            'pin': '1001'
        },
        {
            'employee_id': 'MSG02',
            'first_name': 'Bob',
            'last_name': 'Smith',
            'email': 'bob.smith@company.com',
            'department': 'Engineering',
            'position': 'Software Developer',
            'employment_status': 'active',
            'phone': '+27123456702',
            'pin': '1002'
        },
        {
            'employee_id': 'MSG03',
            'first_name': 'Carol',
            'last_name': 'Davis',
            'email': 'carol.davis@company.com',
            'department': 'Marketing',
            'position': 'Marketing Manager',
            'employment_status': 'active',
            'phone': '+27123456703',
            'pin': '1003'
        },
        {
            'employee_id': 'MSG04',
            'first_name': 'David',
            'last_name': 'Wilson',
            'email': 'david.wilson@company.com',
            'department': 'Finance',
            'position': 'Financial Analyst',
            'employment_status': 'active',
            'phone': '+27123456704',
            'pin': '1004'
        },
        {
            'employee_id': 'MSG05',
            'first_name': 'Emma',
            'last_name': 'Brown',
            'email': 'emma.brown@company.com',
            'department': 'Sales',
            'position': 'Sales Representative',
            'employment_status': 'active',
            'phone': '+27123456705',
            'pin': '1005'
        }
    ]
    
    created_count = 0
    for emp_data in sample_employees:
        if emp_data['employee_id'] not in existing_ids:
            try:
                employee = Employee(**emp_data)
                if employee.validate():
                    db.create('employees', employee)
                    print(f"✅ Created employee: {employee.full_name} ({employee.employee_id})")
                    created_count += 1
                else:
                    print(f"❌ Failed to validate employee: {emp_data['employee_id']}")
            except Exception as e:
                print(f"❌ Error creating employee {emp_data['employee_id']}: {e}")
        else:
            print(f"⏭️  Employee {emp_data['employee_id']} already exists")
    
    if created_count > 0:
        print(f"\n✅ Created {created_count} new employees for messaging system")
    else:
        print(f"\n✅ All sample employees already exist")
    
    # Final count
    final_employees = db.get_all('employees')
    active_employees = [emp for emp in final_employees if getattr(emp, 'employment_status', 'active') == 'active']
    print(f"\n📊 Total employees: {len(final_employees)} ({len(active_employees)} active)")
    
    return len(active_employees) > 0

if __name__ == "__main__":
    success = ensure_sample_employees()
    if success:
        print("\n🎉 Employee messaging system is ready to test!")
        print("   Start the app: py app.py")
        print("   Access messaging: /api/messaging/interface?employee_id=MSG01")
    else:
        print("\n⚠️  No active employees found. Please check database connectivity.")
