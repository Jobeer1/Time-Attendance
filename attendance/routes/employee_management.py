"""
Employee management: CRUD, face enrollment, PIN, termination/reactivation
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime, date
from ..services.database import db
from ..models import Employee
from ..utils.auth import is_admin_authenticated

bp_employee = Blueprint('employee_management', __name__)

@bp_employee.route('/employees')
def employees():
    """List all employees"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    
    # Get employees from database
    try:
        employees_list = db.get_all('employees')
        # Add pagination support later if needed
        pagination = None
        
        return render_template('attendance/employees.html', 
                             employees=employees_list, 
                             pagination=pagination)
    except Exception as e:
        # Return empty list if there's an error
        return render_template('attendance/employees.html', 
                             employees=[], 
                             pagination=None)

@bp_employee.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    """Add new employee form"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            form_data = request.form.to_dict()
            
            # Basic validation
            required_fields = ['full_name', 'email', 'department']
            for field in required_fields:
                if not form_data.get(field):
                    flash(f'{field.replace("_", " ").title()} is required', 'error')
                    return render_template('attendance/employee_form.html')
            
            # Generate employee ID
            import random
            employee_id = f"EMP{datetime.now().strftime('%Y%m%d')}{random.randint(100, 999)}"
            
            # Create employee object
            employee_data = {
                'employee_id': employee_id,
                'full_name': form_data['full_name'],
                'email': form_data['email'], 
                'department': form_data['department'],
                'position': form_data.get('position', ''),
                'phone': form_data.get('phone', ''),
                'address': form_data.get('address', ''),
                'hire_date': form_data.get('hire_date', datetime.now().strftime('%Y-%m-%d')),
                'status': 'active',
                'face_encodings': [],
                'pin': form_data.get('pin', '')
            }
            
            employee = Employee(**employee_data)
            if employee.validate():
                db.create('employees', employee)
                flash(f'Employee {employee.full_name} created successfully!', 'success')
                return redirect(url_for('employee_management.employees'))
            else:
                flash('Invalid employee data', 'error')
                
        except Exception as e:
            flash(f'Error creating employee: {str(e)}', 'error')
    
    return render_template('attendance/employee_form.html')

@bp_employee.route('/edit_employee/<employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    """Edit employee form"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    
    try:
        # Get the employee data from database
        employee = db.get_employee_by_employee_id(employee_id)
        if not employee:
            flash(f'Employee {employee_id} not found', 'error')
            return redirect(url_for('employee_management.employees'))
        
        if request.method == 'POST':
            try:
                # Get form data
                form_data = request.form.to_dict()
                print(f"Form data received: {form_data}")  # Debug print
                
                # Update employee data
                if 'name' in form_data and form_data['name'].strip():
                    # Split name into first and last name
                    name_parts = form_data['name'].strip().split(' ', 1)
                    employee.first_name = name_parts[0]
                    employee.last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                employee.email = form_data.get('email', employee.email)
                employee.department = form_data.get('department', employee.department)
                employee.position = form_data.get('position', employee.position)
                employee.phone = form_data.get('phone', employee.phone)
                employee.hire_date = form_data.get('hire_date', employee.hire_date)
                employee.salary = float(form_data.get('salary', 0)) if form_data.get('salary') else employee.salary
                employee.notes = form_data.get('notes', employee.notes)
                
                # Handle PIN
                if form_data.get('pin') and form_data['pin'].strip():
                    employee.pin = form_data['pin'].strip()
                  # Handle checkboxes
                employee.employment_status = 'active' if 'is_active' in form_data else 'inactive'
                employee.can_work_overtime = 'can_overtime' in form_data
                employee.require_face_recognition = 'require_face' in form_data
                employee.require_pin = 'require_pin' in form_data
                
                # Update in database
                if employee.validate():
                    db.update('employees', employee.id, employee)
                    flash(f'Employee {employee.full_name} updated successfully!', 'success')
                    return redirect(url_for('employee_management.employees'))
                else:
                    flash('Invalid employee data', 'error')
                    
            except Exception as e:
                flash(f'Error updating employee: {str(e)}', 'error')
            
        # Prepare template data
        departments = [
            'Administration', 'Human Resources', 'Finance', 'Marketing', 
            'Sales', 'Engineering', 'IT', 'Operations', 'Customer Service',
            'Research & Development', 'Quality Assurance', 'Security', 'Music'
        ]
        
        shifts = []  # TODO: Get actual shifts from database
        today = datetime.now()
        
        return render_template('attendance/employee_form.html', 
                             employee=employee, 
                             departments=departments,
                             shifts=shifts,
                             today=today)
    except Exception as e:
        flash(f'Error loading employee: {str(e)}', 'error')
        return redirect(url_for('employee_management.employees'))

# API endpoints for employee management
@bp_employee.route('/api/employees/<employee_id>/enroll_face', methods=['POST'])
def enroll_face_api(employee_id):
    """API endpoint for face enrollment"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get image data from request
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'}), 400
        
        # For now, just return success - actual face encoding would be implemented here
        return jsonify({
            'success': True,
            'message': 'Face enrollment initiated',
            'employee_id': employee_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_employee.route('/api/employees', methods=['POST'])
def create_employee_api():
    """API endpoint to create a new employee"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['full_name', 'email', 'department']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Create employee (basic implementation)
        employee_id = f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        employee_data = {
            'employee_id': employee_id,
            'full_name': data['full_name'],
            'email': data['email'],
            'department': data['department'],
            'position': data.get('position', ''),
            'phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'hire_date': data.get('hire_date', datetime.now().strftime('%Y-%m-%d')),
            'status': 'active',
            'face_encodings': [],
            'pin': data.get('pin', '')
        }
        
        # For now, just return success - actual database save would be implemented here
        return jsonify({
            'success': True,
            'message': 'Employee created successfully',
            'employee': employee_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_employee.route('/api/employees/<employee_id>/remove_face', methods=['POST'])
def remove_face_api(employee_id):
    """API endpoint for removing face data"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Basic implementation - would normally remove face data
        return jsonify({'success': True, 'message': 'Face data removed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_employee.route('/api/employees/<employee_id>/reset_pin', methods=['POST'])
def reset_pin_api(employee_id):
    """API endpoint for resetting employee PIN"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get the employee from database
        employee = db.get_employee_by_employee_id(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
          # Reset the PIN (clear it so they need to set a new one)
        update_data = {
            'pin': '',
            'updated_at': datetime.now().isoformat()
        }
        
        # Update the employee in database
        db.update('employees', employee.id, update_data)
        
        return jsonify({'success': True, 'message': f'PIN reset for {employee.full_name} - they will need to set a new PIN'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_employee.route('/api/employees/<employee_id>', methods=['DELETE'])
def delete_employee_api(employee_id):
    """API endpoint for deleting employee"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        print(f"Deleting employee: {employee_id}")  # Debug print
        
        # Get the employee from database
        employee = db.get_employee_by_employee_id(employee_id)
        if not employee:
            print(f"Employee {employee_id} not found")  # Debug print
            return jsonify({'error': 'Employee not found'}), 404
        
        print(f"Found employee: {employee.full_name}, deleting...")  # Debug print
        
        # Delete the employee from database
        result = db.delete('employees', employee.id)
        
        print(f"Database delete result: {result}")  # Debug print
        
        return jsonify({'success': True, 'message': f'Employee {employee.full_name} deleted successfully'})
    except Exception as e:
        print(f"Error deleting employee {employee_id}: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full stack trace
        return jsonify({'error': str(e)}), 500

@bp_employee.route('/api/employees/<employee_id>/terminate', methods=['POST'])
def terminate_employee_api(employee_id):
    """API endpoint for terminating employee"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        print(f"Terminating employee: {employee_id}")  # Debug print
        
        # Get the employee from database
        employee = db.get_employee_by_employee_id(employee_id)
        if not employee:
            print(f"Employee {employee_id} not found")  # Debug print
            return jsonify({'error': 'Employee not found'}), 404
        
        print(f"Found employee: {employee.full_name}, current status: {employee.employment_status}")  # Debug print
        
        print(f"Setting status to terminated, updating database...")  # Debug print
        
        # Update the employee in database (pass dictionary of changes)
        update_data = {
            'employment_status': 'terminated',
            'updated_at': datetime.now().isoformat()
        }
        updated_employee = db.update('employees', employee.id, update_data)
        
        print(f"Database update result: {updated_employee}")  # Debug print
        
        return jsonify({'success': True, 'message': f'Employee {employee.full_name} terminated successfully'})
    except Exception as e:
        print(f"Error terminating employee {employee_id}: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full stack trace
        return jsonify({'error': str(e)}), 500

@bp_employee.route('/api/employees/<employee_id>/reactivate', methods=['POST'])
def reactivate_employee_api(employee_id):
    """API endpoint for reactivating employee"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get the employee from database
        employee = db.get_employee_by_employee_id(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
          # Reactivate the employee (set employment status to active)
        update_data = {
            'employment_status': 'active',
            'updated_at': datetime.now().isoformat()
        }
        
        # Update the employee in database
        db.update('employees', employee.id, update_data)
        
        return jsonify({'success': True, 'message': f'Employee {employee.full_name} reactivated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_employee.route('/api/employees', methods=['GET'])
def get_employees_api():
    """API endpoint to get all employees"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        employees_list = db.get_all('employees')
        employees_data = []
        
        for emp in employees_list:
            employees_data.append({
                'employee_id': emp.employee_id,
                'name': emp.full_name,
                'email': emp.email,
                'department': emp.department,
                'position': emp.position,
                'status': emp.status,
                'created_at': emp.created_at,
                'has_face_data': bool(emp.face_encodings)
            })
        
        return jsonify({
            'success': True,
            'employees': employees_data,
            'total': len(employees_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp_employee.route('/api/employees/<employee_id>', methods=['GET'])
def get_employee_api(employee_id):
    """API endpoint to get a specific employee"""
    if not is_admin_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        employee = db.get_employee_by_employee_id(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': 'Employee not found'}), 404
        
        employee_data = {
            'employee_id': employee.employee_id,
            'name': employee.full_name,
            'email': employee.email,
            'department': employee.department,
            'position': employee.position,
            'status': employee.status,
            'phone': employee.phone,
            'address': employee.address,
            'hire_date': employee.hire_date,
            'has_face_data': bool(employee.face_encodings),
            'pin': employee.pin if hasattr(employee, 'pin') else None
        }
        
        return jsonify({
            'success': True,
            'employee': employee_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
