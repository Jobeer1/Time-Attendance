#!/usr/bin/env python3
"""
Create test attendance data and then test the Present Today functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date
import requests
import json

def create_test_attendance_data():
    """Create test attendance data"""
    try:
        # Import after adding to path
        from attendance.services.database import db
        from attendance.models.employee import Employee
        from attendance.models.attendance import AttendanceRecord
        
        print("Creating test attendance data...")
        
        # Get today's date
        today = date.today().isoformat()
        current_time = datetime.now()
        
        # Check for existing employees
        employees = db.get_all('employees')
        if not employees:
            print("No employees found. Creating test employees...")
            
            # Create test employees
            test_employees = [
                {
                    'employee_id': 'TEST001',
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'full_name': 'John Smith',
                    'department': 'IT Department',
                    'pin': '1234',
                    'employment_status': 'active'
                },
                {
                    'employee_id': 'TEST002', 
                    'first_name': 'Sarah',
                    'last_name': 'Johnson',
                    'full_name': 'Sarah Johnson',
                    'department': 'HR',
                    'pin': '5678',
                    'employment_status': 'active'
                },
                {
                    'employee_id': 'TEST003',
                    'first_name': 'Mike',
                    'last_name': 'Davis',
                    'full_name': 'Mike Davis', 
                    'department': 'Finance',
                    'pin': '9999',
                    'employment_status': 'active'
                }
            ]
            
            created_employees = []
            for emp_data in test_employees:
                emp_data['created_at'] = current_time.isoformat()
                employee = Employee(**emp_data)
                created_emp = db.create('employees', employee)
                created_employees.append(created_emp)
                print(f"Created employee: {created_emp.employee_id} - {created_emp.full_name}")
            
            employees = created_employees
        
        # Create attendance records for today
        print(f"Creating attendance records for {today}...")
        
        for i, employee in enumerate(employees[:3]):  # Only first 3 employees
            # Check if record already exists
            existing_records = db.find('attendance_records', {
                'employee_id': employee.id,
                'date': today
            })
            
            if existing_records:
                print(f"Attendance record already exists for {employee.employee_id}")
                continue
            
            # Create clock-in record (some employees clocked in, some didn't)
            if i < 2:  # First 2 employees are present
                clock_in_time = current_time.replace(hour=8 + i, minute=30 + (i * 15))
                
                attendance_data = {
                    'employee_id': employee.id,
                    'date': today,
                    'clock_in_time': clock_in_time.isoformat(),
                    'clock_in_ip': f'192.168.1.{100 + i}',
                    'clock_in_terminal': f'Terminal-{i + 1}',
                    'status': 'active',  # Present but not clocked out
                    'is_late': i == 1,  # Second employee is late
                    'created_at': current_time.isoformat()
                }
                
                record = AttendanceRecord(**attendance_data)
                created_record = db.create('attendance_records', record)
                print(f"Created attendance record for {employee.employee_id}: clocked in at {clock_in_time.strftime('%H:%M')}")
            else:
                print(f"Employee {employee.employee_id} did not clock in today")
        
        print("Test data creation completed!")
        return True
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Test the API endpoint"""
    try:
        print("\nTesting Present Today API endpoint...")
        
        # Test with different URLs since app runs on different ports
        test_urls = [
            'http://localhost:5001/admin/api/present-employees',
            'https://localhost:5002/admin/api/present-employees'
        ]
        
        for url in test_urls:
            try:
                print(f"Trying {url}...")
                response = requests.get(url, verify=False, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Status: {response.status_code}")
                    print(f"   Success flag: {data.get('success')}")
                    print(f"   Total present: {data.get('total_present')}")
                    print(f"   Message: {data.get('message')}")
                    
                    if data.get('present_employees'):
                        print(f"   Present employees ({len(data['present_employees'])}):")
                        for emp in data['present_employees']:
                            print(f"     - {emp['employee']['name']} ({emp['employee']['employee_id']})")
                            print(f"       Department: {emp['employee']['department']}")
                            print(f"       Clocked in: {emp['timestamp']} from {emp['ip_address']}")
                    
                    return True
                    
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text}")
                    
            except requests.exceptions.SSLError:
                print(f"   SSL Error (expected for HTTPS with self-signed cert)")
                continue
            except requests.exceptions.ConnectionError:
                print(f"   Connection refused")
                continue
            except Exception as e:
                print(f"   Error: {e}")
                continue
        
        print("❌ Could not connect to any endpoint")
        return False
        
    except Exception as e:
        print(f"Error testing API: {e}")
        return False

def main():
    """Main function"""
    print("=== Present Today Functionality Test ===\n")
    
    # Step 1: Create test data
    if create_test_attendance_data():
        print("\n" + "="*50)
        
        # Step 2: Test API
        if test_api_endpoint():
            print("\n" + "="*50)
            print("✅ API is working correctly!")
            print("\nTo test the frontend:")
            print("1. Open your browser and navigate to the admin dashboard")
            print("2. Open browser developer tools (F12)")
            print("3. Click the 'Present Today' card")
            print("4. Check the console for debug messages")
            print("5. The table should update with present employee data")
            
            print("\nAlternatively, open this test page:")
            print("http://localhost:5001/test_present_today_standalone.html")
        else:
            print("\n❌ API test failed")
    else:
        print("\n❌ Test data creation failed")

if __name__ == "__main__":
    main()
