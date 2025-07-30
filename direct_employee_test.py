import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test the employee filtering directly
from attendance.models.employee import Employee

print("=== Direct Employee Database Test ===")

try:
    # Get all employees from database
    employees_raw = Employee.get_all_employees()
    print(f"Total employees in database: {len(employees_raw)}")
    
    # Process each employee
    active_employees = []
    for i, emp_data in enumerate(employees_raw):
        emp = Employee(**emp_data)
        print(f"{i+1}. ID: {emp.employee_id}, Name: {emp.full_name}, Status: {emp.employment_status}")
        
        if emp.employment_status == 'active':
            active_employees.append(emp)
    
    print(f"\nActive employees: {len(active_employees)}")
    
    # Test search for Sarah
    print("\n=== Search Test ===")
    sarah_found = False
    for emp in active_employees:
        if 'sara' in emp.full_name.lower():
            print(f"Found Sarah: {emp.full_name} ({emp.employee_id})")
            sarah_found = True
    
    if not sarah_found:
        print("Sarah not found in active employees")
        print("All active employee names:")
        for emp in active_employees:
            print(f"  - {emp.full_name}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
