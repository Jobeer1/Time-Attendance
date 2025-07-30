"""
Leave Management API Routes
South African BCEA compliant leave management system
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
from typing import Dict, List
import json

from models.leave_management import (
    LeaveManager, LeaveType, LeaveStatus, LeaveEntitlements, 
    LeaveCalculator, LeaveApplication, LeaveBalance
)

leave_bp = Blueprint('leave', __name__, url_prefix='/api/leave')

# Global leave manager instance
leave_manager = LeaveManager()

@leave_bp.route('/types', methods=['GET'])
def get_leave_types():
    """Get all available leave types with their configurations"""
    try:
        leave_types = []
        for leave_type, config in LeaveEntitlements.LEAVE_TYPES.items():
            leave_types.append({
                'type': leave_type.value,
                'name': config.name,
                'description': config.description,
                'is_paid': config.is_paid,
                'max_days_per_cycle': config.max_days_per_cycle,
                'cycle_months': config.cycle_months,
                'requires_proof': config.requires_proof,
                'proof_required_after_days': config.proof_required_after_days,
                'min_employment_months': config.min_employment_months,
                'notes': config.notes
            })
        
        return jsonify({
            'success': True,
            'leave_types': leave_types
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@leave_bp.route('/balance/<employee_id>', methods=['GET'])
def get_employee_leave_balance(employee_id: str):
    """Get leave balance for an employee"""
    try:
        # For demo purposes, calculate sample balances
        # In production, this would come from database
        
        employment_start_date = datetime(2023, 1, 1)  # Sample start date
        working_days_per_week = 5
        
        balances = []
        
        for leave_type in LeaveType:
            if LeaveCalculator.is_eligible_for_leave(leave_type, employment_start_date, working_days_per_week):
                config = LeaveEntitlements.LEAVE_TYPES[leave_type]
                
                # Calculate available days based on leave type
                if leave_type == LeaveType.ANNUAL:
                    available = LeaveCalculator.calculate_annual_leave_accrual(employment_start_date, working_days_per_week)
                elif leave_type == LeaveType.SICK:
                    available = LeaveCalculator.calculate_sick_leave_accrual(employment_start_date, working_days_per_week)
                else:
                    available = config.max_days_per_cycle
                
                # Sample used days (in production, this would be calculated from approved applications)
                used = 0
                if leave_type == LeaveType.ANNUAL:
                    used = 3.5  # Sample used annual leave
                elif leave_type == LeaveType.SICK:
                    used = 2.0  # Sample used sick leave
                
                balances.append({
                    'leave_type': leave_type.value,
                    'leave_name': config.name,
                    'available_days': available,
                    'used_days': used,
                    'remaining_days': available - used,
                    'is_paid': config.is_paid,
                    'cycle_months': config.cycle_months,
                    'notes': config.notes
                })
        
        return jsonify({
            'success': True,
            'employee_id': employee_id,
            'balances': balances
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@leave_bp.route('/apply', methods=['POST'])
def apply_for_leave():
    """Submit a leave application"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['employee_id', 'leave_type', 'start_date', 'end_date', 'reason'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        
        # Validate date range
        if start_date > end_date:
            return jsonify({
                'success': False,
                'error': 'Start date must be before end date'
            }), 400
        
        # Check if leave type is valid
        try:
            leave_type = LeaveType(data['leave_type'])
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid leave type'
            }), 400
        
        # Check eligibility
        employment_start_date = datetime(2023, 1, 1)  # Sample - would come from employee record
        if not LeaveCalculator.is_eligible_for_leave(leave_type, employment_start_date):
            return jsonify({
                'success': False,
                'error': 'Employee not eligible for this leave type'
            }), 400
        
        # Submit application
        application_id = leave_manager.apply_for_leave(
            employee_id=data['employee_id'],
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=data['reason'],
            proof_document=data.get('proof_document')
        )
        
        return jsonify({
            'success': True,
            'application_id': application_id,
            'message': 'Leave application submitted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@leave_bp.route('/applications/<employee_id>', methods=['GET'])
def get_employee_applications(employee_id: str):
    """Get all leave applications for an employee"""
    try:
        applications = leave_manager.get_employee_applications(employee_id)
        
        app_list = []
        for app in applications:
            app_list.append({
                'id': app.id,
                'leave_type': app.leave_type.value,
                'leave_name': LeaveEntitlements.LEAVE_TYPES[app.leave_type].name,
                'start_date': app.start_date.strftime('%Y-%m-%d'),
                'end_date': app.end_date.strftime('%Y-%m-%d'),
                'days_requested': app.days_requested,
                'reason': app.reason,
                'status': app.status.value,
                'applied_date': app.applied_date.strftime('%Y-%m-%d %H:%M'),
                'approved_date': app.approved_date.strftime('%Y-%m-%d %H:%M') if app.approved_date else None,
                'approved_by': app.approved_by,
                'rejection_reason': app.rejection_reason,
                'comments': app.comments
            })
        
        return jsonify({
            'success': True,
            'applications': app_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@leave_bp.route('/applications/pending', methods=['GET'])
def get_pending_applications():
    """Get all pending leave applications (for admin)"""
    try:
        applications = leave_manager.get_all_applications()
        app_list = []
        for app in applications:
            if app.get('status', 'PENDING').upper() == 'PENDING':
                app_list.append({
                    'id': app.get('id'),
                    'employee_id': app.get('employee_id'),
                    'leave_type': app.get('leave_type'),
                    'leave_name': app.get('leave_name', app.get('leave_type')),
                    'start_date': app.get('start_date'),
                    'end_date': app.get('end_date'),
                    'days_requested': app.get('days_requested'),
                    'reason': app.get('reason'),
                    'status': app.get('status'),
                    'applied_date': app.get('applied_date'),
                    'proof_document': app.get('proof_document'),
                })
        return jsonify({'applications': app_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/applications/<application_id>/approve', methods=['POST'])
def approve_leave_application(application_id: str):
    """Approve a leave application"""
    try:
        data = request.get_json()
        approved_by = data.get('approved_by', 'admin')
        comments = data.get('comments', '')
        
        success = leave_manager.approve_leave(application_id, approved_by, comments)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Leave application approved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to approve application (insufficient balance or invalid application)'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@leave_bp.route('/applications/<application_id>/reject', methods=['POST'])
def reject_leave_application(application_id: str):
    """Reject a leave application"""
    try:
        data = request.get_json()
        rejected_by = data.get('rejected_by', 'admin')
        rejection_reason = data.get('rejection_reason', 'No reason provided')
        
        success = leave_manager.reject_leave(application_id, rejected_by, rejection_reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Leave application rejected'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reject application (invalid application ID)'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@leave_bp.route('/eligibility/<employee_id>', methods=['GET'])
def check_leave_eligibility(employee_id: str):
    """Check employee eligibility for different leave types"""
    try:
        # Sample employment data - would come from database
        employment_start_date = datetime(2023, 1, 1)
        working_days_per_week = 5
        
        eligibility = []
        
        for leave_type in LeaveType:
            is_eligible = LeaveCalculator.is_eligible_for_leave(
                leave_type, employment_start_date, working_days_per_week
            )
            
            config = LeaveEntitlements.LEAVE_TYPES[leave_type]
            
            eligibility.append({
                'leave_type': leave_type.value,
                'leave_name': config.name,
                'is_eligible': is_eligible,
                'reason': 'Eligible' if is_eligible else f'Minimum {config.min_employment_months} months employment required'
            })
        
        return jsonify({
            'success': True,
            'employee_id': employee_id,
            'eligibility': eligibility
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@leave_bp.route('/applications', methods=['GET'])
def get_leave_applications():
    """Fetch leave applications for a given employee"""
    employee_id = request.args.get('employee_id')
    limit = request.args.get('limit', 5, type=int)

    if not employee_id:
        return jsonify({"error": "Employee ID is required"}), 400

    # Mock data for demonstration purposes
    leave_applications = [
        {"id": 1, "employee_id": employee_id, "type": "Sick Leave", "status": "Approved", "date": "2025-07-01"},
        {"id": 2, "employee_id": employee_id, "type": "Vacation", "status": "Pending", "date": "2025-07-10"}
    ]

    return jsonify(leave_applications[:limit])

@leave_bp.route('/applications/all', methods=['GET'])
def get_all_applications():
    """Get all leave applications for admin overview"""
    try:
        applications = leave_manager.get_all_applications()
        app_list = []
        for app in applications:
            app_list.append({
                'id': app.get('id'),
                'employee_id': app.get('employee_id'),
                'leave_type': app.get('leave_type'),
                'leave_name': app.get('leave_name', app.get('leave_type')),
                'start_date': app.get('start_date'),
                'end_date': app.get('end_date'),
                'days_requested': app.get('days_requested'),
                'reason': app.get('reason'),
                'status': app.get('status'),
                'applied_date': app.get('applied_date'),
                'approved_date': app.get('approved_date'),
                'approved_by': app.get('approved_by'),
                'rejection_reason': app.get('rejection_reason'),
                'proof_document': app.get('proof_document'),
            })
        return jsonify({'applications': app_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/api/leave/admin-leave', methods=['GET'])
def get_admin_leave_data():
    """API endpoint to fetch admin leave data."""
    try:
        # Fetch leave data from the leave manager
        leave_data = leave_manager.get_all_leave_requests()

        return jsonify({
            'success': True,
            'data': leave_data
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching admin leave data: {str(e)}'
        }), 500

@leave_bp.route('/applications/rejected', methods=['GET'])
def get_rejected_applications():
    """Get all rejected leave applications"""
    try:
        applications = leave_manager.get_all_leave_requests()

        # Filter rejected applications
        rejected_apps = [
            {
                'id': app['id'],
                'employee_id': app['employee_id'],
                'leave_type': app['leave_type'],
                'start_date': app['start_date'],
                'end_date': app['end_date'],
                'reason': app['reason'],
                'rejection_reason': app.get('rejection_reason', 'No reason provided')
            }
            for app in applications if app['status'] == 'rejected'
        ]

        return jsonify({
            'success': True,
            'data': rejected_apps
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@leave_bp.route('/applications/approved', methods=['GET'])
def get_approved_applications():
    """Get all approved leave applications"""
    try:
        applications = leave_manager.get_all_leave_requests()

        # Filter approved applications
        approved_apps = [
            {
                'id': app['id'],
                'employee_id': app['employee_id'],
                'leave_type': app['leave_type'],
                'start_date': app['start_date'],
                'end_date': app['end_date'],
                'reason': app['reason'],
                'approved_by': app.get('reviewed_by', 'admin'),
                'approved_date': app.get('reviewed_date', '')
            }
            for app in applications if app['status'] == 'approved'
        ]

        return jsonify({
            'success': True,
            'data': approved_apps
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Template routes for leave management interfaces
@leave_bp.route('/employee-leave', methods=['GET'])
def employee_leave_interface():
    """Employee leave management interface"""
    return render_template('attendance/employee_leave.html')

@leave_bp.route('/admin-leave', methods=['GET'])
def admin_leave_interface():
    """Admin leave management interface"""
    return render_template('attendance/admin_leave.html')

def register_leave_routes(app):
    """Register leave management routes with the Flask app"""
    app.register_blueprint(leave_bp)
    return leave_bp, leave_manager
