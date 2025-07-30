#!/usr/bin/env python3
"""
Create test attendance data for debugging the Present Today functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date
from attendance.services.database import db

def create_test_data():
    """Create test attendance data"""
    try:
        # Get today's date
        today = date.today().isoformat()
        
        # First, let's see if we have any employees
        employees = db.get_all('employees')
        print(f"Found {len(employees)} employees in database")
        
        if not employees:
            print("No employees found. Creating a test employee...")
            from attendance.models.employee import Employee
            
            test_employee = Employee(
                employee_id='TEST001',
                first_name='Test',
                last_name='Employee',
                full_name='Test Employee',
                department='IT Department',
                pin='1234',
                employment_status='active',
                created_at=datetime.now().isoformat()
            )
            
            employee = db.create('employees', test_employee)
            print(f"Created test employee: {employee.employee_id}")
            employees = [employee]
        
        # Create test attendance record for today
        test_employee = employees[0]
        
        # Check if attendance record already exists for today
        existing_records = db.find('attendance_records', {
            'employee_id': test_employee.id,
            'date': today
        })
        
        if existing_records:
            print(f"Attendance record already exists for {test_employee.employee_id} today")
            record = existing_records[0]
        else:
            print(f"Creating test attendance record for {test_employee.employee_id}")
            from attendance.models.attendance import AttendanceRecord
            
            test_record = AttendanceRecord(
                employee_id=test_employee.id,
                date=today,
                clock_in_time=datetime.now().replace(hour=8, minute=30).isoformat(),
                clock_in_ip='192.168.1.100',
                clock_in_terminal='Terminal-1',
                status='active',
                is_late=False,
                created_at=datetime.now().isoformat()
            )
            
            record = db.create('attendance_records', test_record)
            print(f"Created attendance record: {record.id}")
        
        # Now test the API directly
        print("\nTesting present employees query...")
        
        # Test the database query logic
        present_records = db.find('attendance_records', {
            'date': today,
            'status': 'active'
        })
        
        if not present_records:
            all_today_records = db.find('attendance_records', {'date': today})
            present_records = [r for r in all_today_records if r.clock_in_time and not r.clock_out_time]
        
        print(f"Found {len(present_records)} present employees")
        
        for record in present_records:
            employee = db.get_by_id('employees', record.employee_id)
            if employee:
                print(f"- {employee.full_name} ({employee.employee_id}) - clocked in at {record.clock_in_time}")
        
        return True
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_test_data()
