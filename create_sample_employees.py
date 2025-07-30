"""
Add sample employees for testing the employee management system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from attendance.services.database import DatabaseService
from attendance.models import Employee

def create_sample_employees():
    """Create sample employees for testing"""
    db = DatabaseService()
    
    sample_employees = [
        {
            'employee_id': 'EMP001',
            'full_name': 'John Doe',
            'email': 'john.doe@company.com',
            'department': 'IT',
            'position': 'Software Developer',
            'phone': '+1-555-0101',
            'address': '123 Main St, City, State',
            'hire_date': '2023-01-15',
            'status': 'active',
            'face_encodings': [],
            'pin': '1234'
        },
        {
            'employee_id': 'EMP002',
            'full_name': 'Jane Smith',
            'email': 'jane.smith@company.com',
            'department': 'HR',
            'position': 'HR Manager',
            'phone': '+1-555-0102',
            'address': '456 Oak Ave, City, State',
            'hire_date': '2022-03-20',
            'status': 'active',
            'face_encodings': [],
            'pin': '5678'
        },
        {
            'employee_id': 'EMP003',
            'full_name': 'Bob Wilson',
            'email': 'bob.wilson@company.com',
            'department': 'Finance',
            'position': 'Accountant',
            'phone': '+1-555-0103',
            'address': '789 Pine St, City, State',
            'hire_date': '2023-06-10',
            'status': 'active',
            'face_encodings': [],
            'pin': '9012'
        },
        {
            'employee_id': 'EMP004',
            'full_name': 'Alice Johnson',
            'email': 'alice.johnson@company.com',
            'department': 'Marketing',
            'position': 'Marketing Coordinator',
            'phone': '+1-555-0104',
            'address': '321 Elm St, City, State',
            'hire_date': '2023-09-05',
            'status': 'active',
            'face_encodings': [],
            'pin': '3456'
        }
    ]
    
    print("🔧 CREATING SAMPLE EMPLOYEES")
    print("=" * 40)
    
    for emp_data in sample_employees:
        try:
            # Check if employee already exists
            existing = db.get_employee_by_employee_id(emp_data['employee_id'])
            if existing:
                print(f"ℹ Employee {emp_data['employee_id']} ({emp_data['full_name']}) already exists - skipping")
                continue
            
            # Create new employee
            employee = Employee(**emp_data)
            if employee.validate():
                db.create('employees', employee)
                print(f"✅ Created employee: {emp_data['employee_id']} - {emp_data['full_name']}")
            else:
                print(f"❌ Failed to validate employee: {emp_data['employee_id']}")
                
        except Exception as e:
            print(f"❌ Error creating employee {emp_data['employee_id']}: {e}")
    
    print("=" * 40)
    print("✅ Sample employee creation completed!")

if __name__ == '__main__':
    create_sample_employees()
