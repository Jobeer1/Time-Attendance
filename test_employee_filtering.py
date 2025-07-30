from attendance.models.employee import Employee
from attendance.services.database import db

print("=== Testing Employee Database ===")

# Test 1: Direct database call
employees_raw = db.get_all('employees')
print(f"Total employees in database: {len(employees_raw)}")

# Test 2: Check each employee's status
print("\n=== All Employees ===")
for i, emp in enumerate(employees_raw):
    emp_obj = Employee(**emp)
    print(f"{i+1}. ID: {emp_obj.employee_id}, Name: {emp_obj.full_name}, Status: {emp_obj.employment_status}")

# Test 3: Filter for active employees
print("\n=== Active Employees Only ===")
active_employees = [emp for emp in employees_raw if emp.get('employment_status') == 'active']
print(f"Active employees count: {len(active_employees)}")

for i, emp in enumerate(active_employees):
    emp_obj = Employee(**emp)
    print(f"{i+1}. ID: {emp_obj.employee_id}, Name: {emp_obj.full_name}")

# Test 4: Search test
print("\n=== Search Test for 'sara' ===")
search_results = []
for emp in active_employees:
    emp_obj = Employee(**emp)
    if 'sara' in emp_obj.full_name.lower():
        search_results.append(emp_obj)
        print(f"Found: {emp_obj.full_name} ({emp_obj.employee_id})")

if not search_results:
    print("No employees found matching 'sara'")
    print("Available names:")
    for emp in active_employees:
        emp_obj = Employee(**emp)
        print(f"  - {emp_obj.full_name}")
